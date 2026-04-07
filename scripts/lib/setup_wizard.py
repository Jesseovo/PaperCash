"""配置向导"""

import os
from pathlib import Path
from env import config_dir, diagnose
from ui import header, info, success, warning, section


def run_wizard():
    """交互式配置向导"""
    header("PaperCash 配置向导")

    info("PaperCash 支持 8 个学术数据源。")
    info("其中 4 个无需任何配置即可使用：\n")
    success("Semantic Scholar (2亿+论文)")
    success("arXiv (STEM预印本)")
    success("CrossRef (1.4亿DOI)")
    success("百度学术 (中文论文)")

    section("可选配置")
    info("以下数据源需要额外配置：\n")
    warning("Google Scholar - 需设置代理 (GOOGLE_SCHOLAR_PROXY)")
    warning("知网 CNKI - 需设置 Cookie (CNKI_COOKIE)")
    warning("万方 - 需设置 Cookie (WANFANG_COOKIE)")
    warning("Semantic Scholar API Key - 可提高速率限制")

    section("配置文件位置")

    cfg = config_dir()
    env_file = cfg / ".env"

    info(f"全局配置: {env_file}")
    info(f"项目配置: .papercash.env (当前目录)\n")

    if not cfg.exists():
        cfg.mkdir(parents=True, exist_ok=True)
        success(f"已创建配置目录: {cfg}")

    if not env_file.exists():
        template = """# PaperCash 配置文件
# 作者: Jesse (https://github.com/Jesseovo)
#
# 所有配置均为可选
# Semantic Scholar、arXiv、CrossRef、百度学术无需配置即可使用

# Semantic Scholar API Key（可选，提高速率限制）
# 获取: https://www.semanticscholar.org/product/api
# SEMANTIC_SCHOLAR_API_KEY=

# Google Scholar 代理（可选）
# GOOGLE_SCHOLAR_PROXY=http://127.0.0.1:7890

# 知网 Cookie（可选）
# 获取: 浏览器登录知网 -> F12 -> Network -> 复制 Cookie
# CNKI_COOKIE=

# 万方 Cookie（可选）
# WANFANG_COOKIE=
"""
        env_file.write_text(template, encoding="utf-8")
        success(f"已创建配置模板: {env_file}")
    else:
        info(f"配置文件已存在: {env_file}")

    section("当前数据源状态")
    status = diagnose()
    for name, available in status.items():
        if available is True:
            success(name)
        elif available is False:
            warning(f"{name} (未配置)")
        else:
            warning(f"{name} ({available})")

    print()
    info("配置完成！运行 'python scripts/papercash.py --diagnose' 可随时检查状态。")
