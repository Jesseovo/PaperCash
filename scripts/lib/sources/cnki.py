"""知网 CNKI 数据源 - 需要 Cookie 配置"""

from __future__ import annotations
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper
from http_client import get_text
from env import get as env_get
from dates import parse_year

SEARCH_URL = "https://kns.cnki.net/kns8s/brief/grid"

_HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://kns.cnki.net/",
}


def is_available() -> bool:
    return bool(env_get("CNKI_COOKIE"))


def search(query: str, limit: int = 20) -> list[Paper]:
    """搜索知网

    注意：知网没有公开API，此模块通过Cookie模拟登录用户搜索。
    需要在配置文件中设置 CNKI_COOKIE。
    """
    cookie = env_get("CNKI_COOKIE")
    if not cookie:
        return []

    headers = {**_HEADERS_BASE, "Cookie": cookie}

    params = {
        "QueryJson": f'{{"Platform":"","DBCode":"CFLS","KuaKuCode":"CJFQ,CDMD,CIPD,CCND,CISD,SNAD,BDZK,CCJD,CCVD,CJFN",'
                     f'"QNode":{{"QGroup":[{{"Key":"Subject","Title":"","Logic":1,"Items":[{{"Title":"主题",'
                     f'"Name":"SU","Value":"{query}","Operate":"%3D","BlurType":""}}'
                     f'],"ChildItems":[]}}]}}}}',
        "SearchSql": query,
        "PageName": "DefaultResult",
        "DBCode": "CFLS",
        "KuaKuCodes": "CJFQ,CDMD,CIPD,CCND,CISD,SNAD,BDZK,CCJD,CCVD,CJFN",
        "CurPage": "1",
        "RecordsCntPerPage": str(limit),
    }

    try:
        html = get_text(SEARCH_URL, params=params, headers=headers, timeout=15)
        if not html:
            return []
        return _parse_results(html)
    except Exception:
        return []


def _parse_results(html: str) -> list[Paper]:
    """解析知网搜索结果"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    soup = BeautifulSoup(html, "html.parser")
    papers: list[Paper] = []

    rows = soup.select("table.result-table-list tbody tr")
    if not rows:
        rows = soup.select("div.result-list div.result-item")

    for row in rows:
        title_el = row.select_one("td.name a") or row.select_one("a.fz14")
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        if not title:
            continue

        url = title_el.get("href", "")
        if url and not url.startswith("http"):
            url = "https://kns.cnki.net" + url

        authors: list[str] = []
        author_el = row.select_one("td.author") or row.select_one(".author")
        if author_el:
            for a_tag in author_el.select("a"):
                name = a_tag.get_text(strip=True)
                if name:
                    authors.append(name)

        year = 0
        date_el = row.select_one("td.date") or row.select_one(".date")
        if date_el:
            year = parse_year(date_el.get_text(strip=True))

        venue = ""
        source_el = row.select_one("td.source a") or row.select_one(".source a")
        if source_el:
            venue = source_el.get_text(strip=True)

        papers.append(Paper(
            title=title,
            authors=authors,
            year=year,
            url=url,
            source="知网",
            venue=venue,
        ))

    return papers
