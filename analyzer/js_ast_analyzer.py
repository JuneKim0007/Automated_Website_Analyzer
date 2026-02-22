from __future__ import annotations
from tree_sitter import Parser, Language
import tree_sitter_javascript
from urllib.parse import urljoin

from config.static_extensions import is_static, classify_asset_type
from config.js_patterns import detect_dynamic_behavior, PATTERN_GROUPS
from analyzer.utils import resolve_url, is_internal
from analyzer.result_types import ExtractedItem


def _make_parser() -> Parser:
    p = Parser()
    p.language = Language(tree_sitter_javascript.language())
    return p


def _node_text(node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8")


def _extract_string_value(node, source_bytes: bytes) -> str | None:
    """
    If *node* is a string or template_string without interpolation such as "abc ${example}"
    return the normalized string value.
    """
    if node.type == "string":
        raw = _node_text(node, source_bytes)
        return raw.strip("\"'")

    if node.type == "template_string":
        for child in node.children:
            if child.type == "template_substitution":
                return None 
        raw = _node_text(node, source_bytes)
        return raw.strip("`")

    return None


def _has_interpolation(node, source_bytes: bytes) -> bool:
    if node.type != "template_string":
        return False
    for child in node.children:
        if child.type == "template_substitution":
            return True
    return False


def _extract_object_property(obj_node, key: str, source_bytes: bytes) -> str | None:
    if obj_node.type != "object":
        return None
    for child in obj_node.children:
        if child.type == "pair":
            k = child.child_by_field_name("key")
            v = child.child_by_field_name("value")
            if k and v:
                k_text = _node_text(k, source_bytes).strip("\"'")
                if k_text == key:
                    return _extract_string_value(v, source_bytes) or _node_text(v, source_bytes).strip("\"'")
    return None


def _get_args_list(args_node, source_bytes: bytes):
    if args_node is None:
        return
    for child in args_node.children:
        if child.type not in ("(", ")", ","):
            yield child


class _Walker:
    """
    Stateful single-pass AST walker.

    _captured_ranges tracks (start_byte, end_byte) of string nodes already
    consumed by a call handler so the generic string visitor skips them.
    """

    def __init__(self, source_bytes: bytes, base_url: str, base_domain: str, origin: str):
        self.source = source_bytes
        self.base_url = base_url
        self.base_domain = base_domain
        self.origin = origin
        self.items: list[ExtractedItem] = []
        self._captured_ranges: set[tuple[int, int]] = set()

    # ---- mark a node as consumed -----------------------------------------
    def _mark_captured(self, node):
        self._captured_ranges.add((node.start_byte, node.end_byte))

    def _is_captured(self, node) -> bool:
        return (node.start_byte, node.end_byte) in self._captured_ranges

    # ---- line helpers ----------------------------------------------------
    def _lines(self, node) -> tuple[int, int]:
        return node.start_point[0] + 1, node.end_point[0] + 1

    # ---- build an item ---------------------------------------------------
    def _make_item(self, **kwargs) -> ExtractedItem:
        return ExtractedItem(origin=self.origin, **kwargs)

    # ---- recursive walk --------------------------------------------------
    def walk(self, node):
        # 1) call_expression  — fetch / axios / jquery / xhr / addEventListener
        if node.type == "call_expression":
            self._handle_call(node)

        # 2) assignment_expression  — window.location = ...
        elif node.type == "assignment_expression":
            self._handle_assignment(node)

        # 3) bare string / template_string  — only if NOT already captured
        elif node.type in ("string", "template_string"):
            if not self._is_captured(node):
                self._handle_bare_string(node)

        # Recurse into children
        for child in node.children:
            self.walk(child)

    # ---- call_expression handlers ----------------------------------------

    def _handle_call(self, node):
        func_node = node.child_by_field_name("function")
        args_node = node.child_by_field_name("arguments")
        if not func_node:
            return

        func_text = _node_text(func_node, self.source)
        start_line, end_line = self._lines(node)
        args = list(_get_args_list(args_node, self.source)) if args_node else []

        # ── fetch(url, {method: ...}) ────────────────────────────────
        if func_text == "fetch":
            self._handle_fetch(args, start_line, end_line, node)

        # ── axios.get(url) / axios.post(url) / axios(config) ────────
        elif func_text.startswith("axios"):
            self._handle_axios(func_text, args, start_line, end_line, node)

        # ── $.ajax({url, method}) / $.get(url) / $.post(url) ────────
        elif func_text in ("$.ajax", "$.get", "$.post", "$.getJSON", "$.load"):
            self._handle_jquery(func_text, args, start_line, end_line, node)

        # ── xhr.open('METHOD', url) ─────────────────────────────────
        elif func_text.endswith(".open") and len(args) >= 2:
            self._handle_xhr_open(args, start_line, end_line, node)

        # ── addEventListener ────────────────────────────────────────
        elif func_text.endswith("addEventListener"):
            self.items.append(self._make_item(
                line_start=start_line, line_end=end_line,
                raw=_node_text(node, self.source)[:300],
                dynamic_group="event_listener",
            ))

        # ── window.location.assign(url) / replace(url) ─────────────
        elif func_text in (
            "window.location.assign", "window.location.replace",
            "document.location.assign", "document.location.replace",
            "window.open",
        ):
            url = self._first_string_arg(args)
            if url:
                self._emit_url(url, start_line, end_line, "window_doc", "GET", node)

        # ── navigator.sendBeacon(url) ───────────────────────────────
        elif func_text == "navigator.sendBeacon":
            url = self._first_string_arg(args)
            if url:
                self._emit_url(url, start_line, end_line, "beacon", "POST", node)

        # ── new WebSocket(url) / new EventSource(url) ───────────────
        elif func_text in ("WebSocket", "EventSource"):
            url = self._first_string_arg(args)
            if url:
                self._emit_url(url, start_line, end_line, func_text.lower(), "GET", node)

    def _handle_fetch(self, args, start_line, end_line, node):
        url = self._first_string_arg(args)
        method = "GET"  # fetch defaults to GET
        if len(args) >= 2 and args[1].type == "object":
            m = _extract_object_property(args[1], "method", self.source)
            if m:
                method = m.upper()
        if url:
            self._mark_string_args(args[:1])
            self._emit_url(url, start_line, end_line, "fetch", method, node)
        else:
            # fetch with a variable or expression — record as unresolvable
            self.items.append(self._make_item(
                line_start=start_line, line_end=end_line,
                raw=_node_text(node, self.source)[:300],
                dynamic_group="fetch",
                http_method=method,
            ))

    def _handle_axios(self, func_text, args, start_line, end_line, node):
        # axios.get / axios.post / axios.put etc.  → method from member name
        # axios({url: ..., method: ...})            → method from config
        parts = func_text.split(".")
        if len(parts) == 2 and parts[1] in ("get", "post", "put", "delete", "patch", "head", "options"):
            method = parts[1].upper()
            url = self._first_string_arg(args)
        elif len(parts) == 1 and args and args[0].type == "object":
            # axios(config)
            url_val = _extract_object_property(args[0], "url", self.source)
            method_val = _extract_object_property(args[0], "method", self.source)
            url = url_val
            method = (method_val or "GET").upper()
        else:
            url = self._first_string_arg(args)
            method = "GET"

        if url:
            self._mark_string_args(args[:1])
            self._emit_url(url, start_line, end_line, "axios", method, node)
        else:
            self.items.append(self._make_item(
                line_start=start_line, line_end=end_line,
                raw=_node_text(node, self.source)[:300],
                dynamic_group="axios",
                http_method=method,
            ))

    def _handle_jquery(self, func_text, args, start_line, end_line, node):
        method_map = {"$.get": "GET", "$.getJSON": "GET", "$.load": "GET", "$.post": "POST"}

        if func_text == "$.ajax" and args and args[0].type == "object":
            url = _extract_object_property(args[0], "url", self.source)
            method = (_extract_object_property(args[0], "method", self.source) or
                      _extract_object_property(args[0], "type", self.source) or "GET").upper()
        else:
            url = self._first_string_arg(args)
            method = method_map.get(func_text, "GET")

        if url:
            self._mark_string_args(args[:1])
            self._emit_url(url, start_line, end_line, "jquery", method, node)

    def _handle_xhr_open(self, args, start_line, end_line, node):
        method_str = _extract_string_value(args[0], self.source) if args[0].type == "string" else None
        url_str = _extract_string_value(args[1], self.source) if args[1].type == "string" else None
        method = (method_str or "GET").upper()
        if url_str:
            self._mark_string_args(args[:2])
            self._emit_url(url_str, start_line, end_line, "xhr", method, node)

    # ---- assignment handler  (window.location = url) ---------------------

    def _handle_assignment(self, node):
        left = node.child_by_field_name("left")
        right = node.child_by_field_name("right")
        if not left or not right:
            return

        left_text = _node_text(left, self.source)
        if "window.location" not in left_text and "document.location" not in left_text:
            return

        url = _extract_string_value(right, self.source)
        if url:
            self._mark_captured(right)
            start_line, end_line = self._lines(node)
            self._emit_url(url, start_line, end_line, "window_doc", "GET", node)

    # ---- bare string handler (URLs not consumed by any call) -------------

    def _handle_bare_string(self, node):
        # Template strings with interpolation → flag
        if _has_interpolation(node, self.source):
            start_line, end_line = self._lines(node)
            self.items.append(self._make_item(
                line_start=start_line, line_end=end_line,
                raw=_node_text(node, self.source)[:200],
                dynamic_group="template_interpolation",
            ))
            return

        val = _extract_string_value(node, self.source)
        if not val:
            return

        # Only care about URL-shaped strings
        if not (val.startswith("http://") or val.startswith("https://") or val.startswith("/")):
            return
        # Skip trivial root "/" or "//comment-like" strings
        if val in ("/", "//") or val.startswith("//") and not val.startswith("//cdn"):
            return

        resolved = resolve_url(val, self.base_url)
        start_line, end_line = self._lines(node)

        item = self._make_item(
            url=resolved,
            line_start=start_line,
            line_end=end_line,
            raw=val,
        )

        if is_static(resolved):
            item.asset_type = classify_asset_type(resolved)

        self.items.append(item)

    # ---- shared helpers --------------------------------------------------

    def _first_string_arg(self, args: list) -> str | None:
        """Extract the URL from the first string/template argument."""
        for arg in args:
            val = _extract_string_value(arg, self.source)
            if val:
                return val
        return None

    def _mark_string_args(self, args: list):
        """Mark string nodes in args as captured so bare-string handler skips them."""
        for arg in args:
            if arg.type in ("string", "template_string"):
                self._mark_captured(arg)

    def _emit_url(self, raw_url: str, start_line: int, end_line: int,
                  group: str, method: str, node):
        resolved = resolve_url(raw_url, self.base_url)
        item = self._make_item(
            url=resolved,
            line_start=start_line,
            line_end=end_line,
            raw=_node_text(node, self.source)[:400],
            dynamic_group=group,
            http_method=method,
        )
        if is_static(resolved):
            item.asset_type = classify_asset_type(resolved)
        self.items.append(item)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_script_ast(
    js_text: str,
    base_url: str,
    base_domain: str,
    origin: str = "<inline>",
) -> list[ExtractedItem]:
    """
    Parse JS with tree-sitter and return classified ExtractedItems.

    Raises ImportError if tree-sitter / tree-sitter-javascript
    are not installed (caller should fall back to regex).
    """
    parser = _make_parser()
    source_bytes = js_text.encode("utf-8")
    tree = parser.parse(source_bytes)

    walker = _Walker(source_bytes, base_url, base_domain, origin)
    walker.walk(tree.root_node)

    return walker.items