"""Formatting helper functions for bytes, milliseconds, scores, and URLs."""


def format_bytes(bytes_val: int | float) -> str:
    """Convert a byte count to a human-readable string.

    Examples:
        format_bytes(1_234_567) -> "1.2 MB"
        format_bytes(450_000)   -> "439.5 KB"
        format_bytes(500)       -> "500 B"
    """
    bytes_val = float(bytes_val)
    if bytes_val < 0:
        return "0 B"

    if bytes_val >= 1_000_000:
        return f"{bytes_val / 1_000_000:.1f} MB"
    if bytes_val >= 1_000:
        return f"{bytes_val / 1_000:.1f} KB"
    return f"{int(bytes_val)} B"


def format_ms(ms_val: int | float) -> str:
    """Convert a millisecond value to a human-readable string.

    Examples:
        format_ms(2500) -> "2.5 s"
        format_ms(450)  -> "450 ms"
        format_ms(0.12) -> "0.1 s" (values under 1 ms still shown in ms)
    """
    ms_val = float(ms_val)
    if ms_val < 0:
        return "0 ms"

    if ms_val >= 1_000:
        return f"{ms_val / 1_000:.1f} s"
    return f"{int(round(ms_val))} ms"


def score_color(score: int | float) -> str:
    """Return a hex color for a Lighthouse-style 0-100 score.

    - 0-49:   red   (#ff4e42)
    - 50-89:  orange (#ffa400)
    - 90-100: green  (#0cce6b)
    """
    score = int(score)
    if score >= 90:
        return "#0cce6b"
    if score >= 50:
        return "#ffa400"
    return "#ff4e42"


def truncate_url(url: str, max_len: int = 60) -> str:
    """Truncate a URL in the middle for display purposes.

    If the URL is shorter than *max_len* it is returned unchanged.
    Otherwise the middle is replaced with '...' so the beginning
    (scheme + domain) and the tail (filename / query) stay visible.

    Examples:
        truncate_url("https://example.com/very/long/path/to/resource.html", 40)
        -> "https://example.com/v.../resource.html"
    """
    if len(url) <= max_len:
        return url

    # Keep roughly 60% at the start and 40% at the end
    keep_start = int(max_len * 0.6)
    keep_end = max_len - keep_start - 3  # 3 chars for '...'
    if keep_end < 5:
        keep_end = 5
        keep_start = max_len - keep_end - 3

    return f"{url[:keep_start]}...{url[-keep_end:]}"
