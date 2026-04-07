"""万方数据源 - 需要 Cookie 配置"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper
from http_client import get_text
from env import get as env_get
from dates import parse_year

SEARCH_URL = "https://s.wanfangdata.com.cn/paper"

_HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.wanfangdata.com.cn/",
}


def is_available() -> bool:
    return bool(env_get("WANFANG_COOKIE"))


def search(query: str, limit: int = 20) -> list[Paper]:
    """搜索万方数据"""
    cookie = env_get("WANFANG_COOKIE")
    if not cookie:
        return []

    headers = {**_HEADERS_BASE, "Cookie": cookie}

    params = {
        "q": query,
        "p": "1",
        "s": str(limit),
        "style": "detail",
        "f": "top",
    }

    try:
        html = get_text(SEARCH_URL, params=params, headers=headers, timeout=15)
        if not html:
            return []
        return _parse_results(html)
    except Exception:
        return []


def _parse_results(html: str) -> list[Paper]:
    """解析万方搜索结果"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    soup = BeautifulSoup(html, "html.parser")
    papers: list[Paper] = []

    items = soup.select("div.normal-list") or soup.select("div.record-item")
    for item in items:
        title_el = item.select_one("a.title") or item.select_one("span.title a")
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        if not title:
            continue

        url = title_el.get("href", "")
        if url and not url.startswith("http"):
            url = "https://www.wanfangdata.com.cn" + url

        authors: list[str] = []
        author_el = item.select_one(".author") or item.select_one(".creator")
        if author_el:
            for a_tag in author_el.select("a"):
                name = a_tag.get_text(strip=True)
                if name:
                    authors.append(name)

        year = 0
        date_el = item.select_one(".year") or item.select_one(".publish-date")
        if date_el:
            year = parse_year(date_el.get_text(strip=True))

        abstract = ""
        abs_el = item.select_one(".abstract") or item.select_one(".summary")
        if abs_el:
            abstract = abs_el.get_text(strip=True)

        venue = ""
        source_el = item.select_one(".periodical a") or item.select_one(".source a")
        if source_el:
            venue = source_el.get_text(strip=True)

        papers.append(Paper(
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            url=url,
            source="万方",
            venue=venue,
        ))

    return papers
