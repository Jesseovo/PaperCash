"""环境配置管理"""

import os
from pathlib import Path

_CONFIG_DIR = Path.home() / ".config" / "papercash"
_PROJECT_ENV = Path(".papercash.env")

_cache: dict[str, str] = {}


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


def diagnose() -> dict[str, bool]:
    """诊断各数据源的配置状态"""
    _ensure_loaded()
    return {
        "semantic_scholar": True,
        "arxiv": True,
        "crossref": True,
        "baidu_xueshu": True,
        "google_scholar": bool(get("GOOGLE_SCHOLAR_PROXY")),
        "pubmed": True,
        "cnki": bool(get("CNKI_COOKIE")),
        "wanfang": bool(get("WANFANG_COOKIE")),
    }


def config_dir() -> Path:
    return _CONFIG_DIR
