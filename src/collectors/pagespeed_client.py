"""Google PageSpeed Insights API v5 client with comprehensive response parsing."""

import requests
import time
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PSIResult:
    """Parsed PageSpeed Insights result."""

    # Scores (0-100)
    performance_score: Optional[int] = None
    accessibility_score: Optional[int] = None
    seo_score: Optional[int] = None
    best_practices_score: Optional[int] = None

    # Field data (CrUX) - may be None if no field data available
    field_data: Optional[dict] = None  # {metric_name: {percentile, category, distributions}}

    # Lab metrics
    lab_metrics: dict = field(default_factory=dict)  # {FCP, LCP, TBT, CLS, SI, TTI in ms/score}

    # Opportunities (with resource URLs and savings)
    opportunities: list[dict] = field(default_factory=list)
    # Each: {id, title, score, savings_ms, savings_bytes, items: [{url, totalBytes, wastedBytes, wastedMs, ...}]}

    # Diagnostics
    diagnostics: list[dict] = field(default_factory=list)
    # Each: {id, title, score, displayValue, details}

    # LCP element details
    lcp_element: Optional[dict] = None  # {selector, snippet, nodeLabel, boundingRect, lhId}

    # CLS elements
    cls_elements: list[dict] = field(default_factory=list)

    # Detected technology stacks
    stack_packs: list[dict] = field(default_factory=list)  # [{id, title, descriptions}]

    # Entities (third parties)
    entities: list[dict] = field(default_factory=list)

    # Screenshots
    final_screenshot: Optional[str] = None  # base64
    filmstrip_frames: list[dict] = field(default_factory=list)  # [{timing, data}]
    full_page_screenshot: Optional[str] = None  # base64
    screenshot_nodes: dict = field(default_factory=dict)  # {lhId: {left, top, width, height}}

    # Page stats
    page_stats: dict = field(default_factory=dict)
    # {numRequests, totalByteWeight, numScripts, numStylesheets, numFonts, ...}

    # Resource summary
    resource_summary: list[dict] = field(default_factory=list)
    # [{resourceType, requestCount, transferSize}]

    # Third party summary
    third_party_summary: list[dict] = field(default_factory=list)

    # Network requests (for resource analysis)
    network_requests: list[dict] = field(default_factory=list)

    # Raw response for debug
    raw_response: Optional[dict] = None


# Opportunity audit IDs to check
OPPORTUNITY_AUDIT_IDS = [
    "render-blocking-resources",
    "unused-javascript",
    "unused-css-rules",
    "offscreen-images",
    "modern-image-formats",
    "uses-responsive-images",
    "unminified-css",
    "unminified-javascript",
    "uses-text-compression",
    "uses-optimized-images",
    "server-response-time",
    "efficient-animated-content",
    "total-byte-weight",
    "uses-long-cache-ttl",
    "dom-size",
    "redirects",
    "uses-rel-preconnect",
    "uses-rel-preload",
    "font-display",
    "critical-request-chains",
    "largest-contentful-paint-element",
    "layout-shift-elements",
    "third-party-summary",
    "bootup-time",
    "mainthread-work-breakdown",
    "duplicated-javascript",
    "legacy-javascript",
    "viewport",
    "document-title",
    "image-aspect-ratio",
    "image-size-responsive",
    "efficiently-encode-images",
    "preload-lcp-image",
]

# Diagnostic audit IDs
DIAGNOSTIC_AUDIT_IDS = [
    "dom-size",
    "bootup-time",
    "mainthread-work-breakdown",
    "third-party-summary",
    "third-party-facades",
    "font-display",
    "critical-request-chains",
    "long-tasks",
    "non-composited-animations",
    "unsized-images",
    "uses-http2",
    "lcp-lazy-loaded",
    "no-document-write",
    "uses-passive-event-listeners",
    "prioritize-lcp-image",
    "viewport",
    "total-byte-weight",
]


class PageSpeedClient:
    """Google PageSpeed Insights API v5 client."""

    API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def analyze(self, url: str, strategy: str = "mobile") -> PSIResult:
        """Analyze a URL with PSI API.

        Args:
            url: The URL to analyze.
            strategy: "mobile" or "desktop".

        Returns:
            PSIResult with all parsed data.
        """
        params = {
            "url": url,
            "strategy": strategy,
            "category": ["performance", "accessibility", "seo", "best-practices"],
            "key": self.api_key,
        }

        logger.info(f"Analyzing {url} with strategy={strategy}")
        data = self._make_request(params)

        return self._parse_response(data)

    def _make_request(self, params: dict, max_retries: int = 3) -> dict:
        """Make API request with exponential backoff."""
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.API_URL,
                    params=params,
                    timeout=90,
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError:
                if response.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Rate limited (429). Waiting {wait}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait)
                    continue
                elif response.status_code >= 500 and attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Server error ({response.status_code}). Waiting {wait}s before retry...")
                    time.sleep(wait)
                    continue
                else:
                    logger.error(f"HTTP error {response.status_code}: {response.text[:500]}")
                    raise
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Timeout on attempt {attempt + 1}. Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                logger.error("Max retries exceeded due to timeout")
                raise
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Connection error on attempt {attempt + 1}: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                raise

        raise Exception(f"Max retries ({max_retries}) exceeded for PSI API request")

    def _parse_response(self, data: dict) -> PSIResult:
        """Parse the full PSI API response into PSIResult."""
        result = PSIResult(raw_response=data)

        lr = data.get("lighthouseResult", {})
        audits = lr.get("audits", {})

        # ------------------------------------------------------------------
        # 1. Parse category scores
        # ------------------------------------------------------------------
        self._parse_scores(lr, result)

        # ------------------------------------------------------------------
        # 2. Parse field data (CrUX) from loadingExperience
        # ------------------------------------------------------------------
        self._parse_field_data(data, result)

        # ------------------------------------------------------------------
        # 3. Parse lab metrics from audits.metrics
        # ------------------------------------------------------------------
        self._parse_lab_metrics(audits, result)

        # ------------------------------------------------------------------
        # 4. Parse opportunity audits
        # ------------------------------------------------------------------
        self._parse_opportunities(audits, result)

        # ------------------------------------------------------------------
        # 5. Parse diagnostic audits
        # ------------------------------------------------------------------
        self._parse_diagnostics(audits, result)

        # ------------------------------------------------------------------
        # 6. Parse LCP element
        # ------------------------------------------------------------------
        self._parse_lcp_element(audits, result)

        # ------------------------------------------------------------------
        # 7. Parse CLS elements
        # ------------------------------------------------------------------
        self._parse_cls_elements(audits, result)

        # ------------------------------------------------------------------
        # 8. Parse stack packs
        # ------------------------------------------------------------------
        self._parse_stack_packs(lr, result)

        # ------------------------------------------------------------------
        # 9. Parse entities (third parties)
        # ------------------------------------------------------------------
        self._parse_entities(lr, result)

        # ------------------------------------------------------------------
        # 10. Parse screenshots (final, filmstrip, full-page)
        # ------------------------------------------------------------------
        self._parse_screenshots(lr, audits, result)

        # ------------------------------------------------------------------
        # 11. Parse page stats from audits.diagnostics
        # ------------------------------------------------------------------
        self._parse_page_stats(audits, result)

        # ------------------------------------------------------------------
        # 12. Parse resource summary
        # ------------------------------------------------------------------
        self._parse_resource_summary(audits, result)

        # ------------------------------------------------------------------
        # 13. Parse third party summary
        # ------------------------------------------------------------------
        self._parse_third_party_summary(audits, result)

        # ------------------------------------------------------------------
        # 14. Parse network requests
        # ------------------------------------------------------------------
        self._parse_network_requests(audits, result)

        return result

    # ======================================================================
    # Individual parsing methods
    # ======================================================================

    @staticmethod
    def _parse_scores(lr: dict, result: PSIResult) -> None:
        """Extract category scores (0-100) from lighthouseResult.categories."""
        categories = lr.get("categories", {})

        perf = categories.get("performance", {})
        if perf.get("score") is not None:
            result.performance_score = round(perf["score"] * 100)

        a11y = categories.get("accessibility", {})
        if a11y.get("score") is not None:
            result.accessibility_score = round(a11y["score"] * 100)

        seo = categories.get("seo", {})
        if seo.get("score") is not None:
            result.seo_score = round(seo["score"] * 100)

        bp = categories.get("best-practices", {})
        if bp.get("score") is not None:
            result.best_practices_score = round(bp["score"] * 100)

    @staticmethod
    def _parse_field_data(data: dict, result: PSIResult) -> None:
        """Extract CrUX field data from loadingExperience."""
        loading_exp = data.get("loadingExperience", {})
        metrics = loading_exp.get("metrics", {})

        if not metrics:
            result.field_data = None
            return

        field_data: dict = {
            "overall_category": loading_exp.get("overall_category", "NONE"),
        }

        crux_keys = {
            "LARGEST_CONTENTFUL_PAINT_MS": "lcp",
            "CUMULATIVE_LAYOUT_SHIFT_SCORE": "cls",
            "INTERACTION_TO_NEXT_PAINT": "inp",
            "FIRST_CONTENTFUL_PAINT_MS": "fcp",
            "EXPERIMENTAL_TIME_TO_FIRST_BYTE": "ttfb",
        }

        for crux_key, short_name in crux_keys.items():
            metric_data = metrics.get(crux_key)
            if metric_data is None:
                continue

            percentile = metric_data.get("percentile")
            category = metric_data.get("category")
            distributions = metric_data.get("distributions", [])

            # CLS percentile needs division by 100 to get the actual decimal value
            value = percentile
            if crux_key == "CUMULATIVE_LAYOUT_SHIFT_SCORE" and percentile is not None:
                value = percentile / 100

            field_data[short_name] = {
                "percentile": percentile,
                "value": value,
                "category": category,
                "distributions": distributions,
            }

        result.field_data = field_data

    @staticmethod
    def _parse_lab_metrics(audits: dict, result: PSIResult) -> None:
        """Extract consolidated lab metrics from audits.metrics.details.items[0]."""
        metrics_audit = audits.get("metrics", {})
        items = metrics_audit.get("details", {}).get("items", [])
        metrics_data = items[0] if items else {}

        result.lab_metrics = {
            "fcp_ms": metrics_data.get("firstContentfulPaint"),
            "lcp_ms": metrics_data.get("largestContentfulPaint"),
            "speed_index_ms": metrics_data.get("speedIndex"),
            "tbt_ms": metrics_data.get("totalBlockingTime"),
            "cls": metrics_data.get("cumulativeLayoutShift"),
            "tti_ms": metrics_data.get("interactive"),
        }

        # Also pull display values from the individual metric audits
        metric_audit_keys = {
            "first-contentful-paint": "fcp",
            "largest-contentful-paint": "lcp",
            "speed-index": "si",
            "total-blocking-time": "tbt",
            "cumulative-layout-shift": "cls",
            "interactive": "tti",
        }

        for audit_key, short_name in metric_audit_keys.items():
            audit = audits.get(audit_key, {})
            display_key = f"{short_name}_display"
            score_key = f"{short_name}_score"
            result.lab_metrics[display_key] = audit.get("displayValue")
            result.lab_metrics[score_key] = audit.get("score")

    @staticmethod
    def _parse_opportunities(audits: dict, result: PSIResult) -> None:
        """Extract opportunity audits where score < 1 and there are potential savings."""
        opportunities: list[dict] = []

        for audit_id in OPPORTUNITY_AUDIT_IDS:
            audit = audits.get(audit_id)
            if audit is None:
                continue

            score = audit.get("score")
            # Skip audits that passed (score == 1), are not applicable, or informational-only
            if score is None or score >= 1:
                continue

            details = audit.get("details", {})
            detail_type = details.get("type", "")

            # Only include audits that are opportunity or table type with items
            if detail_type not in ("opportunity", "table", "list", "criticalrequestchain", "debugdata", ""):
                continue

            raw_items = details.get("items", [])

            # Build parsed items list
            parsed_items: list[dict] = []
            for item in raw_items:
                parsed_item: dict = {}

                # Common fields
                if "url" in item:
                    parsed_item["url"] = item["url"]
                if "totalBytes" in item:
                    parsed_item["totalBytes"] = item["totalBytes"]
                if "wastedBytes" in item:
                    parsed_item["wastedBytes"] = item["wastedBytes"]
                if "wastedMs" in item:
                    parsed_item["wastedMs"] = item["wastedMs"]
                if "wastedPercent" in item:
                    parsed_item["wastedPercent"] = item["wastedPercent"]

                # Cache-specific fields
                if "cacheLifetimeMs" in item:
                    parsed_item["cacheLifetimeMs"] = item["cacheLifetimeMs"]
                if "cacheHitProbability" in item:
                    parsed_item["cacheHitProbability"] = item["cacheHitProbability"]

                # Script execution fields
                if "total" in item:
                    parsed_item["total"] = item["total"]
                if "scripting" in item:
                    parsed_item["scripting"] = item["scripting"]
                if "scriptParseCompile" in item:
                    parsed_item["scriptParseCompile"] = item["scriptParseCompile"]

                # Main thread breakdown fields
                if "group" in item:
                    parsed_item["group"] = item["group"]
                    parsed_item["groupLabel"] = item.get("groupLabel")
                    parsed_item["duration"] = item.get("duration")

                # Transfer/resource size
                if "transferSize" in item:
                    parsed_item["transferSize"] = item["transferSize"]
                if "resourceSize" in item:
                    parsed_item["resourceSize"] = item["resourceSize"]
                if "blockingTime" in item:
                    parsed_item["blockingTime"] = item["blockingTime"]
                if "mainThreadTime" in item:
                    parsed_item["mainThreadTime"] = item["mainThreadTime"]

                # Node/element info (for image audits, DOM-related audits)
                node = item.get("node")
                if node:
                    parsed_item["element"] = {
                        "selector": node.get("selector"),
                        "snippet": node.get("snippet"),
                        "nodeLabel": node.get("nodeLabel"),
                        "boundingRect": node.get("boundingRect"),
                        "lhId": node.get("lhId"),
                        "path": node.get("path"),
                    }

                # Entity info (for third-party audits)
                entity = item.get("entity")
                if entity:
                    parsed_item["entity"] = {
                        "text": entity.get("text"),
                        "url": entity.get("url"),
                        "type": entity.get("type"),
                    }

                # Sub-items (e.g., third-party breakdown)
                sub_items = item.get("subItems")
                if sub_items:
                    parsed_item["subItems"] = sub_items.get("items", [])

                # Statistic / value (dom-size audit uses these)
                if "statistic" in item:
                    parsed_item["statistic"] = item["statistic"]
                if "value" in item:
                    parsed_item["value"] = item["value"]

                parsed_items.append(parsed_item)

            opportunity = {
                "id": audit_id,
                "title": audit.get("title", ""),
                "description": audit.get("description", ""),
                "score": score,
                "displayValue": audit.get("displayValue"),
                "numericValue": audit.get("numericValue"),
                "numericUnit": audit.get("numericUnit"),
                "savings_ms": details.get("overallSavingsMs", 0) or 0,
                "savings_bytes": details.get("overallSavingsBytes", 0) or 0,
                "items": parsed_items,
            }

            opportunities.append(opportunity)

        # Sort by savings: ms first, then bytes
        opportunities.sort(
            key=lambda x: (x["savings_ms"], x["savings_bytes"]),
            reverse=True,
        )

        result.opportunities = opportunities

    @staticmethod
    def _parse_diagnostics(audits: dict, result: PSIResult) -> None:
        """Extract diagnostic audits that failed (score < 1)."""
        diagnostics: list[dict] = []

        for audit_id in DIAGNOSTIC_AUDIT_IDS:
            audit = audits.get(audit_id)
            if audit is None:
                continue

            score = audit.get("score")
            # Include diagnostics with a failing score or null score (informative)
            if score is not None and score >= 1:
                continue

            details = audit.get("details", {})

            diagnostic = {
                "id": audit_id,
                "title": audit.get("title", ""),
                "description": audit.get("description", ""),
                "score": score,
                "displayValue": audit.get("displayValue"),
                "numericValue": audit.get("numericValue"),
                "numericUnit": audit.get("numericUnit"),
                "items": details.get("items", []),
                "detail_type": details.get("type"),
            }

            diagnostics.append(diagnostic)

        result.diagnostics = diagnostics

    @staticmethod
    def _parse_lcp_element(audits: dict, result: PSIResult) -> None:
        """Extract LCP element details from largest-contentful-paint-element audit."""
        lcp_audit = audits.get("largest-contentful-paint-element", {})
        items = lcp_audit.get("details", {}).get("items", [])

        if not items:
            result.lcp_element = None
            return

        # The first item may contain nested items or be the node directly
        first_item = items[0]

        # Try to find the node in the first item or its sub-items
        node = first_item.get("node")
        if node:
            result.lcp_element = {
                "selector": node.get("selector"),
                "snippet": node.get("snippet"),
                "nodeLabel": node.get("nodeLabel"),
                "boundingRect": node.get("boundingRect"),
                "lhId": node.get("lhId"),
                "path": node.get("path"),
            }
            return

        # Some versions nest items inside the first item
        sub_items = first_item.get("items", [])
        for sub in sub_items:
            node = sub.get("node")
            if node:
                result.lcp_element = {
                    "selector": node.get("selector"),
                    "snippet": node.get("snippet"),
                    "nodeLabel": node.get("nodeLabel"),
                    "boundingRect": node.get("boundingRect"),
                    "lhId": node.get("lhId"),
                    "path": node.get("path"),
                }
                return

        # If there are multiple items with phase/timing info (LH 13+ format),
        # look through all of them for a node
        for item in items:
            node = item.get("node")
            if node:
                result.lcp_element = {
                    "selector": node.get("selector"),
                    "snippet": node.get("snippet"),
                    "nodeLabel": node.get("nodeLabel"),
                    "boundingRect": node.get("boundingRect"),
                    "lhId": node.get("lhId"),
                    "path": node.get("path"),
                }
                return

        result.lcp_element = None

    @staticmethod
    def _parse_cls_elements(audits: dict, result: PSIResult) -> None:
        """Extract CLS culprit elements from layout-shift-elements audit."""
        cls_audit = audits.get("layout-shift-elements", {})
        items = cls_audit.get("details", {}).get("items", [])

        cls_elements: list[dict] = []
        for item in items:
            node = item.get("node", {})
            element = {
                "selector": node.get("selector"),
                "snippet": node.get("snippet"),
                "nodeLabel": node.get("nodeLabel"),
                "boundingRect": node.get("boundingRect"),
                "lhId": node.get("lhId"),
                "path": node.get("path"),
                "cls_contribution": item.get("score"),
            }
            cls_elements.append(element)

        result.cls_elements = cls_elements

    @staticmethod
    def _parse_stack_packs(lr: dict, result: PSIResult) -> None:
        """Extract detected technology stack packs."""
        raw_packs = lr.get("stackPacks", [])

        stack_packs: list[dict] = []
        for pack in raw_packs:
            stack_packs.append({
                "id": pack.get("id"),
                "title": pack.get("title"),
                "iconDataURL": pack.get("iconDataURL"),
                "descriptions": pack.get("descriptions", {}),
            })

        result.stack_packs = stack_packs

    @staticmethod
    def _parse_entities(lr: dict, result: PSIResult) -> None:
        """Extract entity classification (first-party and third-party origins)."""
        raw_entities = lr.get("entities", [])

        entities: list[dict] = []
        for entity in raw_entities:
            entities.append({
                "name": entity.get("name"),
                "isFirstParty": entity.get("isFirstParty", False),
                "isUnrecognized": entity.get("isUnrecognized", False),
                "origins": entity.get("origins", []),
                "homepage": entity.get("homepage"),
                "category": entity.get("category"),
            })

        result.entities = entities

    @staticmethod
    def _parse_screenshots(lr: dict, audits: dict, result: PSIResult) -> None:
        """Extract final screenshot, filmstrip, and full-page screenshot data."""
        # Final screenshot
        final_ss = audits.get("final-screenshot", {}).get("details", {})
        result.final_screenshot = final_ss.get("data")

        # Filmstrip (screenshot thumbnails)
        filmstrip_audit = audits.get("screenshot-thumbnails", {}).get("details", {})
        raw_frames = filmstrip_audit.get("items", [])
        result.filmstrip_frames = [
            {
                "timing": frame.get("timing"),
                "timestamp": frame.get("timestamp"),
                "data": frame.get("data"),
            }
            for frame in raw_frames
        ]

        # Full page screenshot
        fps = lr.get("fullPageScreenshot", {})
        screenshot_obj = fps.get("screenshot", {})
        result.full_page_screenshot = screenshot_obj.get("data")

        # Screenshot node positions (lhId -> bounding rect)
        raw_nodes = fps.get("nodes", {})
        result.screenshot_nodes = {}
        for lh_id, node_rect in raw_nodes.items():
            result.screenshot_nodes[lh_id] = {
                "top": node_rect.get("top", 0),
                "bottom": node_rect.get("bottom", 0),
                "left": node_rect.get("left", 0),
                "right": node_rect.get("right", 0),
                "width": node_rect.get("width", 0),
                "height": node_rect.get("height", 0),
            }

    @staticmethod
    def _parse_page_stats(audits: dict, result: PSIResult) -> None:
        """Extract aggregated page statistics from audits.diagnostics."""
        diag_audit = audits.get("diagnostics", {})
        items = diag_audit.get("details", {}).get("items", [])
        ds = items[0] if items else {}

        result.page_stats = {
            "numRequests": ds.get("numRequests"),
            "totalByteWeight": ds.get("totalByteWeight"),
            "numScripts": ds.get("numScripts"),
            "numStylesheets": ds.get("numStylesheets"),
            "numFonts": ds.get("numFonts"),
            "numTasks": ds.get("numTasks"),
            "numTasksOver50ms": ds.get("numTasksOver50ms"),
            "totalTaskTime": ds.get("totalTaskTime"),
            "maxRtt": ds.get("maxRtt"),
            "maxServerLatency": ds.get("maxServerLatency"),
            "throughput": ds.get("throughput"),
        }

    @staticmethod
    def _parse_resource_summary(audits: dict, result: PSIResult) -> None:
        """Extract resource summary by type from resource-summary audit."""
        res_audit = audits.get("resource-summary", {})
        items = res_audit.get("details", {}).get("items", [])

        result.resource_summary = [
            {
                "resourceType": item.get("resourceType"),
                "label": item.get("label"),
                "requestCount": item.get("requestCount"),
                "transferSize": item.get("transferSize"),
            }
            for item in items
        ]

    @staticmethod
    def _parse_third_party_summary(audits: dict, result: PSIResult) -> None:
        """Extract third-party impact summary from third-party-summary audit."""
        tp_audit = audits.get("third-party-summary", {})
        items = tp_audit.get("details", {}).get("items", [])

        third_parties: list[dict] = []
        for item in items:
            entity = item.get("entity", {})
            tp_entry = {
                "entity_name": entity.get("text") if isinstance(entity, dict) else str(entity),
                "entity_url": entity.get("url") if isinstance(entity, dict) else None,
                "transferSize": item.get("transferSize"),
                "blockingTime": item.get("blockingTime"),
                "mainThreadTime": item.get("mainThreadTime"),
            }

            # Include sub-item resource URLs if present
            sub_items = item.get("subItems", {})
            if isinstance(sub_items, dict):
                sub_list = sub_items.get("items", [])
            else:
                sub_list = []

            tp_entry["resources"] = [
                {
                    "url": si.get("url"),
                    "transferSize": si.get("transferSize"),
                    "blockingTime": si.get("blockingTime"),
                    "mainThreadTime": si.get("mainThreadTime"),
                }
                for si in sub_list
            ]

            third_parties.append(tp_entry)

        result.third_party_summary = third_parties

    @staticmethod
    def _parse_network_requests(audits: dict, result: PSIResult) -> None:
        """Extract all network requests from network-requests audit."""
        nr_audit = audits.get("network-requests", {})
        items = nr_audit.get("details", {}).get("items", [])

        result.network_requests = [
            {
                "url": item.get("url"),
                "protocol": item.get("protocol"),
                "startTime": item.get("startTime"),
                "endTime": item.get("endTime"),
                "transferSize": item.get("transferSize"),
                "resourceSize": item.get("resourceSize"),
                "statusCode": item.get("statusCode"),
                "mimeType": item.get("mimeType"),
                "resourceType": item.get("resourceType"),
                "priority": item.get("priority"),
                "experimentalFromMainFrame": item.get("experimentalFromMainFrame"),
            }
            for item in items
        ]
