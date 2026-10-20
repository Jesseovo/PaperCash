#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多层次相似度检测引擎 - 查重核心算法"""


class TextSimilarity:
    """增强的字面相似度检测"""

    def compute(self, query: str, target: str) -> float:
        """
        计算字面相似度 (0.0 ~ 1.0)
        结合多种算法提高准确率
        """
        if not query or not target:
            return 0.0

        # 1. 最长公共子序列比例
        lcs_ratio = self._lcs_ratio(query, target)

        # 2. 编辑距离比例
        edit_ratio = self._edit_distance_ratio(query, target)

        # 3. Trigram重叠 (比bigram更准)
        trigram_sim = self._ngram_overlap(query, target, n=3)

        # 4. Jaccard相似度
        jaccard_sim = self._jaccard_similarity(query, target)

        # 加权综合
        return (0.3 * lcs_ratio +
                0.3 * edit_ratio +
                0.25 * trigram_sim +
                0.15 * jaccard_sim)

    def _lcs_ratio(self, s1: str, s2: str) -> float:
        """最长公共子序列比例"""
        m, n = len(s1), len(s2)
        if m == 0 or n == 0:
            return 0.0

        # 动态规划计算LCS
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])

        lcs_len = dp[m][n]
        # 返回LCS长度占两个字符串平均长度的比例
        return 2.0 * lcs_len / (m + n)

    def _edit_distance_ratio(self, s1: str, s2: str) -> float:
        """基于编辑距离的相似度"""
        distance = self._levenshtein(s1, s2)
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        return 1.0 - (distance / max_len)

    def _levenshtein(self, s1: str, s2: str) -> int:
        """计算Levenshtein编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # 插入、删除、替换的代价
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _ngram_overlap(self, query: str, target: str, n: int = 3) -> float:
        """N-gram重叠相似度"""
        def get_ngrams(text: str, n: int) -> set:
            text = text.lower().replace(' ', '')
            return set(text[i:i+n] for i in range(len(text) - n + 1))

        query_ngrams = get_ngrams(query, n)
        target_ngrams = get_ngrams(target, n)

        if not query_ngrams or not target_ngrams:
            return 0.0

        intersection = query_ngrams & target_ngrams
        union = query_ngrams | target_ngrams

        return len(intersection) / len(union) if union else 0.0

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Jaccard相似度 (基于词集合)"""
        def tokenize(text: str) -> set:
            # 简单分词
            tokens = set()
            word = ""
            for ch in text.lower():
                if ch.isalnum() or '一' <= ch <= '鿿':
                    word += ch
                else:
                    if word:
                        tokens.add(word)
                        word = ""
            if word:
                tokens.add(word)
            return tokens

        tokens1 = tokenize(text1)
        tokens2 = tokenize(text2)

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        return len(intersection) / len(union)


class SemanticSimilarity:
    """轻量级语义相似度检测"""

    def __init__(self):
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """检查是否可用TF-IDF"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            return True
        except ImportError:
            return False

    def compute(self, query: str, target: str) -> float:
        """
        计算语义相似度
        使用TF-IDF + Cosine相似度
        """
        if not self.available:
            # 降级到字面相似度
            return TextSimilarity().compute(query, target)

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            # TF-IDF向量化
            vectorizer = TfidfVectorizer(
                analyzer='char',  # 字符级,对中文友好
                ngram_range=(2, 3),  # 2-3gram
                min_df=1
            )

            tfidf_matrix = vectorizer.fit_transform([query, target])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            return float(similarity)
        except Exception:
            # 失败时降级
            return TextSimilarity().compute(query, target)


class StructuralSimilarity:
    """结构相似度检测"""

    def compute(self, query: str, target: str) -> float:
        """
        检测句子结构相似度
        基于词性、长度、标点等特征
        """
        # 1. 长度相似度
        len_sim = 1.0 - abs(len(query) - len(target)) / max(len(query), len(target))

        # 2. 标点符号模式
        punct_sim = self._punctuation_similarity(query, target)

        # 3. 数字模式
        number_sim = self._number_pattern_similarity(query, target)

        return 0.5 * len_sim + 0.3 * punct_sim + 0.2 * number_sim

    def _punctuation_similarity(self, text1: str, text2: str) -> float:
        """标点符号相似度"""
        import string
        punct_set = set(string.punctuation + '，。！？；：""''（）【】《》')

        p1 = [c for c in text1 if c in punct_set]
        p2 = [c for c in text2 if c in punct_set]

        if not p1 and not p2:
            return 1.0
        if not p1 or not p2:
            return 0.0

        # 计算标点序列的编辑距离
        distance = TextSimilarity()._levenshtein(''.join(p1), ''.join(p2))
        max_len = max(len(p1), len(p2))

        return 1.0 - (distance / max_len) if max_len > 0 else 0.0

    def _number_pattern_similarity(self, text1: str, text2: str) -> float:
        """数字模式相似度"""
        import re

        nums1 = re.findall(r'\d+\.?\d*', text1)
        nums2 = re.findall(r'\d+\.?\d*', text2)

        if not nums1 and not nums2:
            return 1.0
        if not nums1 or not nums2:
            return 0.0

        # 比较数字出现的位置和数量
        return min(len(nums1), len(nums2)) / max(len(nums1), len(nums2))


class SimilarityEngine:
    """多层次相似度检测引擎 - 主入口"""

    def __init__(self):
        self.text_sim = TextSimilarity()
        self.semantic_sim = SemanticSimilarity()
        self.struct_sim = StructuralSimilarity()

    def compute_similarity(self, query: str, target: str) -> dict:
        """
        计算多层次相似度

        返回:
        {
            'literal': 0.0-1.0,      # 字面重复度
            'semantic': 0.0-1.0,     # 语义相似度
            'structural': 0.0-1.0,   # 结构相似度
            'final_score': 0.0-1.0,  # 综合评分
            'detection_type': str    # 检测类型
        }
        """
        # 计算各维度相似度
        literal = self.text_sim.compute(query, target)
        semantic = self.semantic_sim.compute(query, target)
        structural = self.struct_sim.compute(query, target)

        # 加权综合得分
        final_score = (0.5 * literal +
                      0.3 * semantic +
                      0.2 * structural)

        # 分类检测类型
        detection_type = self._classify_plagiarism_type(literal, semantic, structural)

        return {
            'literal': round(literal, 3),
            'semantic': round(semantic, 3),
            'structural': round(structural, 3),
            'final_score': round(final_score, 3),
            'detection_type': detection_type
        }

    def _classify_plagiarism_type(self, literal: float, semantic: float, structural: float) -> str:
        """
        分类与候选文本的相似程度；不判断抄袭行为。

        类型:
        - near_exact: 字面高度重合
        - high_overlap: 字面和辅助评分均较高
        - possible_overlap: 辅助评分较高
        - similar: 有一定相似性
        - low_similarity: 与当前候选文本相似度低
        """
        if literal > 0.85:
            return 'near_exact'
        elif literal > 0.6 and semantic > 0.75:
            return 'high_overlap'
        elif literal < 0.5 and semantic > 0.7:
            return 'possible_overlap'
        elif semantic > 0.5 or literal > 0.5:
            return 'similar'
        else:
            return 'low_similarity'

    def assess_risk(self, similarity_result: dict) -> str:
        """
        评估风险等级

        返回:
        - critical: 高度相似
        - high: 较高相似
        - medium: 中等相似
        - low: 较低相似
        """
        detection_type = similarity_result['detection_type']
        final_score = similarity_result['final_score']

        if detection_type == 'near_exact':
            return 'critical'
        elif detection_type == 'high_overlap' or final_score >= 0.75:
            return 'high'
        elif detection_type == 'possible_overlap' or final_score >= 0.6:
            return 'medium'
        return 'low'


# 测试代码
if __name__ == "__main__":
    engine = SimilarityEngine()

    # 测试用例
    test_cases = [
        ("深度学习在医学影像中的应用研究", "深度学习在医学影像中的应用研究"),  # 完全相同
        ("深度学习在医学影像中的应用研究", "深度学习在医学图像领域的应用分析"),  # 轻微改写
        ("深度学习在医学影像中的应用研究", "神经网络技术用于医疗诊断图像的智能处理"),  # 改写抄袭
        ("深度学习在医学影像中的应用研究", "机器学习算法在金融风控领域的实践"),  # 不相关
    ]

    for q, t in test_cases:
        result = engine.compute_similarity(q, t)
        risk = engine.assess_risk(result)
        print(f"\nQuery: {q}")
        print(f"Target: {t}")
        print(f"Result: {result}")
        print(f"Risk: {risk}")
