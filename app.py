"""Page Speed Optimization Agent - Streamlit Application.

This is the main entry point that wires together all modules:
- PageSpeed Insights API collection
- HTML analysis
- CMS detection
- Issue classification
- Screenshot processing
- Resource analysis
- AI-powered recommendations via OpenRouter
- Report generation (HTML + PDF)
"""

import streamlit as st
import os
import sys
import json
import logging
import time
import base64
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so that ``src`` and ``utils`` resolve
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit command)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Page Speed Optimization Agent",
    page_icon="\u26a1",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Imports - modules built in previous phases
# ---------------------------------------------------------------------------
from src.models.speed_issue import (
    Severity,
    CWVMetric,
    CWVStatus,
    CWVAssessment,
    SpeedIssue,
    CMSInfo,
)
from src.models.analysis_result import AnalysisResult, PageStats
from src.collectors.pagespeed_client import PageSpeedClient, PSIResult
from src.collectors.html_analyzer import HTMLAnalyzer, HTMLAnalysis
from src.collectors.screenshot_processor import ScreenshotProcessor
from src.analyzers.cms_detector import CMSDetector
from src.analyzers.issue_classifier import IssueClassifier, CWV_THRESHOLDS
from src.analyzers.resource_analyzer import ResourceAnalyzer
from src.ai.openrouter_client import OpenRouterClient, create_client_from_streamlit
from src.ai.knowledge_base import KnowledgeBase
from src.ai.prompt_builder import PromptBuilder
from src.reports.report_generator import ReportGenerator
from src.reports.pdf_converter import PDFConverter
from utils.url_utils import validate_url, normalize_url
from utils.formatting import format_bytes, format_ms, score_color

# ---------------------------------------------------------------------------
# Model options for the sidebar dropdown
# ---------------------------------------------------------------------------
MODEL_OPTIONS = {
    "Gemini 2.0 Flash (fast, default)": "google/gemini-2.0-flash-001",
    "Claude Sonnet 4.5 (best reasoning)": "anthropic/claude-sonnet-4-5-20250514",
    "GPT-4.1 Mini (balanced)": "openai/gpt-4.1-mini",
}

# =========================================================================
# Helper functions
# =========================================================================


def get_secret(key: str, default: str = "") -> str:
    """Retrieve a secret from Streamlit secrets with .env fallback."""
    try:
        val = st.secrets[key]
        if val:
            return str(val)
    except (KeyError, FileNotFoundError, TypeError):
        pass
    return os.getenv(key, default)


def init_session_state() -> None:
    """Initialise Streamlit session-state keys with safe defaults."""
    defaults = {
        "analysis_result": None,
        "report_html": None,
        "report_pdf": None,
        "analysis_running": False,
        "progress": 0,
        "progress_message": "",
        "error_message": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# =========================================================================
# CWV Assessment Builder
# =========================================================================


def _cwv_status_from_value(value: float, metric_name: str) -> CWVStatus:
    """Determine CWV status (good / needs-improvement / poor) for a value."""
    thresholds = CWV_THRESHOLDS.get(metric_name)
    if thresholds is None or value is None:
        return CWVStatus.POOR
    if value <= thresholds["good"]:
        return CWVStatus.GOOD
    if value < thresholds["poor"]:
        return CWVStatus.NEEDS_IMPROVEMENT
    return CWVStatus.POOR


def build_cwv_assessments(psi_mobile: PSIResult) -> list[CWVAssessment]:
    """Build CWVAssessment objects from combined field + lab data."""
    assessments: list[CWVAssessment] = []

    # Mapping: (CWVMetric enum, lab_metrics key for ms value, lab display key,
    #           field_data short key, threshold dict key)
    metric_defs = [
        (CWVMetric.LCP, "lcp_ms", "lcp_display", "lcp", "LCP"),
        (CWVMetric.CLS, "cls", "cls_display", "cls", "CLS"),
        (CWVMetric.INP, None, None, "inp", "INP"),  # INP is field-only; lab proxy is TBT
        (CWVMetric.TBT, "tbt_ms", "tbt_display", None, "TBT"),
        (CWVMetric.FCP, "fcp_ms", "fcp_display", "fcp", "FCP"),
        (CWVMetric.SI, "speed_index_ms", "si_display", None, "SI"),
        (CWVMetric.TTFB, None, None, "ttfb", "TTFB"),
    ]

    field_data = psi_mobile.field_data or {}
    lab = psi_mobile.lab_metrics or {}

    for cwv_metric, lab_key, lab_disp_key, field_key, thresh_key in metric_defs:
        # --- Lab values ---
        lab_value = lab.get(lab_key) if lab_key else None
        lab_display = lab.get(lab_disp_key) if lab_disp_key else None

        # --- Field values ---
        field_value = None
        field_category = None
        if field_key and field_key in field_data:
            fd = field_data[field_key]
            field_value = fd.get("value")
            field_category = fd.get("category")  # FAST, AVERAGE, SLOW

        # --- Determine status (prefer field data, fall back to lab) ---
        primary_value = field_value if field_value is not None else lab_value
        if primary_value is not None:
            status = _cwv_status_from_value(primary_value, thresh_key)
        elif field_category:
            # Map CrUX categories to status
            cat_map = {
                "FAST": CWVStatus.GOOD,
                "AVERAGE": CWVStatus.NEEDS_IMPROVEMENT,
                "SLOW": CWVStatus.POOR,
            }
            status = cat_map.get(field_category, CWVStatus.POOR)
        else:
            status = CWVStatus.POOR

        thresholds = CWV_THRESHOLDS.get(thresh_key, {})

        assessments.append(
            CWVAssessment(
                metric=cwv_metric,
                field_value=field_value,
                field_category=field_category,
                lab_value=lab_value,
                lab_display=lab_display,
                status=status,
                threshold_good=thresholds.get("good", 0),
                threshold_poor=thresholds.get("poor", 0),
            )
        )

    return assessments


# =========================================================================
# Issue conversion helpers
# =========================================================================


def _severity_from_str(s: str) -> Severity:
    """Convert a severity string to the Severity enum."""
    mapping = {
        "critical": Severity.CRITICAL,
        "important": Severity.IMPORTANT,
        "minor": Severity.MINOR,
    }
    return mapping.get(s.lower(), Severity.MINOR)


def _cwv_metrics_from_strings(names: list[str]) -> list[CWVMetric]:
    """Convert a list of CWV metric name strings to CWVMetric enums."""
    mapping = {
        "LCP": CWVMetric.LCP,
        "CLS": CWVMetric.CLS,
        "INP": CWVMetric.INP,
        "FCP": CWVMetric.FCP,
        "SI": CWVMetric.SI,
        "TBT": CWVMetric.TBT,
        "TTFB": CWVMetric.TTFB,
    }
    result = []
    for name in names:
        metric = mapping.get(name.upper())
        if metric:
            result.append(metric)
    return result


def dict_to_speed_issue(d: dict) -> SpeedIssue:
    """Convert a classified issue dict into a SpeedIssue dataclass."""
    return SpeedIssue(
        issue_id=d.get("issue_id", "unknown"),
        title=d.get("title", "Untitled Issue"),
        severity=_severity_from_str(d.get("severity", "minor")),
        cwv_impact=_cwv_metrics_from_strings(d.get("cwv_impact", [])),
        what_is_wrong=d.get("what_is_wrong", ""),
        why_it_matters=d.get("why_it_matters", ""),
        how_to_fix=d.get("how_to_fix", []),
        cms_specific_fix=d.get("cms_specific_fix"),
        code_example=d.get("code_example"),
        estimated_improvement=d.get("estimated_improvement", ""),
        effort_level=d.get("effort_level", "medium"),
        affected_resources=d.get("affected_resources", [])[:20],
        screenshot_data=d.get("screenshot_data"),
        screenshot_caption=d.get("screenshot_caption"),
        savings_ms=float(d.get("savings_ms", 0) or 0),
        savings_bytes=int(d.get("savings_bytes", 0) or 0),
    )


# =========================================================================
# Page Stats builder
# =========================================================================


def build_page_stats(
    psi_page_stats: dict,
    resource_data: dict,
) -> PageStats:
    """Build a PageStats object from PSI page stats and resource breakdown."""
    breakdown = resource_data.get("resource_breakdown", {})
    return PageStats(
        total_requests=resource_data.get("total_requests", 0)
        or psi_page_stats.get("numRequests", 0)
        or 0,
        total_bytes=resource_data.get("total_transfer_size", 0)
        or psi_page_stats.get("totalByteWeight", 0)
        or 0,
        html_bytes=breakdown.get("documents", 0),
        css_bytes=breakdown.get("stylesheets", 0),
        js_bytes=breakdown.get("scripts", 0),
        image_bytes=breakdown.get("images", 0),
        font_bytes=breakdown.get("fonts", 0),
        third_party_bytes=sum(
            tp.get("transfer_size", 0)
            for tp in resource_data.get("third_party_impact", [])
        ),
        dom_elements=psi_page_stats.get("numRequests", 0) or 0,
    )


# =========================================================================
# Screenshot cropping for issues
# =========================================================================


def attach_screenshots_to_issues(
    merged_issues: list[dict],
    screenshot_proc: ScreenshotProcessor,
    lcp_element: dict | None,
    cls_elements: list[dict],
) -> None:
    """Try to crop and attach screenshots to issues that have element data.

    Modifies ``merged_issues`` in place by setting ``screenshot_data`` and
    ``screenshot_caption`` on matching dicts.
    """
    if screenshot_proc.full_page_image is None:
        return

    # Build a lookup of lhId -> issue for LCP / CLS related issues
    lcp_lh_id = (lcp_element or {}).get("lhId")
    cls_lh_ids: dict[str, dict] = {}
    for el in cls_elements:
        lh_id = el.get("lhId")
        if lh_id:
            cls_lh_ids[lh_id] = el

    for issue in merged_issues:
        issue_id = issue.get("issue_id", "")
        severity_str = issue.get("severity", "minor")

        # --- LCP element screenshot ---
        if issue_id in (
            "largest-contentful-paint-element",
            "preload-lcp-image",
            "lcp-lazy-loaded",
            "prioritize-lcp-image",
        ):
            if lcp_lh_id:
                cropped = screenshot_proc.crop_element(lcp_lh_id, severity=severity_str)
                if cropped:
                    issue["screenshot_data"] = cropped
                    issue["screenshot_caption"] = "LCP element highlighted"
                    continue
            # Try bounding rect from lcp_element directly
            rect = (lcp_element or {}).get("boundingRect")
            if rect:
                cropped = screenshot_proc.crop_by_rect(rect, severity=severity_str)
                if cropped:
                    issue["screenshot_data"] = cropped
                    issue["screenshot_caption"] = "LCP element highlighted"
                    continue

        # --- CLS element screenshots ---
        if issue_id in ("layout-shift-elements", "unsized-images"):
            for cls_lh_id, cls_el in cls_lh_ids.items():
                cropped = screenshot_proc.crop_element(cls_lh_id, severity=severity_str)
                if cropped:
                    issue["screenshot_data"] = cropped
                    issue["screenshot_caption"] = "CLS-contributing element"
                    break  # attach the first successful crop
            continue

        # --- Try to match any issue item that has a node with lhId ---
        items = issue.get("items", [])
        for item in items[:5]:  # limit to first 5 items
            element = item.get("element") or item.get("node") or {}
            lh_id = element.get("lhId")
            if lh_id:
                cropped = screenshot_proc.crop_element(lh_id, severity=severity_str)
                if cropped:
                    issue["screenshot_data"] = cropped
                    node_label = element.get("nodeLabel", "element")
                    issue["screenshot_caption"] = f"Affected element: {node_label}"
                    break


# =========================================================================
# AI recommendation merging
# =========================================================================


def merge_ai_recommendations(
    merged_issues: list[dict],
    ai_issues: list[dict],
) -> None:
    """Match AI recommendations to existing issues by issue_id and enhance them.

    Modifies ``merged_issues`` in place.
    """
    # Index AI recs by issue_id
    ai_by_id: dict[str, dict] = {}
    for ai_rec in ai_issues:
        aid = ai_rec.get("issue_id", "")
        if aid:
            ai_by_id[aid] = ai_rec

    for issue in merged_issues:
        issue_id = issue.get("issue_id", "")
        ai_rec = ai_by_id.get(issue_id)
        if ai_rec is None:
            continue

        # Enhance the existing issue with AI-generated fields
        if ai_rec.get("what_is_wrong"):
            issue["what_is_wrong"] = ai_rec["what_is_wrong"]
        if ai_rec.get("why_it_matters"):
            issue["why_it_matters"] = ai_rec["why_it_matters"]
        if ai_rec.get("how_to_fix"):
            issue["how_to_fix"] = ai_rec["how_to_fix"]
        if ai_rec.get("cms_specific_fix"):
            issue["cms_specific_fix"] = ai_rec["cms_specific_fix"]
        if ai_rec.get("code_example"):
            issue["code_example"] = ai_rec["code_example"]
        if ai_rec.get("estimated_improvement"):
            issue["estimated_improvement"] = ai_rec["estimated_improvement"]
        if ai_rec.get("effort_level"):
            issue["effort_level"] = ai_rec["effort_level"]
        # AI may provide a better title
        if ai_rec.get("title"):
            issue["title"] = ai_rec["title"]
        # AI may override severity
        if ai_rec.get("severity"):
            issue["severity"] = ai_rec["severity"]
        # Merge any extra affected_resources from AI
        ai_resources = ai_rec.get("affected_resources", [])
        existing = set(issue.get("affected_resources", []))
        for res in ai_resources:
            if res not in existing:
                issue.setdefault("affected_resources", []).append(res)
                existing.add(res)

    # Add any AI issues that don't match an existing issue
    existing_ids = {issue.get("issue_id") for issue in merged_issues}
    for ai_rec in ai_issues:
        aid = ai_rec.get("issue_id", "")
        if aid and aid not in existing_ids:
            # This is a new issue identified by the AI
            merged_issues.append({
                "issue_id": aid,
                "title": ai_rec.get("title", aid),
                "severity": ai_rec.get("severity", "minor"),
                "cwv_impact": ai_rec.get("cwv_impact", []),
                "savings_ms": 0.0,
                "savings_bytes": 0,
                "affected_resources": ai_rec.get("affected_resources", []),
                "display_value": "",
                "items": [],
                "priority_score": 100.0,
                "source": "ai_analysis",
                "what_is_wrong": ai_rec.get("what_is_wrong", ""),
                "why_it_matters": ai_rec.get("why_it_matters", ""),
                "how_to_fix": ai_rec.get("how_to_fix", []),
                "cms_specific_fix": ai_rec.get("cms_specific_fix"),
                "code_example": ai_rec.get("code_example"),
                "estimated_improvement": ai_rec.get("estimated_improvement", ""),
                "effort_level": ai_rec.get("effort_level", "medium"),
            })


# =========================================================================
# Main analysis pipeline
# =========================================================================


def run_analysis(
    url: str,
    model: str,
    progress_bar,
    status_text,
) -> tuple[AnalysisResult, str, bytes | None]:
    """Run the complete analysis pipeline.

    Args:
        url: Normalized URL to analyze.
        model: OpenRouter model identifier.
        progress_bar: Streamlit progress bar widget.
        status_text: Streamlit empty placeholder for status messages.

    Returns:
        Tuple of (AnalysisResult, report_html, pdf_bytes_or_None).

    Raises:
        Exception: If a critical step fails (PSI mobile is required).
    """
    result = AnalysisResult(url=url)
    psi_desktop: PSIResult | None = None

    # ------------------------------------------------------------------
    # Step 1: PSI Mobile (required)
    # ------------------------------------------------------------------
    status_text.text("Running PageSpeed Insights (mobile)...")
    progress_bar.progress(10)

    psi_api_key = get_secret("PAGESPEED_API_KEY")
    if not psi_api_key:
        raise ValueError(
            "PageSpeed API key is missing. Add PAGESPEED_API_KEY to your "
            ".env file or Streamlit secrets."
        )

    psi_client = PageSpeedClient(psi_api_key)
    psi_mobile = psi_client.analyze(url, strategy="mobile")
    progress_bar.progress(35)

    # ------------------------------------------------------------------
    # Step 2: PSI Desktop (optional -- continue if it fails)
    # ------------------------------------------------------------------
    status_text.text("Running PageSpeed Insights (desktop)...")
    try:
        psi_desktop = psi_client.analyze(url, strategy="desktop")
    except Exception as e:
        logger.warning("Desktop PSI analysis failed; continuing with mobile only: %s", e)
        psi_desktop = None
    progress_bar.progress(50)

    # ------------------------------------------------------------------
    # Step 3: HTML Analysis
    # ------------------------------------------------------------------
    status_text.text("Analyzing page HTML...")
    html_analyzer = HTMLAnalyzer()
    try:
        html_result = html_analyzer.analyze(url)
    except Exception as e:
        logger.warning("HTML analysis failed: %s", e)
        html_result = HTMLAnalysis(url=url)
    progress_bar.progress(60)

    # ------------------------------------------------------------------
    # Step 4: CMS Detection
    # ------------------------------------------------------------------
    status_text.text("Detecting CMS and technology stack...")
    cms_detector = CMSDetector()
    try:
        cms_data = cms_detector.detect(
            stack_packs=psi_mobile.stack_packs,
            network_requests=psi_mobile.network_requests,
            entities=psi_mobile.entities,
            html_cms=html_result.detected_cms,
            html_cms_signals=html_result.cms_signals,
        )
        result.cms_info = CMSInfo(**cms_data)
    except Exception as e:
        logger.warning("CMS detection failed: %s", e)
        result.cms_info = CMSInfo(name="unknown", confidence="low")
    progress_bar.progress(62)

    # ------------------------------------------------------------------
    # Step 5: Issue Classification
    # ------------------------------------------------------------------
    status_text.text("Classifying performance issues...")
    classifier = IssueClassifier()

    psi_issues = classifier.classify_opportunities(
        psi_mobile.opportunities, psi_mobile.lab_metrics
    )
    psi_issues += classifier.classify_diagnostics(
        psi_mobile.diagnostics, psi_mobile.lab_metrics
    )

    # Convert HTMLFinding objects to the dict format expected by the classifier
    html_finding_dicts = [
        {
            "id": f.finding_id,
            "title": f.description,
            "affected_resources": [
                el.get("snippet", "") for el in f.elements
            ],
            "details": f.description,
            "count": f.count,
        }
        for f in html_result.findings
    ]
    html_issues = classifier.classify_html_findings(html_finding_dicts)

    merged_issues = classifier.merge_and_deduplicate(psi_issues, html_issues)
    progress_bar.progress(65)

    # ------------------------------------------------------------------
    # Step 6: Screenshot Processing
    # ------------------------------------------------------------------
    status_text.text("Processing screenshots...")
    screenshot_proc = ScreenshotProcessor(
        psi_mobile.full_page_screenshot,
        psi_mobile.screenshot_nodes,
    )

    attach_screenshots_to_issues(
        merged_issues,
        screenshot_proc,
        psi_mobile.lcp_element,
        psi_mobile.cls_elements,
    )

    filmstrip = screenshot_proc.get_filmstrip(psi_mobile.filmstrip_frames)
    progress_bar.progress(68)

    # ------------------------------------------------------------------
    # Step 7: Resource Analysis
    # ------------------------------------------------------------------
    status_text.text("Analyzing resources...")
    resource_analyzer = ResourceAnalyzer()
    try:
        resource_data = resource_analyzer.analyze(
            psi_mobile.network_requests,
            psi_mobile.resource_summary,
            psi_mobile.third_party_summary,
            url,
        )
    except Exception as e:
        logger.warning("Resource analysis failed: %s", e)
        resource_data = {
            "largest_resources": [],
            "resource_breakdown": {},
            "third_party_impact": [],
            "total_requests": 0,
            "total_transfer_size": 0,
        }
    progress_bar.progress(70)

    # ------------------------------------------------------------------
    # Step 8: AI Recommendations (optional -- skip if no key)
    # ------------------------------------------------------------------
    ai_client = create_client_from_streamlit(default_model=model)

    if ai_client:
        try:
            status_text.text("Generating AI-powered recommendations...")
            kb = KnowledgeBase()

            audit_ids = [i.get("issue_id", "") for i in merged_issues]
            kb_context = kb.get_relevant_context(audit_ids, result.cms_info.name)

            # Build prompt data dicts for PromptBuilder
            html_findings_for_prompt = [
                {
                    "finding_id": f.finding_id,
                    "category": f.category,
                    "description": f.description,
                    "elements": f.elements,
                    "count": f.count,
                }
                for f in html_result.findings
            ]

            scores_dict = {
                "performance": psi_mobile.performance_score,
                "accessibility": psi_mobile.accessibility_score,
                "best_practices": psi_mobile.best_practices_score,
                "seo": psi_mobile.seo_score,
                "mobile": psi_mobile.performance_score,
                "desktop": psi_desktop.performance_score if psi_desktop else None,
            }

            psi_data_for_prompt = {
                "scores": scores_dict,
                "metrics": psi_mobile.lab_metrics,
                "opportunities": psi_mobile.opportunities,
                "diagnostics": psi_mobile.diagnostics,
                "lcp_element": psi_mobile.lcp_element,
                "cls_elements": psi_mobile.cls_elements,
                "page_stats": psi_mobile.page_stats,
            }

            system_prompt, user_content = PromptBuilder.build_issue_analysis_prompt(
                kb_context=kb_context,
                cms_type=result.cms_info.name,
                psi_data=psi_data_for_prompt,
                html_findings=html_findings_for_prompt,
            )

            ai_response, _llm_resp = ai_client.analyze_json(
                system_prompt=system_prompt,
                user_content=user_content,
                model=model,
            )
            progress_bar.progress(82)

            # Merge AI recommendations into existing issues
            if ai_response and isinstance(ai_response, list):
                merge_ai_recommendations(merged_issues, ai_response)

        except Exception as e:
            logger.warning("AI issue analysis failed: %s", e)
        progress_bar.progress(85)

        # --- Executive summary ---
        try:
            status_text.text("Writing executive summary...")

            cwv_data_for_summary: list[dict] = []
            cwv_assessments_temp = build_cwv_assessments(psi_mobile)
            for a in cwv_assessments_temp:
                value_display = a.lab_display or ""
                if not value_display and a.lab_value is not None:
                    value_display = str(a.lab_value)
                if a.field_value is not None:
                    value_display = str(a.field_value)

                cwv_data_for_summary.append({
                    "name": a.metric.name,
                    "value": value_display,
                    "rating": a.status.value,
                })

            issue_counts = {
                "critical": sum(
                    1 for i in merged_issues if i.get("severity") == "critical"
                ),
                "important": sum(
                    1 for i in merged_issues if i.get("severity") == "important"
                ),
                "minor": sum(
                    1 for i in merged_issues if i.get("severity") == "minor"
                ),
            }

            top_issues_for_summary = merged_issues[:5]

            summary_system, summary_user = PromptBuilder.build_executive_summary_prompt(
                scores=scores_dict,
                cwv_data=cwv_data_for_summary,
                issue_counts=issue_counts,
                top_issues=top_issues_for_summary,
                cms_type=result.cms_info.name,
            )

            summary_json, _llm_resp2 = ai_client.analyze_json(
                system_prompt=summary_system,
                user_content=summary_user,
                model=model,
            )

            if summary_json and isinstance(summary_json, dict):
                result.executive_summary = summary_json.get("summary", "")
                result.implementation_roadmap = summary_json.get("roadmap", [])
                # Store top_actions as part of roadmap metadata
                top_actions = summary_json.get("top_actions", [])
                if top_actions and not result.implementation_roadmap:
                    result.implementation_roadmap = [
                        {"priority": "quick-win", "title": action, "description": action}
                        for action in top_actions
                    ]

        except Exception as e:
            logger.warning("Executive summary generation failed: %s", e)

        progress_bar.progress(90)
    else:
        logger.info("No OpenRouter API key; skipping AI analysis.")
        progress_bar.progress(90)

    # ------------------------------------------------------------------
    # Step 9: Populate scores, CWV, and convert issues
    # ------------------------------------------------------------------
    status_text.text("Assembling results...")

    # Scores
    result.mobile_score = psi_mobile.performance_score
    result.desktop_score = psi_desktop.performance_score if psi_desktop else None
    result.mobile_accessibility_score = psi_mobile.accessibility_score
    result.mobile_seo_score = psi_mobile.seo_score
    result.mobile_best_practices_score = psi_mobile.best_practices_score

    # CWV Assessments
    result.cwv_assessments = build_cwv_assessments(psi_mobile)

    # Convert merged issue dicts to SpeedIssue dataclass instances
    result.issues = [dict_to_speed_issue(d) for d in merged_issues]

    # Visual artifacts
    result.final_screenshot = psi_mobile.final_screenshot
    result.filmstrip_frames = filmstrip

    # Page stats
    result.page_stats = build_page_stats(
        psi_mobile.page_stats or {},
        resource_data,
    )

    # Raw PSI responses (for debugging)
    result.raw_psi_mobile = psi_mobile.raw_response
    result.raw_psi_desktop = psi_desktop.raw_response if psi_desktop else None

    # ------------------------------------------------------------------
    # Step 10: Generate Report
    # ------------------------------------------------------------------
    status_text.text("Generating report...")
    whitelabel = {
        "company_name": st.session_state.get("company_name", "Speed Audit"),
        "company_logo": st.session_state.get("company_logo", ""),
        "brand_color": st.session_state.get("brand_color", "#2563eb"),
    }
    report_gen = ReportGenerator()
    report_html = report_gen.generate(result, whitelabel)
    progress_bar.progress(95)

    # PDF conversion (optional)
    pdf_bytes: bytes | None = None
    if PDFConverter.is_available():
        status_text.text("Converting to PDF...")
        pdf_bytes = PDFConverter.convert(report_html)

    progress_bar.progress(100)
    status_text.text("Analysis complete!")
    time.sleep(0.5)

    return result, report_html, pdf_bytes


# =========================================================================
# UI Rendering helpers
# =========================================================================


def render_cwv_card(assessment: CWVAssessment) -> None:
    """Render a single Core Web Vital metric card inside a Streamlit column."""
    metric_name = assessment.metric.value
    short_name = assessment.metric.name  # e.g. "LCP"
    status_color = assessment.status.color
    status_label = assessment.status.value.replace("-", " ").title()

    # Determine display value
    if assessment.field_value is not None:
        if "Layout Shift" in metric_name:
            display_val = f"{assessment.field_value:.3f}"
        else:
            display_val = format_ms(assessment.field_value)
        source = "Field"
    elif assessment.lab_display:
        display_val = assessment.lab_display
        source = "Lab"
    elif assessment.lab_value is not None:
        if "Layout Shift" in metric_name:
            display_val = f"{assessment.lab_value:.3f}"
        else:
            display_val = format_ms(assessment.lab_value)
        source = "Lab"
    else:
        display_val = "N/A"
        source = ""

    st.markdown(
        f"""<div style="
            border-left: 4px solid {status_color};
            padding: 8px 12px;
            margin-bottom: 8px;
            border-radius: 4px;
            background: rgba(0,0,0,0.02);
        ">
            <div style="font-weight: 600; font-size: 0.85rem; color: #555;">{short_name}</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: {status_color};">{display_val}</div>
            <div style="font-size: 0.75rem; color: #888;">{metric_name} ({source})</div>
            <div style="font-size: 0.7rem; color: {status_color}; font-weight: 600;">{status_label}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_issue_detail(issue: SpeedIssue) -> None:
    """Render the expanded detail of a single issue inside an expander."""
    # CWV impact badges
    if issue.cwv_impact:
        badges = " ".join(
            f"`{m.name}`" for m in issue.cwv_impact
        )
        st.markdown(f"**Affects:** {badges}")

    if issue.what_is_wrong:
        st.markdown(f"**What is wrong:** {issue.what_is_wrong}")

    if issue.why_it_matters:
        st.markdown(f"**Why it matters:** {issue.why_it_matters}")

    if issue.how_to_fix:
        st.markdown("**How to fix:**")
        for idx, step in enumerate(issue.how_to_fix, 1):
            st.markdown(f"{idx}. {step}")

    if issue.cms_specific_fix:
        st.markdown(f"**CMS-specific fix:** {issue.cms_specific_fix}")

    if issue.code_example:
        st.code(issue.code_example, language="html")

    if issue.estimated_improvement:
        st.markdown(f"**Estimated improvement:** {issue.estimated_improvement}")

    col_a, col_b = st.columns(2)
    with col_a:
        if issue.savings_ms > 0:
            st.markdown(f"**Time savings:** {format_ms(issue.savings_ms)}")
    with col_b:
        if issue.savings_bytes > 0:
            st.markdown(f"**Size savings:** {format_bytes(issue.savings_bytes)}")

    if issue.effort_level:
        effort_colors = {"low": "green", "medium": "orange", "high": "red"}
        color = effort_colors.get(issue.effort_level, "gray")
        st.markdown(
            f"**Effort:** :{color}[{issue.effort_level.capitalize()}]"
        )

    if issue.affected_resources:
        with st.expander("Affected resources", expanded=False):
            for res in issue.affected_resources[:15]:
                st.text(res[:200])

    if issue.screenshot_data:
        st.image(issue.screenshot_data, caption=issue.screenshot_caption or "")


# =========================================================================
# Main application
# =========================================================================


def main() -> None:
    """Main Streamlit application entry point."""
    init_session_state()

    # =====================================================================
    # SIDEBAR
    # =====================================================================
    with st.sidebar:
        st.title("\u26a1 Speed Agent")
        st.caption("Page Loading Speed Optimization")

        st.divider()

        # --- API Status indicators ---
        st.subheader("API Status")

        psi_key = get_secret("PAGESPEED_API_KEY")
        or_key = get_secret("OPENROUTER_API_KEY")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if psi_key:
                st.markdown(
                    ":green_circle: **PSI API**", help="PageSpeed Insights key found"
                )
            else:
                st.markdown(
                    ":red_circle: **PSI API**",
                    help="Missing PAGESPEED_API_KEY in .env or secrets",
                )
        with col_s2:
            if or_key:
                st.markdown(
                    ":green_circle: **AI (LLM)**",
                    help="OpenRouter API key found",
                )
            else:
                st.markdown(
                    ":orange_circle: **AI (LLM)**",
                    help="Missing OPENROUTER_API_KEY -- AI features disabled",
                )

        st.divider()

        # --- Model selection ---
        st.subheader("AI Model")
        model_label = st.selectbox(
            "Select model",
            options=list(MODEL_OPTIONS.keys()),
            index=0,
            label_visibility="collapsed",
        )
        selected_model = MODEL_OPTIONS[model_label]
        st.session_state["selected_model"] = selected_model

        st.divider()

        # --- White-label settings ---
        with st.expander("White-label Settings", expanded=False):
            company_name = st.text_input(
                "Company name",
                value=st.session_state.get("company_name", "Speed Audit"),
                key="wl_company_name",
            )
            st.session_state["company_name"] = company_name

            company_logo = st.text_input(
                "Logo URL (optional)",
                value=st.session_state.get("company_logo", ""),
                key="wl_company_logo",
                placeholder="https://example.com/logo.png",
            )
            st.session_state["company_logo"] = company_logo

            brand_color = st.color_picker(
                "Brand color",
                value=st.session_state.get("brand_color", "#2563eb"),
                key="wl_brand_color",
            )
            st.session_state["brand_color"] = brand_color

        st.divider()

        # --- About ---
        st.subheader("About")
        st.markdown(
            "Analyzes any web page using Google PageSpeed Insights, "
            "classifies issues by severity and CWV impact, then generates "
            "AI-powered fix recommendations and a downloadable report."
        )
        st.caption("Built with Streamlit + OpenRouter")

    # =====================================================================
    # MAIN AREA
    # =====================================================================
    st.title("Page Speed Optimization Agent")
    st.markdown(
        "Enter a URL to analyze page loading performance and get actionable "
        "optimization recommendations."
    )

    # --- URL Input Row ---
    col1, col2 = st.columns([4, 1])
    with col1:
        url_input = st.text_input(
            "URL to analyze",
            placeholder="https://example.com",
            label_visibility="collapsed",
        )
    with col2:
        analyze_btn = st.button(
            "Analyze",
            type="primary",
            use_container_width=True,
        )

    # --- Run analysis ---
    if analyze_btn and url_input:
        valid, normalized_or_error = validate_url(url_input)
        if not valid:
            st.error(f"Invalid URL: {normalized_or_error}")
        elif not get_secret("PAGESPEED_API_KEY"):
            st.error(
                "PageSpeed API key is not configured. Add `PAGESPEED_API_KEY` "
                "to your `.env` file or Streamlit secrets."
            )
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                st.session_state["analysis_running"] = True
                result_obj, report_html, pdf_bytes = run_analysis(
                    normalized_or_error,
                    model=st.session_state.get(
                        "selected_model", "google/gemini-2.0-flash-001"
                    ),
                    progress_bar=progress_bar,
                    status_text=status_text,
                )
                st.session_state["analysis_result"] = result_obj
                st.session_state["report_html"] = report_html
                st.session_state["report_pdf"] = pdf_bytes
                st.session_state["error_message"] = None
            except Exception as e:
                logger.error("Analysis failed: %s", e, exc_info=True)
                st.error(f"Analysis failed: {str(e)}")
                st.session_state["error_message"] = str(e)
            finally:
                st.session_state["analysis_running"] = False
                # Clean up progress indicators after a short delay
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()

    elif analyze_btn and not url_input:
        st.warning("Please enter a URL to analyze.")

    # =====================================================================
    # RESULTS DISPLAY
    # =====================================================================
    if st.session_state.get("analysis_result") is not None:
        result: AnalysisResult = st.session_state["analysis_result"]

        st.divider()

        # --- Score overview cards ---
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            mobile_display = (
                f"{result.mobile_score}/100" if result.mobile_score is not None else "N/A"
            )
            delta_color = "normal"
            st.metric("Mobile Score", mobile_display)
        with col2:
            desktop_display = (
                f"{result.desktop_score}/100"
                if result.desktop_score is not None
                else "N/A"
            )
            st.metric("Desktop Score", desktop_display)
        with col3:
            cwv_label = "PASS" if result.cwv_pass else "FAIL"
            st.metric("CWV Status", cwv_label)
        with col4:
            st.metric("Critical Issues", len(result.critical_issues))
        with col5:
            st.metric("Total Issues", len(result.issues))

        # --- Tabs ---
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Summary", "Issues", "Screenshots", "Report"]
        )

        # =============================================================
        # TAB 1: Summary
        # =============================================================
        with tab1:
            # Executive summary
            if result.executive_summary:
                st.markdown(result.executive_summary)
            else:
                if not get_secret("OPENROUTER_API_KEY"):
                    st.info(
                        "AI-powered executive summary is unavailable. "
                        "Add an OPENROUTER_API_KEY to enable it."
                    )
                else:
                    st.info("No executive summary was generated for this analysis.")

            st.divider()

            # CWV Assessments
            st.subheader("Core Web Vitals")
            if result.cwv_assessments:
                # Display in a 2-row grid
                row1_metrics = result.cwv_assessments[:4]
                row2_metrics = result.cwv_assessments[4:]

                cols = st.columns(len(row1_metrics))
                for i, assessment in enumerate(row1_metrics):
                    with cols[i]:
                        render_cwv_card(assessment)

                if row2_metrics:
                    cols2 = st.columns(len(row2_metrics))
                    for i, assessment in enumerate(row2_metrics):
                        with cols2[i]:
                            render_cwv_card(assessment)
            else:
                st.info("No Core Web Vitals data available.")

            st.divider()

            # CMS Detection
            if result.cms_info and result.cms_info.name != "unknown":
                st.subheader("Detected Platform")
                cms_cols = st.columns(3)
                with cms_cols[0]:
                    st.markdown(f"**CMS:** {result.cms_info.name.capitalize()}")
                with cms_cols[1]:
                    st.markdown(f"**Confidence:** {result.cms_info.confidence.capitalize()}")
                with cms_cols[2]:
                    plugins_or_apps = (
                        result.cms_info.detected_plugins or result.cms_info.detected_apps
                    )
                    if plugins_or_apps:
                        st.markdown(f"**Plugins/Apps:** {', '.join(plugins_or_apps[:8])}")

            st.divider()

            # Top priority actions / roadmap
            if result.implementation_roadmap:
                st.subheader("Implementation Roadmap")
                for item in result.implementation_roadmap:
                    priority = item.get("priority", "")
                    title = item.get("title", "Untitled")
                    description = item.get("description", "")
                    effort = item.get("effort", "medium")
                    impact = item.get("impact", "medium")

                    priority_colors = {
                        "quick-win": ":green",
                        "short-term": ":orange",
                        "long-term": ":red",
                    }
                    badge = priority_colors.get(priority, ":blue")

                    st.markdown(
                        f"**{badge}[{priority.replace('-', ' ').title()}]** "
                        f"**{title}**  \n"
                        f"{description}  \n"
                        f"*Effort: {effort} | Impact: {impact}*"
                    )
                    st.markdown("---")

            # Page stats
            if result.page_stats and result.page_stats.total_bytes > 0:
                st.subheader("Page Statistics")
                ps = result.page_stats
                stat_cols = st.columns(4)
                with stat_cols[0]:
                    st.metric("Total Requests", ps.total_requests)
                with stat_cols[1]:
                    st.metric("Total Size", format_bytes(ps.total_bytes))
                with stat_cols[2]:
                    st.metric("JavaScript", format_bytes(ps.js_bytes))
                with stat_cols[3]:
                    st.metric("Images", format_bytes(ps.image_bytes))

                stat_cols2 = st.columns(4)
                with stat_cols2[0]:
                    st.metric("CSS", format_bytes(ps.css_bytes))
                with stat_cols2[1]:
                    st.metric("Fonts", format_bytes(ps.font_bytes))
                with stat_cols2[2]:
                    st.metric("HTML", format_bytes(ps.html_bytes))
                with stat_cols2[3]:
                    st.metric("3rd Party", format_bytes(ps.third_party_bytes))

        # =============================================================
        # TAB 2: Issues
        # =============================================================
        with tab2:
            if not result.issues:
                st.success("No performance issues detected!")
            else:
                # Critical issues
                critical = result.critical_issues
                if critical:
                    st.subheader(f"Critical Issues ({len(critical)})")
                    for issue in critical:
                        with st.expander(
                            f":red_circle: **{issue.title}**",
                            expanded=False,
                        ):
                            render_issue_detail(issue)

                # Important issues
                important = result.important_issues
                if important:
                    st.subheader(f"Important Issues ({len(important)})")
                    for issue in important:
                        with st.expander(
                            f":orange_circle: **{issue.title}**",
                            expanded=False,
                        ):
                            render_issue_detail(issue)

                # Minor issues
                minor = result.minor_issues
                if minor:
                    st.subheader(f"Minor Issues ({len(minor)})")
                    for issue in minor:
                        with st.expander(
                            f":large_yellow_circle: **{issue.title}**",
                            expanded=False,
                        ):
                            render_issue_detail(issue)

        # =============================================================
        # TAB 3: Screenshots
        # =============================================================
        with tab3:
            # Filmstrip
            if result.filmstrip_frames:
                st.subheader("Loading Timeline (Filmstrip)")

                # Display filmstrip frames in a row of columns
                # Limit to ~10 frames for readability
                frames_to_show = result.filmstrip_frames
                if len(frames_to_show) > 10:
                    # Sample evenly
                    step = len(frames_to_show) // 10
                    frames_to_show = frames_to_show[::step][:10]

                if frames_to_show:
                    cols = st.columns(len(frames_to_show))
                    for i, frame in enumerate(frames_to_show):
                        with cols[i]:
                            timing = frame.get("timing_ms", 0)
                            data_uri = frame.get("data_uri", "")
                            if data_uri:
                                st.image(data_uri, width=120)
                                st.caption(format_ms(timing))
            else:
                st.info("No filmstrip data available.")

            st.divider()

            # Final screenshot
            if result.final_screenshot:
                st.subheader("Final Rendered Page")
                st.image(result.final_screenshot, width=400)
            else:
                st.info("No final screenshot available.")

        # =============================================================
        # TAB 4: Report
        # =============================================================
        with tab4:
            st.subheader("Generated Report")

            # Download buttons
            dl_col1, dl_col2, dl_col3 = st.columns(3)

            # Build a safe filename from the URL
            safe_name = (
                result.url.replace("https://", "")
                .replace("http://", "")
                .replace("/", "_")
                .replace("?", "_")
                .replace("&", "_")[:60]
            )

            with dl_col1:
                if st.session_state.get("report_html"):
                    st.download_button(
                        "Download HTML Report",
                        data=st.session_state["report_html"],
                        file_name=f"speed-report-{safe_name}.html",
                        mime="text/html",
                        use_container_width=True,
                    )

            with dl_col2:
                if st.session_state.get("report_pdf"):
                    st.download_button(
                        "Download PDF Report",
                        data=st.session_state["report_pdf"],
                        file_name=f"speed-report-{safe_name}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                elif not PDFConverter.is_available():
                    st.caption("PDF unavailable (WeasyPrint not installed)")

            with dl_col3:
                # JSON export of raw data
                if result.raw_psi_mobile:
                    raw_json = json.dumps(
                        {
                            "url": result.url,
                            "analyzed_at": result.analyzed_at,
                            "mobile_score": result.mobile_score,
                            "desktop_score": result.desktop_score,
                            "issue_count": len(result.issues),
                            "cwv_pass": result.cwv_pass,
                        },
                        indent=2,
                    )
                    st.download_button(
                        "Download Summary JSON",
                        data=raw_json,
                        file_name=f"speed-summary-{safe_name}.json",
                        mime="application/json",
                        use_container_width=True,
                    )

            st.divider()

            # HTML preview in iframe
            if st.session_state.get("report_html"):
                st.markdown("**Report Preview**")
                st.components.v1.html(
                    st.session_state["report_html"],
                    height=800,
                    scrolling=True,
                )
            else:
                st.info("No report has been generated yet.")


# =========================================================================
# Entry point
# =========================================================================
if __name__ == "__main__":
    main()
