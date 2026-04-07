"""参考文献格式化 - GB/T 7714 / APA / BibTeX / MLA / Chicago"""

from __future__ import annotations
import html as html_mod
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper


def _clean_text(text: str) -> str:
    return html_mod.unescape(text) if text else text


_CONF_VENUE_MARKERS = ("conference", "proceedings", "symposium", "workshop")


def _venue_suggests_book(venue_lower: str) -> bool:
    return any(
        k in venue_lower
        for k in ("isbn", "publisher", "press", "monograph", "专著", "出版社")
    )


def _detect_doc_type(paper: Paper) -> str:
    """GB/T 7714 文献类型标识"""
    venue_raw = (paper.venue or "").strip()
    venue_l = venue_raw.lower()
    has_venue = bool(venue_raw)
    has_doi = bool(paper.doi and str(paper.doi).strip())
    has_url = bool(paper.url and str(paper.url).strip())
    ptype = (getattr(paper, "paper_type", None) or "").strip().lower()

    if has_url and not has_doi and not has_venue:
        return "EB/OL"

    if has_venue and any(m in venue_l for m in _CONF_VENUE_MARKERS):
        return "C"

    if has_venue and ("thesis" in venue_l or "dissertation" in venue_l):
        return "D"

    if ptype == "book" or (has_venue and _venue_suggests_book(venue_l)):
        return "M"

    if has_venue:
        return "J/OL" if has_doi else "J"

    if has_doi:
        return "J/OL"

    return "M"


def _get_paper_from_doi(doi: str) -> Paper | None:
    """通过 DOI 获取论文信息（先 CrossRef 再 Semantic Scholar）"""
    from sources.crossref import get_by_doi as cr_get
    paper = cr_get(doi)
    if paper:
        return paper

    from sources.semantic_scholar import get_paper_by_doi as ss_get
    return ss_get(doi)


def format_gb7714(paper: Paper) -> str:
    """GB/T 7714-2015 格式"""
    authors = ", ".join(paper.authors[:3])
    if len(paper.authors) > 3:
        authors += ", 等"

    year = paper.year or "n.d."
    title = _clean_text(paper.title)
    doc = _detect_doc_type(paper)
    marker = f"[{doc}]"

    if paper.venue:
        venue = _clean_text(paper.venue)
        tail = f"{venue}, {year}."
        if paper.doi:
            tail += f" DOI: {paper.doi}."
        result = f"[{paper.citation_key}] {authors}. {title}{marker}. {tail}"
    elif paper.doi:
        result = f"[{paper.citation_key}] {authors}. {title}{marker}. {year}. DOI: {paper.doi}."
    elif paper.url:
        result = f"[{paper.citation_key}] {authors}. {title}{marker}. {year}. {paper.url}."
    else:
        result = f"[{paper.citation_key}] {authors}. {title}{marker}. {year}."

    return result


def format_apa(paper: Paper) -> str:
    """APA 7th Edition 格式"""
    if not paper.authors:
        author_str = "Unknown"
    elif len(paper.authors) == 1:
        parts = paper.authors[0].split()
        if len(parts) >= 2:
            author_str = f"{parts[-1]}, {'. '.join(p[0] for p in parts[:-1])}."
        else:
            author_str = paper.authors[0]
    else:
        formatted = []
        for a in paper.authors[:20]:
            parts = a.split()
            if len(parts) >= 2:
                formatted.append(f"{parts[-1]}, {'. '.join(p[0] for p in parts[:-1])}.")
            else:
                formatted.append(a)

        if len(formatted) <= 2:
            author_str = " & ".join(formatted)
        else:
            author_str = ", ".join(formatted[:-1]) + ", & " + formatted[-1]

    year = f"({paper.year})" if paper.year else "(n.d.)"
    title = paper.title

    parts = [f"{author_str} {year}. {title}."]
    if paper.venue:
        parts.append(f" *{paper.venue}*.")
    if paper.doi:
        parts.append(f" https://doi.org/{paper.doi}")

    return "".join(parts)


def format_mla(paper: Paper) -> str:
    """MLA 9th Edition 格式"""
    if not paper.authors:
        author_str = "Unknown"
    elif len(paper.authors) == 1:
        parts = paper.authors[0].split()
        if len(parts) >= 2:
            author_str = f"{parts[-1]}, {' '.join(parts[:-1])}"
        else:
            author_str = paper.authors[0]
    elif len(paper.authors) == 2:
        p1 = paper.authors[0].split()
        author_str = f"{p1[-1]}, {' '.join(p1[:-1])}, and {paper.authors[1]}"
    else:
        p1 = paper.authors[0].split()
        author_str = f"{p1[-1]}, {' '.join(p1[:-1])}, et al."

    parts = [f'{author_str}. "{paper.title}."']
    if paper.venue:
        parts.append(f" *{paper.venue}*,")
    if paper.year:
        parts.append(f" {paper.year}.")
    if paper.doi:
        parts.append(f" https://doi.org/{paper.doi}.")

    return "".join(parts)


def format_chicago(paper: Paper) -> str:
    """Chicago 格式"""
    if not paper.authors:
        author_str = "Unknown"
    elif len(paper.authors) == 1:
        parts = paper.authors[0].split()
        if len(parts) >= 2:
            author_str = f"{parts[-1]}, {' '.join(parts[:-1])}"
        else:
            author_str = paper.authors[0]
    else:
        formatted_first = paper.authors[0].split()
        if len(formatted_first) >= 2:
            first = f"{formatted_first[-1]}, {' '.join(formatted_first[:-1])}"
        else:
            first = paper.authors[0]

        if len(paper.authors) == 2:
            author_str = f"{first} and {paper.authors[1]}"
        else:
            others = ", ".join(paper.authors[1:-1])
            author_str = f"{first}, {others}, and {paper.authors[-1]}"

    parts = [f'{author_str}. "{paper.title}."']
    if paper.venue:
        parts.append(f" *{paper.venue}*")
    if paper.year:
        parts.append(f" ({paper.year}).")
    if paper.doi:
        parts.append(f" https://doi.org/{paper.doi}.")

    return "".join(parts)


def format_bibtex(paper: Paper) -> str:
    """BibTeX 格式"""
    key = paper.citation_key
    authors_bibtex = " and ".join(paper.authors) if paper.authors else "Unknown"

    lines = [f"@article{{{key},"]
    lines.append(f'  title = {{{paper.title}}},')
    lines.append(f'  author = {{{authors_bibtex}}},')
    if paper.year:
        lines.append(f'  year = {{{paper.year}}},')
    if paper.venue:
        lines.append(f'  journal = {{{paper.venue}}},')
    if paper.doi:
        lines.append(f'  doi = {{{paper.doi}}},')
    if paper.url:
        lines.append(f'  url = {{{paper.url}}},')
    lines.append("}")

    return "\n".join(lines)


_FORMATTERS = {
    "gb7714": format_gb7714,
    "apa": format_apa,
    "mla": format_mla,
    "chicago": format_chicago,
    "bibtex": format_bibtex,
}


def format_citation(doi: str, style: str = "gb7714") -> str:
    """格式化单个 DOI 的引用"""
    paper = _get_paper_from_doi(doi)
    if not paper:
        return f"[错误] 无法通过 DOI '{doi}' 获取文献信息。请检查 DOI 是否正确。"

    formatter = _FORMATTERS.get(style, format_gb7714)
    return formatter(paper)


def format_citations_batch(dois: list[str], style: str = "gb7714") -> str:
    """批量格式化多个 DOI"""
    results: list[str] = []
    formatter = _FORMATTERS.get(style, format_gb7714)

    for i, doi in enumerate(dois, 1):
        doi = doi.strip()
        if not doi:
            continue
        paper = _get_paper_from_doi(doi)
        if paper:
            citation = formatter(paper)
            results.append(f"[{i}] {citation}")
        else:
            results.append(f"[{i}] [错误] 无法解析 DOI: {doi}")

    return "\n\n".join(results)


def format_paper_citation(paper: Paper, style: str = "gb7714") -> str:
    """直接格式化 Paper 对象"""
    formatter = _FORMATTERS.get(style, format_gb7714)
    return formatter(paper)
