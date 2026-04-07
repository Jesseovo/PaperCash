"""HTTP 客户端封装"""

import json
import logging
import time
from typing import Optional

import requests

import cache

logger = logging.getLogger(__name__)

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


def _get_with_429_retry(
    s: requests.Session,
    url: str,
    params: Optional[dict],
    headers: dict,
    timeout: int,
) -> requests.Response:
    r = s.get(url, params=params, headers=headers, timeout=timeout)
    if r.status_code == 429:
        wait_raw = r.headers.get("Retry-After", "2")
        try:
            wait = float(wait_raw)
        except ValueError:
            wait = 2.0
        logger.warning(
            "429 Too Many Requests for %s, retrying once after %.1fs",
            url,
            wait,
        )
        time.sleep(wait)
        r = s.get(url, params=params, headers=headers, timeout=timeout)
    return r


def get_json(url: str, params: Optional[dict] = None,
             headers: Optional[dict] = None,
             timeout: int = DEFAULT_TIMEOUT) -> Optional[dict]:
    cache_key = f"json:{url}:{json.dumps(params or {}, sort_keys=True)}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    r = None
    try:
        s = _get_session()
        r = _get_with_429_retry(s, url, params, merged, timeout)
        r.raise_for_status()
    except requests.Timeout:
        logger.error("Request timeout (%ss) for JSON GET %s", timeout, url)
        return None
    except requests.ConnectionError as e:
        logger.error("Connection failed for JSON GET %s: %s", url, e)
        return None
    except requests.HTTPError:
        code = r.status_code if r is not None else "?"
        logger.error("HTTP %s for JSON GET %s", code, url)
        return None
    try:
        result = r.json()
    except ValueError:
        logger.error("JSON decode failed for response from %s", url)
        return None
    cache.put(cache_key, result)
    return result


def get_text(url: str, params: Optional[dict] = None,
             headers: Optional[dict] = None,
             timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    cache_key = f"text:{url}:{json.dumps(params or {}, sort_keys=True)}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    r = None
    try:
        s = _get_session()
        r = _get_with_429_retry(s, url, params, merged, timeout)
        r.raise_for_status()
    except requests.Timeout:
        logger.error("Request timeout (%ss) for text GET %s", timeout, url)
        return None
    except requests.ConnectionError as e:
        logger.error("Connection failed for text GET %s: %s", url, e)
        return None
    except requests.HTTPError:
        code = r.status_code if r is not None else "?"
        logger.error("HTTP %s for text GET %s", code, url)
        return None
    result = r.text
    cache.put(cache_key, result)
    return result


def rate_limited_get(url: str, params: Optional[dict] = None,
                     delay: float = 0.5, **kwargs) -> Optional[dict]:
    """带速率限制的 GET 请求"""
    time.sleep(delay)
    return get_json(url, params=params, **kwargs)
