# moyu-teacher · 教学、评分与答疑一体的三角色 AI 老师 Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Format: Agent Skills](https://img.shields.io/badge/Agent%20Skills-SKILL.md-blue)](#安装)

**一个技能、三个角色，按你的意图自动切换**——这是一个遵循 [Agent Skills](https://www.anthropic.com/news/skills)
标准的教学技能：Agent 既是循循善诱的**教学导师**（把内容拆成小块，通过多轮「讲解 → 提问 → 练习 → 小结」
带你学会，而不是一次性灌输答案），也是严谨公正的**作业评分官**（依据题目和评分要求逐题给分、
附证据、出反馈，并把成绩导出为 Excel 可打开的表格），还是精准简洁的**解答助教**（课后就具体疑问
答疑，默认你已会基础、不东拉西扯，每个问题留一份复习记录）。三个角色共享一套本地 Markdown/JSON
档案体系，教学出的测验直接能批，批改与答疑发现的薄弱点自动回流到学习档案，**跨会话不遗忘**。

## 三个角色

### 角色 A · 教学导师（促学）

- **全学科通用**：编程、数学、语言、考证、文档研读……教什么由你决定
- **启发式教学**：答错不直接给答案，按「回溯 → 方向 → 类比 → 拆问 → 示范」五级提示引导你自己推导
- **证据驱动的掌握度**：L0~L4 五级，只凭真实回答和独立练习升级，复习答错如实降级
- **学习档案持久化**：本地 Markdown 文件，任何新会话都能从断点继续
- **间隔重复复习**：自动按 +1 / +3 / +7 / +14 / +30 天安排复习与错题重做
- **完整教学产出**：学习计划与知识图谱、讲义笔记、练习测验、掌握度评估报告

### 角色 B · 作业评分官（测评）

- **三要素接单**：题目 + 学生作答 + 评分要求（没有评分标准时先帮你制定采分点/量表并确认）
- **逐题证据给分**：每个给分/扣分点都附学生作答原文摘录，部分给分能拆到具体采分点
- **全题型覆盖**：选择判断填空、计算证明（分步采分、错误不传导）、简答论述、作文（分项量表）、
  编程（用例+技术点）、设计作品与口语展示
- **批量评分一致性**：试评校准、横向评卷、锚点卷、边界卷复评，控制宽严漂移
- **机器校验防错**：分数越界、漏题、总分合计错误自动拦截，总分由脚本重算
- **一键导出**：成绩总表（Markdown + **Excel 直接打开的 CSV**）、每人评分反馈单
- **讲评产出包**：批改后用真实成绩预填批次总评（总体评价/问题点/改进方向）与**习题讲解课教案**
  （按得分率标出必讲题、预排教学过程与匿名错误样本）；**讲解课 PPT 不生成固定文件**，
  而是由 agent 整理需求简报、**派发已安装的 ppt 技能（子 agent）**制作并导出**本地可编辑的
  .pptx 文件（或 PDF）**，亲自打开验收后交付
- **教学联动**：错题与知识点得失分可回填学习档案，无缝衔接针对性补讲与变式再测

### 角色 C · 解答助教（课后答疑）

- **精准答疑**：默认你已具备相关基础知识，不重复铺垫、不从头讲一章，只解开你卡住的那一步
- **紧扣问题**：清晰、简洁、易懂，先给结论再讲关键理由；不主动引申没问到的内容，一种解法讲透为止
- **边界清晰**：发现是系统知识缺口会建议转教学导师系统学；要给整份作业打分则转评分官
- **每问一份记录**：每个问题生成一份答疑记录（原问 → 卡点定位 → 解答 → 复习自测），
  可归入学习档案，课后照着记录就能复习；同一知识点反复提问会提示你该系统复习

## 教学流程（角色 A）

```
启动恢复 → 澄清与备课 → 教学循环（逐知识点反复） → 阶段测验与评估 → 结课
```

1. **启动恢复**：自动在当前目录查找 `学习档案-*`，读取进度并向你复述"上次学到哪"
2. **澄清与备课**：确认学习目标、当前基础、时间预算；你提供 PDF/Word 等资料时会先完整读取；随后拆解知识点、生成知识图谱和学习路线供你确认
3. **教学循环**：每个知识点走完开场回顾、精简讲解、检验提问、启发纠错、独立练习、你来小结，一轮只推进一小步
4. **阶段测验**：里程碑处闭卷限时测验；交卷后可直接切换评分官角色批改，未达标就降级补讲、换题再测
5. **结课**：产出结课报告和带具体日期的长期复习计划

掌握度等级：

| 等级 | 名称 | 判定证据 |
|---|---|---|
| L0 | 未接触 | — |
| L1 | 初识 | 能辨认、复述要点 |
| L2 | 理解 | 用自己的话解释、答对概念性提问 |
| L3 | 应用 | 不看提示独立做对基础练习（默认正确率 ≥80%） |
| L4 | 精通 | 解决变式/综合题，或通过费曼讲解教会别人 |

## 评分流程（角色 B）

```
接单核验 → 建档 → 定标 → 试评校准 → 逐份逐题评分 → 复核校验 → 导出交付
```

1. **接单核验**：确认题目、全部学生作答、评分要求与计分规则；PDF/Word/照片/代码等都能读取
2. **建档与定标**：脚本创建 `评分记录-*` 目录；逐题整理参考答案与采分点/量表，核对分值闭合；
   主观题评分标准先确认（或先试评校准）再批量评分
3. **逐题评分**：边评边把分数、判定、作答证据、给分/扣分说明录入 `grades.json`；
   看不清标"无法辨认"不猜字，疑似违纪只标记、不越权裁决
4. **复核校验**：脚本校验分数区间与总分合计；边界卷、满分/零分等异常卷人工复评
5. **导出与讲评产出**：成绩总表 Markdown + CSV、每人一份评分反馈单；批量作业再出
   **批次总评、习题讲解课教案**（脚本用真实成绩预填骨架，agent 补全）；随后 agent 整理
   PPT 需求简报、**派发 ppt 技能（子 agent）**制作讲解课课件并导出**本地 .pptx（可编辑）/PDF**，
   打开验收后存入 exports/

## 答疑流程（角色 C）

```
接问与澄清 → 定位卡点 → 简洁解答 → 当场确认 → 落档（每问一份答疑记录）
```

1. **接问**：你发来题目、自己的思路和卡在哪一步；问题不清时最多追问一两句，不猜着答
2. **定位与解答**：默认基础你已会，只讲卡点前后最短的内容——先给结论，再给关键步骤和一个最小例子，
   不堆拓展解法、不展开没问到的知识
3. **当场确认**：用一个反向小问题确认你真的通了；换两个角度还不通，就说明该转教学导师系统学
4. **每问落档**：脚本在学习档案的 `答疑记录/`（或独立的 `答疑记录-<姓名>/`）生成一份记录，
   含疑问定位、解答和一个合上书能自测的小问题，告诉你文件位置供复习

## 安装

**前置要求**：[Python 3.7+](https://www.python.org/downloads/)（用于一键创建档案与成绩导出；Windows 安装时勾选 *Add python.exe to PATH*）。

先把仓库下载到本地：

```bash
git clone https://github.com/joker20020/moyu-teacher.git
cd moyu-teacher
```

然后按你使用的 Agent 工具选择安装方式。**核心动作只有一个：把技能文件夹 `moyu-teacher/`（即执行完 `cd` 后当前目录下的 `./moyu-teacher/` 子文件夹，是"源"）整个复制到该工具的 skills 发现目录（"目标"），然后重启会话。**

> **路径说明（项目级安装务必先读）**：执行完上面的 `cd moyu-teacher` 后，你位于**克隆下来的技能仓库根目录**，并不是在自己的项目里。
> - **个人级/全局安装**：目标是 home 目录（`~/..../skills`、`$HOME\....\skills`），下面的命令可直接执行；
> - **项目级安装**：目标是**你自己的项目目录**，必须把命令中的目标路径换成该项目的绝对路径
>   （示例中的 `/path/to/your-project`、`D:\your-project` 都是占位符）；
>   如果直接照抄 `mkdir -p .claude/skills && cp -r moyu-teacher .claude/skills/`，
>   只会把技能装进**技能仓库自己里面**，你的实际项目并不会生效。

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

项目级（只在你指定的某个项目中可用，可随该项目仓库共享给团队）：

```bash
# 把 /path/to/your-project 换成【你自己项目】的绝对路径（当前仍在克隆下来的技能仓库目录内）
mkdir -p /path/to/your-project/.claude/skills
cp -r moyu-teacher /path/to/your-project/.claude/skills/
```

也可以先 `cd` 进自己的项目，再用**绝对路径引用技能源文件夹**：

```bash
cd /path/to/your-project
mkdir -p .claude/skills
cp -r /path/to/moyu-teacher/moyu-teacher .claude/skills/   # 源路径按你实际克隆位置修改
```

Windows（PowerShell，个人级）：

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse .\moyu-teacher "$HOME\.claude\skills\"
```

Windows（PowerShell，项目级）：

```powershell
# 把 $proj 换成【你自己项目】的路径（当前仍在克隆下来的技能仓库目录内）
$proj = "D:\your-project"
New-Item -ItemType Directory -Force "$proj\.claude\skills" | Out-Null
Copy-Item -Recurse .\moyu-teacher "$proj\.claude\skills\"
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

# 或仅当前项目：把 /path/to/your-project 换成【你自己项目】的绝对路径
mkdir -p /path/to/your-project/.cursor/skills
cp -r moyu-teacher /path/to/your-project/.cursor/skills/
```

Windows（PowerShell，全局）：

```powershell
New-Item -ItemType Directory -Force "$HOME\.cursor\skills" | Out-Null
Copy-Item -Recurse .\moyu-teacher "$HOME\.cursor\skills\"
```

Windows（PowerShell，仅当前项目）：

```powershell
# 把 $proj 换成【你自己项目】的路径
$proj = "D:\your-project"
New-Item -ItemType Directory -Force "$proj\.cursor\skills" | Out-Null
Copy-Item -Recurse .\moyu-teacher "$proj\.cursor\skills\"
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

新开一个会话，分别可以这样触发三个角色：

> 教我学 Python 基础，我是零基础，目标是能自己写小脚本

Agent 应先与你确认目标和基础，随后在当前目录创建 `学习档案-Python基础/`，并以提问的方式开始第一课；
之后随时说"**继续学习**"，即可从上次断点恢复。

> 按这份评分标准帮我批改全班的数学第三单元测验，成绩导出成表格

Agent 会完整读取题目、作答与评分标准，在当前目录创建 `评分记录-第三单元测验/`，
逐题评分后导出成绩总表（Markdown + CSV）和每人的评分反馈单。

> 这一步我没看懂：为什么判别式小于 0 就说方程没有实根？

Agent 会默认你已有一元二次方程的基础，直接围绕这个卡点简洁解答，随后在学习档案的
`答疑记录/`（或 `答疑记录-<你的名字>/`）生成一份带复习自测的答疑记录。

## 使用方法

**角色 A 触发示例**：

- "教我学 XX / 带我入门 XX / 我想弄懂 XX"
- "根据这份文档（PDF/Word/笔记）带我系统学一遍"
- "我要考 XX 试，帮我制定学习计划并带我复习"
- "出几道题考考我刚才学的内容"
- "继续之前的学习"

**角色 B 触发示例**：

- "帮我批改/评分/批阅这份作业（试卷、作文、代码、设计稿）"
- "按这份评分标准给学生的作答打分，统计成绩"
- "没有评分细则，你先帮我定一份再批"
- "把这几次作业的成绩汇总导出成 Excel 能打开的表"
- "给每个学生写一段评分反馈/评语，再做个班级分析"
- "这批作业改完，出一份总体评价和习题讲解课的教案、PPT"
- "这份阶段测验我做完了，帮我批改，然后针对错题给我补讲"（B → A 联动）

**角色 C 触发示例**：

- "这一步为什么要变号 / 为什么这样做？我卡在这里了"
- "帮我看看我这个做法错在哪（只讲错的那步，不用整题重批）"
- "这句话/这个概念是什么意思？简单说就行"
- "这道题除了这个结果，我想确认下我的思路对不对"
- "刚那个问题给我留个答疑记录，我回头复习"

### 学习档案结构（角色 A，由 `scripts/init_archive.py` 一键生成）

```
学习档案-<主题>/
├── README.md           # 档案索引与当前进度面板（恢复会话的入口）
├── 00-学习计划.md       # 学习目标、知识图谱、路线图、里程碑、间隔复习表
├── 01-学习日志.md       # 每轮教学的真实过程记录
├── 02-掌握度台账.md     # 各知识点掌握等级与行为证据（权威状态）
├── 03-问答记录.md       # 关键问答与典型误区
├── 04-错题本.md         # 错题、错因、正确思路、重做安排
├── notes/              # 知识笔记与讲义
├── exercises/          # 随堂练习与阶段测验（含答案解析与评分标准）
├── reports/            # 阶段评估报告、结课报告、复习计划
└── 答疑记录/            # 角色 C 课后答疑，一问一份（含索引，init_qa.py 生成）
```

### 评分记录结构（角色 B，由 `scripts/init_grading.py` 一键生成）

```
评分记录-<作业名>/
├── README.md              # 索引、评分进度、问题清单
├── 00-作业与评分标准.md     # 题目、参考答案、采分点/量表、扣分口径、修订记录
├── grades.json            # 逐题成绩与作答证据（唯一权威分数来源）
├── 01-成绩总表.md          # 自动生成：明细 + 平均/合格率/逐题得分率
├── 批改/                  # 每人一份「评分反馈-<姓名>.md」
├── exports/               # 成绩总表.csv、批次总评、讲解课教案、讲解课PPT .pptx/.pdf（ppt 技能导出的本地文件）
└── 原始作答/               # 原始作答文件留存
```

评分完成后，如果该科目已有学习档案，错题与知识点掌握情况会按证据回填台账与错题本，
随后即可让教学导师角色安排针对性补讲与再测。

### 答疑记录结构（角色 C，由 `scripts/init_qa.py` 一问生成一份）

```
学习档案-<主题>/答疑记录/        # 有学习档案时（与档案联动、可回填台账）
或 答疑记录-<学生名>/            # 没有档案时（未署名则为 答疑记录/）
├── README.md                    # 索引表（日期/问题/知识点/是否已自测）
└── YYYY-MM-DD-问题简述.md        # 一问一份：原问 → 卡点定位 → 简洁解答 → 复习自测 → 跟进
```

## 仓库结构

```
moyu-teacher/
└── moyu-teacher/                    # 技能本体（安装时复制这个文件夹）
    ├── SKILL.md                     # 技能主文件：三角色路由 + 三套流程
    ├── scripts/
    │   ├── init_archive.py          # [A] 一键创建学习档案（含全套模板）
    │   ├── init_grading.py          # [B] 一键创建评分记录（含 grades.json 骨架）
    │   ├── export_grades.py         # [B] 校验成绩、重算总分，导出总表/CSV/反馈单/讲评骨架
    │   └── init_qa.py               # [C] 每个问题生成一份答疑记录并登记索引
    └── references/
        ├── teaching-playbook.md     # [A] 教学法手册：讲解、提问、提示阶梯、练习、间隔复习
        ├── archive-spec.md          # [A] 学习档案结构、掌握度规则、跨会话恢复流程
        ├── deliverable-templates.md # [A] 学习计划/讲义/测验/评估报告模板
        ├── grading-playbook.md      # [B] 评分手册：分题型给分法、证据规则、校准、特殊情形、评语
        ├── grading-rubric.md        # [B] 评分标准制定：采分点法/分级与分项量表/扣分规则库
        ├── grading-spec.md          # [B] 评分记录结构、grades.json 规范、导出格式、档案联动
        ├── review-lesson-kit.md     # [B] 批次总评、讲解课教案写法与 PPT 需求简报/派发规范
        └── qa-playbook.md           # [C] 课后答疑流程、简洁解答纪律、答疑记录规范、角色边界
```

## 自定义与贡献

- 想调整教学风格（提问密度、练习数量、课堂节奏）：编辑 `references/teaching-playbook.md`
- 想调整教学档案字段或文档模板：编辑 `references/archive-spec.md` 与 `references/deliverable-templates.md`
- 想调整评分宽严口径、扣分规则或反馈风格：编辑 `references/grading-playbook.md` 与 `references/grading-rubric.md`
- 想调整讲评课结构、教案环节或 PPT 需求简报（建议页序、验收标准）：编辑 `references/review-lesson-kit.md`
- 想调整答疑风格（简洁度、澄清问题数量、自测形式）或答疑记录模板：编辑 `references/qa-playbook.md` 与 `scripts/init_qa.py`
- 想调整成绩表字段、导出列或档案结构：编辑 `references/grading-spec.md` 与 `scripts/export_grades.py`
- Issue 与 PR 欢迎提交；建议先用 Issue 讨论较大的行为变更

## License

[MIT](LICENSE) © joker20020
