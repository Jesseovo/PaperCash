# 📄 PaperCash — 论文全流程辅助 Skill

> 🚀 论文检索、文献综述、写作辅助、查重预检、降AI率、参考文献管理 —— 一个 Skill 全搞定。

[English](#-papercash--full-stack-academic-paper-skill) | [中文](#-papercash--论文全流程辅助-skill)

**PaperCash** 是一个 AI Agent 技能（Skill），帮助中国学生从论文选题到最终提交的全流程。4 个免费数据源开箱即用，覆盖 2 亿+ 学术论文，无需任何 API Key 即可使用。

👤 **作者 / Author:** Jesse (@Jesseovo)

---

## ✨ 核心特性

- 🔍 **8 大学术数据源** — Semantic Scholar、arXiv、CrossRef、百度学术、Google Scholar、PubMed、知网、万方
- 📝 **文献综述生成** — 输入主题，自动检索 + 聚类 + 生成结构化综述
- ✍️ **写作辅助** — 大纲生成、段落扩写、学术润色
- 🔎 **查重预检** — 句子级学术库检索，标记高风险内容
- 🤖 **降AI率改写** — 句式变换 + 个人观点注入 + 学术语气调整
- 📚 **参考文献管理** — DOI 一键解析，GB/T 7714 / APA / BibTeX 格式输出
- 📐 **格式检查** — 字体、字号、行距、页边距一键检查
- 🤖 **7+ Agent 平台兼容** — Cursor、OpenClaw、Claude Code、Windsurf、Augment、Gemini CLI、Codex CLI

---

## ⚡ 快速开始

### 安装

```bash
git clone https://github.com/Jesseovo/PaperCash.git
cd PaperCash
pip install -r requirements.txt
```

### 零配置即用（4 个免费源）

安装完成后，Semantic Scholar、arXiv、CrossRef、百度学术**立即可用**，无需任何 API Key。

```bash
# 检索论文
python scripts/papercash.py search "深度学习在医学图像中的应用"

# 生成文献综述
python scripts/papercash.py review "强化学习在自动驾驶中的研究进展"

# 格式化参考文献
python scripts/papercash.py cite "10.1145/3292500.3330701" --style gb7714

# 检查数据源状态
python scripts/papercash.py --diagnose
```

---

## 📋 数据源支持

| 数据源 | 覆盖范围 | 需要配置 | 状态 |
|--------|---------|---------|------|
| 🔬 Semantic Scholar | 2亿+论文，全领域 | ✅ 无需（免费API） | 可用 |
| 📄 arXiv | STEM预印本 | ✅ 无需（免费） | 可用 |
| 🔗 CrossRef | 1.4亿DOI元数据 | ✅ 无需（免费） | 可用 |
| 🔵 百度学术 | 中文论文元数据 | ✅ 无需（公开搜索） | 可用 |
| 🌐 Google Scholar | 全领域 | 可选（需代理） | 可选 |
| 🏥 PubMed | 生物医学 | 可选（免费） | 可选 |
| 📕 知网 CNKI | 中文核心期刊 | 需Cookie | 可选 |
| 📗 万方 | 中文学术 | 需Cookie | 可选 |

---

## 🚀 功能详解

### 1. 论文检索

```bash
python scripts/papercash.py search "Transformer 文本分类" --limit 20
```

评分公式：`relevance(40%) + citations(25%) + recency(20%) + source_authority(15%)`

### 2. 文献综述生成

```bash
python scripts/papercash.py review "深度学习在自然语言处理中的应用" --format gb7714
```

自动生成：
- 研究背景与现状
- 国内外研究对比
- 研究方法分类
- 研究空白与不足
- 每段附带真实引用

### 3. 写作辅助

```bash
# 生成论文大纲
python scripts/papercash.py outline "基于Transformer的中文文本分类研究"

# 段落扩写
python scripts/papercash.py expand "注意力机制在长文本中的优势"

# 学术润色
python scripts/papercash.py polish "这个方法效果很好，比之前的好很多"
```

### 4. 查重预检

```bash
python scripts/papercash.py check ./my_paper.txt
```

⚠️ **声明**：查重预检仅供参考，正式查重请使用学校指定系统（知网/维普等）。

### 5. 降AI率改写

```bash
python scripts/papercash.py humanize ./ai_generated.txt
```

核心策略：
- 被动句改主动句，长句拆短句
- 注入"笔者认为"等个人视角
- 替换AI高频套话
- 增加领域细节和数据

### 6. 参考文献格式化

```bash
# 单个 DOI
python scripts/papercash.py cite "10.1145/3292500.3330701" --style gb7714

# 批量格式化
python scripts/papercash.py cite "10.1145/3292500.3330701 10.1038/s41586-021-03819-2" --style apa
```

支持格式：GB/T 7714-2015、APA、MLA、Chicago、BibTeX

### 7. 格式检查

```bash
python scripts/papercash.py format ./my_paper.docx
```

---

## ⚙️ 高级配置

### 配置文件

```bash
mkdir -p ~/.config/papercash
touch ~/.config/papercash/.env
```

```env
# Google Scholar（可选，需代理）
GOOGLE_SCHOLAR_PROXY=http://127.0.0.1:7890

# 知网 Cookie（可选）
CNKI_COOKIE=your_cookie_here

# 万方 Cookie（可选）
WANFANG_COOKIE=your_cookie_here

# Semantic Scholar API Key（可选，提高速率限制）
SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

### 诊断

```bash
python scripts/papercash.py --diagnose
```

---

## 🤖 Agent 平台安装

### Cursor（推荐）

克隆项目后，在 Cursor 中将 `SKILL.md` 添加为项目技能。

### OpenClaw

```bash
git clone https://github.com/Jesseovo/PaperCash.git ~/.openclaw/skills/papercash
```

或通过 ClawHub 安装（即将上线）。

### Claude Code

```bash
git clone https://github.com/Jesseovo/PaperCash.git ~/.claude/skills/papercash
```

### Windsurf

```bash
git clone https://github.com/Jesseovo/PaperCash.git
cp -r PaperCash/.windsurf/skills/papercash ~/.codeium/windsurf/skills/papercash
```

或将整个项目作为工作区打开，Windsurf 会自动加载 `.windsurf/skills/` 中的技能。

### Augment Code

```bash
git clone https://github.com/Jesseovo/PaperCash.git
cp -r PaperCash/.augment/skills/papercash ~/.augment/skills/papercash
```

支持 `AGENTS.md` 自动发现，直接在项目根目录使用即可。

### Gemini CLI

```bash
git clone https://github.com/Jesseovo/PaperCash.git
# 在 Gemini CLI 中作为扩展加载（参考 gemini-extension.json）
```

### Codex CLI

```bash
git clone https://github.com/Jesseovo/PaperCash.git ~/.agents/skills/papercash
```

---

## 🏗️ 项目结构

```
PaperCash/
├── 📄 SKILL.md              # Agent 技能定义（含 YAML frontmatter）
├── 📄 AGENTS.md             # Augment / 通用 Agent 指令
├── 📄 clawhub.json          # ClawHub 发布元数据
├── 📄 README.md             # 项目说明（本文件）
├── 📄 requirements.txt      # Python 依赖
├── 📁 scripts/
│   ├── 🐍 papercash.py      # CLI 主入口
│   └── 📁 lib/
│       ├── env.py            # 环境配置
│       ├── query.py          # 查询预处理（中文分词）
│       ├── schema.py         # 数据结构定义
│       ├── score.py          # 评分系统
│       ├── dedupe.py         # 去重
│       ├── relevance.py      # 相关性计算
│       ├── render.py         # 输出渲染
│       ├── http_client.py    # HTTP 客户端
│       ├── cache.py          # 缓存管理
│       ├── 📁 sources/       # 数据源模块
│       │   ├── semantic_scholar.py
│       │   ├── arxiv.py
│       │   ├── crossref.py
│       │   ├── baidu_xueshu.py
│       │   └── ...
│       └── 📁 features/      # 功能模块
│           ├── lit_review.py
│           ├── writing.py
│           ├── plagiarism.py
│           ├── ai_humanize.py
│           ├── format_helper.py
│           └── citation.py
├── 📁 fixtures/              # 示例数据
├── 📁 hooks/                 # Agent 钩子
├── 📁 .windsurf/skills/      # Windsurf 适配
├── 📁 .augment/skills/       # Augment 适配
├── 📁 .claude-plugin/        # Claude Code 适配
└── 📁 agents/                # Codex CLI 适配
```

---

## 📊 评分系统

| 维度 | 权重 | 说明 |
|------|------|------|
| 🎯 相关性 | 40% | 与查询主题的文本匹配度 |
| 📊 引用数 | 25% | 论文被引用次数 |
| 🕐 时效性 | 20% | 发表年份的新鲜程度 |
| 🏛️ 来源权威 | 15% | 数据源可信度 |

---

## 📜 许可证

本项目基于 [MIT License](LICENSE) 发布。

👤 **作者:** Jesse (@Jesseovo)

---

# 📄 PaperCash — Full-Stack Academic Paper Skill

> 🚀 Paper search, literature review, writing assistance, plagiarism pre-check, AI detection reduction, citation management — all in one Skill.

**PaperCash** is an AI Agent Skill that assists students throughout the entire academic paper writing process. 4 free data sources work out of the box, covering 200M+ academic papers with zero API keys required.

## Features

- 🔍 **8 Academic Data Sources** — Semantic Scholar, arXiv, CrossRef, Baidu Scholar, Google Scholar, PubMed, CNKI, Wanfang
- 📝 **Literature Review Generation** — Auto search + cluster + generate structured reviews
- ✍️ **Writing Assistance** — Outline generation, paragraph expansion, academic polishing
- 🔎 **Plagiarism Pre-check** — Sentence-level academic search, flag high-risk content
- 🤖 **AI Detection Reduction** — Sentence restructuring + personal perspective injection
- 📚 **Citation Management** — DOI auto-parsing, GB/T 7714 / APA / BibTeX output
- 📐 **Format Check** — Font, size, spacing, margin verification

## Quick Start

```bash
git clone https://github.com/Jesseovo/PaperCash.git
cd PaperCash
pip install -r requirements.txt
python scripts/papercash.py search "deep learning medical imaging"
```

## License

MIT License. Author: Jesse (@Jesseovo)
