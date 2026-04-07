"""相关性计算（中文 + 英文）"""

from __future__ import annotations


def _tokenize(text: str) -> list[str]:
    """简单分词：中文按字，英文按空格"""
    tokens: list[str] = []
    buf = ""
    for ch in text.lower():
        if "\u4e00" <= ch <= "\u9fff":
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
        elif ch.isalnum():
            buf += ch
        else:
            if buf:
                tokens.append(buf)
                buf = ""
    if buf:
        tokens.append(buf)
    return tokens


def _ngrams(tokens: list[str], n: int = 2) -> set[str]:
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def text_similarity(query: str, text: str) -> float:
    """计算查询与文本的相似度 (0.0 ~ 1.0)"""
    if not query or not text:
        return 0.0

    q_tokens = _tokenize(query)
    t_tokens = _tokenize(text)

    if not q_tokens or not t_tokens:
        return 0.0

    q_set = set(q_tokens)
    t_set = set(t_tokens)
    token_overlap = len(q_set & t_set) / len(q_set) if q_set else 0.0

    q_bigrams = _ngrams(q_tokens)
    t_bigrams = _ngrams(t_tokens)
    if q_bigrams and t_bigrams:
        bigram_sim = len(q_bigrams & t_bigrams) / len(q_bigrams | t_bigrams)
    else:
        bigram_sim = 0.0

    q_lower = query.lower()
    t_lower = text.lower()
    substring_bonus = 0.0
    if q_lower in t_lower:
        substring_bonus = 0.3
    elif t_lower in q_lower:
        substring_bonus = 0.2

    score = 0.5 * token_overlap + 0.3 * bigram_sim + 0.2 * substring_bonus
    return min(1.0, score)


def compute_relevance(query: str, title: str, abstract: str = "") -> float:
    """综合标题和摘要计算相关性"""
    title_sim = text_similarity(query, title)
    abstract_sim = text_similarity(query, abstract) if abstract else 0.0
    return 0.65 * title_sim + 0.35 * abstract_sim


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """Jaccard 相似度（用于查重预检）"""
    a_tokens = set(_tokenize(text_a))
    b_tokens = set(_tokenize(text_b))
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = a_tokens & b_tokens
    union = a_tokens | b_tokens
    return len(intersection) / len(union)
