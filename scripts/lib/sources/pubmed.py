"""PubMed 数据源 - 免费，生物医学文献"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper
from http_client import get_json
from dates import parse_year

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
MAX_RESULTS = 20


def search(query: str, limit: int = MAX_RESULTS) -> list[Paper]:
    """搜索 PubMed"""
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": min(limit, 100),
        "retmode": "json",
        "sort": "relevance",
    }

    search_data = get_json(ESEARCH_URL, params=search_params, timeout=15)
    if not search_data:
        return []

    id_list = search_data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return []

    summary_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "json",
    }

    summary_data = get_json(ESUMMARY_URL, params=summary_params, timeout=15)
    if not summary_data:
        return []

    results = summary_data.get("result", {})
    papers: list[Paper] = []

    for pmid in id_list:
        item = results.get(pmid)
        if not item or not isinstance(item, dict):
            continue

        title = item.get("title", "").strip()
        if not title:
            continue

        authors = []
        for a in (item.get("authors") or []):
            name = a.get("name", "")
            if name:
                authors.append(name)

        year = 0
        pub_date = item.get("pubdate", "")
        if pub_date:
            year = parse_year(pub_date)

        doi = ""
        for eid in (item.get("articleids") or []):
            if eid.get("idtype") == "doi":
                doi = eid.get("value", "")
                break

        venue = item.get("fulljournalname", "") or item.get("source", "")

        papers.append(Paper(
            title=title,
            authors=authors,
            year=year,
            doi=doi if doi else None,
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            source="PubMed",
            venue=venue,
            paper_id=pmid,
        ))

    return papers
