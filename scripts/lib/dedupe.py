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
    norm = _normalize_title(title)
    words = norm.split()
    return " ".join(words[:8])


def dedupe_papers(papers: list[Paper]) -> list[Paper]:
    """基于标题和 DOI 去重，保留分数最高的"""
    seen_dois: dict[str, int] = {}
    seen_titles: dict[str, int] = {}
    result: list[Paper] = []

    sorted_papers = sorted(papers, key=lambda p: p.final_score, reverse=True)

    for paper in sorted_papers:
        if paper.doi:
            doi_lower = paper.doi.lower()
            if doi_lower in seen_dois:
                existing = result[seen_dois[doi_lower]]
                if paper.abstract and not existing.abstract:
                    existing.abstract = paper.abstract
                if paper.citation_count > existing.citation_count:
                    existing.citation_count = paper.citation_count
                continue
            seen_dois[doi_lower] = len(result)

        fp = _title_fingerprint(paper.title)
        if fp and fp in seen_titles:
            existing = result[seen_titles[fp]]
            if paper.abstract and not existing.abstract:
                existing.abstract = paper.abstract
            if paper.citation_count > existing.citation_count:
                existing.citation_count = paper.citation_count
            continue
        if fp:
            seen_titles[fp] = len(result)

        result.append(paper)

    return result
