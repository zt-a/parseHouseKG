from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


DDL = """
CREATE TABLE IF NOT EXISTS properties (
  url_slug TEXT PRIMARY KEY,
  detail_url TEXT NOT NULL,
  ad_id_hk TEXT,
  hk_id_text TEXT,
  category TEXT,
  property_type TEXT,
  title TEXT,
  description TEXT,
  price_som INTEGER,
  price_usd INTEGER,
  price_m2_som INTEGER,
  price_m2_usd INTEGER,
  monthly_payment INTEGER,
  currency TEXT,
  region TEXT,
  town TEXT,
  district TEXT,
  address TEXT,
  city TEXT,
  lat REAL,
  lng REAL,
  rooms TEXT,
  total_area REAL,
  living_area REAL,
  kitchen_area REAL,
  land_area_sotka REAL,
  floor TEXT,
  floors_total TEXT,
  ceiling_height REAL,
  condition TEXT,
  year_built INTEGER,
  documents TEXT,
  exchange TEXT,
  installment INTEGER,
  mortgage INTEGER,
  heating TEXT,
  gas TEXT,
  water TEXT,
  electricity TEXT,
  canalization TEXT,
  internet TEXT,
  furniture TEXT,
  flooring TEXT,
  toilet TEXT,
  security TEXT,
  features_json TEXT,
  raw_params_json TEXT,
  badges_json TEXT,
  seller_type TEXT,
  seller_name TEXT,
  seller_url TEXT,
  photo_count INTEGER,
  image_urls_json TEXT,
  published_at TEXT,
  updated_at_hk TEXT,
  created_at_hk TEXT,
  posted_relative TEXT,
  scraped_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_properties_detail_url ON properties(detail_url);
"""


class Storage:
    def __init__(self, db_path: str | Path = "housekg.db") -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self._init()

    def _init(self) -> None:
        self.conn.executescript(DDL)
        self.conn.commit()

    def has_slug(self, slug: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM properties WHERE url_slug=? LIMIT 1", (slug,))
        return cur.fetchone() is not None

    def upsert(self, data: Dict[str, Any], update_existing: bool = True) -> None:
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        row = dict(data)
        row["scraped_at"] = now
        row["features_json"] = json.dumps(row.get("features") or [], ensure_ascii=False)
        row["raw_params_json"] = json.dumps(row.get("raw_params") or {}, ensure_ascii=False)
        row["badges_json"] = json.dumps(row.get("badges") or [], ensure_ascii=False)
        row["image_urls_json"] = row.get("image_urls_json") or json.dumps(row.get("image_urls") or [], ensure_ascii=False)
        row["installment"] = 1 if row.get("installment") else 0
        row["mortgage"] = 1 if row.get("mortgage") else 0

        cols = [
            "url_slug","detail_url","ad_id_hk","hk_id_text","category","property_type","title","description",
            "price_som","price_usd","price_m2_som","price_m2_usd","monthly_payment","currency",
            "region","town","district","address","city","lat","lng",
            "rooms","total_area","living_area","kitchen_area","land_area_sotka",
            "floor","floors_total","ceiling_height","condition","year_built","documents","exchange",
            "installment","mortgage","heating","gas","water","electricity","canalization","internet","furniture",
            "flooring","toilet","security","features_json","raw_params_json","badges_json",
            "seller_type","seller_name","seller_url","photo_count","image_urls_json",
            "published_at","updated_at_hk","created_at_hk","posted_relative","scraped_at",
        ]
        placeholders = ",".join("?" for _ in cols)
        if update_existing:
            updates = ",".join(f"{c}=excluded.{c}" for c in cols if c != "url_slug")
            sql = f"INSERT INTO properties ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT(url_slug) DO UPDATE SET {updates}"
        else:
            sql = f"INSERT OR IGNORE INTO properties ({','.join(cols)}) VALUES ({placeholders})"
        self.conn.execute(sql, [row.get(c) for c in cols])
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def to_sqlite_row(data: Dict[str, Any]) -> Dict[str, Any]:
    # keep compatibility
    return data
