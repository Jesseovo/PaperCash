"""百度学术数据源 - 免费，中文论文元数据"""

from __future__ import annotations
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper
from http_client import get_text
from dates import parse_year

BASE_URL = "https://xueshu.baidu.com/s"
MAX_RESULTS = 20

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def search(query: str, limit: int = MAX_RESULTS) -> list[Paper]:
    """搜索百度学术"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    params = {
        "wd": query,
        "pn": 0,
        "ie": "utf-8",
    }

    html = get_text(BASE_URL, params=params, headers=_HEADERS, timeout=15)
    if not html:
        return []

    return _parse_html(html, limit)


def _parse_html(html: str, limit: int) -> list[Paper]:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    soup = BeautifulSoup(html, "html.parser")
    papers: list[Paper] = []

    results = soup.select("div.result")
    if not results:
        results = soup.select("div.sc_content")

    for item in results[:limit]:
        title_el = item.select_one("h3 a") or item.select_one(".t a")
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        title = re.sub(r"\s+", " ", title)
        if not title or len(title) < 3:
            continue

        url = title_el.get("href", "")

        authors: list[str] = []
        author_el = item.select_one(".author_text") or item.select_one(".c_author")
        if author_el:
            author_text = author_el.get_text(strip=True)
            author_text = re.sub(r"^作者[:：]?\s*", "", author_text)
            authors = [a.strip() for a in re.split(r"[,，;；、\s]+", author_text) if a.strip()]

        year = 0
        year_el = item.select_one(".year_text") or item.select_one(".c_year")
        if year_el:
            year = parse_year(year_el.get_text(strip=True))
        if not year:
            year_match = re.search(r"(19|20)\d{2}", item.get_text())
            if year_match:
                year = int(year_match.group())

        abstract = ""
        abs_el = item.select_one(".c_abstract") or item.select_one(".abstract")
        if abs_el:
            abstract = abs_el.get_text(strip=True)
            abstract = re.sub(r"^摘要[:：]?\s*", "", abstract)

        venue = ""
        venue_el = item.select_one(".venue_text") or item.select_one(".c_source")
        if venue_el:
            venue = venue_el.get_text(strip=True)

        cite_count = 0
        cite_el = item.select_one(".sc_cite_cont") or item.select_one(".cite_num")
        if cite_el:
            cite_match = re.search(r"\d+", cite_el.get_text())
            if cite_match:
                cite_count = int(cite_match.group())

        papers.append(Paper(
            title=title,
            authors=authors[:5],
            year=year,
            abstract=abstract,
            url=url,
            citation_count=cite_count,
            source="百度学术",
            venue=venue,
        ))

    return papers
