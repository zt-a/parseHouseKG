from __future__ import annotations

import re
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup, Tag

from .jsonld import extract_ld
from .normalize import clean_text, slug_from_url


def _extract_total_found(soup: BeautifulSoup) -> Optional[int]:
    # Найдено 21 873 объявлений
    text = soup.get_text(" ", strip=True)
    m = re.search(r"Найдено\s+([\d\s]+)\s+объявлен", text)
    if m:
        return int(re.sub(r"[^\d]", "", m.group(1)))
    return None


def _max_page_from_pagination(soup: BeautifulSoup) -> Optional[int]:
    max_p = 0
    for a in soup.find_all("a", href=re.compile(r"/kupit(\?|/)")):
        label = a.get("aria-label") or a.text
        m = re.search(r"Страница\s+(\d+)", str(label))
        if m:
            p = int(m.group(1))
            if p > max_p:
                max_p = p
    return max_p or None


def _rel_next(soup: BeautifulSoup) -> Optional[str]:
    a = soup.find("a", rel=re.compile("next", re.I))
    if a and a.get("href"):
        href = a["href"]
        if href.startswith("/"):
            return href
        return href
    return None


def _detail_links_from_cards(soup: BeautifulSoup) -> List[str]:
    seen: set[str] = set()
    links: List[str] = []
    for a in soup.find_all("a", href=re.compile(r"^/details/")):
        href = a["href"]
        if href.startswith("/"):
            full = href
        else:
            full = href
        if full in seen:
            continue
        seen.add(full)
        links.append(full)
    return links


def _detail_links_from_jsonld(soup: BeautifulSoup) -> List[str]:
    ld = extract_ld(soup)
    for t in ("ItemList", "BreadcrumbList", "OfferCatalog"):
        for item in ld.get(t, []):
            if t == "ItemList" and item.get("itemListElement"):
                out: List[str] = []
                for el in item["itemListElement"]:
                    url = (el.get("url") or el.get("item", {}).get("url"))
                    if url:
                        u = url.replace("https://house.kg", "").replace("https://www.house.kg", "")
                        if u.startswith("/"):
                            out.append(u)
                return out
    return []


def parse_list_page(soup: BeautifulSoup) -> dict:
    links_ld = _detail_links_from_jsonld(soup)
    links_dom = _detail_links_from_cards(soup)
    detail_links = links_ld if links_ld else links_dom

    # dedupe preserve order
    seen = set()
    uniq: List[str] = []
    for l in detail_links:
        if l not in seen:
            seen.add(l)
            uniq.append(l)

    return {
        "total_found": _extract_total_found(soup),
        "last_page": _max_page_from_pagination(soup),
        "next_path": _rel_next(soup),
        "detail_links": uniq,
        "count": len(uniq),
    }
