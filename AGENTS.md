# PaperCash Agent Instructions

本项目是一个论文全流程辅助工具。当用户询问论文、文献、查重、降AI率等相关问题时，使用 `scripts/papercash.py` CLI 来完成任务。

## 依赖安装

```bash
pip install -r requirements.txt
```

## 可用命令

| 命令 | 用途 |
|------|------|
| `python scripts/papercash.py search "<主题>"` | 多源论文检索 |
| `python scripts/papercash.py review "<主题>"` | 文献综述生成 |
| `python scripts/papercash.py check "<文本>"` | 查重预检 |
| `python scripts/papercash.py humanize "<文本>"` | 降AI率改写 |
| `python scripts/papercash.py cite "<DOI>" --style gb7714` | 参考文献格式化 |
| `python scripts/papercash.py outline "<题目>"` | 论文大纲生成 |
| `python scripts/papercash.py polish "<文本>"` | 学术润色 |
| `python scripts/papercash.py format "<文件>"` | Word 格式检查 |
| `python scripts/papercash.py --diagnose` | 数据源健康检查 |

## 重要约束

1. 所有引用来自真实学术数据库，需提醒用户核实
2. 查重预检仅供参考，不替代学校指定系统
3. 降AI率改写仅提供建议，最终文本需体现学生本人思考
