"""简易文件缓存"""

import json
import hashlib
import time
from pathlib import Path
from typing import Any, Optional

_CACHE_DIR = Path.home() / ".cache" / "papercash"
_DEFAULT_TTL = 3600 * 24  # 24 hours


def _ensure_dir():
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _key_path(key: str) -> Path:
    h = hashlib.sha256(key.encode()).hexdigest()[:16]
    return _CACHE_DIR / f"{h}.json"


def get(key: str) -> Optional[Any]:
    path = _key_path(key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data.get("_ts", 0) > data.get("_ttl", _DEFAULT_TTL):
            path.unlink(missing_ok=True)
            return None
        return data.get("value")
    except (json.JSONDecodeError, KeyError):
        return None


def put(key: str, value: Any, ttl: int = _DEFAULT_TTL):
    _ensure_dir()
    path = _key_path(key)
    data = {"_ts": time.time(), "_ttl": ttl, "value": value}
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def clear():
    if _CACHE_DIR.exists():
        for f in _CACHE_DIR.glob("*.json"):
            f.unlink(missing_ok=True)
