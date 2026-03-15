"""Generates HTML reports from page speed analysis results."""

import os
import logging
from typing import Optional
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

# Import formatting helpers — fall back to inline functions if unavailable
try:
    from utils.formatting import format_bytes, format_ms, score_color
except ImportError:
    try:
        from ...utils.formatting import format_bytes, format_ms, score_color
    except ImportError:

        def format_bytes(val: int | float) -> str:
            val = float(val)
            if val >= 1_000_000:
                return f"{val / 1_000_000:.1f} MB"
            if val >= 1_000:
                return f"{val / 1_000:.1f} KB"
            return f"{int(val)} B"

        def format_ms(val: int | float) -> str:
            val = float(val)
            if val >= 1_000:
                return f"{val / 1_000:.1f} s"
            return f"{int(round(val))} ms"

        def score_color(score: int | float) -> str:
            score = int(score)
            if score >= 90:
                return "#0cce6b"
            if score >= 50:
                return "#ffa400"
            return "#ff4e42"


class ReportGenerator:
    """Generates HTML reports from AnalysisResult data."""

    def __init__(self) -> None:
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,  # HTML is trusted (AI-generated but sanitised upstream)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        analysis_result,  # AnalysisResult dataclass
        whitelabel: Optional[dict] = None,
    ) -> str:
        """Generate a complete HTML report.

        Args:
            analysis_result: The AnalysisResult from the analysis pipeline.
            whitelabel: Optional dict with keys:
                - company_name (str)
                - company_logo (str, URL or data URI)
                - brand_color (str, hex)
                - contact_email (str)

        Returns:
            Rendered HTML string ready for display or PDF conversion.
        """
        # Load CSS
        css_path = os.path.join(
            os.path.dirname(__file__), "templates", "report_styles.css"
        )
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

        # Apply brand color override
        wl = whitelabel or {}
        brand_color = wl.get("brand_color", "#2563eb")
        if brand_color and brand_color != "#2563eb":
            css_content = css_content.replace("#2563eb", brand_color)
            # Also update the light variant (a simple opacity-based approximation)
            css_content = css_content.replace("#dbeafe", self._lighten_hex(brand_color))

        # Build template context
        context = self._build_context(analysis_result, wl, css_content)

        # Render
        template = self.env.get_template("speed_report.html")
        html = template.render(**context)

        logger.info(
            "Report generated for %s (%d chars)",
            analysis_result.url,
            len(html),
        )
        return html

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def _build_context(
        self,
        result,  # AnalysisResult
        whitelabel: dict,
        css_content: str,
    ) -> dict:
        """Convert an AnalysisResult into a flat dict the Jinja2 template consumes."""

        ctx: dict = {}

        # -- CSS --------------------------------------------------------
        ctx["css_content"] = css_content

        # -- Basic metadata ---------------------------------------------
        ctx["url"] = result.url
        ctx["date"] = self._format_date(result.analyzed_at)

        # -- White-label ------------------------------------------------
        ctx["company_name"] = whitelabel.get("company_name", "Speed Audit")
        ctx["company_logo"] = whitelabel.get("company_logo")
        ctx["brand_color"] = whitelabel.get("brand_color", "#2563eb")
        ctx["contact_email"] = whitelabel.get("contact_email")

        # -- Scores -----------------------------------------------------
        ctx["mobile_score"] = result.mobile_score if result.mobile_score is not None else 0
        ctx["desktop_score"] = result.desktop_score if result.desktop_score is not None else 0
        ctx["accessibility_score"] = result.mobile_accessibility_score
        ctx["seo_score"] = result.mobile_seo_score
        ctx["best_practices_score"] = result.mobile_best_practices_score

        # -- CWV pass/fail ----------------------------------------------
        ctx["cwv_pass"] = result.cwv_pass

        # -- CWV assessments --------------------------------------------
        ctx["cwv_assessments"] = self._format_cwv_assessments(result.cwv_assessments)

        # -- Issues grouped by severity ---------------------------------
        ctx["critical_issues"] = [
            self._format_issue(i) for i in result.critical_issues
        ]
        ctx["important_issues"] = [
            self._format_issue(i) for i in result.important_issues
        ]
        ctx["minor_issues"] = [
            self._format_issue(i) for i in result.minor_issues
        ]

        # -- AI content -------------------------------------------------
        ctx["executive_summary"] = result.executive_summary or ""
        ctx["top_actions"] = self._extract_top_actions(result)

        # -- CMS info ---------------------------------------------------
        ctx["cms_name"] = result.cms_info.name if result.cms_info else "unknown"
        ctx["cms_recommendations"] = self._build_cms_recommendations(result)

        # -- Roadmap ----------------------------------------------------
        ctx["roadmap"] = self._format_roadmap(result.implementation_roadmap)

        # -- Page statistics --------------------------------------------
        ctx["page_stats"] = self._format_page_stats(result.page_stats)

        # -- Visual artifacts -------------------------------------------
        ctx["final_screenshot"] = result.final_screenshot or ""
        ctx["filmstrip_frames"] = self._format_filmstrip(result.filmstrip_frames)

        return ctx

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    def _format_cwv_assessments(self, assessments: list) -> list[dict]:
        """Convert CWVAssessment dataclass instances to template-friendly dicts."""
        formatted: list[dict] = []
        for a in assessments:
            status_str = a.status.value if hasattr(a.status, "value") else str(a.status)
            status_color = a.status.color if hasattr(a.status, "color") else "#ff4e42"
            metric_name = a.metric.value if hasattr(a.metric, "value") else str(a.metric)

            lab_value = a.lab_value
            lab_display = a.lab_display or self._format_metric_value(metric_name, lab_value)

            field_value = a.field_value
            field_display = None
            if field_value is not None:
                field_display = self._format_metric_value(metric_name, field_value)

            formatted.append(
                {
                    "metric_name": metric_name,
                    "lab_value": lab_value,
                    "lab_display": lab_display,
                    "field_value": field_display,
                    "field_category": a.field_category,
                    "status": status_str,
                    "status_color": status_color,
                    "threshold_good": a.threshold_good,
                    "threshold_poor": a.threshold_poor,
                }
            )
        return formatted

    def _format_issue(self, issue) -> dict:
        """Convert a SpeedIssue dataclass to a template-friendly dict."""
        cwv_impact_labels = []
        for metric in issue.cwv_impact:
            if hasattr(metric, "name"):
                cwv_impact_labels.append(metric.name)  # e.g. "LCP"
            elif hasattr(metric, "value"):
                # Use the short form if available
                cwv_impact_labels.append(self._metric_short_name(metric.value))
            else:
                cwv_impact_labels.append(str(metric))

        return {
            "issue_id": issue.issue_id,
            "title": issue.title,
            "severity": issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity),
            "cwv_impact": cwv_impact_labels,
            "what_is_wrong": issue.what_is_wrong,
            "why_it_matters": issue.why_it_matters,
            "how_to_fix": issue.how_to_fix or [],
            "cms_specific_fix": issue.cms_specific_fix,
            "code_example": issue.code_example,
            "estimated_improvement": issue.estimated_improvement,
            "effort_level": issue.effort_level or "medium",
            "affected_resources": issue.affected_resources or [],
            "screenshot_data": issue.screenshot_data,
            "screenshot_caption": issue.screenshot_caption,
            "savings_ms": issue.savings_ms,
            "savings_bytes": issue.savings_bytes,
        }

    def _format_roadmap(self, roadmap_items: list[dict]) -> list[dict]:
        """Normalise roadmap items so the template gets consistent keys."""
        formatted: list[dict] = []
        for idx, item in enumerate(roadmap_items):
            formatted.append(
                {
                    "priority": item.get("priority", idx + 1),
                    "title": item.get("title", "Untitled"),
                    "description": item.get("description", ""),
                    "effort": item.get("effort", "medium"),
                    "impact": item.get("impact", "medium"),
                }
            )
        return formatted

    def _format_page_stats(self, stats) -> dict:
        """Convert a PageStats dataclass into a dict with human-readable display values."""
        total_bytes = stats.total_bytes if stats else 0
        html_bytes = stats.html_bytes if stats else 0
        css_bytes = stats.css_bytes if stats else 0
        js_bytes = stats.js_bytes if stats else 0
        image_bytes = stats.image_bytes if stats else 0
        font_bytes = stats.font_bytes if stats else 0
        other_bytes = max(
            0,
            total_bytes - html_bytes - css_bytes - js_bytes - image_bytes - font_bytes,
        )

        return {
            "total_requests": stats.total_requests if stats else 0,
            "total_bytes": total_bytes,
            "total_bytes_display": format_bytes(total_bytes),
            "html_bytes": html_bytes,
            "html_bytes_display": format_bytes(html_bytes),
            "css_bytes": css_bytes,
            "css_bytes_display": format_bytes(css_bytes),
            "js_bytes": js_bytes,
            "js_bytes_display": format_bytes(js_bytes),
            "image_bytes": image_bytes,
            "image_bytes_display": format_bytes(image_bytes),
            "font_bytes": font_bytes,
            "font_bytes_display": format_bytes(font_bytes),
            "other_bytes": other_bytes,
            "other_bytes_display": format_bytes(other_bytes),
            "dom_elements": stats.dom_elements if stats else 0,
        }

    def _format_filmstrip(self, frames: list[dict]) -> list[dict]:
        """Normalise filmstrip frame dicts for the template."""
        formatted: list[dict] = []
        for frame in frames:
            timing = frame.get("timing_ms") or frame.get("timing") or 0
            data_uri = frame.get("data_uri") or frame.get("data") or ""
            formatted.append(
                {
                    "timing_ms": int(timing),
                    "data_uri": data_uri,
                }
            )
        return formatted

    def _extract_top_actions(self, result) -> list[str]:
        """Extract the top 3 most impactful actions from sorted issues."""
        actions: list[str] = []
        for issue in result.sorted_issues[:3]:
            actions.append(issue.title)
        return actions

    def _build_cms_recommendations(self, result) -> str:
        """Return any AI-generated CMS-specific recommendations.

        The template has built-in defaults for WordPress and Shopify,
        so this only returns non-empty when the AI pipeline has produced
        bespoke guidance.
        """
        # Check if the AI pipeline attached CMS recommendations
        # (they may be stored as a string in the roadmap or as a
        # separate attribute in future versions)
        for item in result.implementation_roadmap:
            if item.get("cms_recommendations"):
                return item["cms_recommendations"]
        return ""

    def _format_metric_value(self, metric_name: str, value) -> str:
        """Format a raw CWV metric value for display."""
        if value is None:
            return "N/A"

        name_lower = metric_name.lower()

        # CLS is a unitless score, typically 0.xxx
        if "layout shift" in name_lower or "cls" in name_lower:
            return f"{float(value):.3f}"

        # Millisecond-based metrics
        return format_ms(float(value))

    @staticmethod
    def _metric_short_name(metric_full_name: str) -> str:
        """Map a full CWV metric name to its common abbreviation."""
        mapping = {
            "Largest Contentful Paint": "LCP",
            "Cumulative Layout Shift": "CLS",
            "Interaction to Next Paint": "INP",
            "First Contentful Paint": "FCP",
            "Speed Index": "SI",
            "Total Blocking Time": "TBT",
            "Time to First Byte": "TTFB",
        }
        return mapping.get(metric_full_name, metric_full_name)

    @staticmethod
    def _format_date(iso_str: str) -> str:
        """Convert an ISO date string to a human-friendly format."""
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime("%B %d, %Y at %H:%M")
        except (ValueError, TypeError):
            return str(iso_str) if iso_str else "N/A"

    @staticmethod
    def _lighten_hex(hex_color: str) -> str:
        """Create a lighter version of a hex color for backgrounds.

        Blends the colour 85% toward white, similar to Tailwind's -100 shade.
        """
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return "#dbeafe"  # fallback
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            factor = 0.85
            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)
            return f"#{r:02x}{g:02x}{b:02x}"
        except ValueError:
            return "#dbeafe"
