"""论文评分系统

评分公式: relevance(40%) + citations(25%) + recency(20%) + source_authority(15%)
"""

from __future__ import annotations
import math

from schema import Paper
from relevance import compute_relevance
from dates import recency_score as calc_recency

SOURCE_AUTHORITY = {
    "Semantic Scholar": 0.9,
    "CrossRef": 0.85,
    "arXiv": 0.8,
    "PubMed": 0.9,
    "Google Scholar": 0.85,
    "百度学术": 0.7,
    "知网": 0.95,
    "万方": 0.85,
    "维普": 0.8,
}

W_RELEVANCE = 0.40
W_CITATIONS = 0.25
W_RECENCY = 0.20
W_AUTHORITY = 0.15


def _citation_score(count: int) -> float:
    """引用数归一化 (0.0 ~ 1.0)，使用对数缩放"""
    if count <= 0:
        return 0.0
    return min(1.0, math.log1p(count) / math.log1p(10000))


def score_paper(paper: Paper, query: str) -> float:
    """为单篇论文计算综合评分 (0 ~ 100)"""
    rel = compute_relevance(query, paper.title, paper.abstract or "")
    paper.relevance_score = rel

    cite = _citation_score(paper.citation_count)
    rec = calc_recency(paper.year) if paper.year else 0.3
    auth = SOURCE_AUTHORITY.get(paper.source, 0.5)

    raw = (W_RELEVANCE * rel + W_CITATIONS * cite +
           W_RECENCY * rec + W_AUTHORITY * auth)

    paper.final_score = round(raw * 100, 1)
    return paper.final_score


def score_papers(papers: list[Paper], query: str) -> list[Paper]:
    """批量评分并按分数降序排列"""
    for p in papers:
        score_paper(p, query)
    papers.sort(key=lambda p: p.final_score, reverse=True)
    return papers
