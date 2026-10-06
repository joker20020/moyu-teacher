#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习档案初始化脚本（interactive-tutor 技能配套工具）

在指定目录下创建一套结构固定的 Markdown 学习档案，用于跨会话记录
教学过程、掌握度状态和产出文档。

用法:
    python init_archive.py --topic "学习主题" [--path 输出目录]
                           [--goal "学习目标"] [--level "学习者基础"]

示例:
    python init_archive.py --topic "Python 基础" --path .
    python init_archive.py --topic "线性代数-矩阵" --goal "通过期末" --level "零基础"

说明:
    - 档案目录名为「学习档案-<主题>」；若已存在则拒绝覆盖，保护已有记录。
    - 所有文件以 UTF-8（无 BOM）、LF 换行写入。
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

# Windows 与通用文件系统禁止出现在文件名/目录名中的字符
_INVALID_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
# 档案根目录名最大长度（主题部分）
_MAX_TOPIC_LEN = 40


def sanitize_topic(topic: str) -> str:
    """把学习主题清洗成可用于目录名的安全字符串。"""
    cleaned = _INVALID_CHARS.sub("", topic)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        raise ValueError("清洗后的主题名为空，请使用有实际内容的主题名")
    if len(cleaned) > _MAX_TOPIC_LEN:
        cleaned = cleaned[:_MAX_TOPIC_LEN].rstrip(" .")
    return cleaned


def w(path: Path, content: str) -> None:
    """以 UTF-8 无 BOM、LF 换行写入文件。"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def build_files(topic: str, goal: str, level: str, today: str) -> dict:
    """返回 {相对路径: 文件内容} 映射。"""
    goal = goal or "（备课阶段补充：用可检验的行为描述学完后能做什么）"
    level = level or "（待课前诊断后填写）"

    readme = f"""# 学习档案：{topic}

> 本档案是该主题学习进度的**唯一权威记录**，由 interactive-tutor 技能维护。
> 每次学习开始前先读本文件与掌握度台账；每次学习结束后立即更新。

## 基本信息

| 项目 | 内容 |
|---|---|
| 学习主题 | {topic} |
| 学习目标 | {goal} |
| 学习者基础 | {level} |
| 创建日期 | {today} |
| 最近学习 | 尚未开始 |
| 当前进度 | 0 / 待备课确定 个知识点（0%） |

## 当前状态

- **当前位置**：尚未开始（等待备课）
- **下一步动作**：完成知识拆解与学习计划，确认后开始第 1 个知识点
- **待复习内容**：无

## 档案导航

| 路径 | 作用 | 何时更新 |
|---|---|---|
| [00-学习计划.md](00-学习计划.md) | 学习目标、知识图谱、路线图、里程碑、复习计划 | 备课时建立，路线调整时更新 |
| [01-学习日志.md](01-学习日志.md) | 每轮教学的过程记录（目标、问答、练习、结论） | **每次学习结束立即追加** |
| [02-掌握度台账.md](02-掌握度台账.md) | 每个知识点的掌握等级与证据（权威状态） | 每次提问/练习取得证据后更新 |
| [03-问答记录.md](03-问答记录.md) | 关键问答、典型误区、引导过程 | 出现有价值的问答时 |
| [04-错题本.md](04-错题本.md) | 错题、错因、正确思路、重做安排 | 每次练习出错时 |
| [notes/](notes/) | 知识笔记与讲义，每个知识块一个文件 | 讲完一个知识块后 |
| [exercises/](exercises/) | 随堂练习、阶段测验及答案解析 | 出题时 |
| [reports/](reports/) | 阶段掌握度评估报告、结课报告、复习计划 | 阶段评估与结课时 |

## 掌握度等级速查

- **L0 未接触** ｜ **L1 初识**：能辨认、复述要点
- **L2 理解**：能用自己的话解释、答对概念性提问
- **L3 应用**：独立做对基础练习
- **L4 精通**：解决变式/综合题，能把别人教会（费曼）

升级必须有行为证据；复习答错要如实降级。
"""

    plan = f"""# 学习计划：{topic}

## 1. 学习目标

{goal}

## 2. 学习者起点

{level}

（课前诊断后补充：已经掌握的相关知识、自评薄弱环节、学习偏好）

## 3. 知识图谱

> 备课时填写。推荐用 mermaid 表达先修/依赖关系；也可用缩进列表。

```mermaid
graph TD
    A["知识点1（示例，备课时替换）"] --> B["知识点2"]
    A --> C["知识点3"]
    B --> D["综合应用"]
    C --> D
```

## 4. 学习路线（知识点清单）

| 序号 | 知识点 | 先修 | 重要度 | 掌握度 | 状态 |
|---|---|---|---|---|---|
| 1 | （备课时填写） | — | 高/中/低 | L0 | ⬜ 未开始 |

状态图例：⬜ 未开始 ｜ 🔄 进行中 ｜ ✅ 已完成（达到 L3 及以上）

## 5. 里程碑与测验安排

| 里程碑 | 覆盖知识点 | 测验形式 | 状态 |
|---|---|---|---|
| M1（备课时填写） | | 随堂提问 / 小测 / 综合测验 | ⬜ |

## 6. 间隔复习计划

> 遵循 1 天 → 3 天 → 7 天 → 14 天 → 30 天间隔；每次复习后填写结果，答错则缩短间隔并降级。

| 复习内容 | 首次学习日 | +1天 | +3天 | +7天 | +14天 | +30天 |
|---|---|---|---|---|---|---|
| （学习过程中补充） | | | | | | |
"""

    log = f"""# 学习日志：{topic}

> 每轮教学结束后**立即追加**一条记录，最新记录追加在文件末尾。
> 日志是跨会话恢复记忆的主要依据，须如实记录用户的回答与表现（不要只写"讲解顺利"）。

---

### 日志条目模板（复制使用）

```markdown
## YYYY-MM-DD 第 N 次学习 · 知识点：

- **本节目标**：
- **教学过程**：
  - 讲解了：
  - 提出的问题 / 用户回答原话要点：
  - 引导过程（给了哪些提示、如何纠错）：
- **练习情况**：题目 → 作答 → 对错
- **暴露的误区 / 薄弱点**：
- **掌握度变化**：知识点 X：La → Lb（证据：……）
- **已产出文档**：notes/…、exercises/…
- **布置的复习任务**：
- **下节预告**：
```
"""

    ledger = f"""# 掌握度台账：{topic}

> **唯一权威的掌握状态记录。**
> 规则：
> 1. 等级只能依据实际行为证据（当场回答、独立练习）更新，禁止凭感觉升级；
> 2. 升到 L3 必须有独立做对基础练习的证据；升到 L4 需解决变式/综合题或完成费曼讲解；
> 3. 复习时答错、遗忘，如实降级并重新安排验证；
> 4. 每次更新同步在末尾「升降级记录」留痕。

## 等级定义

| 等级 | 名称 | 行为证据 |
|---|---|---|
| L0 | 未接触 | 尚未学习 |
| L1 | 初识 | 能辨认概念、复述要点 |
| L2 | 理解 | 能用自己的话解释，答对概念性提问 |
| L3 | 应用 | 不看提示独立做对基础练习 |
| L4 | 精通 | 解决变式/综合题，能清晰教会他人 |

## 知识点掌握度总表

| 知识点 | 当前等级 | 上次验证日期 | 证据（问答/练习） | 下次复习日期 |
|---|---|---|---|---|
| （备课后补充） | L0 | — | — | — |

## 升降级记录

| 日期 | 知识点 | 变化 | 依据 |
|---|---|---|---|
| | | | |
"""

    qa = f"""# 问答记录：{topic}

> 记录有教学价值的问答：关键推理过程、典型误区、有效的引导与提示。
> 简单的确认性问答不必记录。

---

### 条目模板（复制使用）

```markdown
## YYYY-MM-DD · 所属知识点：

**老师问**：
**学生答（原话要点）**：
**点评与引导**：（答对如何加深；答错给了哪几级提示）
**最终结论**：
```
"""

    mistakes = f"""# 错题本：{topic}

> 每道错题记录错因与正确思路，并安排间隔重做；重做答对后标注 ✅ 已过关，记录保留。

错因标签：#概念不清 #方法不会 #审题失误 #计算或操作失误 #知识遗忘 #综合应用困难

---

### 错题条目模板（复制使用）

```markdown
## YYYY-MM-DD · 题目简述（所属知识点）

- **题目**：
- **我的作答**：
- **错因标签**：
- **错因分析**：（为什么会错，卡在哪一步）
- **正确思路 / 答案**：
- **同类练习指引**：
- **重做安排**：+1 天 ⬜ ｜ +3 天 ⬜ ｜ +7 天 ⬜
- **状态**：⬜ 待重做 / ✅ 已过关
```
"""

    notes_readme = """# 讲义笔记（notes/）

每讲完一个知识块，在此目录产出一份笔记/讲义，命名格式 `NN-知识点名.md`，
建议结构：概念定义 → 直观解释/类比 → 典型例子 → 易错点 → 小结 → 关联知识。
笔记用学生能看懂的语言写，避免照搬教材。
"""

    exercises_readme = """# 练习与测验（exercises/）

- 随堂练习命名：`NN-知识点-练习.md`
- 阶段测验命名：`阶段测验M1-范围.md`，须含题目、参考答案、评分标准与考查点映射。
- 每次练习后把错题登记到上级目录的 `04-错题本.md`。
"""

    reports_readme = """# 评估报告（reports/）

- 阶段评估：`阶段评估-M1-YYYY-MM-DD.md`
- 结课报告：`结课报告-YYYY-MM-DD.md`
- 复习计划：`复习计划-YYYY-MM-DD.md`（间隔重复：+1/+3/+7/+14/+30 天）

报告须基于 `02-掌握度台账.md` 的真实证据撰写，区分"已掌握"与"仍薄弱"。
"""

    return {
        "README.md": readme,
        "00-学习计划.md": plan,
        "01-学习日志.md": log,
        "02-掌握度台账.md": ledger,
        "03-问答记录.md": qa,
        "04-错题本.md": mistakes,
        "notes/README.md": notes_readme,
        "exercises/README.md": exercises_readme,
        "reports/README.md": reports_readme,
    }


def init_archive(topic: str, base_path: Path, goal: str, level: str) -> Path:
    safe_topic = sanitize_topic(topic)
    archive_dir = base_path.resolve() / f"学习档案-{safe_topic}"

    if archive_dir.exists():
        raise FileExistsError(f"学习档案已存在，拒绝覆盖：{archive_dir}")

    today = date.today().isoformat()
    files = build_files(safe_topic, goal, level, today)

    archive_dir.mkdir(parents=True)
    for rel_path, content in files.items():
        target = archive_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        w(target, content)

    return archive_dir


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="初始化 interactive-tutor 学习档案")
    parser.add_argument("--topic", required=True, help="学习主题，如 'Python 基础'")
    parser.add_argument("--path", default=".", help="档案输出目录，默认当前目录")
    parser.add_argument("--goal", default="", help="学习目标（可选）")
    parser.add_argument("--level", default="", help="学习者当前基础（可选）")
    args = parser.parse_args()

    base = Path(args.path)
    if not base.exists():
        print(f"错误：输出目录不存在：{base}", file=sys.stderr)
        return 1

    try:
        archive_dir = init_archive(args.topic, base, args.goal, args.level)
    except FileExistsError as e:
        print(f"错误：{e}", file=sys.stderr)
        print("如需重建，请先手动备份并改名/移除旧档案。", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1

    print(f"已创建学习档案：{archive_dir}")
    print("下一步：备课，填写 00-学习计划.md 与 02-掌握度台账.md 的知识点清单。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
