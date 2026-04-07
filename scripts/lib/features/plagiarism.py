"""查重预检 - 句子级学术库检索"""

from __future__ import annotations
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper, CheckResult
from relevance import text_similarity
from query import extract_keywords, is_chinese
from ui import progress


def _split_sentences(text: str) -> list[str]:
    """将文本拆分为句子"""
    text = text.strip()
    if is_chinese(text):
        sentences = re.split(r"[。！？；\n]+", text)
    else:
        sentences = re.split(r"(?<=[.!?])\s+", text)

    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]


def _search_sentence(sentence: str) -> list[Paper]:
    """对单个句子进行学术库检索"""
    keywords = extract_keywords(sentence, top_k=5)
    if not keywords:
        return []

    query = " ".join(keywords)
    papers: list[Paper] = []

    try:
        from sources.semantic_scholar import search as ss_search
        results = ss_search(query, limit=5)
        papers.extend(results)
    except Exception:
        pass

    return papers


def _assess_risk(similarity: float) -> str:
    if similarity >= 0.7:
        return "high"
    elif similarity >= 0.5:
        return "medium"
    return "low"


def _generate_suggestion(sentence: str, risk_level: str) -> str | None:
    if risk_level == "low":
        return None

    if is_chinese(sentence):
        suggestions = [
            "建议改写此句：调整语序，替换同义词，或用自己的语言重新表述",
            "可尝试：将被动句改为主动句，添加具体数据支撑",
            "建议：引用原文并标注出处，或改用间接引述的方式表达",
        ]
    else:
        suggestions = [
            "Consider rephrasing: adjust word order, use synonyms, or express in your own words",
            "Try: convert passive to active voice, add specific data",
            "Suggest: cite the source directly or use indirect quotation",
        ]

    import random
    return random.choice(suggestions)


def check_plagiarism(text: str, sample_rate: float = 0.3) -> list[CheckResult]:
    """查重预检

    Args:
        text: 待检查文本
        sample_rate: 抽样比例（0.0~1.0），降低API调用量
    """
    sentences = _split_sentences(text)
    if not sentences:
        return []

    import random
    sample_size = max(5, int(len(sentences) * sample_rate))
    if sample_size < len(sentences):
        sampled_indices = set(random.sample(range(len(sentences)), sample_size))
    else:
        sampled_indices = set(range(len(sentences)))

    results: list[CheckResult] = []

    for idx, sentence in enumerate(sentences):
        if idx not in sampled_indices:
            results.append(CheckResult(
                sentence=sentence,
                similarity=0.0,
                risk_level="low",
            ))
            continue

        progress(idx + 1, len(sentences), "查重检索中...")

        try:
            matched_papers = _search_sentence(sentence)
        except Exception:
            matched_papers = []

        max_sim = 0.0
        best_match: Paper | None = None

        for paper in matched_papers:
            if paper.abstract:
                sim = max(
                    text_similarity(sentence, paper.title),
                    text_similarity(sentence, paper.abstract),
                )
            else:
                sim = text_similarity(sentence, paper.title)

            if sim > max_sim:
                max_sim = sim
                best_match = paper

        risk = _assess_risk(max_sim)
        suggestion = _generate_suggestion(sentence, risk)

        result = CheckResult(
            sentence=sentence,
            similarity=max_sim,
            risk_level=risk,
            suggestion=suggestion,
        )

        if best_match:
            result.matched_title = best_match.title
            result.matched_authors = best_match.authors_str
            result.matched_source = best_match.source

        results.append(result)

    return results
