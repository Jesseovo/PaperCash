# PaperCash

PaperCash 是一个本地 Python 论文辅助 Skill，提供学术元数据检索、摘要级文献整理、写作提示、DOI 引用格式化、相似内容预检和 Word 格式检查。Skill 的 Agent 使用规则见 [SKILL.md](SKILL.md)。

## 安装与验证

需要 Python 3.10 或更新版本。

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements.txt
# macOS/Linux: .venv/bin/python -m pip install -r requirements.txt
python scripts/papercash.py --version
python scripts/papercash.py --help
python scripts/papercash.py --diagnose
```

开发验证：`python -m pip install pytest`，然后运行 `python -m pytest -q`。测试不依赖线上数据源。

## 常用命令

```bash
python scripts/papercash.py search "医学影像分割" --limit 10 --emit agent
python scripts/papercash.py review "医学影像分割" --format gb7714 --export-docx
python scripts/papercash.py cite "10.1038/s41586-021-03819-2" --style apa
python scripts/papercash.py check "本研究采用可重复的实验方法分析样本差异。" --mode fast --emit agent
python scripts/papercash.py humanize "综上所述，这一方法值得讨论。" --emit agent
python scripts/papercash.py format "论文.docx"
```

`search` 默认尝试 Semantic Scholar、arXiv、Crossref 和百度学术。配置代理或 Cookie 后，Google Scholar、知网和万方也会参与默认检索；PubMed 可用 `--sources pubmed` 指定。配置或可访问不等于保证能取得结果；请使用 `--diagnose` 检查连通性，并核对每条返回的论文。

可选配置写入 `~/.config/papercash/.env` 或当前目录的 `.papercash.env`，也可设为环境变量：`SEMANTIC_SCHOLAR_API_KEY`、`GOOGLE_SCHOLAR_PROXY`、`CNKI_COOKIE`、`WANFANG_COOKIE`。请只使用自己有权访问的数据源凭据。

## 结果边界

- `review` 使用检索到的元数据和摘要，不读取论文全文。研究结论、方法及研究空白须由用户核对原文。
- `check` 比较待检句子与候选文献标题和摘要；无候选时返回“无法判断”。其评分不是正式查重率，也不能证明抄袭或原创。
- `humanize` 只做有限的表达修改，不能保证改变 AI 检测结果。命令需要交互确认，默认保留识别到的高风险内容所在句。
- `check` 和 `humanize` 会在本机 `~/.papercash/audit/` 写入时间、命令、输入摘要及长度；日志不保存原文。
- `expand` 输出写作思路与模板，不生成有证据支撑的新事实。`format` 按内置常见格式样例检查 `.docx`，具体要求以学校模板为准。
- 引用样式输出是初稿。提交前核对 DOI、作者、年份、出版信息和学校引用规范。

项目使用 MIT License，作者 Jesse (@Jesseovo)。
