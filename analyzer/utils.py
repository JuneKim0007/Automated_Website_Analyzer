from __future__ import annotations

from urllib.parse import urlparse, urljoin

def _has_valid_netloc(netloc: str) -> bool:
    if not netloc:
        return False
    host = netloc.split(":")[0]
    if host == "localhost":
        return True
    if "." in host:
        return True
    return False


def normalise_url(raw: str) -> str | None:
    """
    Purpose: Extract the raw url and normalize into the format : "https://<...>"
    """
    raw = raw.strip() #strip taps, whitespace
    if not raw:
        return None

    if raw.startswith("//"):
        raw = "https:" +raw

    elif not raw.startswith(("http://", "https://")):
        raw = "https://" + raw

    #checks the network location
    parsed = urlparse(raw)
    if not _has_valid_netloc(parsed.netloc):
        return None

    return parsed.geturl()

def validate_url(raw: str) -> tuple[str, str] | None:
    url = normalise_url(raw)
    if url is None:
        return None
    domain = extract_base_domain(url)
    if not domain:
        return None
    return url, domain

def extract_base_domain(url: str) -> str:
    return urlparse(url).netloc.lower()

def is_internal(url: str, base_domain: str) -> bool:
    """
    ### Args: 
        - **url:** targeted domain that is going to be compared against base_domain
        - **base_domain:** domain that will be used as a base domain to check the targeted url.
    """
    parsed = urlparse(url)
    if not parsed.netloc:
        return True

    target = parsed.netloc.lower()

    if target == base_domain:
        return True

    if target.endswith("." + base_domain):
        return True

    if base_domain.endswith("." + target):
        return True

    return False

def resolve_url(href: str, base_url: str) -> str:
    """
    Resolve a possibly-relative href against the page's base URL.

    Simply returns the href prefixed with the **base_domain.**
    """
    return urljoin(base_url, href)