"""Prompt Builder Module.

Builds prompts for the two-stage AI analysis:
1. Per-issue detailed recommendations (issue_analysis)
2. Executive summary for client-facing reports (executive_summary)
"""

import json
from typing import Optional


class PromptBuilder:
    """Constructs prompts for AI-powered performance analysis."""

    @staticmethod
    def build_issue_analysis_prompt(
        kb_context: str,
        cms_type: str,
        psi_data: dict,
        html_findings: list[dict],
    ) -> tuple[str, str]:
        """Build system prompt and user content for per-issue recommendations.

        Args:
            kb_context: Relevant knowledge base sections selected by
                KnowledgeBase.get_relevant_context().
            cms_type: Detected CMS ("wordpress", "shopify", or "unknown").
            psi_data: Dictionary with keys:
                - scores: {performance, accessibility, best_practices, seo}
                - metrics: {FCP, LCP, TBT, CLS, SI, TTI} with values and ratings
                - opportunities: list of PSI opportunity audits
                - diagnostics: list of PSI diagnostic audits
                - lcp_element: dict describing the LCP element
                - cls_elements: list of dicts describing CLS-contributing elements
                - page_stats: {total_bytes, total_requests, resource_breakdown}
            html_findings: List of dicts from HTML analyzer, each with:
                - finding_id: str
                - category: str
                - description: str
                - elements: list of element details
                - count: int

        Returns:
            Tuple of (system_prompt, user_content).
        """
        cms_label = cms_type if cms_type != "unknown" else "Unknown CMS / static site"

        system_prompt = f"""You are an elite mobile-first page speed optimization expert. You have deep expertise in Core Web Vitals (LCP, INP, CLS), browser rendering pipelines, HTTP/2, resource loading strategies, and CMS-specific performance tuning.

Your task: analyze the PageSpeed Insights data and HTML analysis findings below, then produce detailed, actionable fix recommendations for EVERY issue detected.

## Critical Instructions

- Be SPECIFIC: Name exact files, images, scripts, CSS selectors. Never give generic advice.
- For each issue, provide step-by-step implementation instructions a web developer can follow.
- ALWAYS provide the direct code solution FIRST (HTML edits, CSS changes, JS modifications, server config, .htaccess rules, Liquid template changes, PHP code). This is the PRIMARY recommendation.
- THEN optionally mention plugin/app alternatives as a secondary convenience option for non-technical users. NEVER recommend ONLY a plugin — always include the manual code approach.
- Include code examples for EVERY issue where applicable (HTML, CSS, JavaScript, Liquid, PHP, nginx/Apache config). These should be copy-paste ready.
- Estimate the improvement each fix will provide.
- Focus 90% on mobile performance — mobile issues are the priority.
- Do NOT repeat the problem description back — focus on HOW to fix it.

## Detected CMS: {cms_label}

## Knowledge Base Reference

Use the following expert knowledge to inform your recommendations:

{kb_context}

## Output Format

Return a JSON array. Each element represents one issue and must follow this exact schema:

```json
[
  {{
    "issue_id": "the-audit-id-or-finding-id",
    "title": "Specific descriptive title naming the exact resource",
    "severity": "critical|important|minor",
    "cwv_impact": ["LCP", "CLS", "INP", "FCP", "TBT"],
    "what_is_wrong": "Specific description naming exact files/elements",
    "why_it_matters": "Impact on user experience and specific CWV metric",
    "how_to_fix": ["Step 1: direct code change...", "Step 2: ...", "Step 3: ..."],
    "cms_specific_fix": "Manual code fix first (HTML/CSS/JS/Liquid/PHP), then optionally mention plugin alternatives. Never recommend ONLY a plugin.",
    "code_example": "Copy-paste-ready code snippet showing the exact fix (HTML, CSS, JS, Liquid, PHP, .htaccess, nginx config). REQUIRED for every issue — never leave null.",
    "estimated_improvement": "e.g., ~800ms LCP reduction",
    "effort_level": "low|medium|high",
    "affected_resources": ["url1", "url2"]
  }}
]
```

Return ONLY the JSON array. No commentary before or after."""

        # Build the user content with all audit data
        user_sections: list[str] = []

        # Section 1: Current scores and metrics
        scores = psi_data.get("scores", {})
        metrics = psi_data.get("metrics", {})
        user_sections.append("## Current Performance Scores (Mobile)")
        user_sections.append(
            f"- Performance: {scores.get('performance', 'N/A')}/100\n"
            f"- Accessibility: {scores.get('accessibility', 'N/A')}/100\n"
            f"- Best Practices: {scores.get('best_practices', 'N/A')}/100\n"
            f"- SEO: {scores.get('seo', 'N/A')}/100"
        )

        user_sections.append("## Core Web Vitals & Metrics (Mobile)")
        if metrics:
            metrics_lines = []
            for metric_name, metric_val in metrics.items():
                if isinstance(metric_val, dict):
                    display = metric_val.get("displayValue", metric_val.get("value", "N/A"))
                    rating = metric_val.get("rating", "")
                    metrics_lines.append(f"- {metric_name}: {display} ({rating})")
                else:
                    metrics_lines.append(f"- {metric_name}: {metric_val}")
            user_sections.append("\n".join(metrics_lines))
        else:
            user_sections.append("No metrics data available.")

        # Section 2: Page stats
        page_stats = psi_data.get("page_stats", {})
        if page_stats:
            user_sections.append("## Page Statistics")
            user_sections.append(
                f"- Total transfer size: {page_stats.get('total_bytes', 'N/A')} bytes\n"
                f"- Total requests: {page_stats.get('total_requests', 'N/A')}"
            )
            breakdown = page_stats.get("resource_breakdown", {})
            if breakdown:
                user_sections.append("### Resource Breakdown")
                for res_type, details in breakdown.items():
                    if isinstance(details, dict):
                        user_sections.append(
                            f"- {res_type}: {details.get('count', '?')} requests, "
                            f"{details.get('size', '?')} bytes"
                        )
                    else:
                        user_sections.append(f"- {res_type}: {details}")

        # Section 3: LCP element
        lcp_element = psi_data.get("lcp_element")
        if lcp_element:
            user_sections.append("## LCP Element Details")
            user_sections.append(json.dumps(lcp_element, indent=2, default=str))

        # Section 4: CLS elements
        cls_elements = psi_data.get("cls_elements", [])
        if cls_elements:
            user_sections.append("## CLS-Contributing Elements")
            user_sections.append(json.dumps(cls_elements, indent=2, default=str))

        # Section 5: PSI Opportunities (with full items/resources)
        opportunities = psi_data.get("opportunities", [])
        if opportunities:
            user_sections.append("## PageSpeed Insights Opportunities")
            for opp in opportunities:
                user_sections.append(f"### {opp.get('id', 'unknown')} — {opp.get('title', '')}")
                if opp.get("displayValue"):
                    user_sections.append(f"Potential savings: {opp['displayValue']}")
                if opp.get("description"):
                    user_sections.append(f"Description: {opp['description']}")
                items = opp.get("items", opp.get("details", {}).get("items", []))
                if items:
                    user_sections.append("Affected resources:")
                    for item in items[:20]:  # Cap at 20 items to manage token budget
                        user_sections.append(f"  - {json.dumps(item, default=str)}")

        # Section 6: PSI Diagnostics
        diagnostics = psi_data.get("diagnostics", [])
        if diagnostics:
            user_sections.append("## PageSpeed Insights Diagnostics")
            for diag in diagnostics:
                user_sections.append(f"### {diag.get('id', 'unknown')} — {diag.get('title', '')}")
                if diag.get("displayValue"):
                    user_sections.append(f"Value: {diag['displayValue']}")
                if diag.get("description"):
                    user_sections.append(f"Description: {diag['description']}")
                items = diag.get("items", diag.get("details", {}).get("items", []))
                if items:
                    user_sections.append("Details:")
                    for item in items[:15]:  # Cap at 15 items
                        user_sections.append(f"  - {json.dumps(item, default=str)}")

        # Section 7: HTML analysis findings
        if html_findings:
            user_sections.append("## HTML Analysis Findings")
            for finding in html_findings:
                user_sections.append(
                    f"### {finding.get('finding_id', 'unknown')} "
                    f"({finding.get('category', 'general')})"
                )
                user_sections.append(f"Description: {finding.get('description', '')}")
                user_sections.append(f"Count: {finding.get('count', 0)}")
                elements = finding.get("elements", [])
                if elements:
                    user_sections.append("Elements:")
                    for elem in elements[:10]:  # Cap at 10
                        user_sections.append(f"  - {json.dumps(elem, default=str)}")

        # Section 8: CMS type
        user_sections.append(f"## Detected CMS: {cms_label}")

        user_content = "\n\n".join(user_sections)

        return system_prompt, user_content

    @staticmethod
    def build_executive_summary_prompt(
        scores: dict,
        cwv_data: list[dict],
        issue_counts: dict,
        top_issues: list[dict],
        cms_type: str,
    ) -> tuple[str, str]:
        """Build prompt for executive summary generation.

        Args:
            scores: Dict with performance, accessibility, best_practices, seo
                scores (0-100).
            cwv_data: List of dicts, each with:
                - name: str (e.g., "LCP", "CLS", "TBT")
                - value: str (display value)
                - rating: str ("good", "needs-improvement", "poor")
            issue_counts: Dict with keys: critical, important, minor (int counts).
            top_issues: List of the top 5 issue dicts (from issue analysis output),
                each with at minimum: title, severity, cwv_impact,
                estimated_improvement.
            cms_type: Detected CMS type.

        Returns:
            Tuple of (system_prompt, user_content).
        """
        system_prompt = """You are writing an executive summary for a client-facing page speed audit report.

## Tone & Style
- Professional, clear, and actionable.
- Avoid technical jargon — explain in business terms when possible.
- Be honest about the current state but optimistic about improvement potential.
- Use concrete numbers and metrics, not vague statements.
- Structure the summary with HTML headings (<h3>), short paragraphs (<p>), and bullet lists (<ul><li>) for easy scanning. Never write a single long paragraph — break it up.

## Output Format

Return a JSON object with this exact schema:

```json
{
  "summary": "Executive summary as structured HTML. Use these elements for readability: <h3> for section headings (e.g. 'Current State', 'Key Problems', 'Recommended Path Forward'), <p> for short paragraphs (2-3 sentences max each), <ul><li> for bullet-point lists of key findings. Keep it scannable — no walls of text. Include concrete numbers and metrics throughout.",
  "top_actions": [
    "Action 1 — the single most impactful thing to do first",
    "Action 2 — second most impactful",
    "Action 3 — third most impactful"
  ],
  "roadmap": [
    {
      "priority": "quick-win",
      "title": "Short title",
      "description": "What to do and expected result",
      "effort": "low",
      "impact": "high"
    },
    {
      "priority": "short-term",
      "title": "Short title",
      "description": "What to do and expected result",
      "effort": "medium",
      "impact": "high"
    },
    {
      "priority": "long-term",
      "title": "Short title",
      "description": "What to do and expected result",
      "effort": "high",
      "impact": "medium"
    }
  ]
}
```

The roadmap should contain 4-8 items covering quick-wins (< 1 day), short-term (1-5 days), and long-term (1+ weeks) improvements. Each item should have:
- priority: "quick-win" | "short-term" | "long-term"
- effort: "low" | "medium" | "high"
- impact: "low" | "medium" | "high"

Return ONLY the JSON object. No commentary before or after."""

        # Build user content
        user_sections: list[str] = []

        # Performance scores
        user_sections.append("## Performance Scores (Mobile)")
        user_sections.append(
            f"- Performance: {scores.get('performance', 'N/A')}/100\n"
            f"- Accessibility: {scores.get('accessibility', 'N/A')}/100\n"
            f"- Best Practices: {scores.get('best_practices', 'N/A')}/100\n"
            f"- SEO: {scores.get('seo', 'N/A')}/100"
        )

        # Core Web Vitals
        user_sections.append("## Core Web Vitals")
        if cwv_data:
            for cwv in cwv_data:
                name = cwv.get("name", "Unknown")
                value = cwv.get("value", "N/A")
                rating = cwv.get("rating", "unknown")
                status_label = {
                    "good": "PASS",
                    "needs-improvement": "NEEDS IMPROVEMENT",
                    "poor": "FAIL",
                }.get(rating, rating.upper())
                user_sections.append(f"- {name}: {value} [{status_label}]")
        else:
            user_sections.append("No CWV data available.")

        # Issue counts
        critical = issue_counts.get("critical", 0)
        important = issue_counts.get("important", 0)
        minor = issue_counts.get("minor", 0)
        total = critical + important + minor
        user_sections.append("## Issues Found")
        user_sections.append(
            f"- Total issues: {total}\n"
            f"- Critical: {critical}\n"
            f"- Important: {important}\n"
            f"- Minor: {minor}"
        )

        # Top 5 issues
        user_sections.append("## Top Issues (by impact)")
        if top_issues:
            for i, issue in enumerate(top_issues[:5], 1):
                title = issue.get("title", "Untitled")
                severity = issue.get("severity", "unknown")
                cwv_impact = ", ".join(issue.get("cwv_impact", []))
                improvement = issue.get("estimated_improvement", "N/A")
                user_sections.append(
                    f"{i}. [{severity.upper()}] {title}\n"
                    f"   CWV Impact: {cwv_impact}\n"
                    f"   Estimated Improvement: {improvement}"
                )
        else:
            user_sections.append("No issues analyzed yet.")

        # CMS info
        cms_label = cms_type if cms_type != "unknown" else "Unknown / static site"
        user_sections.append(f"## Detected CMS: {cms_label}")

        user_content = "\n\n".join(user_sections)

        return system_prompt, user_content
