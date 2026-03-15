"""Data models for the Page Loading Speed Optimization Agent."""

from .speed_issue import (
    Severity,
    CWVMetric,
    CWVStatus,
    CWVAssessment,
    SpeedIssue,
    CMSInfo,
)
from .analysis_result import AnalysisResult, PageStats

__all__ = [
    "Severity",
    "CWVMetric",
    "CWVStatus",
    "CWVAssessment",
    "SpeedIssue",
    "CMSInfo",
    "AnalysisResult",
    "PageStats",
]
