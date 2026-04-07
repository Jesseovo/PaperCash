"""查询预处理（中文分词 + 关键词提取）"""

import re
from typing import Optional

try:
    import jieba
    import jieba.analyse
    _HAS_JIEBA = True
except ImportError:
    _HAS_JIEBA = False

_CN_STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "里",
    "什么", "怎么", "如何", "请", "帮", "帮我", "能", "能不能", "可以",
    "关于", "基于", "研究", "分析", "探讨", "论文", "综述", "最新", "相关",
}

_EN_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "about", "between",
    "through", "during", "before", "after", "and", "but", "or", "not",
    "this", "that", "these", "those", "it", "its", "my", "your", "his",
    "her", "our", "their", "what", "which", "who", "how", "when", "where",
    "paper", "research", "study", "review", "analysis", "latest", "recent",
    "best", "top", "find", "search", "look",
}

_SYNONYMS_CN = {
    "深度学习": ["deep learning", "DL", "深层学习"],
    "机器学习": ["machine learning", "ML"],
    "自然语言处理": ["NLP", "natural language processing"],
    "计算机视觉": ["computer vision", "CV"],
    "强化学习": ["reinforcement learning", "RL"],
    "神经网络": ["neural network", "NN"],
    "卷积神经网络": ["CNN", "convolutional neural network"],
    "生成对抗网络": ["GAN", "generative adversarial network"],
    "注意力机制": ["attention mechanism"],
    "大语言模型": ["LLM", "large language model"],
}


def is_chinese(text: str) -> bool:
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return True
    return False


def segment(text: str) -> list[str]:
    """中文分词"""
    if not _HAS_JIEBA:
        return _simple_segment(text)
    words = jieba.lcut(text)
    return [w.strip() for w in words if w.strip()]


def _simple_segment(text: str) -> list[str]:
    """无 jieba 时的简单分词"""
    parts = re.split(r"[\s,，。、；;：:！!？?()（）\[\]【】{}\"'""'']+", text)
    return [p.strip() for p in parts if p.strip()]


def extract_keywords(text: str, top_k: int = 8) -> list[str]:
    """提取关键词"""
    if _HAS_JIEBA:
        keywords = jieba.analyse.extract_tags(text, topK=top_k)
        if keywords:
            return keywords

    words = segment(text)
    all_stops = _CN_STOPWORDS | _EN_STOPWORDS
    filtered = [w for w in words if w.lower() not in all_stops and len(w) > 1]
    seen: set[str] = set()
    result: list[str] = []
    for w in filtered:
        low = w.lower()
        if low not in seen:
            seen.add(low)
            result.append(w)
    return result[:top_k]


def expand_query(text: str) -> list[str]:
    """扩展查询词（同义词）"""
    keywords = extract_keywords(text)
    expanded = list(keywords)
    for kw in keywords:
        if kw in _SYNONYMS_CN:
            expanded.extend(_SYNONYMS_CN[kw])
    return expanded


def build_search_queries(text: str) -> dict[str, str]:
    """为不同数据源构建搜索查询"""
    keywords = extract_keywords(text)
    cn_keywords = [k for k in keywords if is_chinese(k)]
    en_keywords = [k for k in keywords if not is_chinese(k)]

    expanded = expand_query(text)
    en_expanded = [k for k in expanded if not is_chinese(k)]

    return {
        "semantic_scholar": " ".join(en_expanded or keywords),
        "arxiv": " AND ".join(en_expanded[:5] or keywords[:5]),
        "crossref": " ".join(en_keywords[:3] + en_expanded[:3] or keywords[:5]),
        "baidu_xueshu": " ".join(cn_keywords or keywords),
        "original": text,
    }
