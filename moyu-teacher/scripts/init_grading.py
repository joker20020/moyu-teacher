#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评分记录初始化脚本（moyu-teacher 技能「作业评分官」角色配套工具）

在指定目录下创建一套结构固定的评分记录：题目与评分标准文档、grades.json
成绩数据骨架、反馈单与导出目录、原始作答留存目录。

用法:
    python init_grading.py --assignment "作业名" [--path 输出目录]
                           [--subject 科目] [--students "张三,李四"]
                           [--total 100] [--pass 60] [--date 2026-10-07]

示例:
    python init_grading.py --assignment "第三单元测验" --path . --subject 数学
    python init_grading.py --assignment "英语作文2" --students "张三,李四,王五"

说明:
    - 记录目录名为「评分记录-<作业名>」；若已存在则拒绝覆盖，保护已有成绩。
    - 所有文本文件以 UTF-8（无 BOM）、LF 换行写入；CSV 由 export_grades.py 生成（带 BOM）。
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

# Windows 与通用文件系统禁止出现在文件名/目录名中的字符
_INVALID_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
# 记录根目录名最大长度（作业名部分）
_MAX_NAME_LEN = 40


def sanitize_name(name: str) -> str:
    """把作业名清洗成可用于目录名的安全字符串。"""
    cleaned = _INVALID_CHARS.sub("", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        raise ValueError("清洗后的作业名为空，请使用有实际内容的作业名")
    if len(cleaned) > _MAX_NAME_LEN:
        cleaned = cleaned[:_MAX_NAME_LEN].rstrip(" .")
    return cleaned


def w(path: Path, content: str) -> None:
    """以 UTF-8 无 BOM、LF 换行写入文本文件。"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def split_students(raw: str):
    """解析逗号（中英文）分隔的学生名单，去空去重保序。"""
    if not raw:
        return []
    parts = re.split(r"[,，;；、\s]+", raw.strip())
    seen, result = set(), []
    for p in parts:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            result.append(p)
    return result


def build_files(assignment: str, subject: str, students, total: float,
                pass_score: float, today: str) -> dict:
    """返回 {相对路径: 文件内容} 映射。"""
    subject = subject or "（待填写）"

    readme = f"""# 评分记录：{assignment}

> 本目录是本次作业评分的**唯一权威记录**，由 moyu-teacher 技能「作业评分官」角色维护。
> 评分前先定标（00 文件）；分数只录入 grades.json；反馈与总表由脚本生成。

## 基本信息

| 项目 | 内容 |
|---|---|
| 作业名称 | {assignment} |
| 科目/班级 | {subject} |
| 作业日期 | {today} |
| 卷面满分 | {total:g} |
| 合格线 | {pass_score:g}（不设合格线请在 grades.json 置 null） |
| 评分标准版本 | v0.0（待 B2 定标后改为 v1.0） |
| 评分进度 | 0 / {len(students)} 已评（名单以 grades.json 为准） |

## 当前状态

- **下一步动作**：① 完整读取题目与全部作答 → ② 完成 `00-作业与评分标准.md`（定标）→
  ③ 批量作业先试评 1~3 份校准 → ④ 逐份评分录入 grades.json → ⑤ 运行 export_grades.py 导出
- **问题清单**（无法辨认/缺页/题目有误/疑似雷同等，随时追加，交付时同步给老师）：
  - （暂无）

## 目录导航

| 路径 | 作用 | 何时更新 |
|---|---|---|
| [00-作业与评分标准.md](00-作业与评分标准.md) | 题目、参考答案、采分点/量表、统一扣分口径、修订记录 | 定标与标准修订时 |
| [grades.json](grades.json) | 逐题成绩与证据（**唯一权威分数来源**） | 边评边录 |
| [01-成绩总表.md](01-成绩总表.md) | 脚本生成的成绩总表与统计 | 每次运行导出脚本 |
| [批改/](批改/) | 每人一份评分反馈单 | 导出骨架后补充评语 |
| [exports/](exports/) | 成绩总表 CSV、班级分析 | 导出/撰写时 |
| [原始作答/](原始作答/) | 原始作答文件副本，留存备查 | 接单时 |

## 评分红线速查

- 每一分都有采分点依据；部分给分必须能拆到具体采分点；
- 给分/扣分附学生作答原文证据；看不清标「无法辨认」，不猜字；
- 等价解法同等给分，错误不传导重复扣分；疑似违纪只标记、不裁决；
- 改分只改 grades.json 后重新导出，全程留痕。
"""

    rubric_doc = f"""# 作业与评分标准：{assignment}

> 评分的**唯一依据**。定标方法见技能 `references/grading-rubric.md`。
> 主观题评分标准须经试评校准/老师确认后再全量评分；每次修订在文末登记并回溯已评份数。

## 一、作业信息

| 项目 | 内容 |
|---|---|
| 科目/班级 | {subject} |
| 作业日期 | {today} |
| 满分 / 合格线 | {total:g} / {pass_score:g} |
| 等级划分 | 优秀 ≥90 ｜ 良好 ≥80 ｜ 合格 ≥{pass_score:g} ｜ 不合格 <{pass_score:g}（按老师确认结果修改 grades.json） |
| 迟交/补交规则 | （向老师确认；无规则不擅自扣分） |
| 题目来源 | （原始文件名/页码，便于追溯） |

## 二、题目与评分标准

> 逐题填写。题目全文照录或注明原始文件位置；多解题列出全部等价解法与可接受答案。
> 采分点分值之和必须等于该题满分；各题满分之和必须等于卷面满分 {total:g}。

### 第 1 题（满分 n 分）｜题型：客观/主观 ｜ 考查知识点：

- **题目**：
- **参考答案 / 可接受答案**：
- **采分点 / 量表**：

| 采分点 | 给分表现（学生写出/做出什么即给分） | 分值 |
|---|---|---|
| P1 | | |
| P2 | | |

- **常见错误扣法**：
- **等价解法/可接受表述**：

### 第 2 题（满分 n 分）｜题型： ｜ 考查知识点：

- **题目**：
- **参考答案**：
- **采分点 / 量表**：
- **常见错误扣法**：

## 三、统一扣分口径

- 笔误（方法正确、仅最后誊写/算术错）：只扣结果分，不重复扣过程分；
- 单位/有效数字：按处扣并设全卷上限（默认最多 2 分，以老师规定为准）；
- 错别字：非关键术语每 3 个扣 1 分、上限 2 分；改变术语含义按内容错处理；
- 错误不传导：前步错误、后步方法正确时，后步照常给分；
- 其他：（与老师确认后补充）

## 四、试评校准记录（批量作业）

| 试评对象 | 时间 | 发现的标准问题 | 处理（修订/维持） |
|---|---|---|---|
| | | | |

## 五、修订记录

| 日期 | 版本 | 修订内容 | 原因 | 已评份数是否回溯 |
|---|---|---|---|---|
| {today} | v0.0 | 建档，待制定评分标准 | — | — |
"""

    grade_boundaries = [
        {"grade": "优秀", "min": 90},
        {"grade": "良好", "min": 80},
        {"grade": "合格", "min": pass_score},
        {"grade": "不合格", "min": 0},
    ]
    grades = {
        "schema_version": 1,
        "assignment": {
            "name": assignment,
            "subject": subject if subject != "（待填写）" else "",
            "date": today,
            "total_score": total,
            "pass_score": pass_score,
            "grade_boundaries": grade_boundaries,
            "questions": [],
        },
        "students": [
            {
                "name": s,
                "student_id": "",
                "status": "pending",
                "items": [],
                "comment": "",
            }
            for s in students
        ],
    }
    grades_json = json.dumps(grades, ensure_ascii=False, indent=2) + "\n"

    feedback_readme = """# 评分反馈单（批改/）

- 命名：`评分反馈-<学生姓名>.md`，由 export_grades.py 的 --feedback 生成骨架；
- 骨架已填好成绩总览、逐题得分表与作答证据，评分官补写「亮点 / 问题与建议 / 总评」；
- 反馈单已存在时脚本默认跳过，避免覆盖已写评语；重生成需 --force-feedback（先备份）；
- 评语要求见技能 `references/grading-playbook.md` 第 7 节：具体、可执行、对事不对人。
"""

    exports_readme = """# 导出物（exports/）

- `成绩总表.csv`：export_grades.py 生成，UTF-8 带 BOM，Excel/WPS 可直接打开；
- `批次总评-<作业名>.md`、`讲解课教案-<作业名>.md`：
  export_grades.py --review-kit 生成数据骨架（批量作业 ≥3 人使用），评分官补全定性内容；
- 讲解课 PPT 不由脚本生成：教案定稿后按 `references/review-lesson-kit.md` 第 5 节
  整理需求简报，派发 ppt 技能（子 agent）制作，交付本地可编辑 `讲解课PPT-<作业名>.pptx`
  （用户要求时再出 PDF），文件路径回填教案；
- 写作标准见技能 `references/review-lesson-kit.md`，数据契约见 `references/grading-spec.md` 第 8 节。
"""

    originals_readme = """# 原始作答（原始作答/）

把学生原始作答文件复制或转换后存放在此，按学生命名（如 `张三-第三单元测验.pdf`），
评分证据以此为准；图片注意保留原始分辨率，必要时放大核对字迹。
"""

    return {
        "README.md": readme,
        "00-作业与评分标准.md": rubric_doc,
        "grades.json": grades_json,
        "批改/README.md": feedback_readme,
        "exports/README.md": exports_readme,
        "原始作答/README.md": originals_readme,
    }


def init_grading(assignment: str, base_path: Path, subject: str,
                 students, total: float, pass_score: float,
                 today: str = None) -> Path:
    safe_name = sanitize_name(assignment)
    record_dir = base_path.resolve() / f"评分记录-{safe_name}"

    if record_dir.exists():
        raise FileExistsError(f"评分记录已存在，拒绝覆盖：{record_dir}")

    today = today or date.today().isoformat()
    files = build_files(safe_name, subject, students, total, pass_score, today)

    record_dir.mkdir(parents=True)
    for rel_path, content in files.items():
        target = record_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        w(target, content)

    return record_dir


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="初始化 moyu-teacher 评分记录")
    parser.add_argument("--assignment", required=True, help="作业名称，如 '第三单元测验'")
    parser.add_argument("--path", default=".", help="记录输出目录，默认当前目录")
    parser.add_argument("--subject", default="", help="科目/班级（可选）")
    parser.add_argument("--students", default="", help="学生名单，逗号分隔（可选，可后补）")
    parser.add_argument("--total", type=float, default=100, help="卷面满分，默认 100")
    parser.add_argument("--pass", dest="pass_score", type=float, default=60,
                        help="合格线，默认 60")
    parser.add_argument("--date", default=None, help="作业日期 YYYY-MM-DD，默认今天")
    args = parser.parse_args()

    base = Path(args.path)
    if not base.exists():
        print(f"错误：输出目录不存在：{base}", file=sys.stderr)
        return 1
    if args.total <= 0:
        print("错误：卷面满分必须为正数。", file=sys.stderr)
        return 1
    if not 0 <= args.pass_score <= args.total:
        print("错误：合格线必须在 0 到卷面满分之间。", file=sys.stderr)
        return 1

    try:
        record_dir = init_grading(
            args.assignment, base, args.subject,
            split_students(args.students), args.total, args.pass_score,
            today=args.date,
        )
    except FileExistsError as e:
        print(f"错误：{e}", file=sys.stderr)
        print("如需重建，请先手动备份并改名/移除旧记录。", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1

    print(f"已创建评分记录：{record_dir}")
    print("下一步：① 读取题目与作答 → ② 完成 00-作业与评分标准.md 定标 → "
          "③ 在 grades.json 录入题目与逐题成绩 → ④ 运行 export_grades.py 导出。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
