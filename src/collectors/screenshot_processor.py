"""Process and crop screenshots from PSI API data for visual diagnostics."""

import base64
import io
import logging
from typing import Optional

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class ScreenshotProcessor:
    """Process and crop screenshots from PSI API data.

    Uses the full-page screenshot and node position map from the PSI API
    to crop individual elements and annotate them with severity-colored borders.
    """

    SEVERITY_COLORS = {
        "critical": (220, 38, 38),  # red
        "important": (245, 158, 11),  # orange
        "minor": (234, 179, 8),  # yellow
    }

    def __init__(
        self,
        full_page_screenshot: Optional[str],
        screenshot_nodes: dict,
    ):
        """Initialize the processor.

        Args:
            full_page_screenshot: base64-encoded full page screenshot from PSI
                (may include a ``data:image/...;base64,`` prefix).
            screenshot_nodes: dict mapping Lighthouse ``lhId`` values to
                position dicts ``{left, top, width, height, right, bottom}``.
        """
        self.full_page_image: Optional[Image.Image] = None
        self.screenshot_nodes: dict = screenshot_nodes or {}
        self.fps_width: int = 0
        self.fps_height: int = 0

        if full_page_screenshot:
            try:
                # Strip data URI prefix if present
                raw_b64 = full_page_screenshot.split(",")[-1]
                img_data = base64.b64decode(raw_b64)
                self.full_page_image = Image.open(io.BytesIO(img_data))
                self.fps_width = self.full_page_image.width
                self.fps_height = self.full_page_image.height
                logger.info(
                    f"Loaded full-page screenshot: {self.fps_width}x{self.fps_height}"
                )
            except Exception as e:
                logger.warning(f"Could not decode full page screenshot: {e}")
                self.full_page_image = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def crop_element(
        self,
        lh_id: str,
        severity: str = "critical",
        padding: int = 20,
    ) -> Optional[str]:
        """Crop an element from the full page screenshot by its Lighthouse ID.

        Args:
            lh_id: The Lighthouse element ID (e.g. ``page-0-IMG``).
            severity: One of ``"critical"``, ``"important"``, or ``"minor"``.
                Controls the highlight border color.
            padding: Extra pixels around the element bounding box.

        Returns:
            A ``data:image/png;base64,...`` data URI string, or ``None`` if the
            element cannot be found or the full-page screenshot is unavailable.
        """
        if self.full_page_image is None:
            logger.warning("No full-page screenshot available for cropping.")
            return None

        node = self.screenshot_nodes.get(lh_id)
        if node is None:
            logger.warning(f"Lighthouse ID '{lh_id}' not found in screenshot nodes.")
            return None

        return self.crop_by_rect(node, severity=severity, padding=padding)

    def crop_by_rect(
        self,
        rect: dict,
        severity: str = "critical",
        padding: int = 20,
    ) -> Optional[str]:
        """Crop by explicit bounding rect.

        Args:
            rect: Dict with keys ``left``, ``top``, ``width``, ``height``
                (and optionally ``right``, ``bottom``).
            severity: Highlight border color category.
            padding: Extra pixels around the crop region.

        Returns:
            A ``data:image/png;base64,...`` data URI string, or ``None``.
        """
        if self.full_page_image is None:
            logger.warning("No full-page screenshot available for cropping.")
            return None

        left = rect.get("left", 0)
        top = rect.get("top", 0)
        width = rect.get("width", 0)
        height = rect.get("height", 0)
        right = rect.get("right", left + width)
        bottom = rect.get("bottom", top + height)

        # Validate dimensions
        if width <= 0 or height <= 0:
            logger.warning(
                f"Element has zero or negative dimensions: {width}x{height}. Skipping."
            )
            return None

        # Very small elements: enforce a minimum crop size so the result is visible
        min_size = 10
        if width < min_size:
            center_x = left + width / 2
            left = center_x - min_size / 2
            right = center_x + min_size / 2
        if height < min_size:
            center_y = top + height / 2
            top = center_y - min_size / 2
            bottom = center_y + min_size / 2

        # Apply padding
        crop_left = max(0, int(left - padding))
        crop_top = max(0, int(top - padding))
        crop_right = min(self.fps_width, int(right + padding))
        crop_bottom = min(self.fps_height, int(bottom + padding))

        # Ensure the crop box is valid (element is within the image)
        if crop_left >= crop_right or crop_top >= crop_bottom:
            logger.warning(
                f"Crop box is invalid after clamping: "
                f"({crop_left}, {crop_top}, {crop_right}, {crop_bottom}). "
                f"Image size: {self.fps_width}x{self.fps_height}."
            )
            return None

        try:
            cropped = self.full_page_image.crop(
                (crop_left, crop_top, crop_right, crop_bottom)
            )
        except Exception as e:
            logger.warning(f"Failed to crop screenshot: {e}")
            return None

        # Add a colored highlight border
        color = self.SEVERITY_COLORS.get(severity, self.SEVERITY_COLORS["critical"])
        highlighted = self._add_highlight_border(cropped, color, width=3)

        return self._image_to_data_uri(highlighted)

    def get_filmstrip(self, filmstrip_data: list[dict]) -> list[dict]:
        """Process filmstrip frames into a clean format.

        Args:
            filmstrip_data: List of filmstrip frame dicts from PSI, each with
                ``timing`` (ms from navigation start) and ``data`` (base64 data URI).

        Returns:
            List of dicts ``[{timing_ms: int, data_uri: str}, ...]``.
            Frames with missing or invalid data are skipped.
        """
        processed: list[dict] = []

        for frame in filmstrip_data:
            timing = frame.get("timing")
            data = frame.get("data")

            if timing is None or data is None:
                continue

            # Validate that the data is a proper data URI or base64
            if not isinstance(data, str) or len(data) < 20:
                continue

            # Ensure data URI prefix
            if not data.startswith("data:"):
                data = f"data:image/jpeg;base64,{data}"

            processed.append({
                "timing_ms": int(timing),
                "data_uri": data,
            })

        # Sort by timing just in case
        processed.sort(key=lambda f: f["timing_ms"])

        return processed

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _add_highlight_border(
        img: Image.Image,
        color: tuple,
        width: int = 3,
    ) -> Image.Image:
        """Add a colored border around the image.

        Args:
            img: The PIL Image to annotate.
            color: RGB tuple for the border color.
            width: Border width in pixels.

        Returns:
            A new Image with the border drawn on it.
        """
        # Create a copy so we don't mutate the original
        bordered = img.copy()

        # Ensure the image is in a mode that supports drawing (e.g. RGB/RGBA)
        if bordered.mode not in ("RGB", "RGBA"):
            bordered = bordered.convert("RGB")

        draw = ImageDraw.Draw(bordered)
        w, h = bordered.size

        for i in range(width):
            # Draw concentric rectangles
            draw.rectangle(
                [i, i, w - 1 - i, h - 1 - i],
                outline=color,
            )

        return bordered

    @staticmethod
    def _image_to_data_uri(img: Image.Image) -> str:
        """Convert a PIL Image to a base64-encoded PNG data URI.

        Args:
            img: The PIL Image to encode.

        Returns:
            A ``data:image/png;base64,...`` string.
        """
        buffer = io.BytesIO()
        # Convert to RGB if RGBA to avoid issues with some viewers
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(buffer, format="PNG", optimize=True)
        b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
