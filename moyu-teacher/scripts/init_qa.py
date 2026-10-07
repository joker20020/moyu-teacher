#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
答疑记录初始化脚本（moyu-teacher 技能「解答助教」配套工具）

为一个具体问题生成一份答疑记录 Markdown（供学生课后复习），并在目录
README.md 索引表中登记一行。每个问题一份文件，不合并。

记录位置：
  - 传入 --archive <学习档案目录> 时：<档案>/答疑记录/YYYY-MM-DD-问题简述.md
  - 否则：<path>/答疑记录-<学生名>/  （未提供 --student 时为 <path>/答疑记录/）

用法:
    python init_qa.py --question "学生的原问题" [--student 姓名] [--subject 科目]
                      [--knowledge "知识点"] [--title "文件名简述"]
                      [--archive "学习档案-主题"] [--path .]

示例:
    python init_qa.py --question "为什么判别式小于0就没有实根？" --student 张三 --subject 数学
    python init_qa.py --question "闭包里的变量为什么不释放？" --archive "学习档案-Python基础"

说明:
    - 所有文件以 UTF-8（无 BOM）、LF 换行写入。
    - 同名文件不覆盖，自动追加 -2、-3 序号。
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_MAX_SLUG_LEN = 24


def sanitize(text: str, max_len: int = _MAX_SLUG_LEN) -> str:
    """清洗成可用于文件名/目录名的安全字符串。"""
    cleaned = _INVALID_CHARS.sub("", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        raise ValueError("清洗后的文本为空，请使用有实际内容的文字")
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip(" .，。、？?！!")
    return cleaned


def w(path: Path, content: str) -> None:
    """以 UTF-8 无 BOM、LF 换行写入文件。"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def index_readme() -> str:
    return """# 答疑记录

每个问题一份记录，命名 `YYYY-MM-DD-问题简述.md`，供学生课后复习。
本目录由 moyu-teacher 技能「解答助教」角色维护；记录规范见技能 `references/qa-playbook.md`。

## 索引

| 日期 | 问题 | 科目/知识点 | 学生 | 复习自测 |
|---|---|---|---|---|
"""


def record_content(today, question, student, subject, knowledge) -> str:
    student = student or "—"
    subject = subject or "—"
    knowledge = knowledge or "—"
    return f"""# 答疑记录：{question.splitlines()[0].strip()}

> 一问一份，供课后复习；解答紧扣原问、不过度引申。填写规范见技能 `references/qa-playbook.md`。

| 日期 | 学生 | 科目/章节 | 关联知识点 |
|---|---|---|---|
| {today} | {student} | {subject} | {knowledge} |

## 一、学生原问

> {question.strip()}

## 二、疑问定位

- 疑问类型：□ 概念辨析　□ 原理/为什么　□ 怎么做/步骤　□ 错在哪　□ 题意理解　□ 其他
- 学生已具备（默认不重复讲）：
- 真正卡住的一步：

## 三、解答

### 直接回答

（先给结论/答案，一两句）

### 关键说明

（最短必要的理由或步骤，配一个最小例子；不展开学生没问的内容）

### 易错提醒（可选）

（1~2 条，没有则删除本小节）

## 四、复习自测

- 合上书自问：（一个与本问同构的小问题）
- 答案要点：
- 关联资料：教材/笔记位置；相关错题或答疑：

## 五、跟进（按需）

- □ 当场已理解（复述/自测通过）
- □ 属系统知识缺口，建议转教学导师系统学习，缺口：
"""


def init_qa(question, student, subject, knowledge, title, archive, base_path) -> Path:
    question = (question or "").strip()
    if not question:
        raise ValueError("问题内容为空：--question 必须传入学生的原问题")

    today = date.today().isoformat()

    if archive:
        archive_dir = Path(archive)
        if not archive_dir.is_dir():
            raise FileNotFoundError(f"学习档案目录不存在：{archive_dir}")
        qa_dir = archive_dir / "答疑记录"
    else:
        folder = f"答疑记录-{sanitize(student, 20)}" if student else "答疑记录"
        qa_dir = Path(base_path) / folder

    qa_dir.mkdir(parents=True, exist_ok=True)

    readme = qa_dir / "README.md"
    if not readme.exists():
        w(readme, index_readme())

    slug = sanitize(title or question.splitlines()[0])
    stem = f"{today}-{slug}"
    target = qa_dir / f"{stem}.md"
    seq = 2
    while target.exists():
        target = qa_dir / f"{stem}-{seq}.md"
        seq += 1

    w(target, record_content(today, question, student, subject, knowledge))

    # 在索引表末尾登记一行（表格位于 README 末尾，直接追加）
    qtitle = question.splitlines()[0].strip()
    kp = " / ".join(x for x in (subject, knowledge) if x) or "—"
    row = f"| {today} | [{qtitle}]({target.name}) | {kp} | {student or '—'} | ⬜ |\n"
    with open(readme, "a", encoding="utf-8", newline="\n") as f:
        f.write(row)

    return target


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="生成一份答疑记录并登记索引")
    parser.add_argument("--question", required=True, help="学生的原问题（原话，可含标点）")
    parser.add_argument("--student", default="", help="学生姓名（可选）")
    parser.add_argument("--subject", default="", help="科目/章节（可选）")
    parser.add_argument("--knowledge", default="", help="关联知识点（可选）")
    parser.add_argument("--title", default="", help="自定义文件名简述（默认取问题首行）")
    parser.add_argument("--archive", default="", help="学习档案目录；提供则记录归入该档案的 答疑记录/")
    parser.add_argument("--path", default=".", help="无档案时的输出根目录，默认当前目录")
    args = parser.parse_args()

    base = Path(args.path)
    if not args.archive and not base.exists():
        print(f"错误：输出目录不存在：{base}", file=sys.stderr)
        return 1

    try:
        target = init_qa(args.question, args.student, args.subject,
                         args.knowledge, args.title, args.archive, args.path)
    except (ValueError, FileNotFoundError) as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1

    print(f"已生成答疑记录：{target}")
    print("下一步：按 references/qa-playbook.md 第 4 节补全疑问定位、解答与复习自测，并告知学生文件位置。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
