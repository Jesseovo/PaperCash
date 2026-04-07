"""Semantic Scholar 数据源 - 免费，2亿+论文"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper
from http_client import get_json
from env import get as env_get

BASE_URL = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,authors,year,abstract,citationCount,externalIds,url,venue,s2FieldsOfStudy"
MAX_RESULTS = 30


def search(query: str, limit: int = MAX_RESULTS) -> list[Paper]:
    """搜索 Semantic Scholar"""
    api_key = env_get("SEMANTIC_SCHOLAR_API_KEY")
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": FIELDS,
    }

    data = get_json(f"{BASE_URL}/paper/search", params=params, headers=headers)
    if not data or "data" not in data:
        return []

    papers: list[Paper] = []
    for item in data["data"]:
        if not item.get("title"):
            continue

        authors = []
        for a in (item.get("authors") or []):
            name = a.get("name", "")
            if name:
                authors.append(name)

        doi = None
        ext_ids = item.get("externalIds") or {}
        if ext_ids.get("DOI"):
            doi = ext_ids["DOI"]

        paper = Paper(
            title=item["title"],
            authors=authors,
            year=item.get("year"),
            abstract=item.get("abstract"),
            doi=doi,
            url=item.get("url", ""),
            citation_count=item.get("citationCount", 0) or 0,
            source="Semantic Scholar",
            venue=item.get("venue", ""),
            paper_id=item.get("paperId"),
        )

        fields = item.get("s2FieldsOfStudy") or []
        paper.keywords = [f["category"] for f in fields if f.get("category")]

        papers.append(paper)

    return papers


def get_paper_by_doi(doi: str) -> Paper | None:
    """通过 DOI 获取论文详情"""
    data = get_json(f"{BASE_URL}/paper/DOI:{doi}", params={"fields": FIELDS})
    if not data or not data.get("title"):
        return None

    authors = [a.get("name", "") for a in (data.get("authors") or []) if a.get("name")]
    ext_ids = data.get("externalIds") or {}

    return Paper(
        title=data["title"],
        authors=authors,
        year=data.get("year"),
        abstract=data.get("abstract"),
        doi=ext_ids.get("DOI", doi),
        url=data.get("url", ""),
        citation_count=data.get("citationCount", 0) or 0,
        source="Semantic Scholar",
        venue=data.get("venue", ""),
        paper_id=data.get("paperId"),
    )


def get_citations(paper_id: str, limit: int = 10) -> list[Paper]:
    """获取引用该论文的文献"""
    params = {"fields": "title,authors,year,citationCount,externalIds", "limit": limit}
    data = get_json(f"{BASE_URL}/paper/{paper_id}/citations", params=params)
    if not data or "data" not in data:
        return []

    papers: list[Paper] = []
    for item in data["data"]:
        citing = item.get("citingPaper", {})
        if not citing.get("title"):
            continue
        authors = [a.get("name", "") for a in (citing.get("authors") or []) if a.get("name")]
        ext_ids = citing.get("externalIds") or {}
        papers.append(Paper(
            title=citing["title"],
            authors=authors,
            year=citing.get("year"),
            doi=ext_ids.get("DOI"),
            citation_count=citing.get("citationCount", 0) or 0,
            source="Semantic Scholar",
        ))
    return papers
