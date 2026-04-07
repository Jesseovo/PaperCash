"""arXiv 数据源 - 免费，STEM预印本"""

from __future__ import annotations
import xml.etree.ElementTree as ET
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper
from http_client import get_text
from dates import parse_year

BASE_URL = "http://export.arxiv.org/api/query"
MAX_RESULTS = 30

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def search(query: str, limit: int = MAX_RESULTS) -> list[Paper]:
    """搜索 arXiv"""
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(limit, 100),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    xml_text = get_text(BASE_URL, params=params, timeout=20)
    if not xml_text:
        return []

    return _parse_response(xml_text)


def _parse_response(xml_text: str) -> list[Paper]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    papers: list[Paper] = []
    for entry in root.findall("atom:entry", NS):
        title_el = entry.find("atom:title", NS)
        if title_el is None or not title_el.text:
            continue

        title = re.sub(r"\s+", " ", title_el.text.strip())

        authors = []
        for author in entry.findall("atom:author", NS):
            name_el = author.find("atom:name", NS)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        abstract = ""
        summary_el = entry.find("atom:summary", NS)
        if summary_el is not None and summary_el.text:
            abstract = re.sub(r"\s+", " ", summary_el.text.strip())

        published = ""
        pub_el = entry.find("atom:published", NS)
        if pub_el is not None and pub_el.text:
            published = pub_el.text.strip()
        year = parse_year(published)

        arxiv_id = ""
        id_el = entry.find("atom:id", NS)
        if id_el is not None and id_el.text:
            arxiv_id = id_el.text.strip().split("/abs/")[-1]

        pdf_url = ""
        for link in entry.findall("atom:link", NS):
            if link.get("title") == "pdf":
                pdf_url = link.get("href", "")
                break

        url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""

        doi = None
        doi_el = entry.find("arxiv:doi", NS)
        if doi_el is not None and doi_el.text:
            doi = doi_el.text.strip()

        categories = []
        for cat in entry.findall("atom:category", NS):
            term = cat.get("term", "")
            if term:
                categories.append(term)

        papers.append(Paper(
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            doi=doi,
            url=url,
            pdf_url=pdf_url,
            source="arXiv",
            venue="arXiv",
            keywords=categories,
            paper_id=arxiv_id,
        ))

    return papers
