"""
page_fetcher.py — Two-strategy HTML fetcher.

Strategy 1: requests (default)
    - Fast, lightweight, no browser overhead
    - Gets server-sent HTML only
    - Works for: static sites, server-rendered pages
    - Fails for: SPAs (LinkedIn, Twitter/X, modern React/Angular/Vue apps)

Strategy 2: playwright (headless browser)
    - Launches headless Chromium, executes all JS, waits for DOM to settle
    - Gets the *rendered* DOM including JS-generated elements
    - Works for: everything, including SPAs
    - Requires: pip install playwright && playwright install chromium

Usage:
    html = fetch_page(url)                         # auto-detect
    html = fetch_page(url, renderer="requests")    # force static
    html = fetch_page(url, renderer="playwright")  # force headless

The module probes for playwright at import time and reports availability.
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

# ---- Availability probe -----------------------------------------------------

_HAS_PLAYWRIGHT = False
try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    _HAS_PLAYWRIGHT = True
except ImportError:
    pass

_HAS_REQUESTS = False
try:
    import requests as _requests_mod  # noqa: F401
    _HAS_REQUESTS = True
except ImportError:
    pass


# ---- Shared constants -------------------------------------------------------

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# SPA indicators — if the server-sent HTML matches these patterns,
# the page is likely JS-rendered and needs playwright.
_SPA_INDICATORS = [
    'id="__next"',          # Next.js
    'id="__nuxt"',          # Nuxt
    'id="app"',             # Vue / generic SPA
    'id="root"',            # React CRA
    'ng-app',               # Angular 1.x
    'ng-version',           # Angular 2+
    '<ember-',              # Ember (LinkedIn)
    'window.__INITIAL_STATE__',  # SSR hydration shells
    'clientSideRender',     # LinkedIn specific
]


# ---- Strategy 1: requests ---------------------------------------------------

def _fetch_requests(url: str, timeout: int = 15) -> str:
    """Fetch raw server-sent HTML via requests."""
    import requests
    resp = requests.get(url, timeout=timeout, headers=_DEFAULT_HEADERS)
    resp.raise_for_status()
    return resp.text


# ---- Strategy 2: playwright -------------------------------------------------

def _fetch_playwright(
    url: str,
    wait_until: str = "networkidle",
    extra_wait_ms: int = 2000,
    timeout: int = 30000,
) -> str:
    """
    Fetch fully-rendered DOM via headless Chromium.

    Parameters
    ----------
    wait_until : playwright navigation event to wait for.
                 "networkidle" waits until no network requests for 500ms.
                 Alternatives: "load", "domcontentloaded", "commit".
    extra_wait_ms : additional time (ms) after wait_until to let late
                    JS finish (e.g. lazy-loaded components).
    timeout : max time (ms) for the page load.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=_DEFAULT_HEADERS["User-Agent"],
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until=wait_until, timeout=timeout)

            # Extra wait for late-binding JS (SPA route transitions, etc.)
            if extra_wait_ms > 0:
                page.wait_for_timeout(extra_wait_ms)

            # Return the fully rendered DOM, not the original source
            html = page.content()
        finally:
            context.close()
            browser.close()

    return html


# ---- Auto-detection ---------------------------------------------------------

def _is_likely_spa(html: str) -> bool:
    """
    Heuristic: does the server-sent HTML look like an SPA shell?
    Checks for known framework markers in the first 50KB.
    """
    sample = html[:50_000].lower()
    matches = sum(1 for indicator in _SPA_INDICATORS if indicator.lower() in sample)
    # Also check: very few <a> tags in the body is suspicious for a real page
    a_tag_count = sample.count("<a ")
    body_length = len(sample)

    # SPA shell: has framework markers OR suspiciously few links for the page size
    if matches >= 2:
        return True
    if matches >= 1 and a_tag_count < 5 and body_length > 5000:
        return True
    return False


# ---- Public API --------------------------------------------------------------

class FetchResult:
    """Wraps the fetched HTML with metadata about how it was obtained."""
    def __init__(self, html: str, url: str, renderer: str, is_spa_detected: bool = False):
        self.html = html
        self.url = url
        self.renderer = renderer
        self.is_spa_detected = is_spa_detected
        self.byte_count = len(html.encode("utf-8"))


def fetch_page(
    url: str,
    renderer: str = "auto",
    timeout: int = 20,
    playwright_wait: str = "networkidle",
    playwright_extra_wait_ms: int = 2000,
) -> FetchResult:
    """
    Fetch a web page's HTML.

    Parameters
    ----------
    renderer : "auto" | "requests" | "playwright"
        - "auto": try requests first, detect SPA, escalate to playwright
        - "requests": static fetch only
        - "playwright": headless browser only

    Returns FetchResult with .html, .renderer, .is_spa_detected
    """

    if renderer == "playwright":
        if not _HAS_PLAYWRIGHT:
            raise RuntimeError(
                "playwright requested but not installed. "
                "Run: pip install playwright && playwright install chromium"
            )
        html = _fetch_playwright(url, playwright_wait, playwright_extra_wait_ms, timeout * 1000)
        return FetchResult(html, url, "playwright")

    if renderer == "requests":
        if not _HAS_REQUESTS:
            raise RuntimeError("requests library not installed. Run: pip install requests")
        html = _fetch_requests(url, timeout)
        return FetchResult(html, url, "requests")

    # ---- AUTO mode ----

    # Step 1: Try requests first (fast)
    if _HAS_REQUESTS:
        try:
            html = _fetch_requests(url, timeout)
        except Exception as e:
            logger.warning("requests fetch failed (%s), trying playwright", e)
            html = None

        if html:
            spa_detected = _is_likely_spa(html)

            if not spa_detected:
                return FetchResult(html, url, "requests", is_spa_detected=False)

            # SPA detected — escalate to playwright if available
            logger.info("SPA shell detected for %s — escalating to playwright", url)

            if _HAS_PLAYWRIGHT:
                html_rendered = _fetch_playwright(
                    url, playwright_wait, playwright_extra_wait_ms, timeout * 1000
                )
                return FetchResult(html_rendered, url, "playwright", is_spa_detected=True)
            else:
                logger.warning(
                    "SPA detected but playwright not available. "
                    "Results will be incomplete. "
                    "Install: pip install playwright && playwright install chromium"
                )
                return FetchResult(html, url, "requests", is_spa_detected=True)

    # Step 2: Only playwright available
    if _HAS_PLAYWRIGHT:
        html = _fetch_playwright(url, playwright_wait, playwright_extra_wait_ms, timeout * 1000)
        return FetchResult(html, url, "playwright")

    raise RuntimeError("No HTTP library available. Install requests or playwright.")


def get_capabilities() -> dict:
    """Report which fetchers are available."""
    return {
        "requests": _HAS_REQUESTS,
        "playwright": _HAS_PLAYWRIGHT,
        "recommended_for_spa": "playwright" if _HAS_PLAYWRIGHT else "requests (degraded)",
    }