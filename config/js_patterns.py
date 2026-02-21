import re

# In normal mode, keyword would be first checked then will check any matching patterns based on the found keyword.
JS_KEYWORDS = ["fetch", "axios", "$.", "XMLHttpRequest", "history", "window", "document", "import"]


PATTERN_GROUPS = {
    "axios": [
        r"axios\.", r"axios\.get\(", r"axios\.post\(", r"axios\.request\("
    ],
    "fetch": [
        r"fetch\("
    ],
    "jquery": [
        r"\.ajax\(", r"\$.get\(", r"\$.post\(", r"\$.getJSON\(", r"\$.load\("
    ],
    "history": [
        r"history\.pushState", r"history\.replaceState",
        r"history\.go\(", r"history\.back\(", r"history\.forward\("
    ],
    "window_doc": [
        r"window\.location", r"window\.location\.href", r"window\.location\.assign\(",
        r"window\.location\.replace\(",
        r"document\.location", r"document\.location\.href",
        r"document\.location\.assign\(", r"document\.location\.replace\("
    ],
    "dynamic_runtime": [
        r"eval\(", r"Function\(", r"setTimeout\(", r"setInterval\(",
        r"requestAnimationFrame\(", r"import\(", r"importScripts\("
    ]
}


JS_DYNAMIC_PATTERNS = [p for group in PATTERN_GROUPS.values() for p in group]

def detect_dynamic_behavior(script_text: str):
    if not any(keyword in script_text for keyword in JS_KEYWORDS):
        return "static"

    for group_name, patterns in PATTERN_GROUPS.items():
        for pattern in patterns:
            if re.search(pattern, script_text):
                return f"dynamic_detected:{group_name}"

    for pattern in JS_DYNAMIC_PATTERNS:
        if re.search(pattern, script_text):
            return "dynamic_detected:unknown_group"

    if "<script" in script_text:
        return ""

    return "unknown"