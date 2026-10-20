"""终端 UI 输出"""

import sys

_COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
}

_use_color = sys.stdout.isatty()


def _c(name: str) -> str:
    return _COLORS.get(name, "") if _use_color else ""


def header(text: str):
    print(f"\n{_c('bold')}{_c('cyan')}{'=' * 60}{_c('reset')}")
    print(f"{_c('bold')}{_c('cyan')}  {text}{_c('reset')}")
    print(f"{_c('bold')}{_c('cyan')}{'=' * 60}{_c('reset')}\n")


def section(text: str):
    print(f"\n{_c('bold')}{_c('blue')}--- {text} ---{_c('reset')}\n")


def info(text: str):
    print(f"  {_c('dim')}{text}{_c('reset')}", file=sys.stderr)


def success(text: str):
    print(f"  {_c('green')}[OK] {text}{_c('reset')}", file=sys.stderr)


def warning(text: str):
    print(f"  {_c('yellow')}[!] {text}{_c('reset')}", file=sys.stderr)


def error(text: str):
    print(f"  {_c('red')}[ERROR] {text}{_c('reset')}", file=sys.stderr)


def paper_entry(index: int, title: str, authors: str, year: int,
                citations: int, score: float, source: str):
    rank = f"{_c('bold')}#{index}{_c('reset')}"
    sc = f"(score:{score:.0f})"
    yr = f"[{year}]" if year else ""
    cite = f"[{citations} cited]" if citations else ""
    src = f"{_c('dim')}via {source}{_c('reset')}"
    print(f"  {rank} {sc} {title}")
    print(f"       {authors} {yr} {cite} {src}")


def progress(current: int, total: int, label: str = ""):
    pct = int(current / total * 100) if total else 0
    bar_len = 30
    filled = int(bar_len * current / total) if total else 0
    bar = "#" * filled + "-" * (bar_len - filled)
    sys.stderr.write(f"\r  [{bar}] {pct}% {label}")
    sys.stderr.flush()
    if current >= total:
        print(file=sys.stderr)


def diagnose_table(status: dict[str, bool | str]):
    header("PaperCash 数据源诊断")
    config_only = {"google_scholar", "cnki", "wanfang"}
    for name, available in status.items():
        if available is True:
            success(f"{name} (已配置，未检验访问)" if name in config_only else name)
        elif available is False:
            warning(f"{name} (未配置)")
        else:
            warning(f"{name} ({available})")
    print()
