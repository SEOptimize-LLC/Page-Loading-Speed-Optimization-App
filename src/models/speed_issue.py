"""Data models for page speed issues, Core Web Vitals, and CMS detection."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(Enum):
    """Issue severity level with associated display properties."""

    CRITICAL = "critical"
    IMPORTANT = "important"
    MINOR = "minor"

    @property
    def color(self) -> str:
        """Hex color associated with this severity level."""
        return {
            "critical": "#dc2626",
            "important": "#f59e0b",
            "minor": "#eab308",
        }[self.value]

    @property
    def label(self) -> str:
        """Human-readable label for display."""
        return self.value.capitalize()

    @property
    def weight(self) -> int:
        """Numeric weight used for priority scoring."""
        return {
            "critical": 3,
            "important": 2,
            "minor": 1,
        }[self.value]


class CWVMetric(Enum):
    """Core Web Vitals and related performance metrics."""

    LCP = "Largest Contentful Paint"
    CLS = "Cumulative Layout Shift"
    INP = "Interaction to Next Paint"
    FCP = "First Contentful Paint"
    SI = "Speed Index"
    TBT = "Total Blocking Time"
    TTFB = "Time to First Byte"


class CWVStatus(Enum):
    """Core Web Vitals assessment status (good / needs improvement / poor)."""

    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs-improvement"
    POOR = "poor"

    @property
    def color(self) -> str:
        """Hex color matching Google's CWV color scheme."""
        return {
            "good": "#0cce6b",
            "needs-improvement": "#ffa400",
            "poor": "#ff4e42",
        }[self.value]


@dataclass
class CWVAssessment:
    """Assessment of a single Core Web Vitals metric with field and lab data."""

    metric: CWVMetric
    field_value: Optional[float] = None
    field_category: Optional[str] = None  # FAST, AVERAGE, SLOW
    lab_value: Optional[float] = None
    lab_display: Optional[str] = None
    status: CWVStatus = CWVStatus.POOR
    threshold_good: float = 0
    threshold_poor: float = 0


@dataclass
class SpeedIssue:
    """A single page speed issue with diagnostic details and fix guidance."""

    issue_id: str
    title: str
    severity: Severity
    cwv_impact: list[CWVMetric] = field(default_factory=list)
    what_is_wrong: str = ""
    why_it_matters: str = ""
    how_to_fix: list[str] = field(default_factory=list)
    cms_specific_fix: Optional[str] = None
    code_example: Optional[str] = None
    estimated_improvement: str = ""
    effort_level: str = "medium"  # low, medium, high
    affected_resources: list[str] = field(default_factory=list)
    screenshot_data: Optional[str] = None  # base64
    screenshot_caption: Optional[str] = None
    savings_ms: float = 0
    savings_bytes: int = 0

    @property
    def priority_score(self) -> float:
        """Computed priority based on severity weight and potential savings."""
        return self.severity.weight * (self.savings_ms + self.savings_bytes / 1000)


@dataclass
class CMSInfo:
    """Detected CMS/platform information and associated plugins or apps."""

    name: str  # "wordpress", "shopify", "unknown"
    confidence: str  # "high", "medium", "low"
    detected_plugins: list[str] = field(default_factory=list)
    detected_apps: list[str] = field(default_factory=list)
    stack_packs: list[str] = field(default_factory=list)
