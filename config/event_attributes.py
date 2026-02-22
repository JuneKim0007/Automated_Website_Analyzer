

MEANINGFUL_NAV_EVENTS = frozenset([
    # Mouse — likely navigation triggers
    "onclick",
    "ondblclick",
    "onmousedown",
    "onmouseup",
    # Form — data submission triggers
    "onsubmit",
    "onchange",
    "oninput",
    # Window / History
    "onload",
    "onhashchange",
    "onpopstate",
])

EVENT_ATTRIBUTES = frozenset([
    # ----- Mouse -----
    "onclick", "ondblclick", "onmousedown", "onmouseup", "onmousemove",
    "onmouseover", "onmouseout", "onmouseenter", "onmouseleave", "oncontextmenu",
    # ----- Keyboard -----
    "onkeydown", "onkeyup", "onkeypress",
    # ----- Form -----
    "onsubmit", "onchange", "oninput", "onreset", "onfocus", "onblur", "onselect",
    # ----- Window / Document -----
    "onload", "onunload", "onresize", "onscroll", "onerror", "onhashchange", "onpopstate",
    # ----- Drag / Drop -----
    "ondrag", "ondragstart", "ondragend", "ondragenter", "ondragleave", "ondrop",
    # ----- Clipboard -----
    "oncopy", "oncut", "onpaste",
    # ----- Media -----
    "onplay", "onpause", "onended", "onvolumechange",
])