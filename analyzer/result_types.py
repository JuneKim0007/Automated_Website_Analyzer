# result_types.py
# Main purpose:
#  - Defines the classification of output results.
#  - Provides a dataclass to hold these results.
'''
PageResults 
├─ url: str
├─ base_domain: str
│
├─ static_assets: List[ExtractedItem]
├─ internal_links: List[ExtractedItem]
├─ external_links: List[ExtractedItem]
│
└─ dynamic_behavior: DynamicBehavior
    ├─ internal_links: List[ExtractedItem]
    ├─ external_links: List[ExtractedItem]
    ├─ static_assets: List[ExtractedItem]
    ├─ get_requests: List[ExtractedItem]
    ├─ post_requests: List[ExtractedItem]
    ├─ event_listeners: List[ExtractedItem]
    └─ unidentified: List[ExtractedItem]
'''
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any



@dataclass
class ExtractedItem:
    url: str = ""
    origin: str = ""
    line_start: int =0
    line_end: int =0
    raw: str = ""
    asset_type: str = ""
    http_method: str = ""
    dynamic_group: str = ""
    is_meaningful_nav: bool = False

@dataclass
class DynamicBehavior:
    """
    Keywords that is firsted identified as dynamic behavior will sub-classified into 7 categories:
    - **internal_links**: Links pointing to the subdomain of the target (base) domain.
    - **external_links**: Links pointing to domains outside the target domain.
    - **static_assets**: Static resources such as images, videos, or other files, as defined in `config/static_extensions.py`.
    - **get_requests**: Dynamic behaviors that make GET requests to API endpoints.
    - **post_requests**: Dynamic behaviors that make POST requests to API endpoints.
    - **event_listeners**: Dynamic behaviors that wait for specific event signals.
    - **unidentified**: Behaviors that are dynamic but cannot be classified into the above categories (i.e. the keyword is captured but scrapper couldn't identify the role.)
    """
    internal_links: list[ExtractedItem] =field(default_factory=list)
    external_links: list[ExtractedItem] =field(default_factory=list)
    static_assets: list[ExtractedItem] =field(default_factory=list)
    get_requests: list[ExtractedItem] =field(default_factory=list)
    post_requests: list[ExtractedItem] =field(default_factory=list)
    event_listeners: list[ExtractedItem] =field(default_factory=list)
    unidentified: list[ExtractedItem] =field(default_factory=list)

@dataclass
class PageResults:
    """
    ### Args:
        - **url:** targeted url 
        - **base_domain:** the base domain of the targeted url. 
    """
    url: str = ""
    base_domain: str = ""

    #automatically get a new instace of list 
    static_assets: list[ExtractedItem] = field(default_factory=list)
    internal_links: list[ExtractedItem] = field(default_factory=list)
    external_links: list[ExtractedItem] = field(default_factory=list)

    #dynamic_behavior gets a struct (analogus to struct), that will be used to sub-classify further.
    dynamic_behavior: DynamicBehavior = field(default_factory=DynamicBehavior)

    #helper function to convert to dict data type.
    def to_dict(self) -> dict[str, Any]:
        def _items(lst: list[ExtractedItem]) -> list[dict]:
            return [
                {k: v for k, v in item.__dict__.items() if v}
                for item in lst
            ]
        return {
            "url": self.url,
            "base_domain": self.base_domain,
            "static_assets": _items(self.static_assets),
            "internal_links": _items(self.internal_links),
            "external_links": _items(self.external_links),
            "dynamic_behavior": {
                "internal_links": _items(self.dynamic_behavior.internal_links),
                "external_links": _items(self.dynamic_behavior.external_links),
                "static_assets": _items(self.dynamic_behavior.static_assets),
                "get_requests": _items(self.dynamic_behavior.get_requests),
                "post_requests": _items(self.dynamic_behavior.post_requests),
                "event_listeners": _items(self.dynamic_behavior.event_listeners),
                "unidentified": _items(self.dynamic_behavior.unidentified),
            },
        }