"""Data model for the complete page speed analysis result."""

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime

from .speed_issue import SpeedIssue, CWVAssessment, CMSInfo, Severity


@dataclass
class PageStats:
    """Aggregate resource size and request statistics for the analyzed page."""

    total_requests: int = 0
    total_bytes: int = 0
    html_bytes: int = 0
    css_bytes: int = 0
    js_bytes: int = 0
    image_bytes: int = 0
    font_bytes: int = 0
    third_party_bytes: int = 0
    dom_elements: int = 0


@dataclass
class AnalysisResult:
    """Complete result of a page speed analysis including scores, CWV, issues, and AI insights."""

    url: str
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Scores (0-100)
    mobile_score: Optional[int] = None
    desktop_score: Optional[int] = None
    mobile_accessibility_score: Optional[int] = None
    mobile_seo_score: Optional[int] = None
    mobile_best_practices_score: Optional[int] = None

    # Core Web Vitals assessments
    cwv_assessments: list[CWVAssessment] = field(default_factory=list)

    # Detected issues with fix guidance
    issues: list[SpeedIssue] = field(default_factory=list)

    # CMS / platform detection
    cms_info: CMSInfo = field(default_factory=lambda: CMSInfo("unknown", "low"))

    # Visual artifacts
    final_screenshot: Optional[str] = None  # base64
    filmstrip_frames: list[dict] = field(default_factory=list)

    # Page resource statistics
    page_stats: PageStats = field(default_factory=PageStats)

    # AI-generated content
    executive_summary: str = ""
    implementation_roadmap: list[dict] = field(default_factory=list)

    # Raw PSI API responses (kept for debugging / deeper inspection)
    raw_psi_mobile: Optional[dict] = None
    raw_psi_desktop: Optional[dict] = None

    # -------------------------------------------------------------------------
    # Convenience properties
    # -------------------------------------------------------------------------

    @property
    def critical_issues(self) -> list[SpeedIssue]:
        """Return only critical-severity issues."""
        return [i for i in self.issues if i.severity == Severity.CRITICAL]

    @property
    def important_issues(self) -> list[SpeedIssue]:
        """Return only important-severity issues."""
        return [i for i in self.issues if i.severity == Severity.IMPORTANT]

    @property
    def minor_issues(self) -> list[SpeedIssue]:
        """Return only minor-severity issues."""
        return [i for i in self.issues if i.severity == Severity.MINOR]

    @property
    def sorted_issues(self) -> list[SpeedIssue]:
        """Return all issues sorted by priority score, highest first."""
        return sorted(self.issues, key=lambda i: i.priority_score, reverse=True)

    @property
    def cwv_pass(self) -> bool:
        """Check whether the three core CWV metrics all pass (none are 'poor')."""
        core_metrics = {
            "Largest Contentful Paint",
            "Cumulative Layout Shift",
            "Interaction to Next Paint",
        }
        for assessment in self.cwv_assessments:
            if (
                assessment.metric.value in core_metrics
                and assessment.status.value == "poor"
            ):
                return False
        return True
