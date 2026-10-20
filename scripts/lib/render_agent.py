#!/usr/bin/env python3
"""Agent友好的输出渲染模块"""

from schema import SearchResult, Paper

_SIMILARITY_LABELS = {
    "near_exact": "文字高度重合",
    "high_overlap": "较高重合",
    "possible_overlap": "可能相似",
    "similar": "部分相似",
    "low_similarity": "较低相似",
}


def render_search_for_agent(result: SearchResult, top_n: int = 10) -> str:
    """
    为AI Agent优化的检索结果渲染
    - 结构化清晰
    - 突出关键信息
    - 提供可操作建议
    """
    lines = []

    # 摘要行
    lines.append(f"✅ 检索完成: 找到 {result.total_found} 篇相关论文")
    lines.append(f"   数据源: {', '.join(result.sources_used)}")
    lines.append(f"   用时: {result.search_time_ms}ms\n")

    # 论文列表（结构化）
    for i, paper in enumerate(result.papers[:top_n], 1):
        lines.append(f"📄 [{i}] {paper.title}")
        lines.append(f"    作者: {', '.join(paper.authors[:3])}" +
                     (f" 等 {len(paper.authors)} 人" if len(paper.authors) > 3 else ""))
        lines.append(f"    年份: {paper.year} | 引用: {paper.citation_count}次 | 综合评分: {paper.final_score:.0f}/100")

        # 推荐理由
        reason = _generate_recommendation_reason(paper)
        lines.append(f"    💡 {reason}")

        # 摘要摘录
        if paper.abstract:
            snippet = paper.abstract[:120].replace('\n', ' ')
            lines.append(f"    📝 {snippet}...")

        if paper.url:
            lines.append(f"    🔗 {paper.url}")

        lines.append("")  # 空行分隔

    # 后续操作建议
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 接下来可以:")
    lines.append("   • 生成文献综述 (review)")
    lines.append("   • 格式化参考文献 (cite)")
    lines.append("   • 导出为Word文档 (--export-docx)")

    return '\n'.join(lines)


def _generate_recommendation_reason(paper: Paper) -> str:
    """生成推荐理由"""
    reasons = []

    if paper.final_score >= 85:
        reasons.append("高度相关")
    elif paper.final_score >= 70:
        reasons.append("较为相关")

    if paper.citation_count >= 100:
        reasons.append("高被引")
    elif paper.citation_count >= 50:
        reasons.append("较高被引")

    import datetime
    current_year = datetime.datetime.now().year
    if paper.year and paper.year >= current_year - 2:
        reasons.append("最新研究")
    elif paper.year and paper.year >= current_year - 5:
        reasons.append("近期研究")

    if not reasons:
        reasons.append("相关研究")

    return "、".join(reasons)


def render_check_for_agent(results: list, stats: dict) -> str:
    """Agent友好的查重结果渲染"""
    lines = []

    # 总体统计
    lines.append("🔍 查重预检完成\n")
    lines.append(f"总句数: {stats.get('total_sentences', 0)}")
    lines.append(f"高风险句: {stats.get('high_risk', 0)} (相似度 > 70%)")
    lines.append(f"中风险句: {stats.get('medium_risk', 0)} (相似度 50-70%)")
    lines.append(f"低风险句: {stats.get('low_risk', 0)} (相似度 < 50%)")
    lines.append("")

    # 高风险句子详情
    high_risk = [r for r in results if r.get('similarity', 0) > 0.7]
    if high_risk:
        lines.append("⚠️  高风险句子(需重点修改):")
        for i, item in enumerate(high_risk[:10], 1):  # 最多显示10条
            lines.append(f"\n[{i}] 原句:")
            lines.append(f"    {item['sentence']}")
            lines.append(f"    相似度: {item['similarity']:.0%}")
            if 'source' in item:
                lines.append(f"    相似来源: {item['source']}")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 建议:")
    lines.append("   • 对高风险句进行改写(替换表述、调整结构)")
    lines.append("   • 正式查重请使用学校指定系统")

    return '\n'.join(lines)


def render_humanize_diff(original: str, modified: str, locked_segments: dict = None) -> str:
    """渲染改写前后对比"""
    lines = []

    lines.append("📝 改写完成\n")

    if locked_segments:
        lines.append("🔒 以下内容已保护(未改写):")
        for cat, data in locked_segments.items():
            lines.append(f"   • {data['description']}: {data['count']}处")
        lines.append("")

    # 简单的段落级对比（实际可以更精细）
    orig_paras = [p.strip() for p in original.split('\n\n') if p.strip()]
    mod_paras = [p.strip() for p in modified.split('\n\n') if p.strip()]

    lines.append("━━ 改写对比 ━━")
    for i, (orig, mod) in enumerate(zip(orig_paras, mod_paras), 1):
        if orig != mod:
            lines.append(f"\n段落 {i}:")
            lines.append(f"原文: {orig[:100]}...")
            lines.append(f"改写: {mod[:100]}...")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("⚠️  请务必:")
    lines.append("   • 逐段审核改写质量")
    lines.append("   • 验证事实、数据、引用未被改动")
    lines.append("   • 确保语义与原意一致")

    lines.append("\n━━ 完整改写文本 ━━\n")
    lines.append(modified)

    return '\n'.join(lines)


def render_check_v2_for_agent(results: list, stats: dict) -> str:
    """Agent友好的查重结果渲染 (v2增强版)"""
    lines = []

    # 总体统计
    lines.append("🔍 查重预检完成 (增强引擎v2.0)\n")
    lines.append(f"检测模式: {stats.get('mode', 'standard').upper()}")
    lines.append(f"数据源: {', '.join(stats.get('sources', []))}")
    lines.append("范围: 仅比较检索到的论文标题和摘要")
    lines.append("")

    lines.append(f"总句数: {stats.get('total_sentences', 0)}")
    lines.append(f"发起检索: {stats.get('checked_sentences', 0)} 句")
    lines.append(f"有候选可比较: {stats.get('compared_sentences', 0)} 句")
    lines.append(f"⚠️ 高度相似: {stats.get('critical', 0)}")
    lines.append(f"🔶 较高相似: {stats.get('high', 0)}")
    lines.append(f"🔷 中等相似: {stats.get('medium', 0)}")
    lines.append(f"ℹ️ 较低相似: {stats.get('low', 0)}")
    lines.append(f"❔ 无法判断: {stats.get('unverified', 0)}")
    lines.append("")

    # 按风险等级分组展示
    critical = [r for r in results if r.risk_level == 'critical']
    high = [r for r in results if r.risk_level == 'high']
    medium = [r for r in results if r.risk_level == 'medium']

    # 严重风险
    if critical:
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("⚠️ 高度相似句子 (请核对来源):")
        for i, r in enumerate(critical[:5], 1):  # 最多显示5条
            lines.append(f"\n[{i}] {r.sentence}")
            lines.append(f"    检测类型: {_SIMILARITY_LABELS.get(r.similarity['detection_type'], '未知')}")
            lines.append(f"    字面相似: {r.similarity['literal']:.0%} | "
                        f"辅助相似: {r.similarity['semantic']:.0%}")
            if r.matched_paper:
                lines.append(f"    来源: {r.matched_paper.title}")
                lines.append(f"    作者: {r.matched_paper.authors_str}")
            lines.append(f"    {r.suggestion}")

    # 高风险
    if high:
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🔶 较高相似句子:")
        for i, r in enumerate(high[:5], 1):
            lines.append(f"\n[{i}] {r.sentence[:60]}...")
            lines.append(f"    检测类型: {_SIMILARITY_LABELS.get(r.similarity['detection_type'], '未知')}")
            lines.append(f"    综合评分: {r.similarity['final_score']:.0%}")
            if r.matched_paper:
                lines.append(f"    来源: {r.matched_paper.title}")
            lines.append(f"    {r.suggestion}")

    # 中风险
    if medium and len(medium) <= 3:
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🔷 中等相似句子:")
        for i, r in enumerate(medium, 1):
            lines.append(f"\n[{i}] {r.sentence[:60]}...")
            lines.append(f"    {r.suggestion}")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 检测说明:")
    lines.append("   • 相似度仅用于筛查，不能判定抄袭或原创")
    lines.append(f"   • 尝试检索{len(stats.get('sources', []))}个学术数据源；无候选也可能是检索失败")
    lines.append("")
    lines.append("⚠️ 重要提醒:")
    lines.append("   • 正式查重请使用学校指定系统")
    lines.append("   • 本检测结果仅供参考和改进")

    return '\n'.join(lines)


def render_check_v2_results(results: list, stats: dict, mode: str = 'compact') -> str:
    """v2查重结果的标准渲染"""
    if mode == 'json':
        import json
        return json.dumps({
            'stats': stats,
            'results': [
                {
                    'sentence': r.sentence,
                    'similarity': r.similarity,
                    'risk_level': r.risk_level,
                    'matched_paper': {
                        'title': r.matched_paper.title,
                        'authors': r.matched_paper.authors_str
                    } if r.matched_paper else None
                }
                for r in results
            ]
        }, ensure_ascii=False, indent=2)
    else:
        # 使用Agent友好格式
        return render_check_v2_for_agent(results, stats)
