from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable, List, Optional, Set

from bs4 import BeautifulSoup
from tqdm import tqdm

from .config import CATEGORY_SLUGS, CFG
from .http import build_client, fetch_html
from .list_parser import parse_list_page
from .detail_parser import parse_detail
from .normalize import slug_from_url
from .storage import Storage


def _iter_pages(start_path: str, max_pages: Optional[int] = None, client=None) -> Iterable[BeautifulSoup]:
    path = start_path
    pages = 0
    c = client or build_client()
    try:
        while path:
            if max_pages is not None and pages >= max_pages:
                break
            soup = fetch_html(c, path)
            yield soup
            pages += 1
            lp = parse_list_page(soup)
            nxt = lp.get("next_path")
            if not nxt:
                break
            path = nxt
    finally:
        if client is None and c:
            c.close()


def crawl_category(category_key: str = "buy_all", limit: int = 10000, max_pages: Optional[int] = None, db_path: str = "housekg.db", skip_existing: bool = True, update_existing: bool = False) -> dict:
    start = CATEGORY_SLUGS.get(category_key, CATEGORY_SLUGS["buy_all"])
    storage = Storage(db_path)
    client = build_client()
    seen_slugs: Set[str] = set()
    collected = 0
    skipped = 0
    total_seen_links = 0

    try:
        for soup in _iter_pages(start, max_pages=max_pages, client=client):
            lp = parse_list_page(soup)
            links = lp["detail_links"]
            total_seen_links += len(links)
            if not links:
                continue
            for l in links:
                if collected >= limit:
                    break
                detail_url_full = l if l.startswith("http") else f"{CFG.base_url}{l}"
                slug = slug_from_url(detail_url_full) or slug_from_url(l)
                if not slug:
                    continue
                if skip_existing and storage.has_slug(slug):
                    skipped += 1
                    continue
                try:
                    dsoup = fetch_html(client, l)
                except Exception:
                    continue
                d = parse_detail(dsoup, detail_url_full)
                if slug and slug not in seen_slugs:
                    seen_slugs.add(slug)
                storage.upsert(d, update_existing=update_existing)
                collected += 1
                if collected % 100 == 0:
                    time.sleep(0.2)
            if collected >= limit:
                break
    finally:
        storage.close()
        client.close()

    return {
        "collected": collected,
        "skipped": skipped,
        "total_seen_links": total_seen_links,
        "db_path": str(Path(db_path).resolve()),
    }

    return {
        "collected": collected,
        "total_seen_links": total_seen_links,
        "db_path": str(Path(db_path).resolve()),
    }
from .normalize import slug_from_url  # ensure import
