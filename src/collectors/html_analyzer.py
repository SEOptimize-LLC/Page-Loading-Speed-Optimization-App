"""Fetches raw HTML and analyzes it for performance issues that PSI may not catch."""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


@dataclass
class HTMLFinding:
    """A single finding from HTML analysis."""

    finding_id: str
    category: str  # "images", "scripts", "styles", "fonts", "meta", "dom"
    description: str
    elements: list[dict] = field(default_factory=list)  # [{tag, attributes, snippet}]
    count: int = 0


@dataclass
class HTMLAnalysis:
    """Complete HTML analysis result."""

    url: str
    html_size_bytes: int = 0
    dom_element_count: int = 0
    max_dom_depth: int = 0

    # CMS detection
    detected_cms: Optional[str] = None
    cms_signals: list[str] = field(default_factory=list)

    # Findings
    findings: list[HTMLFinding] = field(default_factory=list)

    # Raw counts
    total_images: int = 0
    total_scripts: int = 0
    total_stylesheets: int = 0
    total_inline_css_bytes: int = 0
    total_inline_js_bytes: int = 0

    # Resource hints
    preload_hints: list[str] = field(default_factory=list)
    preconnect_hints: list[str] = field(default_factory=list)
    prefetch_hints: list[str] = field(default_factory=list)

    # Third party domains
    third_party_domains: list[str] = field(default_factory=list)


class HTMLAnalyzer:
    """Analyzes raw HTML for performance issues."""

    USER_AGENT = (
        "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    )
    MAX_HTML_BYTES = 5 * 1024 * 1024  # 5 MB

    def analyze(self, url: str) -> HTMLAnalysis:
        """Fetch and analyze page HTML.

        Args:
            url: The page URL to fetch and analyze.

        Returns:
            HTMLAnalysis with all detected findings.
        """
        html = self._fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        result = HTMLAnalysis(url=url, html_size_bytes=len(html.encode("utf-8")))

        self._analyze_dom(soup, result)
        self._detect_cms(soup, html, url, result)
        self._analyze_images(soup, url, result)
        self._analyze_scripts(soup, url, result)
        self._analyze_styles(soup, result)
        self._analyze_fonts(soup, html, result)
        self._analyze_meta(soup, result)
        self._analyze_resource_hints(soup, result)
        self._analyze_third_parties(soup, url, result)

        return result

    # ------------------------------------------------------------------
    # Fetching
    # ------------------------------------------------------------------

    def _fetch_html(self, url: str) -> str:
        """Fetch HTML with a mobile User-Agent, following redirects.

        Enforces a 30-second timeout and a 5 MB maximum response size.
        """
        try:
            response = requests.get(
                url,
                headers={"User-Agent": self.USER_AGENT},
                timeout=30,
                allow_redirects=True,
                stream=True,
            )
            response.raise_for_status()

            # Read up to MAX_HTML_BYTES to avoid memory issues on very large pages
            chunks: list[bytes] = []
            total_read = 0
            for chunk in response.iter_content(chunk_size=8192):
                total_read += len(chunk)
                if total_read > self.MAX_HTML_BYTES:
                    logger.warning(
                        f"HTML response for {url} exceeds {self.MAX_HTML_BYTES} bytes; truncating"
                    )
                    chunks.append(chunk[: self.MAX_HTML_BYTES - (total_read - len(chunk))])
                    break
                chunks.append(chunk)

            raw = b"".join(chunks)

            # Attempt to decode using the response encoding, fall back to utf-8
            encoding = response.encoding or "utf-8"
            try:
                return raw.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                return raw.decode("utf-8", errors="replace")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch HTML for {url}: {e}")
            raise

    # ------------------------------------------------------------------
    # DOM analysis
    # ------------------------------------------------------------------

    def _analyze_dom(self, soup: BeautifulSoup, result: HTMLAnalysis) -> None:
        """Count total DOM elements and calculate maximum nesting depth."""
        all_tags = soup.find_all(True)
        result.dom_element_count = len(all_tags)

        # Calculate max nesting depth via iterative traversal
        max_depth = 0
        for tag in all_tags:
            depth = 0
            parent = tag.parent
            while parent and parent.name:
                depth += 1
                parent = parent.parent
            if depth > max_depth:
                max_depth = depth

        result.max_dom_depth = max_depth

        # Flag excessive DOM size
        if result.dom_element_count > 1500:
            result.findings.append(
                HTMLFinding(
                    finding_id="excessive-dom-size",
                    category="dom",
                    description=f"Page has {result.dom_element_count} DOM elements (recommended < 1,500).",
                    count=result.dom_element_count,
                )
            )

        if max_depth > 15:
            result.findings.append(
                HTMLFinding(
                    finding_id="deep-dom-nesting",
                    category="dom",
                    description=f"Maximum DOM depth is {max_depth} levels (recommended < 15).",
                    count=max_depth,
                )
            )

    # ------------------------------------------------------------------
    # CMS detection
    # ------------------------------------------------------------------

    def _detect_cms(
        self, soup: BeautifulSoup, html: str, url: str, result: HTMLAnalysis
    ) -> None:
        """Detect the CMS or platform powering the page."""
        signals: list[str] = []
        detected: Optional[str] = None

        # 1. Check <meta name="generator">
        generator_tag = soup.find("meta", attrs={"name": "generator"})
        if generator_tag and isinstance(generator_tag, Tag):
            content = (generator_tag.get("content") or "").lower()
            if "wordpress" in content:
                detected = "wordpress"
                signals.append(f'meta generator: {generator_tag.get("content")}')
            elif "drupal" in content:
                detected = "drupal"
                signals.append(f'meta generator: {generator_tag.get("content")}')
            elif "joomla" in content:
                detected = "joomla"
                signals.append(f'meta generator: {generator_tag.get("content")}')
            elif "shopify" in content:
                detected = "shopify"
                signals.append(f'meta generator: {generator_tag.get("content")}')
            elif "squarespace" in content:
                detected = "squarespace"
                signals.append(f'meta generator: {generator_tag.get("content")}')
            elif "wix" in content:
                detected = "wix"
                signals.append(f'meta generator: {generator_tag.get("content")}')
            elif "webflow" in content:
                detected = "webflow"
                signals.append(f'meta generator: {generator_tag.get("content")}')

        # 2. Check for WordPress signals in HTML
        if "/wp-content/" in html or "/wp-includes/" in html:
            if detected is None:
                detected = "wordpress"
            signals.append("Found /wp-content/ or /wp-includes/ paths")

        # 3. Check for Shopify signals
        if "cdn.shopify.com" in html:
            if detected is None:
                detected = "shopify"
            signals.append("Found cdn.shopify.com references")

        if "Shopify.theme" in html or "Shopify.shop" in html:
            if detected is None:
                detected = "shopify"
            signals.append("Found Shopify JavaScript globals")

        # 4. Check for Wix signals
        if "static.wixstatic.com" in html or "parastorage.com" in html:
            if detected is None:
                detected = "wix"
            signals.append("Found Wix static asset references")

        # 5. Check for Squarespace signals
        if "static1.squarespace.com" in html or "squarespace-cdn.com" in html:
            if detected is None:
                detected = "squarespace"
            signals.append("Found Squarespace static asset references")

        # 6. Check for Webflow signals
        if "assets.website-files.com" in html or "webflow.com" in html:
            if detected is None:
                detected = "webflow"
            signals.append("Found Webflow asset references")

        # 7. Check for Magento signals
        if "/static/version" in html and "/media/catalog/" in html:
            if detected is None:
                detected = "magento"
            signals.append("Found Magento static/version and media/catalog paths")

        # 8. Check for Drupal signals (if not already detected by generator)
        if "/sites/default/files/" in html or "/core/misc/drupal.js" in html:
            if detected is None:
                detected = "drupal"
            signals.append("Found Drupal default paths")

        result.detected_cms = detected
        result.cms_signals = signals

    # ------------------------------------------------------------------
    # Image analysis
    # ------------------------------------------------------------------

    def _analyze_images(
        self, soup: BeautifulSoup, url: str, result: HTMLAnalysis
    ) -> None:
        """Analyze all <img> tags for performance issues."""
        images = soup.find_all("img")
        result.total_images = len(images)

        missing_dimensions: list[dict] = []
        missing_srcset: list[dict] = []
        missing_fetchpriority: list[dict] = []
        lazy_above_fold: list[dict] = []
        oversized: list[dict] = []
        missing_alt: list[dict] = []

        for idx, img in enumerate(images):
            if not isinstance(img, Tag):
                continue

            snippet = str(img)[:300]
            src = img.get("src", "")
            attrs = dict(img.attrs)

            # --- Missing width/height ---
            has_width = img.get("width") is not None
            has_height = img.get("height") is not None
            if not has_width or not has_height:
                missing_dimensions.append(
                    {"tag": "img", "attributes": attrs, "snippet": snippet}
                )

            # --- Missing srcset/sizes ---
            has_srcset = img.get("srcset") is not None
            has_sizes = img.get("sizes") is not None
            if not has_srcset and not has_sizes and src:
                # Only flag for images that seem to be content images (not icons/trackers)
                missing_srcset.append(
                    {"tag": "img", "attributes": attrs, "snippet": snippet}
                )

            # --- Above-fold images (first 3) checks ---
            if idx < 3:
                # Missing fetchpriority on likely above-fold image
                if not img.get("fetchpriority"):
                    missing_fetchpriority.append(
                        {"tag": "img", "attributes": attrs, "snippet": snippet}
                    )

                # loading="lazy" on above-fold images (bad for LCP)
                loading = (img.get("loading") or "").lower()
                if loading == "lazy":
                    lazy_above_fold.append(
                        {"tag": "img", "attributes": attrs, "snippet": snippet}
                    )

            # --- Very large images ---
            width_attr = img.get("width")
            if width_attr:
                try:
                    width_val = int(str(width_attr).replace("px", "").strip())
                    if width_val > 2000:
                        oversized.append(
                            {"tag": "img", "attributes": attrs, "snippet": snippet}
                        )
                except (ValueError, TypeError):
                    pass

            # --- Missing alt text ---
            alt = img.get("alt")
            if alt is None or (isinstance(alt, str) and alt.strip() == ""):
                # Decorative images (role="presentation") are exempt
                role = (img.get("role") or "").lower()
                if role != "presentation":
                    missing_alt.append(
                        {"tag": "img", "attributes": attrs, "snippet": snippet}
                    )

        # Build findings
        if missing_dimensions:
            result.findings.append(
                HTMLFinding(
                    finding_id="img-missing-dimensions",
                    category="images",
                    description="Images without explicit width and height attributes cause layout shifts.",
                    elements=missing_dimensions,
                    count=len(missing_dimensions),
                )
            )

        if missing_srcset:
            result.findings.append(
                HTMLFinding(
                    finding_id="img-missing-srcset",
                    category="images",
                    description="Images without srcset/sizes serve the same size to all viewports.",
                    elements=missing_srcset,
                    count=len(missing_srcset),
                )
            )

        if missing_fetchpriority:
            result.findings.append(
                HTMLFinding(
                    finding_id="img-missing-fetchpriority",
                    category="images",
                    description=(
                        "Above-the-fold images lack fetchpriority='high', which could delay LCP."
                    ),
                    elements=missing_fetchpriority,
                    count=len(missing_fetchpriority),
                )
            )

        if lazy_above_fold:
            result.findings.append(
                HTMLFinding(
                    finding_id="img-lazy-above-fold",
                    category="images",
                    description=(
                        "Above-the-fold images have loading='lazy', which delays LCP. "
                        "Remove lazy loading from the first few images."
                    ),
                    elements=lazy_above_fold,
                    count=len(lazy_above_fold),
                )
            )

        if oversized:
            result.findings.append(
                HTMLFinding(
                    finding_id="img-oversized",
                    category="images",
                    description="Images with width > 2000px are likely much larger than needed.",
                    elements=oversized,
                    count=len(oversized),
                )
            )

        if missing_alt:
            result.findings.append(
                HTMLFinding(
                    finding_id="img-missing-alt",
                    category="images",
                    description="Images without alt text hurt accessibility and SEO.",
                    elements=missing_alt,
                    count=len(missing_alt),
                )
            )

    # ------------------------------------------------------------------
    # Script analysis
    # ------------------------------------------------------------------

    def _analyze_scripts(
        self, soup: BeautifulSoup, url: str, result: HTMLAnalysis
    ) -> None:
        """Analyze all <script> tags for render-blocking and sizing issues."""
        all_scripts = soup.find_all("script")

        external_scripts: list[Tag] = []
        inline_js_bytes = 0
        render_blocking: list[dict] = []

        head = soup.find("head")

        for script in all_scripts:
            if not isinstance(script, Tag):
                continue

            src = script.get("src")
            if src:
                external_scripts.append(script)
            else:
                # Inline script: measure size
                text = script.string or ""
                inline_js_bytes += len(text.encode("utf-8"))

        result.total_scripts = len(external_scripts)
        result.total_inline_js_bytes = inline_js_bytes

        # Check for render-blocking scripts in <head>
        if head and isinstance(head, Tag):
            head_scripts = head.find_all("script", src=True)
            for script in head_scripts:
                if not isinstance(script, Tag):
                    continue

                has_async = script.get("async") is not None
                has_defer = script.get("defer") is not None
                script_type = (script.get("type") or "").lower()
                is_module = script_type == "module"

                # type="module" is deferred by default, so not render-blocking
                if not has_async and not has_defer and not is_module:
                    snippet = str(script)[:300]
                    render_blocking.append(
                        {
                            "tag": "script",
                            "attributes": dict(script.attrs),
                            "snippet": snippet,
                        }
                    )

        if render_blocking:
            result.findings.append(
                HTMLFinding(
                    finding_id="script-render-blocking",
                    category="scripts",
                    description=(
                        "Scripts in <head> without async, defer, or type='module' "
                        "block rendering until they download and execute."
                    ),
                    elements=render_blocking,
                    count=len(render_blocking),
                )
            )

        # Flag large inline JS
        if inline_js_bytes > 50_000:
            result.findings.append(
                HTMLFinding(
                    finding_id="excessive-inline-js",
                    category="scripts",
                    description=(
                        f"Total inline JavaScript is {inline_js_bytes:,} bytes. "
                        "Large inline scripts increase HTML size and cannot be cached separately."
                    ),
                    count=inline_js_bytes,
                )
            )

    # ------------------------------------------------------------------
    # Stylesheet analysis
    # ------------------------------------------------------------------

    def _analyze_styles(self, soup: BeautifulSoup, result: HTMLAnalysis) -> None:
        """Analyze stylesheets and inline CSS for performance issues."""
        # External stylesheets
        link_css = soup.find_all("link", rel="stylesheet")
        result.total_stylesheets = len(link_css)

        render_blocking_css: list[dict] = []
        head = soup.find("head")

        if head and isinstance(head, Tag):
            head_links = head.find_all("link", rel="stylesheet")
            for link in head_links:
                if not isinstance(link, Tag):
                    continue
                # A stylesheet without a media attribute (or media="all") is render-blocking
                media = (link.get("media") or "").lower().strip()
                if media == "" or media == "all":
                    snippet = str(link)[:300]
                    render_blocking_css.append(
                        {
                            "tag": "link",
                            "attributes": dict(link.attrs),
                            "snippet": snippet,
                        }
                    )

        if render_blocking_css:
            result.findings.append(
                HTMLFinding(
                    finding_id="css-render-blocking",
                    category="styles",
                    description=(
                        "Stylesheets in <head> without a media attribute (or media='all') "
                        "block rendering. Consider using media queries or inlining critical CSS."
                    ),
                    elements=render_blocking_css,
                    count=len(render_blocking_css),
                )
            )

        # Inline <style> tags
        inline_styles = soup.find_all("style")
        inline_css_bytes = 0
        import_found: list[dict] = []

        for style_tag in inline_styles:
            if not isinstance(style_tag, Tag):
                continue
            text = style_tag.string or ""
            inline_css_bytes += len(text.encode("utf-8"))

            # Check for @import in inline styles
            if "@import" in text:
                snippet = text[:200]
                import_found.append(
                    {
                        "tag": "style",
                        "attributes": dict(style_tag.attrs),
                        "snippet": f"<style>...@import...{snippet}...</style>",
                    }
                )

        result.total_inline_css_bytes = inline_css_bytes

        if import_found:
            result.findings.append(
                HTMLFinding(
                    finding_id="css-import-in-style",
                    category="styles",
                    description=(
                        "@import inside <style> tags creates additional blocking network requests. "
                        "Use <link> tags instead."
                    ),
                    elements=import_found,
                    count=len(import_found),
                )
            )

        if inline_css_bytes > 50_000:
            result.findings.append(
                HTMLFinding(
                    finding_id="excessive-inline-css",
                    category="styles",
                    description=(
                        f"Total inline CSS is {inline_css_bytes:,} bytes. "
                        "Large inline styles increase HTML size and cannot be cached separately."
                    ),
                    count=inline_css_bytes,
                )
            )

    # ------------------------------------------------------------------
    # Font analysis
    # ------------------------------------------------------------------

    def _analyze_fonts(
        self, soup: BeautifulSoup, html: str, result: HTMLAnalysis
    ) -> None:
        """Analyze font loading for performance issues."""
        google_fonts_links: list[dict] = []
        font_face_declarations: list[str] = []
        font_display_values: list[str] = []
        missing_font_preloads: list[dict] = []

        # 1. Check for Google Fonts links
        for link in soup.find_all("link"):
            if not isinstance(link, Tag):
                continue
            href = link.get("href") or ""
            if "fonts.googleapis.com" in href:
                snippet = str(link)[:300]
                google_fonts_links.append(
                    {"tag": "link", "attributes": dict(link.attrs), "snippet": snippet}
                )

        if google_fonts_links:
            result.findings.append(
                HTMLFinding(
                    finding_id="google-fonts-link",
                    category="fonts",
                    description=(
                        "Google Fonts loaded via <link> adds extra DNS lookups and round trips. "
                        "Consider self-hosting fonts or using font-display: swap."
                    ),
                    elements=google_fonts_links,
                    count=len(google_fonts_links),
                )
            )

        # 2. Check @font-face in inline CSS
        inline_styles = soup.find_all("style")
        for style_tag in inline_styles:
            if not isinstance(style_tag, Tag):
                continue
            text = style_tag.string or ""
            # Find @font-face blocks
            font_faces = re.findall(r"@font-face\s*\{[^}]*\}", text, re.IGNORECASE)
            for ff in font_faces:
                font_face_declarations.append(ff)
                # Extract font-display value
                display_match = re.search(r"font-display\s*:\s*(\w+)", ff, re.IGNORECASE)
                if display_match:
                    font_display_values.append(display_match.group(1).lower())

        # Also search the raw HTML for @font-face (catches some edge cases)
        raw_font_faces = re.findall(r"@font-face\s*\{[^}]*\}", html, re.IGNORECASE)
        for ff in raw_font_faces:
            if ff not in font_face_declarations:
                font_face_declarations.append(ff)
                display_match = re.search(r"font-display\s*:\s*(\w+)", ff, re.IGNORECASE)
                if display_match:
                    font_display_values.append(display_match.group(1).lower())

        # 3. Flag font-display: block (causes invisible text)
        block_display = [v for v in font_display_values if v == "block"]
        if block_display:
            result.findings.append(
                HTMLFinding(
                    finding_id="font-display-block",
                    category="fonts",
                    description=(
                        f"Found {len(block_display)} @font-face rule(s) using font-display: block. "
                        "This hides text until the font loads. Use font-display: swap or optional instead."
                    ),
                    count=len(block_display),
                )
            )

        # 4. Check for missing font preloads
        preloaded_fonts = set()
        for link in soup.find_all("link", rel="preload"):
            if not isinstance(link, Tag):
                continue
            as_attr = (link.get("as") or "").lower()
            if as_attr == "font":
                href = link.get("href") or ""
                preloaded_fonts.add(href)

        # If there are @font-face declarations but no font preloads, flag it
        if font_face_declarations and not preloaded_fonts:
            result.findings.append(
                HTMLFinding(
                    finding_id="missing-font-preload",
                    category="fonts",
                    description=(
                        f"Found {len(font_face_declarations)} @font-face declaration(s) "
                        "but no <link rel='preload' as='font'> hints. "
                        "Preloading critical fonts speeds up text rendering."
                    ),
                    count=len(font_face_declarations),
                )
            )

    # ------------------------------------------------------------------
    # Meta tag analysis
    # ------------------------------------------------------------------

    def _analyze_meta(self, soup: BeautifulSoup, result: HTMLAnalysis) -> None:
        """Check for essential meta tags related to performance and mobile rendering."""
        # 1. Check for meta viewport presence
        viewport_tag = soup.find("meta", attrs={"name": "viewport"})

        if not viewport_tag:
            result.findings.append(
                HTMLFinding(
                    finding_id="missing-viewport",
                    category="meta",
                    description=(
                        "No <meta name='viewport'> tag found. "
                        "This is required for proper mobile rendering and is a Core Web Vitals factor."
                    ),
                    count=1,
                )
            )
        elif isinstance(viewport_tag, Tag):
            # 2. Check viewport content
            content = (viewport_tag.get("content") or "").lower()
            if "width=device-width" not in content:
                result.findings.append(
                    HTMLFinding(
                        finding_id="viewport-missing-device-width",
                        category="meta",
                        description=(
                            "Viewport meta tag does not include width=device-width. "
                            f"Current content: '{viewport_tag.get('content')}'"
                        ),
                        elements=[
                            {
                                "tag": "meta",
                                "attributes": dict(viewport_tag.attrs),
                                "snippet": str(viewport_tag)[:300],
                            }
                        ],
                        count=1,
                    )
                )

    # ------------------------------------------------------------------
    # Resource hints analysis
    # ------------------------------------------------------------------

    def _analyze_resource_hints(
        self, soup: BeautifulSoup, result: HTMLAnalysis
    ) -> None:
        """Extract preload, preconnect, prefetch, and dns-prefetch hints."""
        for link in soup.find_all("link"):
            if not isinstance(link, Tag):
                continue

            rel_values = link.get("rel", [])
            if isinstance(rel_values, str):
                rel_values = [rel_values]
            rel_set = {r.lower() for r in rel_values}

            href = link.get("href") or ""

            if "preload" in rel_set and href:
                result.preload_hints.append(href)
            if "preconnect" in rel_set and href:
                result.preconnect_hints.append(href)
            if "prefetch" in rel_set and href:
                result.prefetch_hints.append(href)
            if "dns-prefetch" in rel_set and href:
                # dns-prefetch is a lighter form of preconnect; track alongside preconnect
                result.preconnect_hints.append(f"dns-prefetch:{href}")

    # ------------------------------------------------------------------
    # Third-party analysis
    # ------------------------------------------------------------------

    def _analyze_third_parties(
        self, soup: BeautifulSoup, url: str, result: HTMLAnalysis
    ) -> None:
        """Identify third-party domains from script and link elements."""
        parsed_url = urlparse(url)
        first_party_domain = parsed_url.netloc.lower()

        # Strip www. prefix for comparison
        fp_base = first_party_domain.removeprefix("www.")

        third_party_domains: set[str] = set()

        # Check all script[src] tags
        for script in soup.find_all("script", src=True):
            if not isinstance(script, Tag):
                continue
            src = script.get("src") or ""
            domain = self._extract_domain(src)
            if domain and not self._is_same_site(domain, fp_base):
                third_party_domains.add(domain)

        # Check all link[href] tags (stylesheets, etc.)
        for link in soup.find_all("link", href=True):
            if not isinstance(link, Tag):
                continue
            href = link.get("href") or ""
            domain = self._extract_domain(href)
            if domain and not self._is_same_site(domain, fp_base):
                third_party_domains.add(domain)

        # Check all img[src] tags
        for img in soup.find_all("img", src=True):
            if not isinstance(img, Tag):
                continue
            src = img.get("src") or ""
            domain = self._extract_domain(src)
            if domain and not self._is_same_site(domain, fp_base):
                third_party_domains.add(domain)

        result.third_party_domains = sorted(third_party_domains)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_domain(url_str: str) -> Optional[str]:
        """Extract the domain from a URL string. Returns None for relative URLs."""
        if not url_str or url_str.startswith("data:"):
            return None
        try:
            parsed = urlparse(url_str)
            if parsed.netloc:
                return parsed.netloc.lower()
        except Exception:
            pass
        return None

    @staticmethod
    def _is_same_site(domain: str, first_party_base: str) -> bool:
        """Check whether a domain belongs to the same site as the first party."""
        domain_clean = domain.removeprefix("www.")
        # Exact match or subdomain match
        return domain_clean == first_party_base or domain_clean.endswith(
            f".{first_party_base}"
        )
