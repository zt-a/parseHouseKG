from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, Tag

from .jsonld import extract_ld
from .normalize import clean_text, extract_float, extract_number, slug_from_url


def _get_text(el: Tag | None) -> str:
    return clean_text(el.get_text(" ", strip=True)) or "" if el else ""


def _dt_dd_map(soup: BeautifulSoup) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for dl in soup.find_all("dl"):
        for div in dl.find_all("div"):
            dt = div.find("dt")
            dd = div.find("dd")
            if not dt:
                continue
            k = clean_text(dt.get_text(" ", strip=True))
            if not k:
                continue
            if dd:
                v = clean_text(dd.get_text(" ", strip=True))
                if v:
                    out[k] = v
            else:
                # feature tag (Безопасность/Разное)
                out[k] = "true"
    return out


def _features_from_map(dtdd: Dict[str, str]) -> List[str]:
    feats: List[str] = []
    for k, v in dtdd.items():
        if v == "true":
            feats.append(k)
    return feats


def _parse_meta_line(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    text = soup.get_text(" ", strip=True)
    res: Dict[str, Optional[str]] = {"updated": None, "created": None, "ad_id_hk": None, "hk_id_text": None}
    m = re.search(r"Обновлено\s+([^ID]+?)(?:ID:\s*(\d+))?", text)
    if m:
        res["updated"] = clean_text(m.group(1))
        res["ad_id_hk"] = m.group(2)
    m = re.search(r"Объявление\s+создано:\s*([\d.]+)", text)
    if m:
        res["created"] = m.group(1)
    m = re.search(r"ID:\s*(\d+)", text)
    if m and not res["ad_id_hk"]:
        res["ad_id_hk"] = m.group(1)
    m = re.search(r"ID:\s*([^\s]+)", text)
    if m and not res["hk_id_text"]:
        res["hk_id_text"] = m.group(1)
    return res


def _price_block(soup: BeautifulSoup) -> Dict[str, Optional[int]]:
    res = {"price_som": None, "price_usd": None, "price_m2_som": None, "price_m2_usd": None}
    # som main
    for span in soup.find_all("span"):
        t = span.get_text(" ", strip=True)
        if not t:
            continue
        if "\u20c0" in t and res["price_som"] is None and re.search(r"\d", t):
            res["price_som"] = extract_number(t)
        if "$" in t and res["price_usd"] is None and re.search(r"\d", t):
            # avoid m2
            if "за м²" in t or "м²" in t:
                continue
            res["price_usd"] = extract_number(t)
    # m2
    block = soup.find(string=re.compile(r"за м²"))
    if block:
        parent = block.parent
        if parent:
            t = parent.get_text(" ", strip=True)
            m = re.search(r"([\d\s\u20c0]+)\s*\|\s*([\d\s$]+)\s*за\s*м²", t)
            if not m:
                m = re.search(r"([\d\s\u20c0]+)\s*\|\s*([\d\s$]+)", t)
            if m:
                res["price_m2_som"] = extract_number(m.group(1))
                res["price_m2_usd"] = extract_number(m.group(2))
    return res


def _gallery_images(soup: BeautifulSoup) -> List[str]:
    urls: List[str] = []
    seen: set[str] = set()
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not src:
            continue
        if "cdn.house.kg/house/images/" not in src:
            continue
        u = src.split("?")[0]
        if u not in seen:
            seen.add(u)
            urls.append(u)
    return urls


def _seller(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    res = {"seller_type": None, "seller_name": None, "seller_url": None}
    h2s = soup.find_all("h2")
    for h2 in h2s:
        if "Продавец" in h2.get_text(" ", strip=True):
            sec = h2.find_next("div")
            if sec:
                t = sec.get_text(" ", strip=True)
                if "Собственник" in t:
                    res["seller_type"] = "owner"
                for a in sec.find_all("a", href=re.compile(r"^/user/")):
                    res["seller_url"] = a["href"]
                    nm = clean_text(a.get_text(" ", strip=True))
                    if nm:
                        res["seller_name"] = nm
            break
    return res


def _badges(soup: BeautifulSoup) -> List[str]:
    b: List[str] = []
    for el in soup.find_all(["span", "div", "p"]):
        txt = clean_text(el.get_text(" ", strip=True))
        if not txt:
            continue
        if re.fullmatch(r"Собственник", txt) or re.fullmatch(r"Срочно", txt):
            if txt not in b:
                b.append(txt)
        if re.search(r"Ниже рынка", txt):
            if txt not in b:
                b.append(txt)
        if re.search(r"Есть рассрочка", txt):
            if txt not in b:
                b.append(txt)
        if re.search(r"Премиум", txt):
            if txt not in b:
                b.append(txt)
    return b


def parse_detail(soup: BeautifulSoup, detail_url: str) -> Dict[str, Any]:
    slug = slug_from_url(detail_url)
    ld = extract_ld(soup)

    # JSON-LD
    rl_list = ld.get("RealEstateListing", [])
    rl = rl_list[0] if rl_list else {}
    about = rl.get("about") or {}
    addr = (about.get("address") or {})
    offers = (rl.get("offers") or {})
    geo = (about.get("geo") or {})

    dtdd = _dt_dd_map(soup)
    meta = _parse_meta_line(soup)
    priceb = _price_block(soup)
    gal = _gallery_images(soup)
    seller = _seller(soup)
    badges = _badges(soup)

    title = clean_text(rl.get("name") or (soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else None))
    desc = clean_text(rl.get("description"))
    if not desc:
        # try to find Описание section
        for h2 in soup.find_all("h2"):
            if "Описание" in h2.get_text(" ", strip=True):
                parts = []
                for sib in h2.next_siblings:
                    if hasattr(sib, "name") and sib.name == "h2":
                        break
                    if hasattr(sib, "get_text"):
                        t = sib.get_text("\n", strip=True)
                        if t:
                            parts.append(t)
                    else:
                        t = clean_text(str(sib))
                        if t:
                            parts.append(t)
                if parts:
                    desc = clean_text("\n\n".join(parts))
                break
    if not desc:
        ddiv = soup.find("div", class_=re.compile("description", re.I))
        if ddiv:
            desc = clean_text(ddiv.get_text("\n", strip=True))

    features = _features_from_map(dtdd)

    data: Dict[str, Any] = {
        "url_slug": slug,
        "detail_url": detail_url,
        "ad_id_hk": meta.get("ad_id_hk"),
        "hk_id_text": meta.get("hk_id_text"),
        "category": None,
        "property_type": about.get("@type"),
        "title": title,
        "description": desc,
        "price_som": priceb["price_som"] or extract_number(str(offers.get("price"))),
        "price_usd": priceb["price_usd"],
        "price_m2_som": priceb["price_m2_som"],
        "price_m2_usd": priceb["price_m2_usd"],
        "monthly_payment": None,
        "currency": offers.get("priceCurrency") or "KGS",
        "region": None,
        "town": None,
        "district": None,
        "address": clean_text(addr.get("streetAddress") or rl.get("address", {}).get("streetAddress")),
        "city": clean_text(addr.get("addressLocality")),
        "lat": geo.get("latitude"),
        "lng": geo.get("longitude"),
        "rooms": dtdd.get("Кол-во комнат"),
        "total_area": extract_float(dtdd.get("Общая площадь")),
        "living_area": extract_float(dtdd.get("Жилая площадь")),
        "kitchen_area": extract_float(dtdd.get("Площадь кухни")),
        "land_area_sotka": extract_float(dtdd.get("Площадь участка")),
        "floor": dtdd.get("Этаж"),
        "floors_total": dtdd.get("Этажность"),
        "ceiling_height": extract_float(dtdd.get("Высота потолков")),
        "condition": dtdd.get("Состояние"),
        "year_built": extract_number(dtdd.get("Год постройки")),
        "documents": dtdd.get("Документы на недвижимость"),
        "exchange": dtdd.get("Возможность обмена"),
        "installment": (dtdd.get("Возможность рассрочки") == "Есть"),
        "mortgage": (dtdd.get("Возможность ипотеки") == "Есть"),
        "heating": dtdd.get("Отопление"),
        "gas": dtdd.get("Газ"),
        "water": dtdd.get("Питьевая вода"),
        "electricity": dtdd.get("Электричество"),
        "canalization": dtdd.get("Канализация"),
        "internet": dtdd.get("Интернет"),
        "furniture": dtdd.get("Мебель"),
        "flooring": dtdd.get("Пол"),
        "toilet": dtdd.get("Санузел"),
        "security": dtdd.get("Безопасность") if "Безопасность" in dtdd else None,
        "features": features,
        "raw_params": dtdd,
        "badges": badges,
        "seller_type": seller.get("seller_type"),
        "seller_name": seller.get("seller_name"),
        "seller_url": seller.get("seller_url"),
        "photo_count": len(gal),
        "image_urls": gal,
        "image_urls_json": json.dumps(gal, ensure_ascii=False),
        "published_at": rl.get("datePosted"),
        "updated_at_hk": meta.get("updated"),
        "created_at_hk": meta.get("created"),
        "posted_relative": None,
    }
    return data
