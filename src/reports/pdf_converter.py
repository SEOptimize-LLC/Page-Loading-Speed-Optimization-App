"""Converts HTML speed audit reports to PDF using WeasyPrint."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PDFConverter:
    """Converts HTML reports to PDF using WeasyPrint.

    WeasyPrint is an optional dependency. When it is not installed the
    converter degrades gracefully — ``convert()`` returns ``None`` and
    ``is_available()`` returns ``False``.
    """

    @staticmethod
    def convert(html_content: str) -> Optional[bytes]:
        """Convert a rendered HTML report string to PDF bytes.

        Args:
            html_content: Complete HTML report string (as produced by
                :class:`ReportGenerator`).

        Returns:
            PDF file content as ``bytes``, or ``None`` if conversion
            fails or WeasyPrint is not installed.
        """
        try:
            from weasyprint import HTML
        except ImportError:
            logger.warning(
                "WeasyPrint is not installed. PDF generation is unavailable. "
                "Install it with: pip install weasyprint"
            )
            return None

        try:
            pdf_bytes: bytes = HTML(string=html_content).write_pdf()
            logger.info("PDF generated successfully: %d bytes", len(pdf_bytes))
            return pdf_bytes
        except Exception as exc:
            logger.error("PDF generation failed: %s", exc, exc_info=True)
            return None

    @staticmethod
    def is_available() -> bool:
        """Return ``True`` if WeasyPrint can be imported."""
        try:
            import weasyprint  # noqa: F401
            return True
        except ImportError:
            return False
