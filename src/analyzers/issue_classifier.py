"""Classifies PSI opportunities/diagnostics and HTML findings by severity.

Maps issues to CWV metrics and calculates priority scores so the report
can display red / orange / yellow indicators accurately.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CWV metric thresholds (mobile)
# ---------------------------------------------------------------------------

CWV_THRESHOLDS = {
    "LCP": {"good": 2500, "poor": 4000},       # ms
    "CLS": {"good": 0.1, "poor": 0.25},         # score
    "INP": {"good": 200, "poor": 500},           # ms
    "FCP": {"good": 1800, "poor": 3000},         # ms
    "SI":  {"good": 3400, "poor": 5800},          # ms
    "TBT": {"good": 200, "poor": 600},           # ms
    "TTFB": {"good": 800, "poor": 1800},         # ms
}

# ---------------------------------------------------------------------------
# Map audit IDs to the CWV metrics they affect
# ---------------------------------------------------------------------------

AUDIT_CWV_MAP: dict[str, list[str]] = {
    "render-blocking-resources": ["LCP", "FCP"],
    "unused-javascript": ["LCP", "TBT"],
    "unused-css-rules": ["LCP", "FCP"],
    "offscreen-images": ["LCP"],
    "modern-image-formats": ["LCP"],
    "uses-responsive-images": ["LCP"],
    "uses-optimized-images": ["LCP"],
    "unminified-css": ["FCP", "LCP"],
    "unminified-javascript": ["TBT"],
    "uses-text-compression": ["FCP", "LCP"],
    "server-response-time": ["TTFB", "LCP", "FCP"],
    "efficient-animated-content": ["LCP"],
    "total-byte-weight": ["LCP"],
    "uses-long-cache-ttl": ["LCP"],
    "dom-size": ["TBT", "INP"],
    "redirects": ["TTFB", "LCP", "FCP"],
    "uses-rel-preconnect": ["LCP", "FCP"],
    "uses-rel-preload": ["LCP"],
    "font-display": ["CLS", "FCP"],
    "critical-request-chains": ["LCP", "FCP"],
    "third-party-summary": ["TBT", "LCP"],
    "bootup-time": ["TBT", "INP"],
    "mainthread-work-breakdown": ["TBT", "INP"],
    "duplicated-javascript": ["TBT"],
    "legacy-javascript": ["TBT"],
    "largest-contentful-paint-element": ["LCP"],
    "layout-shift-elements": ["CLS"],
    "unsized-images": ["CLS"],
    "image-size-responsive": ["LCP"],
    "viewport": ["LCP", "CLS"],
}

# ---------------------------------------------------------------------------
# Audit sets for static severity classification
# ---------------------------------------------------------------------------

CRITICAL_AUDITS = {
    "render-blocking-resources",    # When savings > 500ms
    "server-response-time",         # When TTFB > 1800ms
    "largest-contentful-paint-element",  # When LCP > 4s
    "viewport",                     # Missing viewport meta
}

IMPORTANT_AUDITS = {
    "unused-javascript",
    "unused-css-rules",
    "offscreen-images",
    "modern-image-formats",
    "uses-responsive-images",
    "uses-optimized-images",
    "total-byte-weight",
    "third-party-summary",
    "dom-size",
    "bootup-time",
    "mainthread-work-breakdown",
    "uses-rel-preload",
    "font-display",
    "layout-shift-elements",
    "unsized-images",
}

# ---------------------------------------------------------------------------
# HTML finding -> severity / CWV mapping
# ---------------------------------------------------------------------------

HTML_FINDING_MAP: dict[str, dict] = {
    "images-missing-dimensions": {
        "default_severity": "important",
        "cwv": ["CLS"],
    },
    "images-missing-srcset": {
        "default_severity": "minor",
        "cwv": ["LCP"],
    },
    "images-lazy-above-fold": {
        "default_severity": "critical",
        "cwv": ["LCP"],
    },
    "scripts-render-blocking": {
        "default_severity": "critical",
        "cwv": ["LCP", "FCP"],
    },
    "styles-render-blocking": {
        "default_severity": "important",
        "cwv": ["FCP"],
    },
    "css-import": {
        "default_severity": "minor",
        "cwv": ["FCP"],
    },
    "fonts-no-display": {
        "default_severity": "minor",
        "cwv": ["CLS"],
    },
    "meta-no-viewport": {
        "default_severity": "critical",
        "cwv": ["LCP", "CLS"],
    },
    "dom-excessive": {
        # Severity is dynamic: IMPORTANT if > 1500 elements, MINOR otherwise.
        # Handled specially in classify_html_findings.
        "default_severity": "minor",
        "cwv": ["TBT", "INP"],
    },
}

# Overlap map: HTML finding IDs that correspond to PSI audit IDs.
# When both exist, PSI takes precedence because it includes savings data.
HTML_TO_PSI_OVERLAP: dict[str, str] = {
    "images-missing-dimensions": "unsized-images",
    "scripts-render-blocking": "render-blocking-resources",
    "styles-render-blocking": "render-blocking-resources",
    "meta-no-viewport": "viewport",
    "dom-excessive": "dom-size",
    "fonts-no-display": "font-display",
}


class IssueClassifier:
    """Classifies PSI and HTML findings into severity levels."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify_opportunities(
        self, opportunities: list[dict], lab_metrics: dict
    ) -> list[dict]:
        """Classify PSI opportunity audits into severity levels.

        Args:
            opportunities: PSI opportunity audits. Each dict should contain at
                least ``id``, ``title``, and optionally ``score``,
                ``savings_ms``, ``savings_bytes``, ``display_value``, ``items``.
            lab_metrics: Lab metric values, e.g.
                ``{"LCP": 4500, "FCP": 2200, "CLS": 0.15, "TBT": 450, "SI": 5000}``.

        Returns:
            List of classified issues, each a dict with keys:
                issue_id, title, severity, cwv_impact, savings_ms,
                savings_bytes, affected_resources, display_value, items,
                priority_score, source.
        """
        classified: list[dict] = []

        for opp in opportunities:
            audit_id = opp.get("id", "")
            title = opp.get("title", audit_id)
            savings_ms = float(opp.get("savings_ms", 0) or 0)
            savings_bytes = int(opp.get("savings_bytes", 0) or 0)
            display_value = opp.get("display_value", "")
            items = opp.get("items", [])
            score = opp.get("score")

            # Skip audits that already passed (score == 1)
            if score is not None and score >= 1:
                continue

            severity = self._determine_severity(
                audit_id, savings_ms, savings_bytes, lab_metrics
            )
            cwv_impact = AUDIT_CWV_MAP.get(audit_id, [])
            affected_resources = self._extract_affected_resources(items)

            priority_score = self._calculate_priority_score(
                severity, savings_ms, savings_bytes, cwv_impact, lab_metrics
            )

            classified.append({
                "issue_id": audit_id,
                "title": title,
                "severity": severity,
                "cwv_impact": cwv_impact,
                "savings_ms": savings_ms,
                "savings_bytes": savings_bytes,
                "affected_resources": affected_resources,
                "display_value": display_value,
                "items": items,
                "priority_score": priority_score,
                "source": "psi_opportunity",
            })

        # Sort by priority score descending
        classified.sort(key=lambda x: x["priority_score"], reverse=True)
        return classified

    def classify_diagnostics(
        self, diagnostics: list[dict], lab_metrics: dict
    ) -> list[dict]:
        """Classify PSI diagnostic audits.

        Diagnostics typically have no ``savings_ms`` but may flag structural
        problems (large DOM, long main-thread work, etc.).

        Args:
            diagnostics: PSI diagnostic audits (same shape as opportunities but
                savings are often absent).
            lab_metrics: Lab metric values.

        Returns:
            List of classified issue dicts (same shape as classify_opportunities).
        """
        classified: list[dict] = []

        for diag in diagnostics:
            audit_id = diag.get("id", "")
            title = diag.get("title", audit_id)
            display_value = diag.get("display_value", "")
            items = diag.get("items", [])
            score = diag.get("score")

            # Skip passed audits
            if score is not None and score >= 1:
                continue

            # Diagnostics rarely have explicit savings; derive from display_value
            savings_ms = float(diag.get("savings_ms", 0) or 0)
            savings_bytes = int(diag.get("savings_bytes", 0) or 0)

            severity = self._determine_severity(
                audit_id, savings_ms, savings_bytes, lab_metrics
            )
            cwv_impact = AUDIT_CWV_MAP.get(audit_id, [])
            affected_resources = self._extract_affected_resources(items)

            priority_score = self._calculate_priority_score(
                severity, savings_ms, savings_bytes, cwv_impact, lab_metrics
            )

            classified.append({
                "issue_id": audit_id,
                "title": title,
                "severity": severity,
                "cwv_impact": cwv_impact,
                "savings_ms": savings_ms,
                "savings_bytes": savings_bytes,
                "affected_resources": affected_resources,
                "display_value": display_value,
                "items": items,
                "priority_score": priority_score,
                "source": "psi_diagnostic",
            })

        classified.sort(key=lambda x: x["priority_score"], reverse=True)
        return classified

    def classify_html_findings(self, findings: list[dict]) -> list[dict]:
        """Classify HTML analysis findings.

        Args:
            findings: HTML-based findings. Each dict should have at least
                ``id`` and ``title``, optionally ``affected_resources``,
                ``details``, and ``count`` (e.g., DOM element count).

        Returns:
            List of classified issue dicts.
        """
        classified: list[dict] = []

        for finding in findings:
            finding_id = finding.get("id", "")
            title = finding.get("title", finding_id)
            affected_resources = finding.get("affected_resources", [])
            count = finding.get("count", 0)
            details = finding.get("details", "")

            mapping = HTML_FINDING_MAP.get(finding_id)
            if mapping is None:
                # Unknown HTML finding; treat as minor with no CWV mapping
                severity = "minor"
                cwv_impact: list[str] = []
            else:
                cwv_impact = mapping["cwv"]
                severity = mapping["default_severity"]

                # Dynamic severity for dom-excessive
                if finding_id == "dom-excessive":
                    if count > 3000:
                        severity = "critical"
                    elif count > 1500:
                        severity = "important"
                    else:
                        severity = "minor"

            # HTML findings have no ms/bytes savings; priority is based purely
            # on severity weight and how many resources are affected.
            severity_weight = {"critical": 3, "important": 2, "minor": 1}.get(severity, 1)
            resource_factor = min(len(affected_resources), 20)  # cap influence
            priority_score = float(severity_weight * 100 + resource_factor * 5)

            classified.append({
                "issue_id": finding_id,
                "title": title,
                "severity": severity,
                "cwv_impact": cwv_impact,
                "savings_ms": 0.0,
                "savings_bytes": 0,
                "affected_resources": affected_resources[:20],  # limit for report
                "display_value": details if isinstance(details, str) else "",
                "items": [],
                "priority_score": priority_score,
                "source": "html_analysis",
            })

        classified.sort(key=lambda x: x["priority_score"], reverse=True)
        return classified

    def merge_and_deduplicate(
        self,
        psi_issues: list[dict],
        html_issues: list[dict],
    ) -> list[dict]:
        """Merge PSI and HTML issues, removing duplicates.

        PSI issues take precedence when there is overlap (they carry savings
        data).  HTML issues that map to the same underlying PSI audit are
        dropped, but any *extra* affected resources from the HTML finding
        are appended to the PSI issue.

        Args:
            psi_issues: Already-classified PSI issues (opportunities + diagnostics).
            html_issues: Already-classified HTML findings.

        Returns:
            Merged and deduplicated list, sorted by priority_score descending.
        """
        # Build a set of PSI audit IDs already present
        psi_ids: set[str] = {issue["issue_id"] for issue in psi_issues}

        # Index PSI issues by id for quick lookup
        psi_by_id: dict[str, dict] = {issue["issue_id"]: issue for issue in psi_issues}

        merged = list(psi_issues)  # start with all PSI issues

        for html_issue in html_issues:
            html_id = html_issue["issue_id"]
            overlapping_psi_id = HTML_TO_PSI_OVERLAP.get(html_id)

            if overlapping_psi_id and overlapping_psi_id in psi_ids:
                # PSI already covers this finding; merge extra resources
                psi_issue = psi_by_id[overlapping_psi_id]
                existing_resources = set(psi_issue.get("affected_resources", []))
                for res in html_issue.get("affected_resources", []):
                    if res not in existing_resources:
                        psi_issue["affected_resources"].append(res)
                        existing_resources.add(res)
                logger.debug(
                    "HTML finding '%s' merged into PSI audit '%s'",
                    html_id, overlapping_psi_id,
                )
            elif html_id in psi_ids:
                # Exact ID match (rare but possible); skip the HTML duplicate
                logger.debug("HTML finding '%s' already exists as PSI audit; skipping", html_id)
            else:
                # No overlap; add the HTML issue as-is
                merged.append(html_issue)

        # Final sort by priority score
        merged.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        return merged

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _determine_severity(
        self,
        audit_id: str,
        savings_ms: float,
        savings_bytes: int,
        lab_metrics: dict,
    ) -> str:
        """Determine severity based on audit type, savings, and metric state.

        Decision hierarchy (first match wins):
        1. If the audit belongs to ``CRITICAL_AUDITS`` AND has large savings
           (>500 ms or >500 KB), return ``"critical"``.
        2. If ANY CWV metric affected by this audit is in the "poor" range,
           return ``"critical"``.
        3. If the audit belongs to ``CRITICAL_AUDITS`` with moderate savings
           (>200 ms or >200 KB), return ``"critical"``.
        4. If the audit belongs to ``IMPORTANT_AUDITS`` or savings > 200 ms
           or > 200 KB, return ``"important"``.
        5. If any affected CWV metric is in the "needs improvement" range,
           bump at least to ``"important"``.
        6. Otherwise return ``"minor"``.
        """
        cwv_metrics = AUDIT_CWV_MAP.get(audit_id, [])

        # Check how the affected metrics are doing
        has_poor_metric = False
        has_needs_improvement = False
        for metric_name in cwv_metrics:
            threshold = CWV_THRESHOLDS.get(metric_name)
            metric_value = lab_metrics.get(metric_name)
            if threshold is None or metric_value is None:
                continue
            if metric_value >= threshold["poor"]:
                has_poor_metric = True
            elif metric_value >= threshold["good"]:
                has_needs_improvement = True

        large_savings = savings_ms > 500 or savings_bytes > 500_000
        moderate_savings = savings_ms > 200 or savings_bytes > 200_000

        # Rule 1: Critical audit with large savings
        if audit_id in CRITICAL_AUDITS and large_savings:
            return "critical"

        # Rule 2: Any affected CWV metric is poor
        if has_poor_metric:
            return "critical"

        # Rule 3: Critical audit with moderate savings
        if audit_id in CRITICAL_AUDITS and moderate_savings:
            return "critical"

        # Rule 4: Important audit or moderate savings
        if audit_id in IMPORTANT_AUDITS or moderate_savings:
            return "important"

        # Rule 5: Needs-improvement metric bumps to important
        if has_needs_improvement:
            return "important"

        # Rule 6: Default
        return "minor"

    def _calculate_priority_score(
        self,
        severity: str,
        savings_ms: float,
        savings_bytes: int,
        cwv_impact: list[str],
        lab_metrics: dict,
    ) -> float:
        """Calculate a composite priority score for sorting.

        The score blends:
        - Severity weight (critical=3, important=2, minor=1) as a base multiplier
        - Savings in milliseconds (direct user-visible impact)
        - Savings in bytes (converted to a ms-equivalent for comparison)
        - A bonus when affected CWV metrics are in poor/needs-improvement state
        - A bonus for the number of CWV metrics affected (broader impact)

        Higher score = higher priority in the report.
        """
        severity_weight = {"critical": 3, "important": 2, "minor": 1}.get(severity, 1)

        # Base score from savings
        ms_score = savings_ms
        bytes_score = savings_bytes / 1000.0  # rough KB-to-ms proxy

        # CWV health bonus: poor metrics get a bigger bonus
        cwv_bonus = 0.0
        for metric_name in cwv_impact:
            threshold = CWV_THRESHOLDS.get(metric_name)
            metric_value = lab_metrics.get(metric_name)
            if threshold is None or metric_value is None:
                continue
            if metric_value >= threshold["poor"]:
                cwv_bonus += 200.0
            elif metric_value >= threshold["good"]:
                cwv_bonus += 80.0

        # Breadth bonus: more affected metrics = more important
        breadth_bonus = len(cwv_impact) * 20.0

        raw = ms_score + bytes_score + cwv_bonus + breadth_bonus
        return float(severity_weight) * max(raw, 1.0)

    @staticmethod
    def _extract_affected_resources(items: list[dict]) -> list[str]:
        """Pull URL strings from PSI audit item lists.

        Items may have a ``url`` key directly or a nested ``node.snippet``
        that is useful when no URL is available.
        """
        resources: list[str] = []
        for item in items:
            url = item.get("url")
            if url:
                resources.append(url)
            elif "node" in item:
                snippet = item["node"].get("snippet", "")
                if snippet:
                    resources.append(snippet)
        # Deduplicate while preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for r in resources:
            if r not in seen:
                seen.add(r)
                deduped.append(r)
        return deduped
