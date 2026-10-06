# moyu-teacher · 交互式教学导师 Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Format: Agent Skills](https://img.shields.io/badge/Agent%20Skills-SKILL.md-blue)](#安装)

一个让 AI Agent 化身**循循善诱的家庭教师**的 [Agent Skills](https://www.anthropic.com/news/skills) 技能：
给它一个主题、知识点或任意文档，它会把内容拆成小块，通过多轮「讲解 → 提问 → 练习 → 小结」
对话带你学会，而不是一次性灌输答案；同时在本地建立一套 **Markdown 学习档案**，
记录学习日志、掌握度、问答、错题与复习计划，**跨会话不遗忘**。

- **全学科通用**：编程、数学、语言、考证、文档研读……教什么由你决定
- **启发式教学**：答错不直接给答案，按「回溯 → 方向 → 类比 → 拆问 → 示范」五级提示引导你自己推导
- **证据驱动的掌握度**：L0~L4 五级，只凭真实回答和独立练习升级，复习答错如实降级
- **学习档案持久化**：本地 Markdown 文件，任何新会话都能从断点继续
- **间隔重复复习**：自动按 +1 / +3 / +7 / +14 / +30 天安排复习与错题重做
- **完整教学产出**：学习计划与知识图谱、讲义笔记、练习测验、掌握度评估报告

## 教学流程

```
启动恢复 → 澄清与备课 → 教学循环（逐知识点反复） → 阶段测验与评估 → 结课
```

1. **启动恢复**：自动在当前目录查找 `学习档案-*`，读取进度并向你复述"上次学到哪"
2. **澄清与备课**：确认学习目标、当前基础、时间预算；你提供 PDF/Word 等资料时会先完整读取；随后拆解知识点、生成知识图谱和学习路线供你确认
3. **教学循环**：每个知识点走完开场回顾、精简讲解、检验提问、启发纠错、独立练习、你来小结，一轮只推进一小步
4. **阶段测验**：里程碑处闭卷限时测验，未达标就降级补讲、换题再测
5. **结课**：产出结课报告和带具体日期的长期复习计划

掌握度等级：

| 等级 | 名称 | 判定证据 |
|---|---|---|
| L0 | 未接触 | — |
| L1 | 初识 | 能辨认、复述要点 |
| L2 | 理解 | 用自己的话解释、答对概念性提问 |
| L3 | 应用 | 不看提示独立做对基础练习（默认正确率 ≥80%） |
| L4 | 精通 | 解决变式/综合题，或通过费曼讲解教会别人 |

## 安装

**前置要求**：[Python 3.7+](https://www.python.org/downloads/)（用于一键创建学习档案；Windows 安装时勾选 *Add python.exe to PATH*）。

先把仓库下载到本地：

```bash
git clone https://github.com/joker20020/moyu-teacher.git
cd moyu-teacher
```

然后按你使用的 Agent 工具选择安装方式。**核心动作只有一个：把 `moyu-teacher/` 整个文件夹复制到该工具的 skills 发现目录，然后重启会话。**

### 豆包桌面端（Doubao）

Windows（PowerShell）：

```powershell
$dst = "$env:LOCALAPPDATA\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills"
New-Item -ItemType Directory -Force $dst | Out-Null
Copy-Item -Recurse .\moyu-teacher $dst
```

macOS / Linux：

```bash
mkdir -p ~/.doubao/agent_mode/workspace/.user_skills
cp -r moyu-teacher ~/.doubao/agent_mode/workspace/.user_skills/
```

复制后重启豆包（或开启新会话）即可自动识别。若版本不同导致路径不存在，在豆包工作区目录下找到 `.user_skills` 文件夹放入即可。

### Claude Code

个人级（所有项目可用，macOS / Linux）：

```bash
mkdir -p ~/.claude/skills
cp -r moyu-teacher ~/.claude/skills/
```

项目级（仅当前项目，可随仓库共享给团队）：

```bash
mkdir -p .claude/skills
cp -r moyu-teacher .claude/skills/
```

Windows（PowerShell，个人级）：

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse .\moyu-teacher "$HOME\.claude\skills\"
```

重启 Claude Code 后生效。详见官方文档：[Claude Code Skills](https://docs.claude.com/en/docs/claude/skills)。

### Gemini CLI

方式一：从 GitHub 一行安装（推荐，需指定子目录 `--path`）：

```bash
gemini skills install https://github.com/joker20020/moyu-teacher.git --path moyu-teacher --consent
```

方式二：手动复制到用户级目录：

```bash
# Gemini 专属目录
mkdir -p ~/.gemini/skills
cp -r moyu-teacher ~/.gemini/skills/

# 或跨工具通用目录（Gemini 同样会发现）
mkdir -p ~/.agents/skills
cp -r moyu-teacher ~/.agents/skills/
```

安装后在交互会话中用 `/skills list` 确认技能已出现。详见官方文档：[Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills.md)。

### Cursor

新版 Cursor（支持 Agent Skills）：

```bash
# 全局（macOS / Linux）
mkdir -p ~/.cursor/skills
cp -r moyu-teacher ~/.cursor/skills/

# 或仅当前项目
mkdir -p .cursor/skills
cp -r moyu-teacher .cursor/skills/
```

Windows（PowerShell，全局）：

```powershell
New-Item -ItemType Directory -Force "$HOME\.cursor\skills" | Out-Null
Copy-Item -Recurse .\moyu-teacher "$HOME\.cursor\skills\"
```

也可以在 **Settings → Rules, Skills, Subagents → New → Add from GitHub** 中填入本仓库地址安装，安装后重启 Cursor。

旧版 Cursor 仅支持 Rules：将 `moyu-teacher/SKILL.md` 的正文转存为 `.cursor/rules/moyu-teacher.mdc`（frontmatter 按 Cursor Rules 格式调整）即可，scripts 与 references 放在同级目录引用。

### 其他兼容 Agent Skills 标准的工具

本技能是标准的 `SKILL.md`（YAML frontmatter 含 `name` / `description`）+ `scripts/` + `references/` 结构，
任何遵循 Agent Skills 开放标准的工具（如支持 `~/.agents/skills/` 通用目录的 CLI）均可安装：

```bash
mkdir -p ~/.agents/skills
cp -r moyu-teacher ~/.agents/skills/
```

也可以尝试社区安装器：`npx skills add https://github.com/joker20020/moyu-teacher`，按交互提示选择 `moyu-teacher` 目录。

### 验证安装成功

新开一个会话，输入例如：

> 教我学 Python 基础，我是零基础，目标是能自己写小脚本

Agent 应先与你确认目标和基础，随后在当前目录创建 `学习档案-Python基础/`，并以提问的方式开始第一课。
之后随时说"**继续学习**"，即可从上次断点恢复。

## 使用方法

**触发示例**：

- "教我学 XX / 带我入门 XX / 我想弄懂 XX"
- "根据这份文档（PDF/Word/笔记）带我系统学一遍"
- "我要考 XX 试，帮我制定学习计划并带我复习"
- "出几道题考考我刚才学的内容"
- "继续之前的学习"

**学习档案结构**（由 `scripts/init_archive.py` 一键生成，位于你学习时所在的目录）：

```
学习档案-<主题>/
├── README.md           # 档案索引与当前进度面板（恢复会话的入口）
├── 00-学习计划.md       # 学习目标、知识图谱、路线图、里程碑、间隔复习表
├── 01-学习日志.md       # 每轮教学的真实过程记录
├── 02-掌握度台账.md     # 各知识点掌握等级与行为证据（权威状态）
├── 03-问答记录.md       # 关键问答与典型误区
├── 04-错题本.md         # 错题、错因、正确思路、重做安排
├── notes/              # 知识笔记与讲义
├── exercises/          # 随堂练习与阶段测验（含答案解析）
└── reports/            # 阶段评估报告、结课报告、复习计划
```

档案是纯 Markdown，可随时直接阅读、用 Git 管理或自行修改。技能遵循"无证据不升级、不落档不下课"
的原则，任何进度变化都有据可查。

## 仓库结构

```
moyu-teacher/
└── moyu-teacher/          # 技能本体（安装时复制这个文件夹）
    ├── SKILL.md                # 技能主文件：触发条件与教学全流程
    ├── scripts/
    │   └── init_archive.py     # 一键创建学习档案（含全套模板）
    └── references/
        ├── teaching-playbook.md      # 教学法手册：讲解、提问、提示阶梯、练习、间隔复习
        ├── archive-spec.md           # 学习档案结构、掌握度规则、跨会话恢复流程
        └── deliverable-templates.md  # 学习计划/讲义/测验/评估报告的模板
```

## 自定义与贡献

- 想调整教学风格（提问密度、练习数量、课堂节奏）：编辑 `references/teaching-playbook.md`
- 想调整档案字段或文档模板：编辑 `references/archive-spec.md` 与 `references/deliverable-templates.md`
- Issue 与 PR 欢迎提交；建议先用 Issue 讨论较大的行为变更

## License

[MIT](LICENSE) © joker20020
