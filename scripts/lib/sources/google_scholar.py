"""Google Scholar 数据源 - 可选，需代理"""

from __future__ import annotations
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper
from http_client import get_text
from env import get as env_get
from dates import parse_year

BASE_URL = "https://scholar.google.com/scholar"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
}


def is_available() -> bool:
    return bool(env_get("GOOGLE_SCHOLAR_PROXY"))


def search(query: str, limit: int = 20) -> list[Paper]:
    """搜索 Google Scholar（需代理）"""
    proxy = env_get("GOOGLE_SCHOLAR_PROXY")
    if not proxy:
        return []

    params = {
        "q": query,
        "hl": "en",
        "num": min(limit, 20),
    }

    import requests
    try:
        session = requests.Session()
        session.headers.update(_HEADERS)
        if proxy:
            session.proxies = {"http": proxy, "https": proxy}
        r = session.get(BASE_URL, params=params, timeout=15)
        r.raise_for_status()
        html = r.text
    except Exception:
        return []

    return _parse_results(html)


def _parse_results(html: str) -> list[Paper]:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    soup = BeautifulSoup(html, "html.parser")
    papers: list[Paper] = []

    for item in soup.select("div.gs_r.gs_or.gs_scl"):
        title_el = item.select_one("h3.gs_rt a")
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        url = title_el.get("href", "")

        authors: list[str] = []
        year = 0
        venue = ""
        meta_el = item.select_one("div.gs_a")
        if meta_el:
            meta_text = meta_el.get_text()
            parts = meta_text.split(" - ")
            if parts:
                raw_authors = parts[0].strip()
                authors = [a.strip() for a in raw_authors.split(",") if a.strip() and a.strip() != "…"]
            year_match = re.search(r"(19|20)\d{2}", meta_text)
            if year_match:
                year = int(year_match.group())
            if len(parts) >= 2:
                venue = parts[1].strip()

        abstract = ""
        abs_el = item.select_one("div.gs_rs")
        if abs_el:
            abstract = abs_el.get_text(strip=True)

        cite_count = 0
        cite_el = item.select_one("a[href*='cites']")
        if cite_el:
            cite_match = re.search(r"\d+", cite_el.get_text())
            if cite_match:
                cite_count = int(cite_match.group())

        papers.append(Paper(
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            url=url,
            citation_count=cite_count,
            source="Google Scholar",
            venue=venue,
        ))

    return papers
