---
name: papercash
description: "论文全流程辅助: 8源检索、综述生成、查重预检、降AI率、参考文献格式化、Word导出"
---

请参阅项目根目录的 SKILL.md 获取完整指令。

核心命令：
- `python scripts/papercash.py search "<主题>"` — 多源论文检索
- `python scripts/papercash.py review "<主题>"` — 文献综述生成
- `python scripts/papercash.py check "<文本>"` — 查重预检
- `python scripts/papercash.py humanize "<文本>"` — 降AI率改写
- `python scripts/papercash.py cite "<DOI>" --style gb7714` — 参考文献格式化
- `python scripts/papercash.py outline "<题目>"` — 论文大纲生成
- `python scripts/papercash.py polish "<文本>"` — 学术润色
- `python scripts/papercash.py format "<文件>"` — Word 格式检查
