MEANINGFUL_NAV_EVENTS =[
    # Values in this list will be only inspected by the AI agent.
    # Mouse
    "onclick",
    "ondblclick",
    "onmousedown",
    "onmouseup",
    # Form
    "onsubmit",
    "onchange", 
    "oninput",
    "onload",
    "onhashchange",
    "onpopstate"
]
EVENT_ATTRIBUTES = [
    #-Mouse------------
    "onclick", "ondblclick", "onmousedown", "onmouseup", "onmousemove",
    "onmouseover", "onmouseout", "onmouseenter", "onmouseleave", "oncontextmenu",

    #-Keyboard---------
    "onkeydown", "onkeyup", "onkeypress",

    #-Form-------------
    "onsubmit", "onchange", "oninput", "onreset", "onfocus", "onblur", "onselect",

    #-Window/Document--
    "onload", "onunload", "onresize", "onscroll", "onerror", "onhashchange", "onpopstate",

    #-Drag/Drop--------
    "ondrag", "ondragstart", "ondragend", "ondragenter", "ondragleave", "ondrop",

    #-Clipboard--------
    "oncopy", "oncut", "onpaste",

    #-Media------------
    "onplay", "onpause", "onended", "onvolumechange"
]