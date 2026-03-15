"""Knowledge Base Module.

Loads the 6 knowledge base markdown files, splits them into sections,
and selects relevant sections based on detected issues and CMS type.
"""

import os
import re
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Map PSI audit IDs to knowledge base topics for section selection.
# Each audit ID maps to a list of keywords used to match relevant KB sections.
AUDIT_TO_TOPIC = {
    # Image audits -> Image sections
    "offscreen-images": ["image", "lazy loading", "loading attribute"],
    "modern-image-formats": ["image", "avif", "webp", "image format"],
    "uses-responsive-images": ["image", "srcset", "sizes", "responsive"],
    "uses-optimized-images": ["image", "compress", "optimization"],
    "unsized-images": ["image", "width", "height", "cls"],
    "image-size-responsive": ["image", "srcset", "responsive"],
    # CSS/rendering audits -> CSS sections
    "render-blocking-resources": ["render-blocking", "css", "critical css", "defer"],
    "unused-css-rules": ["unused css", "css optimization", "remove"],
    "unminified-css": ["minif", "css optimization"],
    # JS audits -> JavaScript sections
    "unused-javascript": ["javascript", "unused", "code splitting"],
    "unminified-javascript": ["javascript", "minif"],
    "bootup-time": ["javascript", "execution", "main thread"],
    "mainthread-work-breakdown": ["main thread", "javascript", "long task"],
    "legacy-javascript": ["javascript", "legacy", "polyfill"],
    "duplicated-javascript": ["javascript", "duplicate"],
    "total-byte-weight": ["total", "weight", "compression"],
    # Font audits -> Font sections
    "font-display": ["font", "font-display", "foit", "fout", "swap"],
    # Server/network audits
    "server-response-time": ["ttfb", "server", "response time", "hosting"],
    "uses-text-compression": ["compression", "brotli", "gzip"],
    "uses-long-cache-ttl": ["cache", "caching", "ttl"],
    "uses-rel-preconnect": ["preconnect", "resource hint"],
    "uses-rel-preload": ["preload", "resource hint", "lcp"],
    "redirects": ["redirect", "ttfb"],
    # DOM/rendering
    "dom-size": ["dom", "element", "node"],
    "critical-request-chains": ["critical", "chain", "waterfall"],
    "efficient-animated-content": ["animation", "gif", "video"],
    # Third party
    "third-party-summary": ["third-party", "third party", "external script"],
    # CWV elements
    "largest-contentful-paint-element": ["lcp", "largest contentful", "hero image"],
    "layout-shift-elements": ["cls", "layout shift", "cumulative"],
}

# Files associated with each CMS type
_CMS_FILES = {
    "wordpress": ["wordpress-optimization", "wpspeedmatters-insights"],
    "shopify": ["shopify-and-inp-cases", "shopify-liquid-patterns"],
}


class KnowledgeBase:
    """Loads and selects relevant knowledge base sections."""

    def __init__(self, kb_dir: Optional[str] = None):
        """Initialize with knowledge base directory path.

        Args:
            kb_dir: Path to the knowledge-base directory. Defaults to
                    <project_root>/knowledge-base.
        """
        if kb_dir is None:
            kb_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "knowledge-base",
            )
        self.kb_dir = kb_dir
        self.sections: dict[str, list[dict]] = {}  # {filename_stem: [{heading, content, level}]}
        self._load_all()

    def _load_all(self):
        """Load all markdown files and split into sections."""
        kb_path = Path(self.kb_dir)
        if not kb_path.exists():
            logger.warning(f"Knowledge base directory not found: {self.kb_dir}")
            return

        for md_file in sorted(kb_path.glob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                self.sections[md_file.stem] = self._split_sections(content)
                logger.info(
                    f"Loaded {len(self.sections[md_file.stem])} sections "
                    f"from {md_file.name}"
                )
            except Exception as e:
                logger.warning(f"Could not load {md_file.name}: {e}")

    def _split_sections(self, content: str) -> list[dict]:
        """Split markdown content into sections by heading markers.

        Each section captures the heading text, the content below it (until
        the next heading), and the heading level (number of # characters).
        Sections shorter than 50 characters are discarded.

        Args:
            content: Full markdown file content.

        Returns:
            List of section dicts with keys: heading, content, level.
        """
        sections = []
        current_heading = "Introduction"
        current_content: list[str] = []
        current_level = 1

        for line in content.split("\n"):
            heading_match = re.match(r"^(#{1,4})\s+(.+)$", line)
            if heading_match:
                # Save the previous section
                if current_content:
                    text = "\n".join(current_content).strip()
                    if len(text) > 50:
                        sections.append(
                            {
                                "heading": current_heading,
                                "content": text,
                                "level": current_level,
                            }
                        )
                current_heading = heading_match.group(2)
                current_level = len(heading_match.group(1))
                current_content = []
            else:
                current_content.append(line)

        # Capture the last section
        if current_content:
            text = "\n".join(current_content).strip()
            if len(text) > 50:
                sections.append(
                    {
                        "heading": current_heading,
                        "content": text,
                        "level": current_level,
                    }
                )

        return sections

    def get_relevant_context(
        self,
        audit_ids: list[str],
        cms_type: str = "unknown",
        max_chars: int = 45000,
    ) -> str:
        """Select relevant KB sections based on detected issues and CMS.

        The selection algorithm:
        1. Collects topic keywords from AUDIT_TO_TOPIC for each audit_id.
        2. Searches all loaded sections (headings and content) for keyword matches.
        3. Scores each section by the number of distinct keyword hits.
        4. Adds CMS-specific sections with a bonus score.
        5. Sorts by score descending.
        6. Concatenates sections until hitting max_chars budget.

        Args:
            audit_ids: List of PSI audit IDs that had issues.
            cms_type: "wordpress", "shopify", or "unknown".
            max_chars: Maximum characters of context (~15,000 tokens).

        Returns:
            Combined relevant KB context string, formatted with section headers.
        """
        # Step 1: Collect all unique topic keywords from the provided audit IDs
        all_keywords: list[str] = []
        for audit_id in audit_ids:
            keywords = AUDIT_TO_TOPIC.get(audit_id, [])
            all_keywords.extend(keywords)
        # Deduplicate while preserving order
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                unique_keywords.append(kw_lower)

        # Determine which files are CMS-specific
        cms_files = set(_CMS_FILES.get(cms_type.lower(), []))

        # Step 2 & 3: Score every section across all files
        scored_sections: list[tuple[float, str, dict]] = []

        for file_stem, file_sections in self.sections.items():
            for section in file_sections:
                searchable_text = (
                    section["heading"].lower() + " " + section["content"].lower()
                )
                # Count distinct keyword hits
                hit_count = 0
                for kw in unique_keywords:
                    if kw in searchable_text:
                        hit_count += 1

                # Skip sections with zero relevance (unless CMS-specific)
                is_cms_file = file_stem in cms_files

                if hit_count == 0 and not is_cms_file:
                    continue

                score = float(hit_count)

                # Heading matches are more valuable: bonus for keyword in heading
                heading_lower = section["heading"].lower()
                for kw in unique_keywords:
                    if kw in heading_lower:
                        score += 1.5

                # Step 4: CMS-specific sections get a bonus
                if is_cms_file:
                    score += 3.0

                    # Even CMS sections with no keyword hits get a small base score
                    # so they appear in the context when the CMS matches
                    if hit_count == 0:
                        score = 1.0

                scored_sections.append((score, file_stem, section))

        # Step 5: Sort by score descending (higher relevance first)
        scored_sections.sort(key=lambda x: x[0], reverse=True)

        # Step 6: Concatenate until max_chars budget is reached
        output_parts: list[str] = []
        total_chars = 0

        for score, file_stem, section in scored_sections:
            formatted = self._format_section(file_stem, section)
            section_len = len(formatted)

            if total_chars + section_len > max_chars:
                # If we have room for at least part of this section, include it
                remaining = max_chars - total_chars
                if remaining > 200:
                    output_parts.append(formatted[:remaining] + "\n...[truncated]")
                break

            output_parts.append(formatted)
            total_chars += section_len

        if not output_parts:
            return "No relevant knowledge base sections found for the detected issues."

        return "\n\n".join(output_parts)

    def get_cms_context(
        self,
        cms_type: str,
        max_chars: int = 15000,
    ) -> str:
        """Get CMS-specific optimization context only.

        For WordPress: returns sections from wordpress-optimization and
        wpspeedmatters-insights.
        For Shopify: returns sections from shopify-and-inp-cases and
        shopify-liquid-patterns.

        Args:
            cms_type: "wordpress", "shopify", or other.
            max_chars: Maximum characters to return.

        Returns:
            CMS-specific KB context string.
        """
        cms_key = cms_type.lower()
        target_files = _CMS_FILES.get(cms_key, [])

        if not target_files:
            return f"No CMS-specific knowledge base found for: {cms_type}"

        output_parts: list[str] = []
        total_chars = 0

        for file_stem in target_files:
            file_sections = self.sections.get(file_stem, [])
            if not file_sections:
                logger.warning(
                    f"CMS file '{file_stem}' not found in loaded knowledge base."
                )
                continue

            for section in file_sections:
                formatted = self._format_section(file_stem, section)
                section_len = len(formatted)

                if total_chars + section_len > max_chars:
                    remaining = max_chars - total_chars
                    if remaining > 200:
                        output_parts.append(
                            formatted[:remaining] + "\n...[truncated]"
                        )
                    break

                output_parts.append(formatted)
                total_chars += section_len

        if not output_parts:
            return f"No CMS-specific sections loaded for: {cms_type}"

        return "\n\n".join(output_parts)

    @staticmethod
    def _format_section(file_stem: str, section: dict) -> str:
        """Format a single section for inclusion in the context string.

        Produces a readable header with source attribution followed by the
        section content.

        Args:
            file_stem: The source file name (without extension).
            section: Section dict with heading, content, level keys.

        Returns:
            Formatted section string.
        """
        header_prefix = "#" * section["level"]
        return (
            f"--- [{file_stem}] ---\n"
            f"{header_prefix} {section['heading']}\n\n"
            f"{section['content']}"
        )
