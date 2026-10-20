"""HTTP 客户端封装"""

import json
import logging
import time
import hashlib
import threading
from typing import Optional

import requests

import cache

logger = logging.getLogger(__name__)

_thread_state = threading.local()

DEFAULT_TIMEOUT = 15
DEFAULT_HEADERS = {
    "User-Agent": "PaperCash/2.0 (Academic Research Tool)",
    "Accept": "application/json",
}


def _get_session() -> requests.Session:
    if not hasattr(_thread_state, "session"):
        _thread_state.session = requests.Session()
        _thread_state.session.headers.update(DEFAULT_HEADERS)
    return _thread_state.session


def _cache_key(kind: str, url: str, params: Optional[dict], headers: Optional[dict]) -> str:
    # Include authorization context without storing credential bytes in cache filenames.
    request_shape = json.dumps({"params": params or {}, "headers": headers or {}},
                               sort_keys=True, ensure_ascii=False)
    fingerprint = hashlib.sha256(request_shape.encode("utf-8")).hexdigest()
    return f"{kind}:{url}:{fingerprint}"


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
        time.sleep(min(max(wait, 0.0), 10.0))
        r = s.get(url, params=params, headers=headers, timeout=timeout)
    return r


def get_json(url: str, params: Optional[dict] = None,
             headers: Optional[dict] = None,
             timeout: int = DEFAULT_TIMEOUT) -> Optional[dict]:
    cache_key = _cache_key("json", url, params, headers)
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
    cache_key = _cache_key("text", url, params, headers)
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
