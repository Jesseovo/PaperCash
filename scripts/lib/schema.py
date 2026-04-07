"""数据结构定义"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Paper:
    """论文统一数据结构"""
    title: str
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    abstract: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    citation_count: int = 0
    source: str = ""
    venue: Optional[str] = None
    paper_type: Optional[str] = None  # e.g. "book" for GB/T 7714 [M]
    keywords: list[str] = field(default_factory=list)
    paper_id: Optional[str] = None
    relevance_score: float = 0.0
    final_score: float = 0.0

    @property
    def authors_str(self) -> str:
        if not self.authors:
            return "未知作者"
        if len(self.authors) <= 3:
            return ", ".join(self.authors)
        return f"{self.authors[0]} 等"

    @property
    def citation_key(self) -> str:
        first_author = self.authors[0].split()[-1] if self.authors else "Unknown"
        return f"{first_author}{self.year or 'n.d.'}"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "doi": self.doi,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "citation_count": self.citation_count,
            "source": self.source,
            "venue": self.venue,
            "paper_type": self.paper_type,
            "keywords": self.keywords,
            "relevance_score": self.relevance_score,
            "final_score": self.final_score,
        }


@dataclass
class SearchResult:
    """搜索结果集合"""
    query: str
    papers: list[Paper] = field(default_factory=list)
    total_found: int = 0
    sources_used: list[str] = field(default_factory=list)
    search_time_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "total_found": self.total_found,
            "sources_used": self.sources_used,
            "search_time_ms": self.search_time_ms,
            "papers": [p.to_dict() for p in self.papers],
        }


@dataclass
class CheckResult:
    """查重预检结果"""
    sentence: str
    similarity: float
    matched_title: Optional[str] = None
    matched_authors: Optional[str] = None
    matched_source: Optional[str] = None
    risk_level: str = "low"  # low / medium / high
    suggestion: Optional[str] = None


@dataclass
class FormatIssue:
    """格式检查问题"""
    location: str
    issue_type: str
    expected: str
    actual: str
    severity: str = "warning"  # info / warning / error
