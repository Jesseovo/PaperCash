"""日期工具"""

from datetime import datetime, timezone


def current_year() -> int:
    return datetime.now(timezone.utc).year


def years_ago(year: int) -> int:
    return max(0, current_year() - year)


def recency_score(year: int, max_age: int = 10) -> float:
    """计算时效性分数 (0.0 ~ 1.0)，越新越高"""
    age = years_ago(year)
    if age <= 0:
        return 1.0
    if age >= max_age:
        return 0.1
    return 1.0 - (age / max_age) * 0.9


def parse_year(text: str) -> int:
    """从各种日期格式中提取年份"""
    if not text:
        return 0
    text = text.strip()
    if text.isdigit() and len(text) == 4:
        return int(text)
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%d %b %Y", "%B %Y"):
        try:
            return datetime.strptime(text[:10], fmt).year
        except ValueError:
            continue
    for i in range(len(text) - 3):
        chunk = text[i:i + 4]
        if chunk.isdigit():
            y = int(chunk)
            if 1900 <= y <= 2100:
                return y
    return 0
