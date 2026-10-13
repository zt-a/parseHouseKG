from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


def extract_ld(soup: BeautifulSoup) -> Dict[str, List[dict]]:
    res: Dict[str, List[dict]] = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
        except Exception:
            continue
        if isinstance(data, dict):
            t = data.get("@type")
            if t:
                res.setdefault(t, []).append(data)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("@type"):
                    res.setdefault(item["@type"], []).append(item)
    return res
