"""
js_regex_fallback.py — Regex-based JavaScript analysis.

FALLBACK ONLY.  Used when tree-sitter / tree-sitter-javascript are not installed.
Limitations vs the AST path (js_ast_analyzer.py):
  • HTTP method inference is block-level, not per-call
  • Cannot track captured nodes — some URLs may be double-counted
  • Template interpolation detection is heuristic

Architecture:
  1. Keyword pre-check  → bail early if "static"
  2. Pattern-group scan → identify *what kind* of dynamic behaviour
  3. URL extraction      → pull out all string literals that look like URLs/paths
  4. HTTP method inference
  5. Return structured list of ExtractedItems, already tagged as dynamic sub-type
"""

from __future__ import annotations

import re
from typing import Sequence

from config.js_patterns import detect_dynamic_behavior, infer_http_method, PATTERN_GROUPS
from config.static_extensions import is_static, classify_asset_type
from analyzer.utils import resolve_url, is_internal
from analyzer.result_types import ExtractedItem

# Regex to pull string literals (single-quoted, double-quoted, back-ticked without interpolation).
_STRING_LITERAL = re.compile(
    r"""(?:["'])((?:https?://|/)[^\s"'<>]+?)(?:["'])"""
    r"""|"""
    r"""`((?:https?://|/)[^\s`<>]+?)`"""
)

# Matches template strings WITH interpolation — we flag these as unresolvable.
_TEMPLATE_INTERPOLATED = re.compile(r"`[^`]*\$\{[^}]+\}[^`]*`")


def _extract_urls_from_js(js_text: str) -> list[tuple[str, int]]:
    """
    Pull every URL-like string literal from JS source.
    Returns list of (raw_url, approx_line_number).
    """
    results: list[tuple[str, int]] = []
    for m in _STRING_LITERAL.finditer(js_text):
        url = m.group(1) or m.group(2)
        if url:
            # approximate line number
            line = js_text[:m.start()].count("\n") + 1
            results.append((url, line))
    return results


def analyze_script_regex(
    js_text: str,
    base_url: str,
    base_domain: str,
    origin: str = "<inline>",
) -> list[ExtractedItem]:
    """
    Analyze a single <script> block or .js file body.

    Returns a list of ExtractedItems with metadata already filled in.
    The caller (html_analyzer) routes these into the correct PageResults bucket.
    """
    items: list[ExtractedItem] = []

    # ---- Step 1: keyword pre-check ----
    behaviour = detect_dynamic_behavior(js_text)
    if behaviour == "static":
        # No dynamic keywords at all — still scan for plain URL references.
        pass  # fall through to URL extraction below

    is_dynamic = behaviour.startswith("dynamic_detected") or behaviour == "suspect"
    dynamic_group = behaviour.split(":")[-1] if ":" in behaviour else behaviour

    # ---- Step 2: HTTP method heuristic (for the whole block) ----
    block_method = infer_http_method(js_text) if is_dynamic else "unidentified"

    # ---- Step 3: Extract URL string literals ----
    for raw_url, line in _extract_urls_from_js(js_text):
        resolved = resolve_url(raw_url, base_url)

        item = ExtractedItem(
            url=resolved,
            origin=origin,
            line_start=line,
            raw=raw_url,
            http_method=block_method,
            dynamic_group=dynamic_group if is_dynamic else "",
        )

        if is_static(resolved):
            item.asset_type = classify_asset_type(resolved)
        else:
            item.asset_type = ""

        items.append(item)

    # ---- Step 4: If dynamic but we found no URLs, still record the behaviour ----
    if is_dynamic and not items:
        items.append(ExtractedItem(
            origin=origin,
            raw=js_text[:300],  # truncated raw for the agent
            http_method=block_method,
            dynamic_group=dynamic_group,
        ))

    # ---- Step 5: Flag template-interpolated strings as unresolvable ----
    for m in _TEMPLATE_INTERPOLATED.finditer(js_text):
        line = js_text[:m.start()].count("\n") + 1
        items.append(ExtractedItem(
            origin=origin,
            line_start=line,
            raw=m.group(0)[:200],
            dynamic_group="template_interpolation",
        ))

    # Tag every item from a dynamic block
    for item in items:
        if is_dynamic:
            item.dynamic_group = item.dynamic_group or dynamic_group

    return items