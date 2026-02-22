from __future__ import annotations
from bs4 import BeautifulSoup, Tag, Comment

from config.event_attributes import EVENT_ATTRIBUTES, MEANINGFUL_NAV_EVENTS
from config.static_extensions import is_static, classify_asset_type
from analyzer.utils import is_internal, resolve_url
from analyzer.result_types import ExtractedItem, PageResults
from analyzer.js_analyzer import analyze_script


_STATIC_SRC_TAGS: dict[str, str] = {
    "img": "src",
    "video":"src",
    "audio":"src",
    "source":"src",
    "embed": "src",
    "object": "data",
}

#<link rel="..."> values 
_LINK_ASSET_RELS = frozenset({
    "stylesheet", "icon", "shortcut icon", "apple-touch-icon",
    "apple-touch-icon-precomposed", "preload", "prefetch",
    "preconnect", "dns-prefetch", "manifest", "mask-icon",
})


def analyze_page(html: str, page_url: str, base_domain: str) -> PageResults:
    
    results = PageResults(url=page_url, base_domain=base_domain)
    soup = BeautifulSoup(html, "lxml") #only .html should be passed!

    _seen: set[str] = set()

    def _already_captured(url: str) -> bool:
        if url in _seen:
            return True
        _seen.add(url)
        return False

    #Find all hyperlinks (<a href="...">) on the page.
    #Clean up and normalize href
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        #if dynamic behavior continue.
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        resolved = resolve_url(href, page_url)
        if _already_captured(resolved):
            continue

        line = _approx_line(tag)
        #hard coded maximum up to :300
        # need to define that in constant.
        item = ExtractedItem(
            url=resolved,
            origin=page_url,
            line_start=line,
            raw=str(tag)[:300],
        )

        # If the <a> href points to a CDN image/video URL (not a link to other (sub)domains),
        # classify it as a static asset instead of a link.
        if is_static(resolved):
            item.asset_type = classify_asset_type(resolved)
            results.static_assets.append(item)
        elif is_internal(resolved, base_domain):
            results.internal_links.append(item)
        else:
            results.external_links.append(item)

    # for static assets in html files.
    for tag_name, attr in _STATIC_SRC_TAGS.items():
        for tag in soup.find_all(tag_name):
            #get attribute and if None just take ""
            src = (tag.get(attr) or "").strip()
            if not src:
                srcset = tag.get("srcset", "")
                if srcset:
                    src = srcset.split(",")[0].split()[0]
            if not src:
                continue

            resolved = resolve_url(src, page_url)
            #to remove duplicates
            if _already_captured(resolved):
                continue

            #hard coded maximum up to :300
            # need to define that in constant.
            item = ExtractedItem(
                url=resolved,
                origin=page_url,
                line_start=_approx_line(tag),
                raw=str(tag)[:300],
                asset_type=classify_asset_type(resolved),
            )
            results.static_assets.append(item)

    #get <link rel =""> tags
    for tag in soup.find_all("link", href=True):
        rel_list = tag.get("rel", [])
        #returns rel as a list; normalize to lowercase set
        if isinstance(rel_list, str):
            rel_list = [rel_list]
        rel_set = {r.lower() for r in rel_list}

        # checks if this matches with the predefined list.
        # need to move to th constants.py or some other structure for customization.
        if not rel_set & _LINK_ASSET_RELS:
            continue

        href = tag["href"].strip()
        if not href:
            continue

        resolved = resolve_url(href, page_url)
        if _already_captured(resolved):
            continue

        #hard coded maximum up to :300
        # need to define that in constant.
        item = ExtractedItem(
            url=resolved,
            origin=page_url,
            line_start=_approx_line(tag),
            raw=str(tag)[:300],
            asset_type=classify_asset_type(resolved),
        )
        results.static_assets.append(item)
    # extract any form that requires user input
    # forms are inherently dynamic so anything inside of the form should be classified as dynamic behaviors
    for tag in soup.find_all("form"):
        action = (tag.get("action") or "").strip()
        method = (tag.get("method") or "GET").upper()
        resolved = resolve_url(action, page_url) if action else page_url

        item = ExtractedItem(
            url=resolved,
            origin=page_url,
            line_start=_approx_line(tag),
            #adjusted to 500 since this would be often lengthier.
            raw=str(tag)[:500],
            http_method=method,
            dynamic_group="form",
        )

        if method == "POST":
            results.dynamic_behavior.post_requests.append(item)
        else:
            results.dynamic_behavior.get_requests.append(item)

    #checks all html tags with event attributes such as on_clink
    for tag in soup.find_all(True):
        for attr in tag.attrs:
            if attr.lower() not in EVENT_ATTRIBUTES:
                continue
            handler_code = tag.get(attr, "")
            if not handler_code:
                continue

            item = ExtractedItem(
                origin=page_url,
                line_start=_approx_line(tag),
                raw=f'{attr}="{handler_code[:200]}"',
                dynamic_group="inline_event",
                is_meaningful_nav=(attr.lower() in MEANINGFUL_NAV_EVENTS),
            )
            _enrich_inline_event(item, handler_code, page_url, base_domain, results, _seen)

            results.dynamic_behavior.event_listeners.append(item)

    # checks the <script> tags that will be needed to send to js analyzer
    script_idx = 0
    for tag in soup.find_all("script"):
        #each script found will have idx as primary key auto increment.
        script_idx += 1

        # external script src => record as static asset
        src = (tag.get("src") or "").strip()
        if src:
            resolved = resolve_url(src, page_url)
            if not _already_captured(resolved):
                results.static_assets.append(ExtractedItem(
                    url=resolved,
                    origin=page_url,
                    line_start=_approx_line(tag),
                    raw=f'<script src="{src}">',
                    asset_type="script",
                ))

        js_text = tag.string
        if not js_text or not js_text.strip():
            continue
        
        origin_label = f"<script block #{script_idx}>"
        js_items = analyze_script(
            js_text=js_text,
            base_url=page_url,
            base_domain=base_domain,
            origin=origin_label,
        )

        _route_js_items(js_items, base_domain, results, _seen)

    return results


#approxiate the line number

def _approx_line(tag: Tag) -> int:
    """Best-effort line number from a BS4 tag (uses sourceline if available)."""
    return getattr(tag, "sourceline", 0) or 0


def _enrich_inline_event(
    item: ExtractedItem,
    handler_code: str,
    page_url: str,
    base_domain: str,
    results: PageResults,
    _seen: set[str],
):
    """for data wrapped around by <script> tags"""
    origin_label = f'inline:{item.raw[:60]}'

    js_items = analyze_script(
        js_text=handler_code,
        base_url=page_url,
        base_domain=base_domain,
        origin=origin_label,
    )

    if not js_items:
        return

    for ji in js_items:
        if ji.url:
            item.url = ji.url
            break

    # Route all extracted items through the standard dynamic router
    _route_js_items(js_items, base_domain, results, _seen)


def _already_captured_check(url: str, _seen: set[str]) -> bool:
    if url in _seen:
        return True
    _seen.add(url)
    return False


def _route_js_items(
    js_items: list[ExtractedItem],
    base_domain: str,
    results: PageResults,
    _seen: set[str],
):
    """
    Route items produced by js_analyzer into the correct PageResults bucket.
    """
    for item in js_items:
        # Skip duplicates
        if item.url and _already_captured_check(item.url, _seen):
            continue

        is_dyn = bool(item.dynamic_group)

        if item.asset_type and item.asset_type != "unidentified":
            if is_dyn:
                results.dynamic_behavior.static_assets.append(item)
            else:
                results.static_assets.append(item)
            continue

        if item.url:
            internal = is_internal(item.url, base_domain)

            if is_dyn:
                method_upper = item.http_method.upper() if item.http_method else ""
                if method_upper == "POST":
                    results.dynamic_behavior.post_requests.append(item)
                elif method_upper in ("GET",):
                    results.dynamic_behavior.get_requests.append(item)
                elif internal:
                    results.dynamic_behavior.internal_links.append(item)
                else:
                    results.dynamic_behavior.external_links.append(item)
            else:
                if internal:
                    results.internal_links.append(item)
                else:
                    results.external_links.append(item)
            continue

        if is_dyn:
            results.dynamic_behavior.unidentified.append(item)