"""URL validation, normalization, and utility functions."""

from urllib.parse import urlparse, urlunparse
import re


def validate_url(url: str) -> tuple[bool, str]:
    """Validate and normalize a URL for PageSpeed analysis.

    Returns:
        A tuple of (is_valid, result) where *result* is the normalized URL
        on success or an error message on failure.

    Examples:
        validate_url("example.com")          -> (True, "https://example.com")
        validate_url("https://example.com/") -> (True, "https://example.com")
        validate_url("")                     -> (False, "URL cannot be empty")
        validate_url("not a url")            -> (False, "Invalid URL format...")
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    url = url.strip()

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format: could not parse URL"

    # Must have a valid scheme
    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid URL scheme: '{parsed.scheme}'. Use http or https."

    # Must have a hostname
    if not parsed.hostname:
        return False, "Invalid URL: no hostname found"

    # Basic hostname validation (must contain a dot for a real domain)
    hostname = parsed.hostname
    if "." not in hostname:
        return False, f"Invalid hostname: '{hostname}'. Please enter a full domain (e.g., example.com)."

    # Check for obviously invalid characters in hostname
    if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$", hostname):
        return False, f"Invalid hostname: '{hostname}'. Contains invalid characters."

    # Normalize the URL
    normalized = normalize_url(url)
    return True, normalized


def normalize_url(url: str) -> str:
    """Normalize a URL by adding https:// if missing and stripping trailing slash.

    Examples:
        normalize_url("example.com")           -> "https://example.com"
        normalize_url("http://example.com/")    -> "http://example.com"
        normalize_url("https://example.com/page/") -> "https://example.com/page"
    """
    url = url.strip()

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)

    # Strip trailing slash from path (but keep root "/" as empty)
    path = parsed.path.rstrip("/")

    # Reconstruct the URL with cleaned path
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        path,
        parsed.params,
        parsed.query,
        "",  # drop fragment
    ))

    return normalized


def extract_domain(url: str) -> str:
    """Extract the domain (hostname) from a URL.

    Examples:
        extract_domain("https://www.example.com/page") -> "www.example.com"
        extract_domain("example.com/page")             -> "example.com"
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    return parsed.hostname or ""


def is_same_origin(url1: str, url2: str) -> bool:
    """Check whether two URLs share the same origin (scheme + hostname + port).

    Examples:
        is_same_origin("https://example.com/a", "https://example.com/b")  -> True
        is_same_origin("https://example.com", "https://sub.example.com")  -> False
        is_same_origin("http://example.com", "https://example.com")       -> False
    """
    def _origin(url: str) -> tuple[str, str, int]:
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        parsed = urlparse(url)
        scheme = parsed.scheme
        hostname = parsed.hostname or ""
        port = parsed.port or (443 if scheme == "https" else 80)
        return scheme, hostname, port

    return _origin(url1) == _origin(url2)
