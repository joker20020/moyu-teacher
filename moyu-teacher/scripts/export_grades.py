#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成绩校验与导出脚本（moyu-teacher 技能「作业评分官」角色配套工具）

读取评分记录目录中的 grades.json，完成分数校验与总分重算，并导出：
  - 01-成绩总表.md（成绩明细 + 班级统计，UTF-8 无 BOM）
  - exports/成绩总表.csv（UTF-8 带 BOM，Excel/WPS 可直接打开）
  - 批改/评分反馈-<姓名>.md（--feedback 时生成骨架，已存在默认跳过）
  - exports/ 批次总评、讲解课教案（--review-kit 时生成数据骨架）；
    讲解课 PPT 不由本脚本生成，由 agent 整理需求后派发 ppt 技能制作，交付本地 .pptx/.pdf

用法:
    python export_grades.py <grades.json 路径> [--feedback] [--force-feedback]
                            [--review-kit] [--force-kit] [--strict]

退出码：
  0 成功（可能伴随警告）；1 存在硬错误（不产出任何文件）；--strict 下警告也按失败处理。
"""

import argparse
import csv
import json
import re
import statistics
import sys
from pathlib import Path

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
VALID_STATUS = {"graded", "pending", "absent", "exempt"}
STATUS_CN = {"graded": "已评", "pending": "待评", "absent": "缺考", "exempt": "免修"}
VALID_VERDICTS = {"正确", "部分正确", "错误", "未作答", "无法辨认"}
SUBJECTIVE = "subjective"


def fmt(num):
    """分数/百分比数字格式化：整数不带 .0，否则最多两位小数并去尾零。"""
    if num is None:
        return ""
    num = round(float(num), 2)
    if num == int(num):
        return str(int(num))
    return f"{num:.2f}".rstrip("0").rstrip(".")


def pct(ratio):
    """0.925 -> '92.5%'。"""
    if ratio is None:
        return ""
    v = round(ratio * 100, 1)
    if v == int(v):
        v = int(v)
    return f"{v}%"


def sanitize_filename(name: str) -> str:
    return _INVALID_CHARS.sub("_", name).strip() or "未命名"


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def load_and_validate(path: Path, rep: Report):
    """加载并校验 grades.json，返回 (data, questions, students_calc) 或 None。"""
    if not path.exists():
        rep.err(f"找不到 grades.json：{path}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        rep.err(f"grades.json 不是合法 JSON：{e}")
        return None

    assignment = data.get("assignment")
    questions = assignment.get("questions") if isinstance(assignment, dict) else None
    students = data.get("students")
    if not isinstance(assignment, dict):
        rep.err("缺少 assignment 对象")
        return None
    if not isinstance(questions, list) or not questions:
        rep.err("assignment.questions 为空：请先在 grades.json 录入题目（id/title/type/max_score）")
        return None
    if not isinstance(students, list):
        rep.err("缺少 students 数组")
        return None

    # 题目校验
    qids, qmap = [], {}
    sum_max = 0.0
    for i, q in enumerate(questions):
        loc = f"questions[{i}]"
        qid = str(q.get("id", "")).strip()
        if not qid:
            rep.err(f"{loc} 缺少 id")
            continue
        if qid in qmap:
            rep.err(f"题号重复：{qid}")
            continue
        max_score = q.get("max_score")
        if not isinstance(max_score, (int, float)) or max_score < 0:
            rep.err(f"第 {qid} 题 max_score 非法（需为 ≥0 的数字）：{max_score}")
            continue
        q.setdefault("title", "")
        q.setdefault("type", "subjective")
        q.setdefault("knowledge", "")
        if q["type"] not in ("objective", "subjective"):
            rep.warn(f"第 {qid} 题 type={q['type']} 非标准值，按主观题处理")
            q["type"] = "subjective"
        qids.append(qid)
        qmap[qid] = q
        sum_max += max_score

    total = assignment.get("total_score")
    if total is None:
        total = sum_max
        assignment["total_score"] = total
    elif not isinstance(total, (int, float)) or total <= 0:
        rep.err(f"total_score 非法：{total}")
    elif abs(total - sum_max) > 0.001:
        rep.warn(f"卷面满分 {fmt(total)} 与各题满分之和 {fmt(sum_max)} 不一致")

    pass_score = assignment.get("pass_score", 60)
    if pass_score is not None and (not isinstance(pass_score, (int, float))
                                   or not 0 <= pass_score <= total):
        rep.err(f"pass_score 非法：{pass_score}")
        pass_score = None

    boundaries = assignment.get("grade_boundaries") or []
    bnds = []
    for b in boundaries:
        if not isinstance(b, dict) or "grade" not in b or not isinstance(b.get("min"), (int, float)):
            rep.err(f"grade_boundaries 条目非法：{b}")
        else:
            bnds.append((str(b["grade"]), float(b["min"])))
    bnds.sort(key=lambda x: -x[1])

    # 学生校验与计算
    seen_names = set()
    calc = []
    for i, st in enumerate(students):
        if not isinstance(st, dict):
            rep.err(f"students[{i}] 不是对象")
            continue
        name = str(st.get("name", "")).strip()
        if not name:
            rep.err(f"students[{i}] 缺少姓名")
            continue
        if name in seen_names:
            rep.warn(f"学生姓名重复：{name}（请在姓名后加班级等区分）")
        seen_names.add(name)

        status = st.get("status", "graded")
        if status not in VALID_STATUS:
            rep.warn(f"{name} 的 status={status} 非标准值，按 pending 处理")
            status = "pending"
        st["status"] = status

        entry = {"name": name, "student_id": str(st.get("student_id", "") or ""),
                 "status": status, "items": {}, "raw": None, "delta": 0.0,
                 "adjustment_reason": "", "final": None, "rate": None,
                 "grade": "", "pass": "", "comment": str(st.get("comment", "") or "")}

        adj = st.get("adjustment")
        if adj is not None:
            if not isinstance(adj, dict) or not isinstance(adj.get("delta"), (int, float)):
                rep.err(f"{name} 的 adjustment 缺少数值型 delta")
            elif not str(adj.get("reason", "")).strip():
                rep.err(f"{name} 的 adjustment.delta={adj.get('delta')} 但缺少 reason")
            else:
                entry["delta"] = float(adj["delta"])
                entry["adjustment_reason"] = str(adj["reason"])

        items = st.get("items", [])
        if not isinstance(items, list):
            rep.err(f"{name} 的 items 不是数组")
            items = []
        for it in items:
            qid = str(it.get("qid", "")).strip()
            if qid not in qmap:
                rep.err(f"{name} 的作答引用了不存在的题号：{qid}")
                continue
            if qid in entry["items"]:
                rep.err(f"{name} 的第 {qid} 题录入了多条记录")
                continue
            score = it.get("score")
            if not isinstance(score, (int, float)):
                rep.err(f"{name} 第 {qid} 题 score 非法：{score}")
                continue
            mx = qmap[qid]["max_score"]
            if score < 0 or score > mx + 1e-9:
                rep.err(f"{name} 第 {qid} 题得分 {fmt(score)} 超出 [0, {fmt(mx)}]")
                continue
            verdict = str(it.get("verdict", "")).strip()
            if verdict and verdict not in VALID_VERDICTS:
                rep.warn(f"{name} 第 {qid} 题 verdict={verdict} 非标准取值")
            evidence = str(it.get("evidence", "") or "").strip()
            awarded = str(it.get("awarded", "") or "").strip()
            deductions = str(it.get("deductions", "") or "").strip()
            if not evidence:
                rep.warn(f"{name} 第 {qid} 题缺少 evidence（作答证据摘录）")
            if qmap[qid]["type"] == SUBJECTIVE and not (awarded or deductions):
                rep.warn(f"{name} 第 {qid} 题（主观题）缺少 awarded/deductions 采分点说明")
            entry["items"][qid] = {
                "score": float(score), "verdict": verdict or "—",
                "evidence": evidence, "awarded": awarded,
                "deductions": deductions,
                "note": str(it.get("note", "") or "").strip(),
            }

        if status == "graded":
            missing = [q for q in qids if q not in entry["items"]]
            if missing:
                rep.err(f"{name} 状态为 graded 但漏录题目：{', '.join(missing)}")
            else:
                raw = sum(entry["items"][q]["score"] for q in qids)
                final = raw + entry["delta"]
                if final < -1e-9 or final > total + 1e-9:
                    rep.err(f"{name} 最终总分 {fmt(final)} 超出 [0, {fmt(total)}]")
                entry["raw"] = round(raw, 2)
                entry["final"] = round(final, 2)
                entry["rate"] = final / total if total else None
                if pass_score is not None:
                    entry["pass"] = "是" if final >= pass_score else "否"
                else:
                    entry["pass"] = "—"
                for g, gmin in bnds:
                    if final >= gmin:
                        entry["grade"] = g
                        break
        calc.append(entry)

    pending = [e["name"] for e in calc if e["status"] == "pending"]
    if pending:
        rep.warn("以下学生尚未评完（status=pending）：" + "、".join(pending))
    if not any(e["status"] == "graded" for e in calc):
        rep.warn("没有任何 status=graded 的学生，统计与反馈单为空")

    return {"assignment": assignment, "questions": [qmap[q] for q in qids],
            "qids": qids, "total": total, "pass_score": pass_score,
            "boundaries": bnds, "entries": calc}


def compute_stats(d):
    """返回班级统计字典（仅统计 graded 学生）。"""
    qids, questions = d["qids"], d["questions"]
    graded = [e for e in d["entries"] if e["status"] == "graded"]
    stats = {"n": len(d["entries"]), "graded": len(graded),
             "pending": sum(1 for e in d["entries"] if e["status"] == "pending"),
             "absent": sum(1 for e in d["entries"] if e["status"] == "absent"),
             "exempt": sum(1 for e in d["entries"] if e["status"] == "exempt")}
    if not graded:
        stats["per_question"] = []
        return stats
    finals = [e["final"] for e in graded]
    stats.update({
        "avg": round(statistics.mean(finals), 1),
        "median": round(statistics.median(finals), 1),
        "max": max(finals), "min": min(finals),
    })
    if d["pass_score"] is not None:
        passed = sum(1 for e in graded if e["pass"] == "是")
        stats["pass_rate"] = passed / len(graded)
    if d["boundaries"]:
        stats["grade_dist"] = {g: sum(1 for e in graded if e["grade"] == g)
                               for g, _ in d["boundaries"]}
    pq = []
    for qid, q in zip(qids, questions):
        scores = [e["items"][qid]["score"] for e in graded]
        avg = round(statistics.mean(scores), 2)
        pq.append({"qid": qid, "title": q["title"], "max": q["max_score"],
                   "avg": avg, "rate": (avg / q["max_score"]) if q["max_score"] else None,
                   "knowledge": q.get("knowledge", "")})
    stats["per_question"] = pq
    return stats


def write_markdown(d, stats, out: Path):
    a = d["assignment"]
    lines = []
    lines.append(f"# 成绩总表：{a.get('name', '')}")
    lines.append("")
    lines.append(f"- 科目/班级：{a.get('subject') or '—'} ｜ 作业日期：{a.get('date', '—')}")
    lines.append(f"- 满分：{fmt(d['total'])} ｜ 合格线：{fmt(d['pass_score']) if d['pass_score'] is not None else '不设'}"
                 f" ｜ 应评：{stats['n']} ｜ 已评：{stats['graded']}"
                 f" ｜ 待评：{stats['pending']} ｜ 缺考：{stats['absent']} ｜ 免修：{stats['exempt']}")
    lines.append("")
    header = ["学号", "姓名", "状态"] + [f"第{q}题({fmt(m['max_score'])})"
                                        for q, m in zip(d["qids"], d["questions"])]
    header += ["调整", "总分", "得分率", "等级", "合格"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    for e in d["entries"]:
        if e["status"] == "graded":
            row = [e["student_id"] or "—", e["name"], STATUS_CN[e["status"]]]
            row += [fmt(e["items"][q]["score"]) for q in d["qids"]]
            row += [fmt(e["delta"]) if e["delta"] else "—", fmt(e["final"]),
                    pct(e["rate"]), e["grade"] or "—", e["pass"]]
        else:
            row = [e["student_id"] or "—", e["name"], STATUS_CN[e["status"]]]
            row += [""] * (len(d["qids"]) + 5)
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    lines.append("")

    if stats["graded"]:
        lines.append("## 班级统计（仅含已评学生）")
        lines.append("")
        lines.append(f"- 平均分：{fmt(stats['avg'])} ｜ 中位数：{fmt(stats['median'])} "
                     f"｜ 最高：{fmt(stats['max'])} ｜ 最低：{fmt(stats['min'])}")
        if "pass_rate" in stats:
            lines.append(f"- 合格率：{pct(stats['pass_rate'])}（按合格线 {fmt(d['pass_score'])}）")
        if "grade_dist" in stats:
            dist = " ｜ ".join(f"{g} {n} 人" for g, n in stats["grade_dist"].items())
            lines.append(f"- 等级分布：{dist}")
        lines.append("")
        lines.append("### 逐题得分率")
        lines.append("")
        lines.append("| 题号 | 题目 | 考查知识点 | 满分 | 平均得分 | 得分率 |")
        lines.append("|---|---|---|---|---|---|")
        for p in stats["per_question"]:
            flag = " ⚠️ 重点讲评" if p["rate"] is not None and p["rate"] < 0.6 else ""
            lines.append(f"| {p['qid']} | {p['title']} | {p['knowledge'] or '—'} "
                         f"| {fmt(p['max'])} | {fmt(p['avg'])} | {pct(p['rate'])}{flag} |")
        lines.append("")
    lines.append("> 本表由 export_grades.py 依据 grades.json 自动生成，请勿手改；"
                 "改分请修改 grades.json 后重新导出。")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_csv(d, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        header = ["学号", "姓名", "状态"] + [f"第{q}题(满分{m['max_score']})"
                                            for q, m in zip(d["qids"], d["questions"])]
        header += ["调整分", "调整原因", "总分", "得分率", "等级", "是否合格", "总评"]
        writer.writerow(header)
        for e in d["entries"]:
            if e["status"] == "graded":
                row = [e["student_id"], e["name"], STATUS_CN[e["status"]]]
                row += [fmt(e["items"][q]["score"]) for q in d["qids"]]
                row += [fmt(e["delta"]) if e["delta"] else "", e["adjustment_reason"],
                        fmt(e["final"]), pct(e["rate"]), e["grade"], e["pass"],
                        e["comment"]]
            else:
                row = [e["student_id"], e["name"], STATUS_CN[e["status"]]]
                row += [""] * (len(d["qids"]) + 8)
            writer.writerow(row)


def write_feedback(feedback_dir: Path, force_flag: bool, d):
    a = d["assignment"]
    written, skipped = [], []
    for e in d["entries"]:
        if e["status"] != "graded":
            continue
        path = feedback_dir / f"评分反馈-{sanitize_filename(e['name'])}.md"
        if path.exists() and not force_flag:
            skipped.append(e["name"])
            continue
        L = []
        L.append(f"# 评分反馈：{a.get('name', '')} · {e['name']}")
        L.append("")
        L.append(f"- 学号：{e['student_id'] or '—'} ｜ 科目/班级：{a.get('subject') or '—'} "
                 f"｜ 评分日期：{a.get('date', '—')}")
        L.append("- 评分依据：00-作业与评分标准.md（注明版本号）")
        L.append(f"- **总分：{fmt(e['final'])} / {fmt(d['total'])} ｜ 得分率：{pct(e['rate'])} "
                 f"｜ 等级：{e['grade'] or '—'} ｜ 是否合格：{e['pass']}**")
        if e["delta"]:
            L.append(f"- 卷面调整：{fmt(e['delta'])}（{e['adjustment_reason']}）")
        L.append("")
        L.append("## 逐题得分")
        L.append("")
        L.append("| 题号 | 题目 | 满分 | 得分 | 判定 | 考查知识点 |")
        L.append("|---|---|---|---|---|---|")
        for qid, q in zip(d["qids"], d["questions"]):
            it = e["items"][qid]
            L.append(f"| {qid} | {q['title']} | {fmt(q['max_score'])} | {fmt(it['score'])} "
                     f"| {it['verdict']} | {q.get('knowledge', '') or '—'} |")
        L.append("")
        L.append("## 逐题详评")
        L.append("")
        for qid, q in zip(d["qids"], d["questions"]):
            it = e["items"][qid]
            L.append(f"### 第 {qid} 题（{fmt(it['score'])} / {fmt(q['max_score'])}）· {it['verdict']}")
            L.append("")
            L.append(f"- **学生作答**：{it['evidence'] or '（待补充证据摘录）'}")
            if it["awarded"]:
                L.append(f"- **给分点**：{it['awarded']}")
            if it["deductions"]:
                L.append(f"- **扣分说明**：{it['deductions']}")
            if it["note"]:
                L.append(f"- **备注**：{it['note']}")
            L.append("- **订正指引**：（评分官补充：回到哪个知识点、正确思路、怎么练）")
            L.append("")
        L.append("## 亮点")
        L.append("")
        L.append("（评分官补充：具体到题/步骤的肯定，至少 1 条）")
        L.append("")
        L.append("## 主要问题与改进建议（按优先级，2~4 条）")
        L.append("")
        L.append("1. （问题表现 → 错因归类：概念/方法/审题/计算/表达 → 下一步具体动作）")
        L.append("")
        L.append("## 总评")
        L.append("")
        L.append(e["comment"] or "（评分官补充：一段话水平定位 + 鼓励 + 下一阶段重点）")
        L.append("")
        L.append("---")
        L.append("如对评分有疑问，请在老师规定时限内注明题号申请复核。")
        L.append("")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(L), encoding="utf-8", newline="\n")
        written.append(e["name"])
    if written:
        print("已生成反馈单：" + "、".join(written))
    if skipped:
        print("反馈单已存在而跳过（如需覆盖加 --force-feedback）：" + "、".join(skipped))


def priority_of(rate):
    """按逐题得分率给出讲题优先级。"""
    if rate is None:
        return "🟢 略讲/个别辅导"
    if rate < 0.6:
        return "🔴 必讲"
    if rate < 0.8:
        return "🟡 选讲"
    return "🟢 略讲/个别辅导"


def typical_errors(entries, qid, limit=3):
    """从 grades 记录中摘取某题未满分学生的匿名错误样本。"""
    samples = []
    seq = 0
    for e in entries:
        if e["status"] != "graded" or qid not in e["items"]:
            continue
        it = e["items"][qid]
        if it["verdict"] == "正确" and not it["deductions"]:
            continue
        seq += 1
        if it["deductions"]:
            line = (f"  - 样本{seq}（{it['verdict']}，得 {fmt(it['score'])} 分）：{it['deductions']}"
                    f"｜作答摘录：{it['evidence'] or '（无）'}")
        else:
            line = f"  - 样本{seq}（{it['verdict']}，得 {fmt(it['score'])} 分）：{it['evidence'] or '（缺证据描述）'}"
        samples.append(line)
        if seq >= limit:
            break
    return samples


def write_review_kit(d, stats, exports_dir: Path, force_flag: bool):
    """生成批次总评、讲解课教案两份骨架（数据预填，定性留空）。"""
    a = d["assignment"]
    name = a.get("name", "")
    date_ = a.get("date", "—")
    subject = a.get("subject") or "—"
    total = d["total"]
    pq = stats.get("per_question", [])
    graded = [e for e in d["entries"] if e["status"] == "graded"]
    must = [p for p in pq if p["rate"] is not None and p["rate"] < 0.6]
    select = [p for p in pq if p["rate"] is not None and 0.6 <= p["rate"] < 0.8]
    brief = [p for p in pq if p["rate"] is not None and p["rate"] >= 0.8]

    # ---------- 批次总评 ----------
    bands = [("优秀 [90%~100%]", 0.9, 0), ("良好 [80%~90%)", 0.8, 0),
             ("中等 [70%~80%)", 0.7, 0), ("合格 [60%~70%)", 0.6, 0),
             ("不合格 (<60%)", -1, 0)]
    for e in graded:
        r = e["rate"]
        if r >= 0.9:
            bands[0] = (bands[0][0], 0.9, bands[0][2] + 1)
        elif r >= 0.8:
            bands[1] = (bands[1][0], 0.8, bands[1][2] + 1)
        elif r >= 0.7:
            bands[2] = (bands[2][0], 0.7, bands[2][2] + 1)
        elif r >= 0.6:
            bands[3] = (bands[3][0], 0.6, bands[3][2] + 1)
        else:
            bands[4] = (bands[4][0], -1, bands[4][2] + 1)

    L = []
    L.append(f"# 批次总评：{name}（{date_}）")
    L.append("")
    L.append("> 统计数据由脚本预填（与 01-成绩总表.md 同源，请勿手改）；")
    L.append("> 定性结论由评分官依据 grades.json 逐题证据补全，不写无数据支撑的判断。")
    L.append("")
    L.append("## 一、基本数据")
    L.append("")
    L.append(f"- 应评 {stats['n']} ｜ 已评 {stats['graded']} ｜ 待评 {stats['pending']} "
             f"｜ 缺考 {stats['absent']} ｜ 免修 {stats['exempt']}")
    if graded:
        L.append(f"- 平均分 {fmt(stats['avg'])} ｜ 中位数 {fmt(stats['median'])} "
                 f"｜ 最高 {fmt(stats['max'])} ｜ 最低 {fmt(stats['min'])} "
                 f"｜ 合格率 {pct(stats.get('pass_rate'))}")
    L.append("")
    L.append("### 分数段分布（占满分比例）")
    L.append("")
    L.append("| 分数段 | 人数 |")
    L.append("|---|---|")
    for label, _, cnt in bands:
        L.append(f"| {label} | {cnt} |")
    L.append("")
    if stats.get("grade_dist"):
        L.append("### 等级分布")
        L.append("")
        L.append("| 等级 | 人数 |")
        L.append("|---|---|")
        for g, cnt in stats["grade_dist"].items():
            L.append(f"| {g} | {cnt} |")
        L.append("")
    L.append("### 逐题得分率与讲题优先级")
    L.append("")
    L.append("| 题号 | 题目 | 考查知识点 | 满分 | 均分 | 得分率 | 优先级 |")
    L.append("|---|---|---|---|---|---|---|")
    for p in pq:
        L.append(f"| {p['qid']} | {p['title']} | {p['knowledge'] or '—'} "
                 f"| {fmt(p['max'])} | {fmt(p['avg'])} | {pct(p['rate'])} | {priority_of(p['rate'])} |")
    L.append("")
    L.append("## 二、总体评价")
    L.append("")
    L.append("### 1. 整体达成度（2~3 句：对照作业目标与合格线，引用上面数据说明是否达成预期）")
    L.append("")
    L.append("### 2. 班级亮点（具体到题号与好解法，至少 1 条）")
    L.append("")
    L.append("### 3. 分层情况（头部/中部/薄弱占比与表现，不公开排名）")
    L.append("")
    L.append("## 三、主要问题点（按影响面排序，3~5 个；按错因归并而非简单按题号罗列）")
    L.append("")
    for i, p in enumerate(must[:4] or pq[:2], 1):
        L.append(f"### 问题 {i}：{p['title']}（第 {p['qid']} 题，得分率 {pct(p['rate'])}）")
        L.append("")
        L.append(f"- **问题表现**：第 {p['qid']} 题满分 {fmt(p['max'])}、均分 {fmt(p['avg'])}，"
                 f"考查「{p['knowledge'] or '—'}」；失分人数与比例（从总表核对补充）")
        L.append("- **典型证据（匿名）**：")
        for s in typical_errors(d["entries"], p["qid"]):
            L.append(s)
        L.append("- **错因归类**：□概念不清 □方法不会 □审题失误 □计算/操作失误 "
                 "□表达规范 □知识遗忘 □时间管理")
        L.append("- **根源判断**：□教学未到位 □题目偏难/超纲/歧义 □前置知识缺口 □训练量不足")
        L.append("")
    L.append("## 四、改进方向（可执行、有时限、分层）")
    L.append("")
    L.append("### 1. 教学侧（讲评课重点、需补讲知识点、教法调整、再测安排）")
    L.append("")
    L.append("### 2. 学生侧（共性订正要求；分层任务：保底/熟练/拓展）")
    L.append("")
    L.append("### 3. 个别辅导名单（教师掌握，不公开点名：学生 × 对应知识点）")
    L.append("")
    L.append("### 4. 时间节点（讲评日期 / 变式练习日期 / 复测日期，写具体日历日）")
    L.append("")
    L.append("## 五、后续衔接")
    L.append("")
    L.append(f"- 习题讲解课：见 `讲解课教案-{name}.md`；讲解课 PPT 由 ppt 技能按需求简报制作，交付本地 `讲解课PPT-{name}.pptx`（或 PDF，见 review-lesson-kit 第 5 节），文件路径回填教案")
    L.append("- 学习档案：错题入错题本、知识点等级按证据更新台账、补讲与再测进学习计划")
    L.append("")
    total_review = exports_dir / f"批次总评-{sanitize_filename(name)}.md"

    # ---------- 讲解课教案 ----------
    L2 = []
    L2.append(f"# 习题讲解课教案：{name}")
    L2.append("")
    L2.append("## 一、基本信息")
    L2.append("")
    L2.append("| 项目 | 内容 |")
    L2.append("|---|---|")
    L2.append(f"| 授课对象 | {subject}（班级补填） |")
    L2.append("| 课型 | 习题讲评课 |")
    L2.append("| 课时 | 45 分钟（必讲题多时拆 2 课时） |")
    L2.append(f"| 授课日期 | （填写） ｜ 数据依据：{date_} 作业成绩 |")
    L2.append("")
    L2.append("## 二、学情依据（脚本预填，数字勿改）")
    L2.append("")
    if graded:
        L2.append(f"- 已评 {stats['graded']} 人：平均 {fmt(stats['avg'])}、中位 {fmt(stats['median'])}、"
                  f"最高 {fmt(stats['max'])}、最低 {fmt(stats['min'])}、合格率 {pct(stats.get('pass_rate'))}")
    L2.append("- 讲解层级：🔴 必讲（得分率 <60%）｜ 🟡 选讲（60%~80%）｜ 🟢 略讲/个别辅导（≥80%）")
    L2.append("")
    L2.append("| 题号 | 题目 | 考查知识点 | 满分 | 均分 | 得分率 | 层级 |")
    L2.append("|---|---|---|---|---|---|---|")
    for p in pq:
        L2.append(f"| {p['qid']} | {p['title']} | {p['knowledge'] or '—'} "
                  f"| {fmt(p['max'])} | {fmt(p['avg'])} | {pct(p['rate'])} | {priority_of(p['rate'])} |")
    L2.append("")
    L2.append("## 三、教学目标（围绕必讲题知识点补全；必须可检验，如：课后变式正确率 ≥80%）")
    L2.append("")
    for i, p in enumerate(must, 1):
        L2.append(f"{i}. 知识/能力目标：纠正「{p['knowledge'] or p['title']}」的典型错误，"
                  f"能独立完成同构变式题（对应第 {p['qid']} 题）")
    L2.append(f"{len(must) + 1}. 规范/习惯目标：（按问题点补全，如：写检验、带单位、审题圈画）")
    L2.append("")
    L2.append("## 四、教学重点与难点")
    L2.append("")
    L2.append(f"- 重点：{('、'.join('第' + p['qid'] + '题' for p in must) or '（按实际补全）')}")
    L2.append("- 难点：（错因根源，如概念辨析/建模转化/步骤跳跃，补全）")
    L2.append("")
    L2.append("## 五、教学过程")
    L2.append("")
    L2.append("| 环节 | 时长 | 教师活动 | 学生活动 | 设计意图 |")
    L2.append("|---|---|---|---|---|")
    L2.append("| 数据反馈·自评 | 5′ | 公布分布与亮点，发回作业 | 自标「会而做错/真不会」 | 区分错因、主动回忆 |")
    for p in must:
        L2.append(f"| 错题精讲：第 {p['qid']} 题 | 8′ | 呈现匿名典型错误→问题串诊断→推导正解→提炼方法 "
                  f"| 找错、回答、复述方法 | 纠错归因（{p['knowledge'] or ''}） |")
        L2.append(f"| 变式验证：第 {p['qid']} 题 | 3′ | 出示同构变式题 | 闭卷独立完成、同桌互批 | 行为证据验证 |")
    L2.append("| 综合变式巩固 | 8′ | 2 道混合变式（覆盖多个必讲点） | 独立完成、展示思路 | 迁移 |")
    L2.append("| 小结·分层作业 | 5′ | 引导归纳「防错清单」 | 说收获、记作业 | 费曼输出 |")
    teach_minutes = 5 + 11 * len(must) + 8 + 5
    if teach_minutes > 45:
        L2.append("")
        L2.append(f"> ⚠️ 上表合计约 {teach_minutes} 分钟，超出 45 分钟：请只保留错误最集中的 2~3 题，"
                  "其余转为个别辅导或拆为 2 课时。")
    L2.append("")
    L2.append("## 六、逐题精讲脚本（每个 🔴必讲/🟡选讲 题一份）")
    L2.append("")
    for p in must + select:
        L2.append(f"### 第 {p['qid']} 题（得分率 {pct(p['rate'])}，{priority_of(p['rate'])}）")
        L2.append("")
        L2.append(f"- **题面**：（补全，考查「{p['knowledge'] or '—'}」，满分 {fmt(p['max'])}）")
        L2.append("- **典型错误（脚本自 grades.json 匿名摘录；课堂展示前再次确认脱敏）**：")
        errs = typical_errors(d["entries"], p["qid"])
        L2.extend(errs if errs else ["  - （无未满分样本，补全其他来源）"])
        L2.append("- **错因诊断问题串**：")
        L2.append("  1. 这位同学第一步做了什么？题目条件都用上了吗？")
        L2.append("  2. 错在哪一步？当时可能怎么想的？")
        L2.append("  3. 正确做法与它的关键区别是什么？")
        L2.append("- **正确思路推导**：（板书关键步骤，留白让学生补）")
        L2.append("- **方法提炼（一句话规则/步骤卡）**：")
        L2.append("- **变式题**：（同构换情境，难度相当；附答案与采分点）")
        L2.append("- **预设与对策**：（仍答错时回退到哪一级提示，见 teaching-playbook 第 5 节）")
        L2.append("")
    L2.append("## 七、板书 / 课件")
    L2.append("")
    L2.append("- 板书分区：左=错因诊断，中=正确方法，右=变式")
    L2.append("- 讲解课 PPT：由 ppt 技能按 review-lesson-kit 第 5 节需求简报制作，交付本地可编辑 `.pptx`（用户要求时再出 PDF），本技能不生成固定 PPT 文件")
    L2.append("- PPT 文件路径：`../exports/讲解课PPT-" + name + ".pptx`（制作并验收后回填实际路径）")
    L2.append("")
    L2.append("## 八、分层作业")
    L2.append("")
    L2.append("- 全体：错题订正（写错因 + 正确过程）＋ 变式题组（覆盖必讲点）")
    L2.append("- 薄弱学生（名单见批次总评，不公开）：补前置知识 ＋ 基础题")
    L2.append("- 学有余力：拓展/综合题 1~2 道")
    L2.append("")
    L2.append("## 九、教学反思（课后填写）")
    L2.append("")
    L2.append("- 当堂变式正确率： ｜ 仍未解决的问题： ｜ 再测日期与对比结果：")
    L2.append("")
    lesson_plan = exports_dir / f"讲解课教案-{sanitize_filename(name)}.md"

    # 注：讲解课 PPT 不由此脚本生成固定文件；agent 补全教案后，按
    # references/review-lesson-kit.md 第 5 节整理需求简报，派发 ppt 技能/子 agent
    # 制作并导出本地 .pptx（或 PDF）到 exports/。

    outputs = [total_review, lesson_plan]
    contents = [L, L2]
    written, skipped = [], []
    for path, lines in zip(outputs, contents):
        if path.exists() and not force_flag:
            skipped.append(path.name)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        written.append(path.name)
    return written, skipped


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="校验 grades.json 并导出成绩总表与评分反馈单")
    parser.add_argument("grades_json", help="grades.json 的路径")
    parser.add_argument("--feedback", action="store_true", help="同时生成每人评分反馈单骨架")
    parser.add_argument("--force-feedback", action="store_true",
                        help="覆盖已存在的反馈单（默认跳过以保护已写评语）")
    parser.add_argument("--review-kit", action="store_true",
                        help="同时生成批次总评、讲解课教案两份骨架到 exports/")
    parser.add_argument("--force-kit", action="store_true",
                        help="覆盖已存在的讲评产出骨架（默认跳过以保护已补全内容）")
    parser.add_argument("--strict", action="store_true", help="警告也按失败处理")
    args = parser.parse_args()

    json_path = Path(args.grades_json).resolve()
    record_dir = json_path.parent
    rep = Report()
    d = load_and_validate(json_path, rep)

    if d is None or rep.errors:
        print("校验未通过，未导出任何文件：", file=sys.stderr)
        for m in rep.errors:
            print(f"  [错误] {m}", file=sys.stderr)
        for m in rep.warnings:
            print(f"  [警告] {m}", file=sys.stderr)
        return 1

    if rep.warnings and args.strict:
        print("strict 模式：存在警告，未导出任何文件：", file=sys.stderr)
        for m in rep.warnings:
            print(f"  [警告] {m}", file=sys.stderr)
        return 1

    stats = compute_stats(d)
    write_markdown(d, stats, record_dir / "01-成绩总表.md")
    write_csv(d, record_dir / "exports" / "成绩总表.csv")
    if args.feedback:
        write_feedback(record_dir / "批改", args.force_feedback, d)
    if args.review_kit:
        if stats["graded"]:
            written, skipped = write_review_kit(d, stats, record_dir / "exports", args.force_kit)
            print("已生成讲评骨架：" + "、".join(written))
            if skipped:
                print("讲评骨架已存在而跳过（如需覆盖加 --force-kit）：" + "、".join(skipped))
        else:
            print("没有已评学生，跳过讲评产出骨架。")

    print(f"已导出：{record_dir / '01-成绩总表.md'}")
    print(f"已导出：{record_dir / 'exports' / '成绩总表.csv'}")
    if stats["graded"]:
        print(f"已评 {stats['graded']} 人 ｜ 平均 {fmt(stats['avg'])} ｜ "
              f"中位 {fmt(stats['median'])} ｜ 最高 {fmt(stats['max'])} ｜ 最低 {fmt(stats['min'])}", )
        if "pass_rate" in stats:
            print(f"合格率 {pct(stats['pass_rate'])}")
        weak = [p["qid"] for p in stats["per_question"] if p["rate"] is not None and p["rate"] < 0.6]
        if weak:
            print("得分率 <60% 的重点讲评分：" + "、".join(weak))
    for m in rep.warnings:
        print(f"  [警告] {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
