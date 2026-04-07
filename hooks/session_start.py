"""Session 启动钩子 - 验证配置"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "lib"))

from env import diagnose
from ui import header, success, warning, info


def on_session_start():
    """Session 启动时自动检查配置"""
    status = diagnose()
    free_sources = [
        "semantic_scholar",
        "arxiv",
        "crossref",
        "baidu_xueshu",
        "pubmed",
    ]
    free_ok = all(status.get(s) is True for s in free_sources)

    if free_ok:
        info("PaperCash: 免费数据源就绪")
    else:
        warning("PaperCash: 部分数据源不可用，运行 'papercash --diagnose' 检查")

    optional = {k: v for k, v in status.items() if k not in free_sources}
    configured = [k for k, v in optional.items() if v is True]
    if configured:
        info(f"PaperCash: 已配置扩展源: {', '.join(configured)}")


if __name__ == "__main__":
    on_session_start()
