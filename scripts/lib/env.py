"""环境配置管理"""

import os
from pathlib import Path

import requests

_CONFIG_DIR = Path.home() / ".config" / "papercash"
_PROJECT_ENV = Path(".papercash.env")

_cache: dict[str, str] = {}

_PROBE_TIMEOUT = 3.0
_PROBE_HEADERS = {"User-Agent": "PaperCash/1.0 (diagnostic)"}


def _load_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip("'\"")
    return result


def _ensure_loaded():
    if _cache:
        return
    global_env = _CONFIG_DIR / ".env"
    _cache.update(_load_env_file(global_env))
    _cache.update(_load_env_file(_PROJECT_ENV))


def get(key: str, default: str = "") -> str:
    _ensure_loaded()
    return os.environ.get(key, _cache.get(key, default))


def _probe_head(url: str) -> bool | str:
    try:
        r = requests.head(
            url,
            timeout=_PROBE_TIMEOUT,
            allow_redirects=True,
            headers=_PROBE_HEADERS,
        )
        if r.status_code == 405:
            r = requests.get(
                url,
                timeout=_PROBE_TIMEOUT,
                allow_redirects=True,
                headers=_PROBE_HEADERS,
                stream=True,
            )
            r.close()
        if 200 <= r.status_code < 400:
            return True
        return f"HTTP {r.status_code}"
    except requests.Timeout:
        return "timeout"
    except requests.ConnectionError:
        return "connection error"
    except OSError as e:
        return str(e)


def diagnose() -> dict[str, bool | str]:
    """诊断各数据源的配置状态；免费源通过轻量请求检验连通性。"""
    _ensure_loaded()
    endpoints = {
        "semantic_scholar": (
            "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1"
        ),
        "arxiv": "https://export.arxiv.org/api/query?search_query=test&max_results=1",
        "crossref": "https://api.crossref.org/works?query=test&rows=1",
        "pubmed": (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            "?db=pubmed&term=test&retmax=1"
        ),
        "baidu_xueshu": "https://xueshu.baidu.com/s?wd=test",
    }
    result: dict[str, bool | str] = {k: _probe_head(u) for k, u in endpoints.items()}
    result["google_scholar"] = bool(get("GOOGLE_SCHOLAR_PROXY"))
    result["cnki"] = bool(get("CNKI_COOKIE"))
    result["wanfang"] = bool(get("WANFANG_COOKIE"))
    return result


def config_dir() -> Path:
    return _CONFIG_DIR
