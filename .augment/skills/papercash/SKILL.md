---
name: papercash
description: 使用本地 Python CLI 辅助论文检索、摘要级文献整理、DOI 引用格式化、Word 格式检查、查重预检和写作修改。涉及“降AI率”时只提供表达建议；不把检索结果当成全文阅读或正式查重结果。
metadata:
  version: "2.0.0"
---

# PaperCash

本 Skill 的入口是 `scripts/papercash.py`。先在 Skill 目录安装 `requirements.txt`，然后按用户实际请求选择命令。无需为了普通论文问题强制运行全部功能。

## 命令

| 任务 | 命令 |
| --- | --- |
| 检索论文 | `python scripts/papercash.py search "主题" --emit agent --limit 20` |
| 整理文献 | `python scripts/papercash.py review "主题" --format gb7714` |
| 起草大纲 | `python scripts/papercash.py outline "题目"` |
| 获取扩写思路 | `python scripts/papercash.py expand "段落"` |
| 修改表达 | `python scripts/papercash.py polish "段落"` |
| 相似内容预检 | `python scripts/papercash.py check "文本或路径" --emit agent` |
| 表达修改建议 | `python scripts/papercash.py humanize "文本或路径" --emit agent` |
| DOI 引用 | `python scripts/papercash.py cite "10.xxxx/..." --style gb7714` |
| Word 格式检查 | `python scripts/papercash.py format "论文.docx"` |
| 数据源诊断 | `python scripts/papercash.py --diagnose` |

`search` 支持 `--sources`、`--export-docx`、`--save-dir`。`review` 支持 `--format gb7714|apa`、`--export-docx`、`--save-dir`。查重预检支持 `--mode fast|standard|deep|legacy`。确切参数以 `--help` 为准。

## 使用结果时的判断

- 逐条核对论文标题、作者、年份、DOI 与链接。数据库元数据可能不完整或重复，引用格式输出也需要人工核对。
- `review` 依据检索到的元数据与摘要生成整理稿。涉及方法、结论、研究空白时，阅读原文后再作判断；不要将其表述为已经完成全文综述。
- `check` 仅将句子与检索到的标题和摘要比较。没有候选文献时报告“无法判断”，任何相似度都不能证明抄袭或原创。正式查重使用学校指定系统。
- `humanize` 只提供有限的表达修改建议，不预测 AI 检测结果。工具交互式要求确认；默认保留识别到的数据、公式、法条和引用所在句。修改后仍需核对原意。
- `check` 与 `humanize` 会在本机 `~/.papercash/audit/` 记录时间、命令、输入摘要和长度，不保存原文。
- `expand` 输出扩写思路和模板，不会凭空补充可靠数据或文献。`format` 使用固定的常见格式样例，具体要求以学校模板为准。

## 交付方式

把命令结果整理成用户能直接使用的形式，保留可核对的来源链接，明确哪些内容仍需全文核实。如果数据源失败或没有结果，如实说明，不补造论文、引用、查重率或检测准确率。
