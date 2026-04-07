---
name: papercash
description: "论文全流程辅助: 8源检索、综述生成、查重预检、降AI率、参考文献格式化、Word导出"
---

# PaperCash — 论文全流程辅助 Skill

> 论文检索、文献综述、写作辅助、查重预检、降AI率、参考文献管理 —— 一个 Skill 全搞定。

## 触发方式

当用户提到以下关键词时激活本技能：
- "论文"、"paper"、"文献"、"查重"、"降重"、"降AI"、"参考文献"、"引用"、"综述"、"摘要"
- "/papercash"、"papercash"

## 核心能力

### 1. 论文检索 (search)
搜索 Semantic Scholar、arXiv、CrossRef、百度学术等 8 大学术数据源，返回评分排序的论文列表。

**调用方式：**
```
/papercash search <研究主题>
```

**示例：**
```
/papercash search 深度学习在医学图像中的应用
```

**Agent 执行步骤：**
1. 运行 `python scripts/papercash.py search "<主题>" --emit compact`
2. 将输出结果呈现给用户，包含论文标题、作者、年份、引用数、摘要摘录
3. 可选 `--export-docx` 导出 Word 文档
4. 提供后续建议：生成综述、格式化引用、深入某篇论文

### 2. 文献综述 (review)
基于检索结果，自动生成结构化文献综述。

**调用方式：**
```
/papercash review <研究主题> [--format gb7714|apa]
```

**Agent 执行步骤：**
1. 运行 `python scripts/papercash.py review "<主题>" --format gb7714`
2. 脚本自动完成检索 + 综述生成，输出结构化综述：
   - 研究背景与现状
   - 国内外研究对比
   - 研究方法分类
   - 研究空白与不足
   - 每段附带真实引用 [作者, 年份]
3. 可选 `--export-docx` 直接导出 Word 文档

### 3. 写作辅助 (outline / expand / polish)
生成论文大纲、段落扩写、学术润色。

**调用方式：**
```
/papercash outline <论文题目>
/papercash expand <关键点描述>
/papercash polish <待润色文本>
```

**Agent 执行步骤：**
- outline: Agent 基于题目和检索到的相关文献，生成符合学术规范的多级大纲
- expand: Agent 将关键点扩展为学术段落，附带文献支撑
- polish: Agent 将口语化表达改为学术用语，保持原意不变

### 4. 查重预检 (check)
将论文拆成句子，逐句检索学术库，标记高相似度句子。

**调用方式：**
```
/papercash check <文件路径或粘贴内容>
```

**Agent 执行步骤：**
1. 运行 `python scripts/papercash.py check "<文件路径>" --emit json`
2. 呈现结果：标记高风险句子（相似度 > 70%）、中风险句子（50-70%）
3. 对高风险句提供改写建议
4. **重要提示**：告知用户"这是预检工具，不替代知网/维普等正式查重"

### 5. 降AI率改写 (humanize)
通过句式变换、个人观点注入、学术语气调整，降低AI生成内容的检测率。

**调用方式：**
```
/papercash humanize <文件路径或粘贴内容>
```

**Agent 执行步骤：**
1. 运行 `python scripts/papercash.py humanize "<文件路径>"`
2. 返回改写后的文本，并标注修改点
3. 改写策略：
   - 被动改主动、长句拆短句
   - 注入"笔者认为"、"从实践角度看"等个人视角
   - 替换AI高频套话（"综上所述"→具体总结）
   - 增加领域特有细节

### 6. 参考文献格式化 (cite)
从 DOI/URL 提取文献信息，输出 GB/T 7714、APA、BibTeX 等格式。

**调用方式：**
```
/papercash cite <DOI或URL> [--style gb7714|apa|bibtex]
```

**Agent 执行步骤：**
1. 运行 `python scripts/papercash.py cite "<DOI>" --style gb7714`
2. 返回格式化的引用条目
3. 支持批量输入（多个 DOI 用空格分隔）

### 7. 格式检查 (format)
检查论文是否符合常见高校格式要求。

**调用方式：**
```
/papercash format <Word文件路径>
```

**Agent 执行步骤：**
1. 运行 `python scripts/papercash.py format "<文件路径>"`
2. 返回格式检查报告：字体、字号、行距、页边距、参考文献格式等

## 配置诊断

```
/papercash setup    # 交互式配置向导
/papercash diagnose # 检查数据源可用状态
```

## 数据源说明

| 数据源 | 覆盖范围 | 需要配置 |
|--------|---------|---------|
| Semantic Scholar | 2亿+论文，全领域 | 无需（免费API） |
| arXiv | STEM预印本 | 无需（免费） |
| CrossRef | 1.4亿DOI元数据 | 无需（免费） |
| 百度学术 | 中文论文元数据 | 无需（公开搜索） |
| Google Scholar | 全领域 | 可选（需代理） |
| PubMed | 生物医学 | 可选（免费） |
| 知网 CNKI | 中文核心期刊 | 需Cookie |
| 万方 | 中文学术 | 需Cookie |

## 重要约束

1. **学术诚信**：本工具辅助写作，不鼓励学术不端。生成内容需用户审核修改。
2. **查重声明**：查重预检仅供参考，正式查重请使用学校指定系统。
3. **引用真实性**：所有引用来自真实学术数据库检索结果，但 Agent 应提醒用户核实。
4. **降AI率说明**：改写结果仅供参考，最终文本需体现学生本人的思考和理解。
