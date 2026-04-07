"""文献综述生成"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper, SearchResult
from features.citation import format_paper_citation
from query import is_chinese


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
        f'关于"{topic}"的研究在学术界受到了广泛关注。'
        f"本综述涵盖了 {year_range} 年间的 {len(papers)} 篇相关文献，"
        f"累计被引用 {total_citations} 次。",
    ]

    if high_impact:
        lines.append(f"其中，{len(high_impact)} 篇高影响力论文（被引用 50 次以上）"
                      f"对该领域的发展产生了重要推动作用。")

    if years:
        recent = [p for p in papers if p.year and p.year >= years[-1] - 2]
        lines.append(f"近三年（{years[-1] - 2}-{years[-1]}）发表的 {len(recent)} 篇论文"
                      f"表明该领域仍在活跃发展中。")

    return "\n".join(lines)


def _methodology_classification(papers: list[Paper]) -> str:
    """按研究方法/领域对论文进行简单分类"""
    categories: dict[str, list[Paper]] = {}

    for p in papers:
        cat = _categorize_paper(p)
        categories.setdefault(cat, []).append(p)

    lines = ["## 2. 研究方法分类", ""]

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
    """总结关键发现"""
    top_papers = sorted(papers, key=lambda p: p.final_score, reverse=True)[:10]

    lines = ["## 3. 主要研究发现", ""]

    for i, p in enumerate(top_papers, 1):
        year_str = f"({p.year})" if p.year else ""
        lines.append(f"**发现 {i}**: {p.title}")
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
    """分析研究空白"""
    lines = [
        "## 4. 研究空白与未来方向",
        "",
        f'基于对以上 {len(papers)} 篇文献的分析，当前"{topic}"领域存在以下研究空白：',
        "",
    ]

    years = [p.year for p in papers if p.year]
    if years:
        avg_year = sum(years) / len(years)
        if avg_year < 2023:
            lines.append("1. **时效性不足**：部分研究成果发表较早，可能未涵盖最新技术进展，"
                         "需要结合最新文献进行补充。")

    venues = set(p.venue for p in papers if p.venue)
    if len(venues) < 3:
        lines.append("2. **研究视角单一**：现有文献主要集中在少数期刊/会议，"
                     "建议拓展更多领域的交叉研究视角。")

    cn_papers = [p for p in papers if any(is_chinese(c) for c in p.title)]
    en_papers = [p for p in papers if not any(is_chinese(c) for c in p.title)]
    if cn_papers and en_papers:
        lines.append(f"3. **中外研究对比**：检索到 {len(cn_papers)} 篇中文文献和 "
                     f"{len(en_papers)} 篇英文文献，建议深入对比中外研究异同。")
    elif not cn_papers:
        lines.append("3. **缺少中文研究**：当前检索结果以英文文献为主，"
                     "建议补充国内学者的相关研究。")

    lines.append("")
    lines.append("**建议**：在撰写论文时，应结合以上文献综述，明确自身研究的创新点和贡献，"
                 "避免重复已有工作。")

    return "\n".join(lines)


def _references(papers: list[Paper], cite_format: str) -> str:
    """生成参考文献列表"""
    lines = ["## 参考文献", ""]

    for i, p in enumerate(papers, 1):
        citation = format_paper_citation(p, style=cite_format)
        lines.append(f"[{i}] {citation}")

    return "\n".join(lines)
