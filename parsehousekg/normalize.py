from __future__ import annotations

import re
import unicodedata
from typing import Optional


# U+20C0 SOM SIGN
_SOM_SIGN = "\u20c0"


def clean_text(s: str | None) -> str | None:
    if not s:
        return None
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", " ", s)
    s = s.replace("\xa0", " ").replace("\u00a0", " ")
    s = s.strip()
    return s if s else None


def extract_number(s: str | None) -> Optional[int]:
    if not s:
        return None
    s = clean_text(s) or ""
    s = s.replace(_SOM_SIGN, "").replace("$", "").replace("KGS", "").replace("сом", "")
    s = re.sub(r"[^\d]", "", s)
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def extract_float(s: str | None) -> Optional[float]:
    if not s:
        return None
    s = clean_text(s) or ""
    s = s.replace(",", ".").replace(_SOM_SIGN, "").replace("$", "").replace("м²", "").replace("соток", "").replace("сот.", "")
    s = re.sub(r"[^0-9.]", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_area_m2(s: str | None) -> Optional[float]:
    return extract_float(s)


def parse_land_sotka(s: str | None) -> Optional[float]:
    return extract_float(s)


def slug_from_url(u: str) -> Optional[str]:
    m = re.search(r"/details/([^/?#]+)", u)
    if m:
        return m.group(1)
    return None
