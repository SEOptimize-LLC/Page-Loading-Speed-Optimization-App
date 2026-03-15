"""Analyzes network requests and resource distribution from PSI data.

Breaks down resources by type, identifies the largest payloads,
quantifies third-party impact, and flags compression / caching gaps.
"""

import logging
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Text-based MIME types that should benefit from compression (gzip / brotli)
COMPRESSIBLE_MIME_PREFIXES = (
    "text/",
    "application/javascript",
    "application/x-javascript",
    "application/json",
    "application/xml",
    "application/xhtml+xml",
    "application/rss+xml",
    "application/atom+xml",
    "image/svg+xml",
    "application/ld+json",
    "application/manifest+json",
)

# Minimum cache lifetime considered acceptable (24 hours in milliseconds)
MIN_CACHE_LIFETIME_MS = 86_400_000  # 24 h

# Resource type normalisation map (PSI resourceType -> our canonical name)
RESOURCE_TYPE_MAP = {
    "script": "scripts",
    "stylesheet": "stylesheets",
    "image": "images",
    "font": "fonts",
    "document": "documents",
    "media": "media",
    "xhr": "xhr",
    "fetch": "xhr",
    "other": "other",
}


class ResourceAnalyzer:
    """Analyzes network requests and resource distribution."""

    def analyze(
        self,
        network_requests: list[dict],
        resource_summary: list[dict],
        third_party_summary: list[dict],
        page_url: str,
    ) -> dict:
        """Analyze resources and return a comprehensive summary.

        Args:
            network_requests: Items from the PSI ``network-requests`` audit.
                Each item has keys like ``url``, ``transferSize``,
                ``resourceSize``, ``mimeType``, ``resourceType``, and
                optionally ``cache-lifetime-ms``, ``protocol``, ``statusCode``.
            resource_summary: Items from the PSI ``resource-summary`` audit
                (aggregated by type).
            third_party_summary: Items from the PSI ``third-party-summary``
                audit (grouped by third-party entity).
            page_url: The URL of the analyzed page (used for first-party /
                third-party classification).

        Returns:
            dict with keys:
                largest_resources, resource_breakdown, third_party_impact,
                uncompressed_resources, poor_cache_resources,
                critical_chain_depth, total_requests, total_transfer_size.
        """
        page_domain = self._extract_root_domain(page_url)

        # ------------------------------------------------------------------
        # 1. Largest resources (top 10 by transferSize)
        # ------------------------------------------------------------------
        sorted_by_size = sorted(
            network_requests,
            key=lambda r: r.get("transferSize", 0) or 0,
            reverse=True,
        )

        largest_resources: list[dict] = []
        for req in sorted_by_size[:10]:
            url = req.get("url", "")
            transfer_size = req.get("transferSize", 0) or 0
            resource_type = self._normalise_resource_type(req)
            is_third_party = self._is_third_party(url, page_domain)

            largest_resources.append({
                "url": url,
                "type": resource_type,
                "size_bytes": transfer_size,
                "is_third_party": is_third_party,
            })

        # ------------------------------------------------------------------
        # 2. Resource breakdown by type
        # ------------------------------------------------------------------
        breakdown: dict[str, int] = {
            "images": 0,
            "scripts": 0,
            "stylesheets": 0,
            "fonts": 0,
            "documents": 0,
            "media": 0,
            "xhr": 0,
            "other": 0,
        }

        for req in network_requests:
            rtype = self._normalise_resource_type(req)
            transfer = req.get("transferSize", 0) or 0
            if rtype in breakdown:
                breakdown[rtype] += transfer
            else:
                breakdown["other"] += transfer

        # ------------------------------------------------------------------
        # 3. Third-party impact
        # ------------------------------------------------------------------
        third_party_impact = self._analyze_third_parties(
            third_party_summary, network_requests, page_domain
        )

        # ------------------------------------------------------------------
        # 4. Uncompressed text resources
        # ------------------------------------------------------------------
        uncompressed_resources = self._find_uncompressed(network_requests)

        # ------------------------------------------------------------------
        # 5. Poorly-cached resources
        # ------------------------------------------------------------------
        poor_cache_resources = self._find_poor_cache(network_requests)

        # ------------------------------------------------------------------
        # 6. Total requests and transfer size
        # ------------------------------------------------------------------
        total_requests = len(network_requests)
        total_transfer_size = sum(
            (r.get("transferSize", 0) or 0) for r in network_requests
        )

        # ------------------------------------------------------------------
        # 7. Critical chain depth (estimated from request waterfall)
        # ------------------------------------------------------------------
        critical_chain_depth = self._estimate_critical_chain_depth(network_requests)

        result = {
            "largest_resources": largest_resources,
            "resource_breakdown": breakdown,
            "third_party_impact": third_party_impact,
            "uncompressed_resources": uncompressed_resources,
            "poor_cache_resources": poor_cache_resources,
            "critical_chain_depth": critical_chain_depth,
            "total_requests": total_requests,
            "total_transfer_size": total_transfer_size,
        }

        logger.info(
            "Resource analysis complete: %d requests, %d bytes total, "
            "%d third-party domains, %d uncompressed, %d poorly cached",
            total_requests,
            total_transfer_size,
            len(third_party_impact),
            len(uncompressed_resources),
            len(poor_cache_resources),
        )

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_root_domain(url: str) -> str:
        """Extract the registrable (root) domain from a URL.

        For example, ``https://www.shop.example.com/page`` yields
        ``example.com``.  This is a best-effort heuristic that keeps the
        last two domain segments (or three when the second-level domain is a
        known country-code SLD like ``co.uk``).
        """
        try:
            hostname = urlparse(url).hostname or ""
        except Exception:
            return ""

        parts = hostname.lower().split(".")
        if len(parts) <= 2:
            return hostname.lower()

        # Handle common two-part TLDs (co.uk, com.au, co.nz, etc.)
        known_two_part_tlds = {
            "co.uk", "com.au", "co.nz", "co.jp", "com.br",
            "co.kr", "co.in", "com.sg", "com.mx", "co.za",
        }
        last_two = ".".join(parts[-2:])
        if last_two in known_two_part_tlds and len(parts) >= 3:
            return ".".join(parts[-3:])

        return ".".join(parts[-2:])

    def _is_third_party(self, url: str, page_domain: str) -> bool:
        """Determine if a URL belongs to a third party relative to the page."""
        try:
            hostname = urlparse(url).hostname or ""
        except Exception:
            return True

        request_domain = self._extract_root_domain(url)
        return request_domain != page_domain

    @staticmethod
    def _normalise_resource_type(request: dict) -> str:
        """Return a canonical resource type string from a network request.

        Uses ``resourceType`` first, falling back to ``mimeType`` heuristics.
        """
        rtype = (request.get("resourceType") or "").lower()
        if rtype in RESOURCE_TYPE_MAP:
            return RESOURCE_TYPE_MAP[rtype]

        # Fallback: infer from mimeType
        mime = (request.get("mimeType") or "").lower()
        if "javascript" in mime or "ecmascript" in mime:
            return "scripts"
        if "css" in mime:
            return "stylesheets"
        if mime.startswith("image/"):
            return "images"
        if mime.startswith("font/") or "woff" in mime or "opentype" in mime:
            return "fonts"
        if mime.startswith("text/html") or mime.startswith("application/xhtml"):
            return "documents"
        if mime.startswith("video/") or mime.startswith("audio/"):
            return "media"
        if "json" in mime or "xml" in mime:
            return "xhr"

        return "other"

    def _analyze_third_parties(
        self,
        third_party_summary: list[dict],
        network_requests: list[dict],
        page_domain: str,
    ) -> list[dict]:
        """Build a list of third-party impacts grouped by domain.

        Prefers data from the PSI ``third-party-summary`` audit when
        available.  Falls back to aggregating from raw network requests.

        Returns:
            List of dicts with keys: domain, transfer_size, blocking_time,
            request_count.
        """
        # Prefer the curated PSI third-party-summary if present
        if third_party_summary:
            results: list[dict] = []
            for tp in third_party_summary:
                entity = tp.get("entity", {})
                entity_name = entity.get("text", "") if isinstance(entity, dict) else str(entity)
                transfer_size = tp.get("transferSize", 0) or 0
                blocking_time = tp.get("blockingTime", 0) or 0

                # Count sub-items for request count
                sub_items = tp.get("subItems", {}).get("items", [])
                request_count = len(sub_items) if sub_items else 1

                results.append({
                    "domain": entity_name,
                    "transfer_size": transfer_size,
                    "blocking_time": blocking_time,
                    "request_count": request_count,
                })

            # Sort by blocking_time descending (most impactful first)
            results.sort(key=lambda x: x["blocking_time"], reverse=True)
            return results

        # Fallback: aggregate from network requests
        domain_data: dict[str, dict] = {}
        for req in network_requests:
            url = req.get("url", "")
            if not self._is_third_party(url, page_domain):
                continue

            try:
                hostname = urlparse(url).hostname or "unknown"
            except Exception:
                hostname = "unknown"

            root = self._extract_root_domain(url)
            key = root or hostname

            if key not in domain_data:
                domain_data[key] = {
                    "domain": key,
                    "transfer_size": 0,
                    "blocking_time": 0,
                    "request_count": 0,
                }

            domain_data[key]["transfer_size"] += req.get("transferSize", 0) or 0
            domain_data[key]["request_count"] += 1

        results = list(domain_data.values())
        results.sort(key=lambda x: x["transfer_size"], reverse=True)
        return results

    @staticmethod
    def _find_uncompressed(network_requests: list[dict]) -> list[dict]:
        """Identify text-based resources that appear to lack compression.

        A resource is flagged if it has a compressible MIME type AND its
        ``transferSize`` is at least 90 % of ``resourceSize`` AND the
        resource is larger than 1 KB (to avoid noise from tiny files).

        Returns:
            List of dicts with keys: url, size_bytes, type.
        """
        uncompressed: list[dict] = []

        for req in network_requests:
            mime = (req.get("mimeType") or "").lower()
            if not any(mime.startswith(prefix) for prefix in COMPRESSIBLE_MIME_PREFIXES):
                continue

            transfer = req.get("transferSize", 0) or 0
            resource = req.get("resourceSize", 0) or 0

            # Skip tiny resources
            if resource < 1024:
                continue

            # If transfer is at least 90% of resource size, compression is
            # likely missing or ineffective.  (Well-compressed text is
            # typically 20-40% of the original.)
            if transfer > 0 and resource > 0 and transfer >= resource * 0.90:
                rtype = (req.get("resourceType") or "unknown").lower()
                uncompressed.append({
                    "url": req.get("url", ""),
                    "size_bytes": resource,
                    "type": rtype,
                })

        # Sort largest first
        uncompressed.sort(key=lambda x: x["size_bytes"], reverse=True)
        return uncompressed

    @staticmethod
    def _find_poor_cache(network_requests: list[dict]) -> list[dict]:
        """Identify resources with a cache lifetime below 24 hours.

        Skips the main document (HTML) since it is expected to have a short
        or zero cache lifetime.

        Returns:
            List of dicts with keys: url, cache_lifetime, size_bytes.
        """
        poor_cache: list[dict] = []

        for req in network_requests:
            rtype = (req.get("resourceType") or "").lower()
            # Skip HTML documents; short caching is expected
            if rtype == "document":
                continue

            cache_ms = req.get("cache-lifetime-ms")
            if cache_ms is None:
                # No cache information available; skip (we can't flag it)
                continue

            cache_ms = int(cache_ms)
            transfer = req.get("transferSize", 0) or 0

            # Only flag resources with meaningful size (> 1 KB)
            if transfer < 1024:
                continue

            if cache_ms < MIN_CACHE_LIFETIME_MS:
                poor_cache.append({
                    "url": req.get("url", ""),
                    "cache_lifetime": cache_ms,
                    "size_bytes": transfer,
                })

        # Sort by size descending (biggest waste of re-downloading first)
        poor_cache.sort(key=lambda x: x["size_bytes"], reverse=True)
        return poor_cache

    @staticmethod
    def _estimate_critical_chain_depth(network_requests: list[dict]) -> int:
        """Estimate the depth of the critical request chain.

        Uses a simple heuristic: count the maximum number of sequential
        requests that overlap on the timeline during the first 3 seconds
        of page load, filtering to render-critical types (Document,
        Stylesheet, Script, Font).

        This is an approximation. The PSI ``critical-request-chains`` audit
        provides the authoritative chain, but its deeply-nested structure
        varies across Lighthouse versions, so we compute a practical proxy
        here.
        """
        critical_types = {"document", "stylesheet", "script", "font"}

        # Filter to critical resource types in the first 3 seconds
        critical_requests = []
        for req in network_requests:
            rtype = (req.get("resourceType") or "").lower()
            if rtype not in critical_types:
                continue
            start = req.get("startTime", 0) or 0
            if start > 3000:
                continue
            end = req.get("endTime", start) or start
            critical_requests.append({"start": start, "end": end})

        if not critical_requests:
            return 0

        # Sort by start time
        critical_requests.sort(key=lambda r: r["start"])

        # Walk through requests and count chain depth.
        # A new chain link starts when a request begins after (or very close to)
        # the end of a previous one, indicating a dependency.
        depth = 1
        chain_end = critical_requests[0]["end"]

        for req in critical_requests[1:]:
            # If this request starts after (or within 50ms of) the previous
            # chain's end, it may be a dependent request; extend the chain.
            if req["start"] >= chain_end - 50:
                depth += 1
                chain_end = req["end"]
            else:
                # Parallel request; update chain_end if this one finishes later
                chain_end = max(chain_end, req["end"])

        return depth
