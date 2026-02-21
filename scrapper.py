import requests
import re
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse
import tldextract

STATIC_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".css", ".js", ".ico", ".woff", ".woff2", ".ttf",
    ".pdf", ".zip", ".rar", ".mp4", ".mp3"
}

MEANINGFUL_NAV_EVENTS = [
    # Mouse
    "onclick",        # button clicks, link clicks, load more
    "ondblclick",     # sometimes triggers actions
    "onmousedown",    # occasionally used for drag+drop triggers that initiate fetch
    "onmouseup",      # same as above
    # Form
    "onsubmit",       # form submission → GET/POST → navigation or API fetch
    "onchange",       # filters / selects / dynamic input
    "oninput",        # live search fields
    # Window / Document
    "onload",         # auto-run scripts on page load → can trigger fetches
    "onhashchange",   # SPA route change via hash
    "onpopstate"      # SPA navigation using history API
]

EVENT_ATTRIBUTES = [
    # Mouse
    "onclick", "ondblclick", "onmousedown", "onmouseup", "onmousemove",
    "onmouseover", "onmouseout", "onmouseenter", "onmouseleave", "oncontextmenu",

    # Keyboard
    "onkeydown", "onkeyup", "onkeypress",

    # Form
    "onsubmit", "onchange", "oninput", "onreset", "onfocus", "onblur", "onselect",

    # Window / Document
    "onload", "onunload", "onresize", "onscroll", "onerror", "onhashchange", "onpopstate",

    # Drag & Drop
    "ondrag", "ondragstart", "ondragend", "ondragenter", "ondragleave", "ondrop",

    # Clipboard
    "oncopy", "oncut", "onpaste",

    # Media
    "onplay", "onpause", "onended", "onvolumechange"
]

JS_KEYWORDS = ["fetch", "axios", "$.", "XMLHttpRequest", "history", "window", "document", "import"]
axios_patterns = [
    r"axios\.", r"axios\.get\(", r"axios\.post\(", r"axios\.request\("
]

fetch_patterns = [
    r"fetch\("
]

jquery_patterns = [
    r"\.ajax\(", r"\$.get\(", r"\$.post\(", r"\$.getJSON\(", r"\$.load\("
]

history_patterns = [
    r"history\.pushState", r"history\.replaceState",
    r"history\.go\(", r"history\.back\(", r"history\.forward\("
]

window_doc_patterns = [
    r"window\.location", r"window\.location\.href", r"window\.location\.assign\(",
    r"window\.location\.replace\(",
    r"document\.location", r"document\.location\.href",
    r"document\.location\.assign\(", r"document\.location\.replace\("
]

dynamic_runtime_patterns = [
    r"eval\(", r"Function\(", r"setTimeout\(", r"setInterval\(",
    r"requestAnimationFrame\(", r"import\(", r"importScripts\("
]
JS_DYNAMIC_PATTERNS = [
    # -------- Fetch / Ajax / HTTP calls --------
    r"fetch\(",                 # native fetch
    r"axios\.",                 # axios calls
    r"XMLHttpRequest",          # old-style AJAX
    r"\.ajax\(",                # jQuery AJAX
    r"\$.get\(",                # jQuery GET
    r"\$.post\(",               # jQuery POST
    r"\$.getJSON\(",             # jQuery getJSON
    r"\$.load\(",                # jQuery load
    r"axios\.get\(",             # axios GET
    r"axios\.post\(",            # axios POST
    r"axios\.request\(",         # generic axios request
    r"superagent\.",             # superagent library
    r"$.ajaxSetup\(",            # global jQuery AJAX setup

    # -------- SPA / Navigation / Redirection --------
    r"history\.pushState",       # SPA push
    r"history\.replaceState",    # SPA replace
    r"router\.push",             # Vue/React router push
    r"router\.replace",          # Vue/React router replace
    r"useNavigate\(",            # React Router v6
    r"window\.location",         # redirect / full page reload
    r"window\.location\.href",
    r"window\.location\.assign\(",
    r"window\.location\.replace\(",
    r"document\.location",
    r"document\.location\.href",
    r"document\.location\.assign\(",
    r"document\.location\.replace\(",

    # -------- Framework / Library hints --------
    r"next/router",              # Next.js
    r"react-router",             # React Router
    r"vue-router",               # Vue Router
    r"angular\.router",          # Angular
    r"ngRoute",                  # AngularJS
    r"vue\.router",              # Vue Router instance
    r"history\.go\(",            # history navigation
    r"history\.back\(",          # history navigation
    r"history\.forward\(",       # history navigation

    # -------- Dynamic JS calls / eval / runtime --------
    r"eval\(",                   # dynamic JS execution
    r"Function\(",               # dynamic JS creation
    r"setTimeout\(",             # delayed calls
    r"setInterval\(",            # periodic calls
    r"requestAnimationFrame\(",  # dynamic frame updates
    r"import\(",                 # dynamic import (ES modules)
    r"importScripts\("            # Web Workers
]

if "axios" in script_text:
    check_patterns(axios_patterns, script_text)
elif "fetch" in script_text:
    check_patterns(fetch_patterns, script_text)
elif "$." in script_text:
    check_patterns(jquery_patterns, script_text)
elif "history" in script_text:
    check_patterns(history_patterns, script_text)
elif "window" in script_text or "document" in script_text:
    check_patterns(window_doc_patterns, script_text)
elif any(k in script_text for k in ["eval", "Function", "setTimeout", "setInterval", "import"]):
    check_patterns(dynamic_runtime_patterns, script_text)
def analyze_page(url):

    results = {
        "internal_routes": [],
        "external_routes": [],
        "static_assets": [],
        "dynamic_behaviors": {
            "forms": [],
            "event_handlers": [],
            "js_dynamic_patterns_found": [],
            "spa_router_detected": False
        }
    }

    response = requests.get(url, timeout=5)
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    base_domain = ".".join(tldextract.extract(url)[1:3])

    # 🔥 SINGLE PASS
    for element in soup.descendants:

        if not hasattr(element, "name"):
            continue

        # ------------------------
        # A TAG
        # ------------------------
        if element.name == "a":
            href = element.get("href")
            if not href:
                continue

            text = element.get_text(strip=True)
            if len(text) < 100:
                continue

            full_url = urljoin(url, href)
            parsed = urlparse(full_url)

            if any(parsed.path.lower().endswith(ext) for ext in STATIC_EXTENSIONS):
                results["static_assets"].append(full_url)
                continue

            link_domain = ".".join(tldextract.extract(full_url)[1:3])

            if link_domain == base_domain:
                results["internal_routes"].append(full_url)
            else:
                results["external_routes"].append(full_url)

        # ------------------------
        # FORMS
        # ------------------------
        elif element.name == "form":
            form_info = {
                "method": element.get("method", "GET").upper(),
                "action": element.get("action"),
                "inputs": []
            }

            for input_tag in element.find_all("input"):
                form_info["inputs"].append({
                    "name": input_tag.get("name"),
                    "type": input_tag.get("type")
                })

            results["dynamic_behaviors"]["forms"].append(form_info)

        # ------------------------
        # EVENT HANDLERS
        # ------------------------
        for attr in EVENT_ATTRIBUTES:
            if element.has_attr(attr):
                results["dynamic_behaviors"]["event_handlers"].append({
                    "tag": element.name,
                    "event": attr
                })

        # ------------------------
        # SCRIPT TAG
        # ------------------------
        if element.name == "script" and element.string:
            content = element.string

            for pattern in JS_DYNAMIC_PATTERNS:
                if re.search(pattern, content):
                    results["dynamic_behaviors"]["js_dynamic_patterns_found"].append(pattern)

            if "react-router" in content or "vue-router" in content:
                results["dynamic_behaviors"]["spa_router_detected"] = True

    return results