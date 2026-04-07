"""输出渲染"""

from __future__ import annotations
import json

from schema import Paper, SearchResult, CheckResult


def render_search(result: SearchResult, mode: str = "compact") -> str:
    """渲染搜索结果"""
    if mode == "json":
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    elif mode == "context":
        return _render_context(result)
    elif mode == "md":
        return _render_markdown(result)
    else:
        return _render_compact(result)


def _render_compact(result: SearchResult) -> str:
    lines: list[str] = []
    lines.append(f"\n{'=' * 60}")
    lines.append(f"  PaperCash 论文检索结果")
    lines.append(f"{'=' * 60}")
    lines.append(f"  查询: {result.query}")
    lines.append(f"  找到: {result.total_found} 篇 | 数据源: {', '.join(result.sources_used)}")
    lines.append(f"  耗时: {result.search_time_ms}ms")
    lines.append(f"{'=' * 60}\n")

    for i, p in enumerate(result.papers, 1):
        score_str = f"(score:{p.final_score:.0f})"
        cite_str = f"[{p.citation_count} cited]" if p.citation_count else ""
        year_str = f"[{p.year}]" if p.year else ""
        lines.append(f"  #{i} {score_str} {p.title}")
        lines.append(f"       {p.authors_str} {year_str} {cite_str} via {p.source}")
        if p.abstract:
            abstract_short = p.abstract[:150] + "..." if len(p.abstract) > 150 else p.abstract
            lines.append(f"       {abstract_short}")
        if p.doi:
            lines.append(f"       DOI: {p.doi}")
        lines.append("")

    return "\n".join(lines)


def _render_context(result: SearchResult) -> str:
    """渲染为 Agent 可消费的上下文格式"""
    lines: list[str] = []
    lines.append(f"SEARCH_QUERY: {result.query}")
    lines.append(f"TOTAL_RESULTS: {result.total_found}")
    lines.append(f"SOURCES: {','.join(result.sources_used)}")
    lines.append("")

    for i, p in enumerate(result.papers, 1):
        lines.append(f"--- PAPER {i} ---")
        lines.append(f"TITLE: {p.title}")
        lines.append(f"AUTHORS: {', '.join(p.authors)}")
        lines.append(f"YEAR: {p.year or 'N/A'}")
        lines.append(f"CITATIONS: {p.citation_count}")
        lines.append(f"DOI: {p.doi or 'N/A'}")
        lines.append(f"SOURCE: {p.source}")
        lines.append(f"VENUE: {p.venue or 'N/A'}")
        lines.append(f"SCORE: {p.final_score}")
        if p.abstract:
            lines.append(f"ABSTRACT: {p.abstract[:500]}")
        if p.url:
            lines.append(f"URL: {p.url}")
        lines.append("")

    return "\n".join(lines)


def _render_markdown(result: SearchResult) -> str:
    lines: list[str] = []
    lines.append(f"# PaperCash 论文检索结果\n")
    lines.append(f"**查询**: {result.query}  ")
    lines.append(f"**结果**: {result.total_found} 篇 | **数据源**: {', '.join(result.sources_used)}  ")
    lines.append(f"**耗时**: {result.search_time_ms}ms\n")
    lines.append("---\n")

    for i, p in enumerate(result.papers, 1):
        cite_str = f" | {p.citation_count} cited" if p.citation_count else ""
        year_str = f" ({p.year})" if p.year else ""
        lines.append(f"### {i}. {p.title}\n")
        lines.append(f"**作者**: {p.authors_str}{year_str}{cite_str}  ")
        lines.append(f"**来源**: {p.source} | **评分**: {p.final_score:.0f}  ")
        if p.venue:
            lines.append(f"**期刊/会议**: {p.venue}  ")
        if p.abstract:
            abstract_short = p.abstract[:300] + "..." if len(p.abstract) > 300 else p.abstract
            lines.append(f"\n> {abstract_short}\n")
        if p.doi:
            lines.append(f"DOI: `{p.doi}`  ")
        if p.url:
            lines.append(f"链接: {p.url}  ")
        lines.append("")

    return "\n".join(lines)


def render_check_results(
    results: list[CheckResult],
    mode: str = "compact",
    stats: dict | None = None,
) -> str:
    if mode == "json":
        rows = [{
            "sentence": r.sentence,
            "similarity": r.similarity,
            "risk_level": r.risk_level,
            "matched_title": r.matched_title,
            "suggestion": r.suggestion,
        } for r in results]
        if stats is not None:
            return json.dumps(
                {"statistics": stats, "results": rows},
                ensure_ascii=False,
                indent=2,
            )
        return json.dumps(rows, ensure_ascii=False, indent=2)

    lines: list[str] = []
    lines.append(f"\n{'=' * 60}")
    lines.append(f"  PaperCash 查重预检报告")
    lines.append(f"{'=' * 60}\n")

    if stats is not None:
        lines.append(
            f"  总句数: {stats['total_sentences']} | 检查句数: {stats['checked_sentences']} | "
            f"高风险: {stats['high_risk']} | 中风险: {stats['medium_risk']} | "
            f"低风险: {stats['low_risk']}\n"
        )
    else:
        high = sum(1 for r in results if r.risk_level == "high")
        med = sum(1 for r in results if r.risk_level == "medium")
        low = sum(1 for r in results if r.risk_level == "low")
        lines.append(
            f"  总句数: {len(results)} | 高风险: {high} | 中风险: {med} | 低风险: {low}\n"
        )

    risk_order = {"high": 0, "medium": 1, "low": 2}
    sorted_results = sorted(results, key=lambda r: risk_order.get(r.risk_level, 3))

    for r in sorted_results:
        if r.risk_level == "low":
            continue
        tag = "[高风险]" if r.risk_level == "high" else "[中风险]"
        lines.append(f"  {tag} 相似度: {r.similarity:.0%}")
        lines.append(f"    原句: {r.sentence[:100]}...")
        if r.matched_title:
            lines.append(f"    匹配: {r.matched_title}")
        if r.suggestion:
            lines.append(f"    建议: {r.suggestion}")
        lines.append("")

    lines.append("  ⚠️  声明：本结果仅供参考，正式查重请使用学校指定系统。\n")
    return "\n".join(lines)
