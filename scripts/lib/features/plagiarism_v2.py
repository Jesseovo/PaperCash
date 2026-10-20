#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查重预检 v2.0 - 增强版多层次检测"""

from __future__ import annotations
import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schema import Paper
from similarity_engine import SimilarityEngine
from query import extract_keywords, is_chinese
from ui import progress, warning, info


class CheckResult:
    """查重结果"""

    def __init__(self, sentence: str, similarity: dict, matched_paper: Paper | None = None):
        self.sentence = sentence
        self.similarity = similarity  # {literal, semantic, structural, final_score, detection_type}
        self.matched_paper = matched_paper
        self.risk_level = self._assess_risk()
        self.suggestion = self._generate_suggestion()

    def _assess_risk(self) -> str:
        if self.matched_paper is None:
            return 'unverified'
        detection_type = self.similarity['detection_type']
        final_score = self.similarity['final_score']

        if detection_type == 'near_exact':
            return 'critical'
        elif detection_type == 'high_overlap' or final_score >= 0.75:
            return 'high'
        elif detection_type == 'possible_overlap' or final_score >= 0.6:
            return 'medium'
        elif final_score >= 0.4:
            return 'low'
        else:
            return 'low'

    def _generate_suggestion(self) -> str:
        """根据检测类型生成建议"""
        if self.matched_paper is None:
            return "未找到可比较的候选文献；不能据此判断原创性。"
        detection_type = self.similarity['detection_type']
        lang = 'zh' if is_chinese(self.sentence) else 'en'

        suggestions = {
            'near_exact': {
                'zh': "与候选文献元数据高度相似；请核对原文并规范引用。",
                'en': "High similarity to retrieved metadata; verify the source and cite it."
            },
            'high_overlap': {
                'zh': "与候选文献较相似；请核对原文、观点归属和引用。",
                'en': "Similar to retrieved metadata; verify attribution and citation."
            },
            'possible_overlap': {
                'zh': "存在表达相似性；请阅读候选文献并确认是否需要引用。",
                'en': "Some similarity was found; check the source and citation."
            },
            'similar': {
                'zh': "发现一定的文字相似性；请核对是否需要引用。",
                'en': "Some text similarity was found; check whether citation is needed."
            },
            'low_similarity': {
                'zh': "与当前候选文献相似度较低；不能据此判断原创性。",
                'en': "Low similarity to this candidate; originality is not established."
            }
        }

        return suggestions.get(detection_type, {}).get(lang, "")


def _split_sentences(text: str) -> list[str]:
    """将文本拆分为句子"""
    text = text.strip()
    if is_chinese(text):
        sentences = re.split(r"[。！？；\n]+", text)
    else:
        sentences = re.split(r"(?<=[.!?])\s+", text)

    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]


def _search_multiple_sources(query: str, sources: list[str], limit_per_source: int = 10) -> list[Paper]:
    """
    并行搜索多个数据源

    Args:
        query: 搜索查询
        sources: 数据源列表 ['semantic_scholar', 'crossref', 'baidu_xueshu']
        limit_per_source: 每个源返回的数量

    Returns:
        合并去重后的论文列表
    """
    all_papers = []
    seen_titles = set()

    source_map = {
        'semantic_scholar': 'sources.semantic_scholar',
        'arxiv': 'sources.arxiv',
        'crossref': 'sources.crossref',
        'baidu_xueshu': 'sources.baidu_xueshu',
        'cnki': 'sources.cnki',
        'wanfang': 'sources.wanfang',
    }

    def search_one_source(source_name: str):
        try:
            if source_name not in source_map:
                return []

            import importlib
            module = importlib.import_module(source_map[source_name])
            papers = module.search(query, limit=limit_per_source)
            return papers or []
        except Exception as e:
            warning(f"{source_name} 搜索失败: {e}")
            return []

    if not sources:
        return []

    # 并行搜索
    with ThreadPoolExecutor(max_workers=min(len(sources), 4)) as executor:
        future_to_source = {executor.submit(search_one_source, src): src for src in sources}

        for future in as_completed(future_to_source):
            papers = future.result()
            for paper in papers:
                # 去重
                title_key = paper.title.lower().strip()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    all_papers.append(paper)

    return all_papers


def check_plagiarism_v2(
    text: str,
    mode: str = 'standard',
    sources: list[str] | None = None
) -> tuple[list[CheckResult], dict]:
    """
    增强版查重检测

    Args:
        text: 待检测文本
        mode: 检测模式
            - 'fast': 快速模式 (CrossRef + arXiv，每源最多5篇)
            - 'standard': 标准模式 (4源，每源最多10篇)
            - 'deep': 深度模式 (6源，每源最多20篇)
        sources: 自定义数据源列表

    Returns:
        (结果列表, 统计信息)
    """
    # 配置检测策略
    if mode == 'fast':
        sources = sources or ['crossref', 'arxiv']
        limit_per_source = 5
    elif mode == 'standard':
        sources = sources or ['semantic_scholar', 'crossref', 'arxiv', 'baidu_xueshu']
        limit_per_source = 10
    else:  # deep
        sources = sources or ['semantic_scholar', 'crossref', 'arxiv',
                              'baidu_xueshu', 'cnki', 'wanfang']
        limit_per_source = 20

    info(f"🔍 检测模式: {mode}")
    info(f"📚 数据源: {', '.join(sources)} (每源{limit_per_source}篇)")
    print(file=sys.stderr)

    sentences = _split_sentences(text)
    if not sentences:
        return [], {
            'total_sentences': 0,
            'checked_sentences': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'unverified': 0,
            'compared_sentences': 0,
            'mode': mode,
            'sources': sources,
        }

    # 初始化相似度引擎
    similarity_engine = SimilarityEngine()
    results = []
    attempted = 0

    for idx, sentence in enumerate(sentences):
        progress(idx + 1, len(sentences), f"检测中... ({mode}模式)")

        # 提取关键词
        keywords = extract_keywords(sentence, top_k=5)
        if not keywords:
            # 无关键词时无法检索，不能判断原创性。
            results.append(CheckResult(
                sentence=sentence,
                similarity={
                    'literal': 0.0,
                    'semantic': 0.0,
                    'structural': 0.0,
                    'final_score': 0.0,
                    'detection_type': 'low_similarity'
                },
                matched_paper=None
            ))
            continue

        # 搜索多个数据源
        attempted += 1
        query = " ".join(keywords)
        matched_papers = _search_multiple_sources(query, sources, limit_per_source)

        # 对每篇论文计算相似度
        best_match = None
        max_score = 0.0

        for paper in matched_papers:
            # 按标题和摘要片段比较，避免长摘要稀释一句话的相似度。
            candidates = [paper.title]
            if paper.abstract:
                candidates.extend(s.strip() for s in re.split(r"[。！？；.!?]+", paper.abstract[:500])
                                  if len(s.strip()) > 10)
            for target_text in candidates:
                sim_result = similarity_engine.compute_similarity(sentence, target_text)
                if sim_result['final_score'] > max_score:
                    max_score = sim_result['final_score']
                    best_match = {'paper': paper, 'similarity': sim_result}

        # 构建结果
        if best_match:
            result = CheckResult(
                sentence=sentence,
                similarity=best_match['similarity'],
                matched_paper=best_match['paper']
            )
        else:
            # 没有候选文献，结果不可判定。
            result = CheckResult(
                sentence=sentence,
                similarity={
                    'literal': 0.0,
                    'semantic': 0.0,
                    'structural': 0.0,
                    'final_score': 0.0,
                    'detection_type': 'low_similarity'
                },
                matched_paper=None
            )

        results.append(result)

    # 统计
    stats = {
        'total_sentences': len(sentences),
        'checked_sentences': attempted,
        'compared_sentences': len([r for r in results if r.matched_paper is not None]),
        'critical': len([r for r in results if r.risk_level == 'critical']),
        'high': len([r for r in results if r.risk_level == 'high']),
        'medium': len([r for r in results if r.risk_level == 'medium']),
        'low': len([r for r in results if r.risk_level == 'low']),
        'unverified': len([r for r in results if r.risk_level == 'unverified']),
        'mode': mode,
        'sources': sources,
    }

    return results, stats


# 向后兼容的函数
def check_plagiarism(text: str) -> tuple[list, dict]:
    """
    兼容旧版API
    使用标准模式检测
    """
    results, stats = check_plagiarism_v2(text, mode='standard')

    # 转换为旧格式
    legacy_results = []
    for r in results:
        legacy_results.append({
            'sentence': r.sentence,
            'similarity': r.similarity['final_score'],
            'risk_level': r.risk_level,
            'suggestion': r.suggestion,
            'matched_title': r.matched_paper.title if r.matched_paper else None,
            'matched_authors': r.matched_paper.authors_str if r.matched_paper else None,
            'matched_source': r.matched_paper.source if r.matched_paper else None,
        })

    # 转换统计格式 (兼容旧版)
    legacy_stats = {
        'total_sentences': stats['total_sentences'],
        'checked_sentences': stats['checked_sentences'],
        'high_risk': stats['critical'] + stats['high'],
        'medium_risk': stats['medium'],
        'low_risk': stats['low'],
    }

    return legacy_results, legacy_stats
