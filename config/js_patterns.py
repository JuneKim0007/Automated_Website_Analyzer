"""
JavaScript dynamic-behavior detection via keyword pre-check + regex patterns.

Flow:
  1. Fast keyword scan (string `in`) — if no keyword hit, script is "static".
  2. Pattern-group scan — first matching group wins and names the behaviour.
  3. If keywords matched but no pattern group → "suspect" (flagged for agent).
"""

import re
from typing import List, Tuple

# ---- Fast keyword gate -------------------------------------------------------
JS_KEYWORDS: List[str] = [
    "fetch", "axios", "$.", "XMLHttpRequest",
    "history", "window", "document", "import",
    "addEventListener", "navigator.sendBeacon",
    "WebSocket", "EventSource",
]

# ---- Pattern groups (first match wins) ---------------------------------------
PATTERN_GROUPS: dict[str, List[str]] = {
    "fetch": [
        r"fetch\s*\(",
    ],
    "axios": [
        r"axios\s*\.\s*get\s*\(",
        r"axios\s*\.\s*post\s*\(",
        r"axios\s*\.\s*put\s*\(",
        r"axios\s*\.\s*delete\s*\(",
        r"axios\s*\.\s*patch\s*\(",
        r"axios\s*\.\s*request\s*\(",
        r"axios\s*\(",
    ],
    "jquery": [
        r"\$\s*\.\s*ajax\s*\(",
        r"\$\s*\.\s*get\s*\(",
        r"\$\s*\.\s*post\s*\(",
        r"\$\s*\.\s*getJSON\s*\(",
        r"\$\s*\.\s*load\s*\(",
    ],
    "xhr": [
        r"new\s+XMLHttpRequest",
        r"\.open\s*\(\s*['\"](?:GET|POST|PUT|DELETE|PATCH)",
    ],
    "websocket": [
        r"new\s+WebSocket\s*\(",
    ],
    "sse": [
        r"new\s+EventSource\s*\(",
    ],
    "beacon": [
        r"navigator\s*\.\s*sendBeacon\s*\(",
    ],
    "history": [
        r"history\s*\.\s*pushState",
        r"history\s*\.\s*replaceState",
        r"history\s*\.\s*go\s*\(",
        r"history\s*\.\s*back\s*\(",
        r"history\s*\.\s*forward\s*\(",
    ],
    "window_doc": [
        r"window\s*\.\s*location",
        r"document\s*\.\s*location",
        r"window\s*\.\s*open\s*\(",
    ],
    "dynamic_runtime": [
        r"eval\s*\(",
        r"Function\s*\(",
        r"setTimeout\s*\(",
        r"setInterval\s*\(",
        r"requestAnimationFrame\s*\(",
        r"import\s*\(",
        r"importScripts\s*\(",
    ],
    "event_listener": [
        r"\.addEventListener\s*\(",
        r"\.removeEventListener\s*\(",
    ],
}

# ---- HTTP method heuristics --------------------------------------------------
HTTP_METHOD_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"""method\s*:\s*['"]POST['"]""", re.I),      "POST"),
    (re.compile(r"""method\s*:\s*['"]PUT['"]""", re.I),        "PUT"),
    (re.compile(r"""method\s*:\s*['"]DELETE['"]""", re.I),     "DELETE"),
    (re.compile(r"""method\s*:\s*['"]PATCH['"]""", re.I),      "PATCH"),
    (re.compile(r"""method\s*:\s*['"]GET['"]""", re.I),        "GET"),
    (re.compile(r"axios\s*\.\s*post\s*\(", re.I),             "POST"),
    (re.compile(r"axios\s*\.\s*put\s*\(", re.I),              "PUT"),
    (re.compile(r"axios\s*\.\s*delete\s*\(", re.I),           "DELETE"),
    (re.compile(r"axios\s*\.\s*patch\s*\(", re.I),            "PATCH"),
    (re.compile(r"axios\s*\.\s*get\s*\(", re.I),              "GET"),
    (re.compile(r"""\.\s*open\s*\(\s*['"]POST['"]""", re.I),  "POST"),
    (re.compile(r"""\.\s*open\s*\(\s*['"]PUT['"]""", re.I),   "PUT"),
    (re.compile(r"""\.\s*open\s*\(\s*['"]DELETE['"]""", re.I), "DELETE"),
    (re.compile(r"""\.\s*open\s*\(\s*['"]GET['"]""", re.I),   "GET"),
    (re.compile(r"\$\s*\.\s*post\s*\(", re.I),                "POST"),
    (re.compile(r"\$\s*\.\s*get\s*\(", re.I),                 "GET"),
]


# ---- Public API --------------------------------------------------------------

def detect_dynamic_behavior(script_text: str) -> str:
    """
    Returns one of:
      "static"                       — no dynamic keywords found at all
      "dynamic_detected:<group>"     — matched a known pattern group
      "suspect"                      — keywords present but no pattern matched (flag for agent)
    """
    if not any(kw in script_text for kw in JS_KEYWORDS):
        return "static"

    for group_name, patterns in PATTERN_GROUPS.items():
        for pattern in patterns:
            if re.search(pattern, script_text):
                return f"dynamic_detected:{group_name}"

    return "suspect"


def infer_http_method(script_text: str) -> str:
    """Best-effort extraction of the HTTP method from a JS snippet."""
    for regex, method in HTTP_METHOD_PATTERNS:
        if regex.search(script_text):
            return method
    return "unidentified"