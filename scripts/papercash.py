#!/usr/bin/env python3
"""PaperCash - 论文全流程辅助引擎 CLI"""

import argparse
import importlib
import json
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from schema import Paper, SearchResult
from query import extract_keywords, build_search_queries, is_chinese
from score import score_papers
from dedupe import dedupe_papers
from render import render_search, render_check_results
from render_agent import (render_search_for_agent, render_check_for_agent, render_humanize_diff,
                          render_check_v2_for_agent, render_check_v2_results)
from env import diagnose
from ui import header, info, error, success, warning, diagnose_table, progress
from safety import show_risk_warning, identify_high_risk_segments, get_academic_integrity_notice


def _search_all_sources(query: str, limit: int = 20,
                        sources: list[str] | None = None) -> SearchResult:
    """并行搜索所有可用数据源"""
    start = time.time()
    queries = build_search_queries(query)
    all_papers: list[Paper] = []
    sources_used: list[str] = []

    default_sources = ["semantic_scholar", "arxiv", "crossref", "baidu_xueshu"]

    from env import get as env_get
    for extra, key in [("google_scholar", "GOOGLE_SCHOLAR_PROXY"),
                       ("cnki", "CNKI_COOKIE"), ("wanfang", "WANFANG_COOKIE")]:
        if env_get(key):
            default_sources.append(extra)

    available = sources if sources is not None else default_sources

    _SOURCE_MAP = {
        "semantic_scholar": ("sources.semantic_scholar", "semantic_scholar", "Semantic Scholar"),
        "arxiv": ("sources.arxiv", "arxiv", "arXiv"),
        "crossref": ("sources.crossref", "crossref", "CrossRef"),
        "baidu_xueshu": ("sources.baidu_xueshu", "baidu_xueshu", "百度学术"),
        "google_scholar": ("sources.google_scholar", "original", "Google Scholar"),
        "pubmed": ("sources.pubmed", "semantic_scholar", "PubMed"),
        "cnki": ("sources.cnki", "baidu_xueshu", "知网"),
        "wanfang": ("sources.wanfang", "baidu_xueshu", "万方"),
    }

    def _search_one_source(src: str):
        module_path, query_key, display_name = _SOURCE_MAP[src]
        try:
            mod = importlib.import_module(module_path)
            search_query = queries.get(query_key, queries.get("original", query))
            papers = mod.search(search_query, limit=limit)
            return display_name, papers, None
        except Exception as e:
            return display_name, [], e

    unknown = [s for s in available if s not in _SOURCE_MAP]
    if unknown:
        raise ValueError(f"未知数据源: {', '.join(unknown)}")
    to_run = available
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(_search_one_source, src): src for src in to_run}
        for fut in as_completed(futures):
            display_name, papers, err = fut.result()
            if err is not None:
                warning(f"{display_name} 搜索失败: {err}")
                continue
            if papers:
                all_papers.extend(papers)
                sources_used.append(display_name)

    scored = score_papers(all_papers, query)
    deduped = dedupe_papers(scored)
    elapsed = int((time.time() - start) * 1000)

    return SearchResult(
        query=query,
        papers=deduped[:limit],
        total_found=len(deduped),
        sources_used=sources_used,
        search_time_ms=elapsed,
    )


def cmd_search(args):
    """论文检索"""
    if args.emit != "json":
        header("PaperCash 论文检索")
    info(f"查询: {args.query}")
    info(f"限制: {args.limit} 篇\n")

    sources = [s.strip() for s in args.sources.split(",")] if args.sources else None
    try:
        result = _search_all_sources(args.query, limit=args.limit, sources=sources)
    except ValueError as exc:
        error(str(exc))
        raise SystemExit(2) from exc

    # 根据输出模式选择渲染器
    if args.emit == "agent":
        output = render_search_for_agent(result, top_n=args.limit)
    elif args.emit == "json":
        output = render_search(result, mode="json")
    else:
        output = render_search(result, mode=args.emit)

    print(output)

    if args.save_dir:
        _save_result(output, args.save_dir, args.query, args.emit)

    if args.export_docx is not None:
        from features.docx_export import export_search_to_docx
        out = args.export_docx or _default_docx_path(args.query, "search")
        msg = export_search_to_docx(result, out)
        if msg.startswith("[错误]"):
            error(msg)
        else:
            success(msg)


def cmd_review(args):
    """文献综述生成"""
    if args.emit != "json":
        header("PaperCash 文献综述生成")
    info(f"主题: {args.topic}")

    result = _search_all_sources(args.topic, limit=30)

    if not result.papers:
        error("未找到相关论文，请尝试调整搜索词。")
        raise SystemExit(1)

    review = _generate_review(result, args.format)
    output = (json.dumps({"topic": args.topic, "review": review,
                          "papers": [p.to_dict() for p in result.papers]},
                         ensure_ascii=False, indent=2)
              if args.emit == "json" else review)
    print(output)

    if args.save_dir:
        _save_result(output, args.save_dir, args.topic,
                     "json" if args.emit == "json" else "md")

    if args.export_docx is not None:
        from features.docx_export import export_review_to_docx
        out = args.export_docx or _default_docx_path(args.topic, "review")
        msg = export_review_to_docx(review, out, title=args.topic)
        if msg.startswith("[错误]"):
            error(msg)
        else:
            success(msg)


def _generate_review(result: SearchResult, cite_format: str = "gb7714") -> str:
    """基于搜索结果生成结构化文献综述"""
    from features.lit_review import generate_review
    return generate_review(result, cite_format)


def cmd_outline(args):
    """生成论文大纲"""
    header("PaperCash 论文大纲生成")
    info(f"题目: {args.title}")

    result = _search_all_sources(args.title, limit=15)
    from features.writing import generate_outline
    outline = generate_outline(args.title, result)
    print(outline)


def cmd_expand(args):
    """段落扩写"""
    # 显示使用建议
    show_risk_warning("expand")

    from features.writing import expand_paragraph
    text = _read_input(args.text)
    expanded = expand_paragraph(text)
    print(expanded)


def cmd_polish(args):
    """学术润色"""
    from features.writing import polish_text
    text = _read_input(args.text)
    polished = polish_text(text)
    print(polished)


def cmd_check(args):
    """查重预检"""
    if args.emit != "json":
        header("PaperCash 查重预检")

    # ========== v2.0 安全强化: 显示警告 + 审计日志 ==========
    from safety import show_risk_warning, log_operation
    show_risk_warning("check")

    text = _read_input(args.input)
    info(f"文本长度: {len(text)} 字\n")

    # 记录审计日志
    log_operation("check", text, "查重预检")

    # 选择检测引擎
    if args.engine == 'v2' and args.mode != 'legacy':
        # 使用增强引擎
        from features.plagiarism_v2 import check_plagiarism_v2
        results, stats = check_plagiarism_v2(text, mode=args.mode)

        # v2结果需要特殊渲染
        if args.emit == "agent":
            output = render_check_v2_for_agent(results, stats)
        else:
            output = render_check_v2_results(results, stats, mode=args.emit)
    else:
        # 使用旧引擎(向后兼容)
        from features.plagiarism import check_plagiarism
        results, stats = check_plagiarism(text)

        if args.emit == "agent":
            output = render_check_for_agent(results, stats)
        else:
            output = render_check_results(results, mode=args.emit, stats=stats)

    print(output)


def cmd_humanize(args):
    """表达修改建议"""
    if args.emit != "json":
        header("PaperCash 表达修改建议")

    # ========== v2.0 安全强化: 强制确认机制 ==========
    from safety import require_explicit_confirmation, log_operation, check_abuse

    confirmation = require_explicit_confirmation("humanize")
    if not confirmation["confirmed"]:
        sys.exit(1)

    # 检查异常使用模式
    check_abuse()

    # 检查危险参数 --allow-modify-protected
    if hasattr(args, 'allow_modify_protected') and args.allow_modify_protected:
        print("\n🚨 您正在禁用内容保护!", file=sys.stderr)
        print("   可能导致: 医学剂量错误、法律条文篡改", file=sys.stderr)
        print("   输入 'YES I ACCEPT' 继续: ", end="", file=sys.stderr, flush=True)
        try:
            confirm = input().strip()
        except EOFError:
            confirm = ""
        if confirm != "YES I ACCEPT":
            print("❌ 操作已取消", file=sys.stderr)
            sys.exit(1)

    text = _read_input(args.input)
    info(f"文本长度: {len(text)} 字\n")

    # 记录审计日志
    log_operation("humanize", text, confirmation["purpose"])

    # 识别高风险段落
    risk_segments = identify_high_risk_segments(text)
    lock = not (hasattr(args, 'allow_modify_protected') and args.allow_modify_protected)
    if risk_segments and lock:
        warning("⚠️  检测到以下高风险内容，所在句将保持原样:")
        for category, data in risk_segments.items():
            print(f"  • {data['description']}: {data['count']}处", file=sys.stderr)
            print(f"    示例: {', '.join(data['examples'])}", file=sys.stderr)
        print(file=sys.stderr)

    from features.ai_humanize import rewrite_text
    modified = rewrite_text(text, protect_high_risk=lock)
    if args.emit == "json":
        output = json.dumps({"original": text, "suggestion": modified,
                             "protected": bool(lock and risk_segments)}, ensure_ascii=False, indent=2)
    elif args.emit == "agent":
        output = render_humanize_diff(text, modified, risk_segments if lock else None)
    elif args.emit == "md":
        output = f"# 表达修改建议\n\n## 原文\n\n{text}\n\n## 修改后\n\n{modified}"
    else:
        output = modified
    print(output)

    # 再次提醒审核
    warning("\n⚠️  请务必逐句审核改写结果，确保数据、引用未被改动")


def cmd_cite(args):
    """参考文献格式化"""
    from features.citation import format_citation, format_citations_batch
    dois = args.doi.split()
    if len(dois) == 1:
        output = format_citation(dois[0], style=args.style)
        print(output)
    else:
        output = format_citations_batch(dois, style=args.style)
        print(output)
    if "[错误]" in output:
        raise SystemExit(1)


def cmd_format(args):
    """格式检查"""
    if args.emit != "json":
        header("PaperCash 格式检查")
    from features.format_helper import check_format
    result = check_format(args.file)
    print(json.dumps({"file": args.file, "report": result}, ensure_ascii=False, indent=2)
          if args.emit == "json" else result)
    if result.startswith("[错误]"):
        raise SystemExit(1)


def cmd_diagnose(args):
    """诊断数据源"""
    status = diagnose()
    diagnose_table(status)


def cmd_setup(args):
    """配置向导"""
    from setup_wizard import run_wizard
    run_wizard()


def _read_input(path_or_text: str) -> str:
    """读取文件或直接使用文本"""
    if os.path.isfile(path_or_text):
        with open(path_or_text, "r", encoding="utf-8") as f:
            return f.read()
    return path_or_text


_EMIT_TO_EXT = {"compact": "txt", "json": "json", "md": "md", "context": "md", "agent": "txt"}


def _default_docx_path(topic: str, kind: str) -> str:
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in topic)[:50]
    return os.path.join(os.getcwd(), f"papercash_{kind}_{safe}.docx")


def _save_result(content: str, save_dir: str, topic: str, ext: str):
    """保存结果到文件"""
    os.makedirs(save_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in topic)[:50]
    file_ext = _EMIT_TO_EXT.get(ext, ext)
    path = os.path.join(save_dir, f"papercash_{safe_name}.{file_ext}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    success(f"已保存到: {path}")


def main():
    parser = argparse.ArgumentParser(
        prog="papercash",
        description="PaperCash - 论文检索与写作辅助工具",
    )
    parser.add_argument("--diagnose", action="store_true", help="诊断数据源配置")
    parser.add_argument("--version", action="version", version="PaperCash 2.0.0")

    sub = parser.add_subparsers(dest="command")

    # search
    p_search = sub.add_parser("search", help="论文检索")
    p_search.add_argument("query", help="搜索查询")
    p_search.add_argument("--limit", type=int, default=20, help="结果数量限制")
    p_search.add_argument("--emit", default="compact",
                          choices=["compact", "json", "md", "context", "agent"],
                          help="输出格式(agent=AI Agent友好)")
    p_search.add_argument("--sources", default=None, help="指定数据源（逗号分隔）")
    p_search.add_argument("--save-dir", default=None, help="保存结果目录")
    p_search.add_argument(
        "--export-docx",
        nargs="?",
        const="",
        default=None,
        metavar="PATH",
        help="导出检索结果为 Word；省略路径则写入当前目录",
    )
    p_search.set_defaults(func=cmd_search)

    # review
    p_review = sub.add_parser("review", help="文献综述生成")
    p_review.add_argument("topic", help="研究主题")
    p_review.add_argument("--format", default="gb7714",
                          choices=["gb7714", "apa"], help="引用格式")
    p_review.add_argument("--emit", default="md",
                          choices=["md", "json", "context"], help="输出格式")
    p_review.add_argument("--save-dir", default=None, help="保存结果目录")
    p_review.add_argument(
        "--export-docx",
        nargs="?",
        const="",
        default=None,
        metavar="PATH",
        help="导出综述为 Word；省略路径则写入当前目录",
    )
    p_review.set_defaults(func=cmd_review)

    # outline
    p_outline = sub.add_parser("outline", help="生成论文大纲")
    p_outline.add_argument("title", help="论文题目")
    p_outline.set_defaults(func=cmd_outline)

    # expand
    p_expand = sub.add_parser("expand", help="段落扩写")
    p_expand.add_argument("text", help="待扩写文本或文件路径")
    p_expand.set_defaults(func=cmd_expand)

    # polish
    p_polish = sub.add_parser("polish", help="学术润色")
    p_polish.add_argument("text", help="待润色文本或文件路径")
    p_polish.set_defaults(func=cmd_polish)

    # check
    p_check = sub.add_parser("check", help="查重预检")
    p_check.add_argument("input", help="文件路径或文本内容")
    p_check.add_argument("--emit", default="compact",
                         choices=["compact", "json", "agent"], help="输出格式")
    p_check.add_argument("--mode", default="standard",
                         choices=["fast", "standard", "deep", "legacy"],
                         help="检测模式: fast(快速), standard(标准,推荐), deep(深度), legacy(旧版兼容)")
    p_check.add_argument("--engine", default="v2",
                         choices=["v1", "v2"],
                         help="检测引擎: v1(旧版), v2(增强版,推荐)")
    p_check.set_defaults(func=cmd_check)

    # humanize
    p_human = sub.add_parser("humanize", help="表达修改建议（不能预测AI检测结果）")
    p_human.add_argument("input", help="文件路径或文本内容")
    p_human.add_argument("--emit", default="compact",
                         choices=["compact", "md", "json", "agent"], help="输出格式")
    p_human.add_argument("--allow-modify-protected", action="store_true",
                         help="⚠️ 危险: 允许改写受保护内容（需二次确认）")
    p_human.set_defaults(func=cmd_humanize)

    # cite
    p_cite = sub.add_parser("cite", help="参考文献格式化")
    p_cite.add_argument("doi", help="DOI（多个用空格分隔）")
    p_cite.add_argument("--style", default="gb7714",
                        choices=["gb7714", "apa", "mla", "chicago", "bibtex"],
                        help="引用格式")
    p_cite.set_defaults(func=cmd_cite)

    # format
    p_format = sub.add_parser("format", help="格式检查")
    p_format.add_argument("file", help="Word 文件路径")
    p_format.add_argument("--emit", default="compact",
                         choices=["compact", "json"], help="输出格式")
    p_format.set_defaults(func=cmd_format)

    # setup
    p_setup = sub.add_parser("setup", help="配置向导")
    p_setup.set_defaults(func=cmd_setup)

    args = parser.parse_args()

    if args.diagnose:
        cmd_diagnose(args)
        return

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
