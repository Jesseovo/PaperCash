"""论文去重"""

from __future__ import annotations
import re

from schema import Paper


def _normalize_title(title: str) -> str:
    text = title.lower().strip()
    text = re.sub(r"[^\w\s\u4e00-\u9fff]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _title_fingerprint(title: str) -> str:
    return _normalize_title(title)


def _merge_metadata(existing: Paper, paper: Paper) -> None:
    """保留高分记录，补齐另一个数据源提供的元数据。"""
    for field_name in ("abstract", "doi", "url", "pdf_url", "venue", "year",
                       "volume", "issue", "pages"):
        if not getattr(existing, field_name) and getattr(paper, field_name):
            setattr(existing, field_name, getattr(paper, field_name))
    if not existing.authors and paper.authors:
        existing.authors = paper.authors
    existing.citation_count = max(existing.citation_count, paper.citation_count)


def dedupe_papers(papers: list[Paper]) -> list[Paper]:
    """基于标题和 DOI 去重，保留分数最高的"""
    seen_dois: dict[str, int] = {}
    seen_titles: dict[str, int] = {}
    result: list[Paper] = []

    sorted_papers = sorted(papers, key=lambda p: p.final_score, reverse=True)

    for paper in sorted_papers:
        doi_lower = paper.doi.strip().lower() if paper.doi else ""
        fp = _title_fingerprint(paper.title)
        existing_index = seen_dois.get(doi_lower) if doi_lower else None
        if existing_index is None and fp:
            existing_index = seen_titles.get(fp)
        if existing_index is not None:
            _merge_metadata(result[existing_index], paper)
            if doi_lower:
                seen_dois[doi_lower] = existing_index
            if fp:
                seen_titles[fp] = existing_index
            continue

        index = len(result)
        result.append(paper)
        if doi_lower:
            seen_dois[doi_lower] = index
        if fp:
            seen_titles[fp] = index

    return result
