"""Analysis and classification modules for page speed optimization."""

from .cms_detector import CMSDetector
from .issue_classifier import IssueClassifier, CWV_THRESHOLDS, AUDIT_CWV_MAP
from .resource_analyzer import ResourceAnalyzer

__all__ = [
    "CMSDetector",
    "IssueClassifier",
    "ResourceAnalyzer",
    "CWV_THRESHOLDS",
    "AUDIT_CWV_MAP",
]
