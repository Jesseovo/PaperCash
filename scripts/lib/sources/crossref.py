"""CrossRef 数据源 - 免费，1.4亿 DOI 元数据"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper
from http_client import get_json
from dates import parse_year

BASE_URL = "https://api.crossref.org/works"
MAX_RESULTS = 30


def search(query: str, limit: int = MAX_RESULTS) -> list[Paper]:
    """搜索 CrossRef"""
    params = {
        "query": query,
        "rows": min(limit, 100),
        "sort": "relevance",
        "order": "desc",
        "select": "DOI,title,author,published-print,published-online,"
                  "abstract,is-referenced-by-count,container-title,URL,subject",
    }

    data = get_json(BASE_URL, params=params, timeout=20)
    if not data or "message" not in data:
        return []

    items = data["message"].get("items", [])
    papers: list[Paper] = []

    for item in items:
        titles = item.get("title", [])
        if not titles:
            continue
        title = titles[0]

        authors = []
        for a in (item.get("author") or []):
            given = a.get("given", "")
            family = a.get("family", "")
            name = f"{given} {family}".strip()
            if name:
                authors.append(name)

        year = 0
        for date_key in ("published-print", "published-online"):
            date_parts = item.get(date_key, {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]
                break

        abstract = item.get("abstract", "")
        if abstract:
            import re
            import html as html_mod
            abstract = re.sub(r"<[^>]+>", "", abstract).strip()
            abstract = html_mod.unescape(abstract)

        venues = item.get("container-title", [])
        venue = venues[0] if venues else ""
        if venue:
            import html as html_mod
            venue = html_mod.unescape(venue)

        subjects = item.get("subject", [])

        papers.append(Paper(
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            doi=item.get("DOI"),
            url=item.get("URL", ""),
            citation_count=item.get("is-referenced-by-count", 0) or 0,
            source="CrossRef",
            venue=venue,
            keywords=subjects,
        ))

    return papers


def get_by_doi(doi: str) -> Paper | None:
    """通过 DOI 获取文献元数据"""
    from urllib.parse import quote
    encoded_doi = quote(doi, safe="")
    data = get_json(f"{BASE_URL}/{encoded_doi}")
    if not data or "message" not in data:
        return None

    import html as html_mod
    item = data["message"]
    titles = item.get("title", [])
    if not titles:
        return None
    titles = [html_mod.unescape(t) for t in titles]

    authors = []
    for a in (item.get("author") or []):
        given = a.get("given", "")
        family = a.get("family", "")
        name = f"{given} {family}".strip()
        if name:
            authors.append(name)

    year = 0
    for date_key in ("published-print", "published-online"):
        date_parts = item.get(date_key, {}).get("date-parts", [[]])
        if date_parts and date_parts[0]:
            year = date_parts[0][0]
            break

    abstract = item.get("abstract", "")
    if abstract:
        import re
        import html as html_mod
        abstract = re.sub(r"<[^>]+>", "", abstract).strip()
        abstract = html_mod.unescape(abstract)

    venues = item.get("container-title", [])

    return Paper(
        title=titles[0],
        authors=authors,
        year=year,
        abstract=abstract,
        doi=doi,
        url=item.get("URL", ""),
        citation_count=item.get("is-referenced-by-count", 0) or 0,
        source="CrossRef",
        venue=venues[0] if venues else "",
        keywords=item.get("subject", []),
    )
