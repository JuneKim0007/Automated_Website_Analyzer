import re
from urllib.parse import urlparse

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tiff", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".avi", ".mov", ".mkv", ".flv", ".ogv", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".wma"}
FONT_EXTENSIONS  = {".woff", ".woff2", ".ttf", ".eot", ".otf"}
DOC_EXTENSIONS   = {".pdf", ".zip", ".rar", ".7z", ".tar", ".gz"}
STYLE_EXTENSIONS = {".css", ".scss", ".less"}
SCRIPT_EXTENSIONS = {".js", ".mjs", ".ts"}

STATIC_EXTENSIONS = (
    IMAGE_EXTENSIONS|VIDEO_EXTENSIONS|AUDIO_EXTENSIONS|FONT_EXTENSIONS|
    DOC_EXTENSIONS|STYLE_EXTENSIONS|SCRIPT_EXTENSIONS
)

# predefined Content delivery network host,
_IMAGE_CDN_HOSTS = (
    "mzstatic.com",
    "cloudinary.com",
    "imgix.net",
    "images.unsplash.com",
    "cdn.shopify.com",
    "twimg.com",
    "fbcdn.net",
    "googleusercontent.com",
    "akamaized.net",
)

_IMAGE_PATH_RE = re.compile(
    r"/image/|/images/|/img/|/thumb/|/photo/|/artwork/"
    r"|/\d+x\d+\."
    r"|\{\w+\}x\{\w+\}",
    re.IGNORECASE,
)

_VIDEO_PATH_RE = re.compile(
    r"/video/|/videos/|/stream/|/media/.*\.m3u8",
    re.IGNORECASE,
)


def _classify_by_path(url: str) -> str:
    try:
        parsed = urlparse(url)
    except Exception:
        return ""

    host = parsed.netloc.lower()
    path = parsed.path.lower()
    full = host + path

    # CDN host check
    if any(cdn in host for cdn in _IMAGE_CDN_HOSTS):
        if _VIDEO_PATH_RE.search(full):
            return "video"
        return "image"  # most CDN image hosts serve images by default

    # Path pattern check
    if _IMAGE_PATH_RE.search(full):
        return "image"
    if _VIDEO_PATH_RE.search(full):
        return "video"

    return ""


# ---- helpers ----------------------------------------------------------------

def classify_asset_type(url: str) -> str:
    """Return a media-type bucket string for a URL / filename."""
    lower = url.lower()
    for ext in IMAGE_EXTENSIONS:
        if lower.endswith(ext):
            return "image"
    for ext in VIDEO_EXTENSIONS:
        if lower.endswith(ext):
            return "video"
    for ext in AUDIO_EXTENSIONS:
        if lower.endswith(ext):
            return "audio"
    for ext in FONT_EXTENSIONS:
        if lower.endswith(ext):
            return "font"
    for ext in DOC_EXTENSIONS:
        if lower.endswith(ext):
            return "document"
    for ext in STYLE_EXTENSIONS:
        if lower.endswith(ext):
            return "stylesheet"
    for ext in SCRIPT_EXTENSIONS:
        if lower.endswith(ext):
            return "script"

    # Fallback: CDN / path-based heuristic
    path_type = _classify_by_path(url)
    if path_type:
        return path_type

    return "unidentified"


def is_static(url: str) -> bool:
    """
    Check if a URL points to a static asset.
    Uses extension matching first, then CDN/path heuristics.
    """
    if any(url.lower().endswith(ext) for ext in STATIC_EXTENSIONS):
        return True
    # Heuristic: CDN image/video URLs without standard extensions
    return bool(_classify_by_path(url))