"""降AI率改写 - 让AI生成内容更像人写的"""

from __future__ import annotations
import re
import random
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from query import is_chinese

_AI_CLICHES_CN = {
    "综上所述": ["基于上述分析", "通过以上论述可以发现", "回顾前文的讨论"],
    "总而言之": ["概括而言", "从整体来看", "纵观全局"],
    "值得注意的是": ["需要指出的是", "一个关键的发现是", "不容忽视的是"],
    "众所周知": ["学界普遍认为", "已有研究表明", "根据现有文献"],
    "随着社会的发展": ["在当前背景下", "伴随着相关技术的演进", "在新形势下"],
    "随着科技的进步": ["技术变革推动下", "得益于技术突破", "在技术快速迭代的背景下"],
    "本文认为": ["笔者认为", "基于实证分析发现", "从研究结果来看"],
    "在当今社会": ["在现阶段", "当下", "目前"],
    "具有重要意义": ["对该领域具有参考价值", "有助于推动相关研究", "为后续研究提供了启示"],
    "不可或缺": ["至关重要", "扮演着关键角色", "是核心要素之一"],
    "日益重要": ["愈发受到重视", "其重要性不断凸显", "关注度持续上升"],
    "由此可见": ["这进一步说明", "由此推断", "据此分析"],
    "毋庸置疑": ["可以确认的是", "研究证据表明", "数据显示"],
    "显而易见": ["从数据中可以观察到", "分析结果表明", "实证结果显示"],
    "总的来说": ["整体而言", "从全局来看", "综合各方面因素"],
}

_AI_CLICHES_EN = {
    "In conclusion": ["Drawing from the analysis above", "Based on the findings presented"],
    "It is worth noting": ["A notable observation is", "One key finding suggests"],
    "plays a crucial role": ["serves as a key factor in", "is central to"],
    "In today's world": ["In the current landscape", "Under present conditions"],
    "It goes without saying": ["The evidence clearly indicates", "As demonstrated"],
    "Furthermore": ["Additionally", "In a related vein", "Moreover"],
    "However": ["Nevertheless", "That said", "On the other hand"],
    "In summary": ["To synthesize the above points", "Reviewing the discussed evidence"],
    "As we all know": ["Existing literature suggests", "Prior research indicates"],
    "In recent years": ["Over the past decade", "In the contemporary period"],
    "more and more": ["an increasing number of", "a growing body of"],
    "a wide range of": ["diverse", "various", "multiple"],
}

_PERSONAL_INJECTIONS_CN = [
    "从笔者的研究经验来看，",
    "结合实际情况分析，",
    "从实践角度而言，",
    "在笔者看来，",
    "根据笔者的观察，",
    "基于本研究的数据分析，",
    "从理论与实践相结合的角度，",
]

_PERSONAL_INJECTIONS_EN = [
    "From our analysis, ",
    "Based on the empirical evidence gathered, ",
    "In our observation, ",
    "Drawing from the data presented, ",
    "Considering the practical implications, ",
]


def humanize_text(text: str) -> str:
    """降AI率改写"""
    is_cn = is_chinese(text)

    lines = ["# PaperCash 降AI率改写结果\n"]
    lines.append("## 原文\n")
    lines.append(f"{text}\n")
    lines.append("---\n")
    lines.append("## 改写后\n")

    result = text

    result = _replace_cliches(result, is_cn)
    result = _restructure_sentences(result, is_cn)
    result = _inject_perspective(result, is_cn)
    result = _vary_sentence_length(result, is_cn)

    lines.append(f"{result}\n")
    lines.append("---\n")

    changes = _diff_summary(text, result, is_cn)
    lines.append("## 修改摘要\n")
    lines.extend(changes)

    lines.append("\n## 降AI率策略说明\n")
    if is_cn:
        lines.extend([
            '1. **替换AI高频套话**: 将"综上所述"等AI常用表达替换为更自然的学术用语',
            '2. **注入个人视角**: 添加"笔者认为"等体现独立思考的表述',
            "3. **调整句式结构**: 长短句交替，被动改主动，增加句式多样性",
            "4. **增加具体性**: 建议在改写基础上补充具体数据、案例或对比",
            "",
            "⚠️ 本工具仅提供改写建议，最终文本需体现学生本人的思考和理解。",
        ])
    else:
        lines.extend([
            "1. **Replace AI clichés**: Swap common AI phrases for more natural academic language",
            "2. **Inject perspective**: Add phrases showing independent thinking",
            "3. **Restructure sentences**: Vary length and voice for diversity",
            "4. **Add specificity**: Supplement with data, examples, or comparisons",
            "",
            "⚠️ This tool provides rewriting suggestions only. Final text should reflect your own understanding.",
        ])

    return "\n".join(lines)


def _replace_cliches(text: str, is_cn: bool) -> str:
    """替换AI高频套话"""
    cliches = _AI_CLICHES_CN if is_cn else _AI_CLICHES_EN
    result = text

    for cliche, alternatives in cliches.items():
        if cliche in result:
            replacement = random.choice(alternatives)
            result = result.replace(cliche, replacement, 1)

    return result


def _restructure_sentences(text: str, is_cn: bool) -> str:
    """调整句式结构"""
    if is_cn:
        sentences = re.split(r"(。)", text)
    else:
        sentences = re.split(r"(\. )", text)

    result_parts: list[str] = []
    for i, part in enumerate(sentences):
        if is_cn and part == "。":
            result_parts.append(part)
            continue
        if not is_cn and part == ". ":
            result_parts.append(part)
            continue

        if is_cn:
            part = _cn_restructure(part)
        else:
            part = _en_restructure(part)

        result_parts.append(part)

    return "".join(result_parts)


def _cn_restructure(sentence: str) -> str:
    """中文句式重构"""
    if "被" in sentence and random.random() > 0.5:
        sentence = sentence.replace("被广泛应用", "在实践中得到了广泛运用")
        sentence = sentence.replace("被认为是", "通常被视为")

    if sentence.startswith("这") and random.random() > 0.5:
        sentence = "该" + sentence[1:]

    return sentence


def _en_restructure(sentence: str) -> str:
    """英文句式重构"""
    passive_patterns = [
        (r"is considered to be", "is generally regarded as"),
        (r"has been widely used", "sees widespread application"),
        (r"can be seen that", "becomes apparent that"),
    ]
    for pattern, replacement in passive_patterns:
        sentence = re.sub(pattern, replacement, sentence, flags=re.IGNORECASE)

    return sentence


def _inject_perspective(text: str, is_cn: bool) -> str:
    """在适当位置注入个人视角"""
    if is_cn:
        sentences = text.split("。")
        injections = _PERSONAL_INJECTIONS_CN
    else:
        sentences = re.split(r"\. ", text)
        injections = _PERSONAL_INJECTIONS_EN

    if len(sentences) < 3:
        return text

    inject_pos = len(sentences) // 3
    if inject_pos < len(sentences) and sentences[inject_pos].strip():
        prefix = random.choice(injections)
        s = sentences[inject_pos].strip()
        if is_cn:
            if s:
                sentences[inject_pos] = prefix + s
        else:
            if s:
                sentences[inject_pos] = prefix + s[0].lower() + s[1:]

    separator = "。" if is_cn else ". "
    return separator.join(sentences)


def _vary_sentence_length(text: str, is_cn: bool) -> str:
    """调整句子长度变化"""
    if is_cn:
        sentences = text.split("。")
        result: list[str] = []
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if len(s) > 60 and "，" in s:
                parts = s.split("，", 1)
                if len(parts[0]) > 15 and len(parts[1]) > 15:
                    result.append(parts[0])
                    result.append(parts[1])
                    continue
            result.append(s)
        return "。".join(result) + ("。" if result else "")
    return text


def _diff_summary(original: str, modified: str, is_cn: bool) -> list[str]:
    """生成修改摘要"""
    lines: list[str] = []
    orig_len = len(original)
    mod_len = len(modified)

    diff_chars = sum(1 for a, b in zip(original, modified) if a != b)
    diff_chars += abs(orig_len - mod_len)
    change_rate = diff_chars / max(orig_len, 1) * 100

    lines.append(f"- 原文长度: {orig_len} 字符")
    lines.append(f"- 改写后长度: {mod_len} 字符")
    lines.append(f"- 预估修改率: {change_rate:.1f}%")

    return lines
