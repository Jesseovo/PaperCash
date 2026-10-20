"""文献综述生成"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper, SearchResult
from features.citation import format_paper_citation


def generate_review(result: SearchResult, cite_format: str = "gb7714") -> str:
    """基于搜索结果生成结构化文献综述"""
    if not result.papers:
        return "未找到相关文献，无法生成综述。"

    papers = result.papers
    topic = result.query

    sections: list[str] = []

    sections.append(_header(topic, result))
    sections.append(_research_background(topic, papers))
    sections.append(_methodology_classification(papers))
    sections.append(_key_findings(papers, cite_format))
    sections.append(_research_gaps(topic, papers))
    sections.append(_references(papers, cite_format))

    return "\n\n".join(sections)


def _header(topic: str, result: SearchResult) -> str:
    lines = [
        f"# 文献综述：{topic}",
        "",
        f"本综述基于 {len(result.papers)} 篇学术文献，"
        f"来源包括 {', '.join(result.sources_used)}。"
        f"检索时间：{result.search_time_ms}ms。",
        "本稿仅依据检索元数据和可用摘要整理；论文论点、研究方法及引用信息需阅读原文核实。",
    ]
    return "\n".join(lines)


def _research_background(topic: str, papers: list[Paper]) -> str:
    years = sorted(set(p.year for p in papers if p.year))
    year_range = f"{years[0]}-{years[-1]}" if years else "近年"

    total_citations = sum(p.citation_count for p in papers)
    high_impact = [p for p in papers if p.citation_count >= 50]

    lines = [
        "## 1. 研究背景与现状",
        "",
        f"本次检索收录了 {year_range} 年间的 {len(papers)} 篇相关文献，"
        f"累计被引用 {total_citations} 次。",
    ]

    if high_impact:
        lines.append(f"其中 {len(high_impact)} 篇的数据库被引次数达到 50 次以上。")

    if years:
        recent = [p for p in papers if p.year and p.year >= years[-1] - 2]
        lines.append(f"按检索结果的最新年份计算，{years[-1] - 2}-{years[-1]} 年间有 {len(recent)} 篇。")

    return "\n".join(lines)


def _methodology_classification(papers: list[Paper]) -> str:
    """按标题和摘要关键词做粗分类。"""
    categories: dict[str, list[Paper]] = {}

    for p in papers:
        cat = _categorize_paper(p)
        categories.setdefault(cat, []).append(p)

    lines = ["## 2. 标题与摘要关键词粗分类", "", "类别只供浏览，不代表已经核实论文方法。", ""]

    for cat, cat_papers in sorted(categories.items(), key=lambda x: -len(x[1])):
        lines.append(f"### {cat}（{len(cat_papers)} 篇）")
        lines.append("")

        for p in cat_papers[:3]:
            year_str = f" ({p.year})" if p.year else ""
            cite_str = f"，被引 {p.citation_count} 次" if p.citation_count else ""
            lines.append(f"- **{p.title}** - {p.authors_str}{year_str}{cite_str}")

        if len(cat_papers) > 3:
            lines.append(f"- ...及其他 {len(cat_papers) - 3} 篇")
        lines.append("")

    return "\n".join(lines)


def _categorize_paper(paper: Paper) -> str:
    """基于关键词和标题对论文分类"""
    text = (paper.title + " " + (paper.abstract or "")).lower()

    category_keywords = {
        "深度学习方法": ["deep learning", "neural network", "cnn", "rnn", "transformer",
                     "深度学习", "神经网络", "卷积"],
        "机器学习方法": ["machine learning", "svm", "random forest", "classification",
                     "机器学习", "分类", "聚类", "回归"],
        "自然语言处理": ["nlp", "natural language", "text", "sentiment", "language model",
                     "自然语言", "文本", "情感分析"],
        "计算机视觉": ["image", "vision", "object detection", "segmentation",
                    "图像", "视觉", "目标检测"],
        "系统与工程": ["system", "framework", "architecture", "platform",
                    "系统", "框架", "架构", "平台"],
        "综述与调查": ["survey", "review", "overview", "综述", "调查", "概述"],
        "理论研究": ["theory", "proof", "mathematical", "理论", "证明", "数学"],
    }

    for cat, keywords in category_keywords.items():
        if any(kw in text for kw in keywords):
            return cat

    return "其他研究"


def _key_findings(papers: list[Paper], cite_format: str) -> str:
    """列出重点文献和数据库摘要摘录。"""
    top_papers = sorted(papers, key=lambda p: p.final_score, reverse=True)[:10]

    lines = ["## 3. 重点文献及摘要摘录", ""]

    for i, p in enumerate(top_papers, 1):
        year_str = f"({p.year})" if p.year else ""
        lines.append(f"**文献 {i}**: {p.title}")
        lines.append(f"- 作者: {p.authors_str} {year_str}")

        if p.abstract:
            abstract_short = p.abstract[:200] + "..." if len(p.abstract) > 200 else p.abstract
            lines.append(f"- 摘要: {abstract_short}")

        if p.citation_count:
            lines.append(f"- 影响力: 被引用 {p.citation_count} 次")

        if p.venue:
            lines.append(f"- 发表于: {p.venue}")

        lines.append("")

    return "\n".join(lines)


def _research_gaps(topic: str, papers: list[Paper]) -> str:
    """列出还需要从原文核实的事项，不从检索结果推断研究空白。"""
    lines = [
        "## 4. 后续核查",
        "",
        "- 阅读全文，核实研究问题、方法、样本和主要结论。",
        "- 核对每条 DOI、作者、年份及发表来源。",
        "- 结合更完整的检索结果，再判断是否存在研究空白。",
    ]
    return "\n".join(lines)


def _references(papers: list[Paper], cite_format: str) -> str:
    """生成参考文献列表"""
    lines = ["## 参考文献", ""]

    ordered = (sorted(papers, key=lambda p: (p.authors[0].lower() if p.authors else "", p.year or 0))
               if cite_format == "apa" else papers)
    for i, p in enumerate(ordered, 1):
        citation = format_paper_citation(p, style=cite_format)
        lines.append(f"[{i}] {citation}" if cite_format == "gb7714" else citation)

    return "\n".join(lines)
