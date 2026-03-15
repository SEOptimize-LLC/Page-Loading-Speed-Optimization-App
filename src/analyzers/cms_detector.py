"""Detects CMS type by combining multiple signals from PSI and HTML analysis."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CMSDetector:
    """Detects CMS type from PSI and HTML analysis data."""

    # Known Shopify app script patterns
    SHOPIFY_APP_DOMAINS = [
        "judge.me", "loox.io", "stamped.io", "yotpo.com", "klaviyo.com",
        "privy.com", "omnisend.com", "smile.io", "rechargeapps.com",
        "bold.co", "pagefly.io", "shogun.io", "gempages.net",
        "tidio.co", "gorgias.com", "zendesk.com",
    ]

    # Known WordPress plugin patterns in URLs
    WP_PLUGIN_PATTERNS = [
        ("elementor", "Elementor"),
        ("wpbakery", "WPBakery"),
        ("divi", "Divi"),
        ("woocommerce", "WooCommerce"),
        ("yoast", "Yoast SEO"),
        ("rank-math", "Rank Math"),
        ("wpforms", "WPForms"),
        ("contact-form-7", "Contact Form 7"),
        ("jetpack", "Jetpack"),
        ("wordfence", "Wordfence"),
        ("wp-rocket", "WP Rocket"),
        ("autoptimize", "Autoptimize"),
        ("w3-total-cache", "W3 Total Cache"),
        ("litespeed-cache", "LiteSpeed Cache"),
        ("wp-super-cache", "WP Super Cache"),
        ("revslider", "Revolution Slider"),
        ("gravityforms", "Gravity Forms"),
    ]

    # CMS indicators found in network request URLs
    CMS_URL_INDICATORS = {
        "wordpress": ["/wp-content/", "/wp-includes/", "/wp-admin/", "/wp-json/"],
        "shopify": [".myshopify.com", "cdn.shopify.com", "/shopify/"],
        "wix": ["static.wixstatic.com", "parastorage.com", "wix.com"],
        "squarespace": ["static1.squarespace.com", "squarespace.com/assets"],
        "webflow": ["assets.website-files.com", "webflow.com"],
        "drupal": ["/sites/default/files/", "/modules/", "/core/misc/drupal.js"],
        "joomla": ["/media/system/", "/components/com_"],
        "magento": ["/static/version", "/media/catalog/", "mage/"],
    }

    def detect(
        self,
        stack_packs: list[dict],
        network_requests: list[dict],
        entities: list[dict],
        html_cms: Optional[str],
        html_cms_signals: list[str],
    ) -> dict:
        """Detect CMS and return CMSInfo-compatible dict.

        Args:
            stack_packs: From PSI lighthouseResult.stackPacks
            network_requests: From PSI network-requests audit
            entities: From PSI lighthouseResult.entities
            html_cms: CMS detected from HTML analysis
            html_cms_signals: Signals found in HTML

        Returns:
            dict with keys: name, confidence, detected_plugins, detected_apps, stack_packs
        """
        signals: list[dict] = []  # {source, cms, confidence_boost}
        pack_titles: list[str] = []

        # --- Signal 1: PSI stack packs (highest confidence) ---
        for pack in stack_packs:
            pack_id = pack.get("id", "").lower()
            pack_title = pack.get("title", pack_id)
            pack_titles.append(pack_title)

            if pack_id == "wordpress":
                signals.append({"source": "stack_pack", "cms": "wordpress", "confidence_boost": 40})
            elif pack_id == "drupal":
                signals.append({"source": "stack_pack", "cms": "drupal", "confidence_boost": 40})
            elif pack_id == "magento":
                signals.append({"source": "stack_pack", "cms": "magento", "confidence_boost": 40})
            elif pack_id == "wp-rocket":
                # WP Rocket is WordPress-only, so it implies WordPress
                signals.append({"source": "stack_pack_wp_rocket", "cms": "wordpress", "confidence_boost": 30})

        # --- Signal 2: Network request URLs ---
        request_urls = [req.get("url", "") for req in network_requests]
        cms_url_hits: dict[str, int] = {}

        for url in request_urls:
            url_lower = url.lower()
            for cms, patterns in self.CMS_URL_INDICATORS.items():
                if any(pattern in url_lower for pattern in patterns):
                    cms_url_hits[cms] = cms_url_hits.get(cms, 0) + 1

        for cms, hit_count in cms_url_hits.items():
            # More hits = stronger signal; cap the confidence boost
            boost = min(30, 10 + hit_count * 2)
            signals.append({"source": "network_urls", "cms": cms, "confidence_boost": boost})

        # --- Signal 3: Entities ---
        for entity in entities:
            entity_name = entity.get("name", "").lower()
            entity_origins = [o.lower() for o in entity.get("origins", [])]
            all_text = entity_name + " " + " ".join(entity_origins)

            if "shopify" in all_text:
                signals.append({"source": "entity", "cms": "shopify", "confidence_boost": 25})
            elif "squarespace" in all_text:
                signals.append({"source": "entity", "cms": "squarespace", "confidence_boost": 25})
            elif "wix" in all_text:
                signals.append({"source": "entity", "cms": "wix", "confidence_boost": 25})
            elif "wordpress" in all_text or "wp.com" in all_text:
                signals.append({"source": "entity", "cms": "wordpress", "confidence_boost": 20})

        # --- Signal 4: HTML analysis results ---
        if html_cms:
            html_cms_lower = html_cms.lower()
            # HTML meta generator tags are very reliable
            boost = 35 if len(html_cms_signals) >= 2 else 25
            signals.append({"source": "html_analysis", "cms": html_cms_lower, "confidence_boost": boost})

        # --- Aggregate signals to find the best CMS candidate ---
        if not signals:
            logger.info("No CMS signals detected; returning unknown")
            return {
                "name": "unknown",
                "confidence": "low",
                "detected_plugins": [],
                "detected_apps": [],
                "stack_packs": pack_titles,
            }

        cms_scores: dict[str, float] = {}
        for signal in signals:
            cms = signal["cms"]
            cms_scores[cms] = cms_scores.get(cms, 0) + signal["confidence_boost"]

        best_cms = max(cms_scores, key=cms_scores.get)  # type: ignore[arg-type]
        best_score = cms_scores[best_cms]

        # Map aggregate score to confidence level
        if best_score >= 50:
            confidence = "high"
        elif best_score >= 25:
            confidence = "medium"
        else:
            confidence = "low"

        logger.info(
            "CMS detected: %s (confidence=%s, score=%.0f, signals=%d)",
            best_cms, confidence, best_score, len(signals),
        )

        # --- Detect plugins (WordPress) or apps (Shopify) ---
        detected_plugins: list[str] = []
        detected_apps: list[str] = []

        if best_cms == "wordpress":
            detected_plugins = self._detect_wp_plugins(request_urls)
        elif best_cms == "shopify":
            detected_apps = self._detect_shopify_apps(request_urls, entities)

        return {
            "name": best_cms,
            "confidence": confidence,
            "detected_plugins": detected_plugins,
            "detected_apps": detected_apps,
            "stack_packs": pack_titles,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_wp_plugins(self, request_urls: list[str]) -> list[str]:
        """Scan network request URLs for known WordPress plugin patterns.

        Returns a deduplicated list of detected plugin names.
        """
        found: set[str] = set()
        for url in request_urls:
            url_lower = url.lower()
            # Most WP plugins serve assets from /wp-content/plugins/<slug>/
            if "/wp-content/plugins/" in url_lower:
                # Extract plugin slug from the path
                try:
                    after = url_lower.split("/wp-content/plugins/")[1]
                    slug = after.split("/")[0]
                    if slug:
                        # Try to match against known patterns for a friendly name
                        friendly = self._match_wp_plugin_name(slug)
                        found.add(friendly)
                except (IndexError, ValueError):
                    pass

            # Also check for known plugin patterns anywhere in the URL
            for pattern, name in self.WP_PLUGIN_PATTERNS:
                if pattern in url_lower:
                    found.add(name)

        plugins = sorted(found)
        if plugins:
            logger.debug("Detected WordPress plugins: %s", plugins)
        return plugins

    def _match_wp_plugin_name(self, slug: str) -> str:
        """Try to match a plugin slug to a known friendly name.

        Falls back to a title-cased version of the slug itself.
        """
        slug_lower = slug.lower()
        for pattern, name in self.WP_PLUGIN_PATTERNS:
            if pattern in slug_lower:
                return name
        # Fallback: convert slug to a readable name
        return slug.replace("-", " ").replace("_", " ").title()

    def _detect_shopify_apps(
        self, request_urls: list[str], entities: list[dict]
    ) -> list[str]:
        """Scan network requests and entities for known Shopify app domains.

        Returns a deduplicated list of detected app names.
        """
        found: set[str] = set()

        # Check network request URLs against known Shopify app domains
        for url in request_urls:
            url_lower = url.lower()
            for domain in self.SHOPIFY_APP_DOMAINS:
                if domain in url_lower:
                    # Use the domain root as the app name
                    app_name = domain.split(".")[0].title()
                    found.add(app_name)

        # Check entities for Shopify app providers
        for entity in entities:
            entity_name = entity.get("name", "").lower()
            entity_origins = [o.lower() for o in entity.get("origins", [])]
            combined = entity_name + " " + " ".join(entity_origins)

            for domain in self.SHOPIFY_APP_DOMAINS:
                if domain in combined:
                    app_name = domain.split(".")[0].title()
                    found.add(app_name)

        apps = sorted(found)
        if apps:
            logger.debug("Detected Shopify apps: %s", apps)
        return apps
