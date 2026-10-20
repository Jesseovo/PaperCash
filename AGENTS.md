# PaperCash 项目指引

本项目的功能和使用边界以 [SKILL.md](SKILL.md) 为准。用户提出论文检索、文献整理、相似内容预检、引用格式化或 Word 格式检查时，按需调用 `scripts/papercash.py`；先安装 `requirements.txt`。

修改代码时优先核对命令入口、核心函数签名和实际输出是否一致。运行 `python -m pytest -q` 验证行为；涉及数据源时另做适度的实时检查，明确数据源失败与零结果的区别。

不要把摘要整理称为全文综述，不要把相似度当作正式查重率、抄袭判定或原创证明。没有实际核实的论文和引用不要补造。

## 论文发现页

- `docs/index.html`、`docs/styles.css`、`docs/app.js` 是静态网页；`docs/assets/` 是自有像素素材，不依赖前端框架或第三方脚本。
- `scripts/build_discovery.py` 从 arXiv 和 Crossref 构建 `docs/data/papers.json`。保留来源、作者、实际日期精度和预印本标记；按 DOI/arXiv ID 去重。某组来源失败时保留该组旧数据及原更新时间，不能显示成刚更新成功。
- `.github/workflows/discovery-pages.yml` 每天 UTC 00:20（北京时间 08:20）刷新并发布 GitHub Pages，站点为 `https://jesseovo.github.io/PaperCash/`。构建只打包网页文件、素材与公开数据，不上传其他文档或本地配置。
- 收藏只写当前浏览器 localStorage；引用复用现有格式化逻辑，预印本单独标记；“交给 Agent”复制含来源的研究指令，不在网页伪造研究结果。
- 验证：`python -m pytest -q`、`node --check docs/app.js`；浏览器检查筛选、收藏刷新、引用、Agent 复制和窄屏布局。修改样式不需要重新抓取论文。
