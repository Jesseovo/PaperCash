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


def _search_sentence(query: str, search_cache: dict[str, list[Paper]]) -> list[Paper]:
    if query in search_cache:
        return search_cache[query]
    papers: list[Paper] = []
    try:
        from sources.semantic_scholar import search as ss_search
        papers = ss_search(query, limit=5)
    except Exception:
        pass
    search_cache[query] = papers
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


def check_plagiarism(text: str) -> tuple[list[CheckResult], dict]:
    sentences = _split_sentences(text)
    if not sentences:
        stats = {
            "total_sentences": 0,
            "checked_sentences": 0,
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0,
        }
        return [], stats

    search_cache: dict[str, list[Paper]] = {}
    results: list[CheckResult] = []
    checked_sentences = 0

    for idx, sentence in enumerate(sentences):
        progress(idx + 1, len(sentences), "查重检索中...")

        keywords = extract_keywords(sentence, top_k=5)
        matched_papers: list[Paper] = []
        if keywords:
            checked_sentences += 1
            q = " ".join(keywords)
            try:
                matched_papers = _search_sentence(q, search_cache)
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

    high = sum(1 for r in results if r.risk_level == "high")
    med = sum(1 for r in results if r.risk_level == "medium")
    low = sum(1 for r in results if r.risk_level == "low")
    stats = {
        "total_sentences": len(sentences),
        "checked_sentences": checked_sentences,
        "high_risk": high,
        "medium_risk": med,
        "low_risk": low,
    }

    return results, stats
