"""写作辅助 - 大纲生成、段落扩写、学术润色"""

from __future__ import annotations
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import SearchResult
from query import is_chinese

_ORAL_TO_ACADEMIC_CN = {
    "非常": "极为",
    "太": "过于",
    "还有": "另外",
    "之后": "此后",
    "看一下": "审视",
    "瞧一瞧": "考察",
    "说一下": "阐述",
    "讲一讲": "论述",
    "好像": "似乎",
    "大约": "约",
    "左右": "上下",
    "我认为": "笔者认为",
    "我们觉得": "研究认为",
    "我们发现": "研究发现",
    "我感觉": "可见",
    "超级": "极为",
    "特别": "尤为",
    "挺": "较为",
    "蛮": "颇为",
    "巨": "极为",
    "贼": "极为",
    "接下来": "继而",
    "更是": "愈加",
    "老是": "往往",
    "立马": "即刻",
    "马上": "即刻",
    "啥的": "等相关要素",
    "之类": "等",
    "反正": "总体而言",
    "说白了": "换言之",
    "基本上": "总体上",
    "差不多": "基本一致",
    "一点点": "若干",
    "一下": "简要",
    "搞定": "完成",
    "弄好": "完善",
    "挺多": "较多",
    "挺好": "较佳",
    "还行": "尚可",
    "不好": "欠佳",
    "很好": "表现优异",
    "很多": "大量",
    "很大": "显著",
    "效果很好": "取得了显著成效",
    "越来越多": "日益增多",
    "经常": "频繁",
    "大概": "约",
    "可能": "或许",
    "觉得": "认为",
    "想要": "旨在",
    "搞清楚": "明确",
    "说明了": "表明",
    "看出来": "可以观察到",
    "没什么": "并无显著",
    "比较好": "较为理想",
    "特别是": "尤其是",
    "而且": "此外",
    "但是": "然而",
    "所以": "因此",
    "因为": "由于",
    "虽然": "尽管",
    "不过": "但",
    "其实": "实际上",
    "总之": "综上",
    "然后": "随后",
    "接着": "继而",
    "首先": "第一",
    "最后": "最终",
    "这个方法": "该方法",
    "这种方式": "此方式",
    "用了": "采用了",
    "做了": "进行了",
    "拿来": "用以",
    "弄出来": "提出",
}

_ORAL_TO_ACADEMIC_EN = {
    "also": "additionally",
    "besides": "moreover",
    "after that": "subsequently",
    "later on": "thereafter",
    "take a look at": "examine",
    "have a look": "review",
    "talk about": "discuss",
    "tell you": "elucidate",
    "seems like": "appears to",
    "kinda": "somewhat",
    "pretty much": "largely",
    "I think": "it is argued that",
    "we think": "the analysis suggests",
    "we found": "the study reveals",
    "we believe": "the evidence indicates",
    "very much": "considerably",
    "too much": "excessive",
    "super": "highly",
    "awesome": "noteworthy",
    "huge": "substantial",
    "tiny": "minimal",
    "fix": "remedy",
    "a lot of": "numerous",
    "lots of": "a significant number of",
    "really good": "highly effective",
    "pretty good": "satisfactory",
    "get better": "improve",
    "find out": "determine",
    "look at": "examine",
    "point out": "indicate",
    "set up": "establish",
    "come up with": "propose",
    "deal with": "address",
    "figure out": "ascertain",
    "make sure": "ensure",
    "kind of": "somewhat",
    "sort of": "to some extent",
    "big": "substantial",
    "small": "minimal",
    "good": "favorable",
    "bad": "unfavorable",
    "show": "demonstrate",
    "use": "utilize",
    "help": "facilitate",
    "need": "require",
    "try": "attempt",
    "start": "initiate",
    "end": "conclude",
    "give": "provide",
    "get": "obtain",
    "things": "factors",
    "stuff": "elements",
}


def generate_outline(title: str, search_result: SearchResult | None = None) -> str:
    """生成论文大纲"""
    has_cn = is_chinese(title)
    papers = search_result.papers[:10] if search_result else []

    lines: list[str] = []
    lines.append(f"# 论文大纲：{title}\n")

    if has_cn:
        lines.extend(_cn_outline(title, papers))
    else:
        lines.extend(_en_outline(title, papers))

    if papers:
        lines.append("\n## 建议参考文献\n")
        for i, p in enumerate(papers[:8], 1):
            year_str = f"({p.year})" if p.year else ""
            lines.append(f"{i}. {p.authors_str} {year_str}. {p.title}")

    return "\n".join(lines)


def _cn_outline(title: str, papers: list) -> list[str]:
    lines = [
        "## 摘要",
        "- 研究背景与意义（1-2句）",
        "- 研究目的与方法（1-2句）",
        "- 主要结果（1-2句）",
        "- 结论与贡献（1句）",
        "",
        "## 关键词",
        "- 建议 3-5 个关键词",
        "",
        "## 第1章 绪论",
        "### 1.1 研究背景",
        "- 领域发展历史与现状",
        "- 国内外研究动态",
        "### 1.2 研究意义",
        "- 理论意义",
        "- 实践价值",
        "### 1.3 研究内容与方法",
        "- 研究问题界定",
        "- 研究方法概述",
        "### 1.4 论文结构安排",
        "",
        "## 第2章 文献综述",
        "### 2.1 核心概念界定",
        "### 2.2 国内研究现状",
        "### 2.3 国外研究现状",
        "### 2.4 研究述评与不足",
        "",
        "## 第3章 研究设计与方法",
        "### 3.1 研究框架",
        "### 3.2 数据来源与样本",
        "### 3.3 研究方法",
        "### 3.4 变量定义与测量",
        "",
        "## 第4章 实证分析/实验结果",
        "### 4.1 描述性统计",
        "### 4.2 相关性分析",
        "### 4.3 主要结果",
        "### 4.4 稳健性检验",
        "",
        "## 第5章 讨论",
        "### 5.1 结果讨论",
        "### 5.2 与已有研究的对比",
        "### 5.3 研究局限性",
        "",
        "## 第6章 结论与建议",
        "### 6.1 研究结论",
        "### 6.2 实践建议",
        "### 6.3 未来研究方向",
        "",
        "## 参考文献",
        "",
        "## 致谢",
    ]
    return lines


def _en_outline(title: str, papers: list) -> list[str]:
    lines = [
        "## Abstract",
        "- Background and motivation (1-2 sentences)",
        "- Research objective and methodology (1-2 sentences)",
        "- Key findings (1-2 sentences)",
        "- Conclusion and contribution (1 sentence)",
        "",
        "## Keywords",
        "- 3-5 keywords recommended",
        "",
        "## 1. Introduction",
        "### 1.1 Background",
        "### 1.2 Research Significance",
        "### 1.3 Research Questions",
        "### 1.4 Paper Organization",
        "",
        "## 2. Literature Review",
        "### 2.1 Key Concepts",
        "### 2.2 Related Work",
        "### 2.3 Research Gaps",
        "",
        "## 3. Methodology",
        "### 3.1 Research Framework",
        "### 3.2 Data Collection",
        "### 3.3 Analysis Methods",
        "",
        "## 4. Results",
        "### 4.1 Descriptive Statistics",
        "### 4.2 Main Findings",
        "### 4.3 Robustness Checks",
        "",
        "## 5. Discussion",
        "### 5.1 Interpretation of Results",
        "### 5.2 Comparison with Prior Work",
        "### 5.3 Limitations",
        "",
        "## 6. Conclusion",
        "### 6.1 Summary",
        "### 6.2 Implications",
        "### 6.3 Future Work",
        "",
        "## References",
        "",
        "## Acknowledgments",
    ]
    return lines


def expand_paragraph(text: str) -> str:
    """段落扩写指引"""
    lines = [
        "# 段落扩写建议\n",
        f"**原文**: {text}\n",
        "## 扩写方向\n",
        "1. **添加背景说明**：在论点前补充研究背景或领域现状",
        "2. **补充数据支撑**：加入具体数据、比例或统计结果",
        "3. **增加对比分析**：与其他方法/理论进行对比",
        "4. **引入文献佐证**：引用相关文献支撑观点",
        "5. **阐释因果关系**：解释现象背后的原因和机制",
        "6. **举例说明**：用具体案例论证观点",
        "",
        "## 学术扩写模板\n",
    ]

    if is_chinese(text):
        lines.extend([
            "```",
            "在[领域]中，[核心概念]是一个关键问题。[引用]的研究表明，",
            "[原始观点的学术化表述]。具体而言，[补充细节/数据]。",
            "与[对比方法]相比，该方法在[方面]具有[优势]。",
            "这一发现与[相关研究者]的结论一致，进一步证实了[观点]。",
            "```",
        ])
    else:
        lines.extend([
            "```",
            "In the field of [domain], [core concept] has been a subject of",
            "considerable interest. Prior studies [citation] have demonstrated that",
            "[academic rephrasing of original point]. Specifically, [supplementary",
            "data/details]. Compared to [alternative method], this approach exhibits",
            "[advantages] in [aspects]. These findings corroborate the conclusions",
            "of [related researchers], further substantiating [viewpoint].",
            "```",
        ])

    return "\n".join(lines)


def polish_text(text: str) -> str:
    """学术润色"""
    lines = ["# 学术润色结果\n"]
    lines.append(f"**原文**: {text}\n")

    polished = text
    replacements_made: list[tuple[str, str]] = []

    mapping = _ORAL_TO_ACADEMIC_CN if is_chinese(text) else _ORAL_TO_ACADEMIC_EN
    items = sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True)

    for oral, academic in items:
        if oral in polished.lower() if not is_chinese(text) else oral in polished:
            if is_chinese(text):
                polished = polished.replace(oral, academic)
            else:
                polished = re.sub(re.escape(oral), academic, polished, flags=re.IGNORECASE)
            replacements_made.append((oral, academic))

    lines.append(f"**润色后**: {polished}\n")

    if replacements_made:
        lines.append("## 修改明细\n")
        lines.append("| 原表述 | 学术化表述 |")
        lines.append("|--------|----------|")
        for oral, academic in replacements_made:
            lines.append(f"| {oral} | {academic} |")

    lines.append("\n## 进一步建议\n")
    if is_chinese(text):
        lines.extend([
            "- 检查主谓宾是否完整",
            '- 避免使用第一人称"我"',
            "- 确保每句话有明确的论证逻辑",
            "- 引用文献支撑关键论断",
        ])
    else:
        lines.extend([
            "- Ensure subject-verb agreement",
            "- Avoid first-person pronouns in formal sections",
            "- Support key claims with citations",
            "- Use hedging language where appropriate (e.g., 'suggests', 'appears to')",
        ])

    return "\n".join(lines)
