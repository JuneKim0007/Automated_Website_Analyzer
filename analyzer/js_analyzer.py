
from __future__ import annotations

import logging
from analyzer.result_types import ExtractedItem

logger = logging.getLogger(__name__)

_USE_TREE_SITTER = False

try:
    from analyzer.js_ast_analyzer import analyze_script_ast
    _USE_TREE_SITTER = True
except (ImportError, Exception) as _e:
    logger.warning(
        "tree-sitter not available (%s). "
        "Falling back to regex-based JS analysis. "
        "Install tree-sitter + tree-sitter-javascript for per-call method extraction.",
        _e,
    )
    from analyzer.js_regex_fallback import analyze_script_regex

def analyze_script(
    js_text: str,
    base_url: str,
    base_domain: str,
    origin: str = "<inline>",
) -> list[ExtractedItem]:
    """
    Analyze a JavaScript code block and return classified ExtractedItems.

    Automatically selects the best available backend:
      • tree-sitter AST  (preferred — per-call accuracy)
      • regex fallback    (degraded — block-level heuristic)
    """
    if _USE_TREE_SITTER:
        return analyze_script_ast(
            js_text=js_text,
            base_url=base_url,
            base_domain=base_domain,
            origin=origin,
        )
    else:
        return analyze_script_regex(
            js_text=js_text,
            base_url=base_url,
            base_domain=base_domain,
            origin=origin,
        )


def is_tree_sitter_active() -> bool:
    """Let callers check which backend is in use."""
    return _USE_TREE_SITTER