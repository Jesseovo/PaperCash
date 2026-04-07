"""HTTP 客户端封装"""

import time
import requests
from typing import Optional

_session: Optional[requests.Session] = None

DEFAULT_TIMEOUT = 15
DEFAULT_HEADERS = {
    "User-Agent": "PaperCash/1.0 (Academic Research Tool; mailto:papercash@example.com)",
    "Accept": "application/json",
}


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(DEFAULT_HEADERS)
    return _session


def get_json(url: str, params: Optional[dict] = None,
             headers: Optional[dict] = None,
             timeout: int = DEFAULT_TIMEOUT) -> Optional[dict]:
    try:
        s = _get_session()
        r = s.get(url, params=params, headers=headers or {}, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except (requests.RequestException, ValueError):
        return None


def get_text(url: str, params: Optional[dict] = None,
             headers: Optional[dict] = None,
             timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    try:
        s = _get_session()
        r = s.get(url, params=params, headers=headers or {}, timeout=timeout)
        r.raise_for_status()
        return r.text
    except requests.RequestException:
        return None


def rate_limited_get(url: str, params: Optional[dict] = None,
                     delay: float = 0.5, **kwargs) -> Optional[dict]:
    """带速率限制的 GET 请求"""
    time.sleep(delay)
    return get_json(url, params=params, **kwargs)
