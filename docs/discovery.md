# 论文发现页维护

网页入口是 `docs/index.html`，使用原生 HTML、CSS 与 JavaScript。可用任意静态文件服务器预览 `docs/` 目录。

```bash
python -m http.server 8778 --directory docs
```

## 数据

`python scripts/build_discovery.py` 从三组 arXiv 分类检索、两组 Crossref 主题检索生成 `docs/data/papers.json`。默认每组最多 12 篇，按 DOI 或 arXiv ID 合并交叉分类；Crossref 检索窗口为运行当天起的一年，arXiv 按提交日期排序。

每条记录包含实际来源链接、作者、原文摘要（如有）、发表日期、类型、主题和引用草稿。日期只精确到年或月时不补造月日。Crossref 文献类型限期刊文章；arXiv 明确标为预印本，BibTeX 使用 `@misc` 和 arXiv 标识符。

`feeds` 记录每组来源的检查时间、成功更新时间和状态。单组失败保留旧数据并标记 `stale`；首次抓取失败且没有旧数据时标记 `unavailable`；全部失败且没有旧书单时构建报错。部署失败不会替换现有站点。

## 部署

GitHub Pages 使用 GitHub Actions 作为发布来源。`PaperCash Discovery` 工作流在网页相关改动推送、手动运行及每天北京时间 08:20 时触发。任务刷新数据、构建站点目录并部署，定时刷新不向默认分支追加提交。

打包清单仅包含 `index.html`、`styles.css`、`app.js`、`.nojekyll`、`assets/` 和 `data/`。仓库内的其他文档不随站点发布。

## 本地收藏与交互

收藏存储键为 `papercash.saved.v1`。每条收藏保留当时的论文元数据，因此论文退出日常书单后仍可从书签继续查看和导出；清除站点数据会移除本地收藏。网页不接收上传、Cookie、密钥或账户资料。

筛选只检索当前书单；深入检索通过复制 Agent 指令完成。引用属于元数据草稿，提交前需人工核对。
