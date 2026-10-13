from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Listing(BaseModel):
    url_slug: str = Field(...)
    detail_url: str
    ad_id_hk: Optional[str] = None
    hk_id_text: Optional[str] = None
    category: Optional[str] = None
    property_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price_som: Optional[int] = None
    price_usd: Optional[int] = None
    price_m2_som: Optional[int] = None
    price_m2_usd: Optional[int] = None
    monthly_payment: Optional[int] = None
    currency: Optional[str] = "KGS"
    region: Optional[str] = None
    town: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    rooms: Optional[str] = None
    total_area: Optional[float] = None
    living_area: Optional[float] = None
    kitchen_area: Optional[float] = None
    land_area_sotka: Optional[float] = None
    floor: Optional[str] = None
    floors_total: Optional[str] = None
    ceiling_height: Optional[float] = None
    condition: Optional[str] = None
    year_built: Optional[int] = None
    documents: Optional[str] = None
    exchange: Optional[str] = None
    installment: Optional[bool] = False
    mortgage: Optional[bool] = False
    heating: Optional[str] = None
    gas: Optional[str] = None
    water: Optional[str] = None
    electricity: Optional[str] = None
    canalization: Optional[str] = None
    internet: Optional[str] = None
    furniture: Optional[str] = None
    flooring: Optional[str] = None
    toilet: Optional[str] = None
    security: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    raw_params: Dict[str, str] = Field(default_factory=dict)
    badges: List[str] = Field(default_factory=list)
    seller_type: Optional[str] = None
    seller_name: Optional[str] = None
    seller_url: Optional[str] = None
    photo_count: Optional[int] = 0
    image_urls_json: Optional[str] = None
    published_at: Optional[str] = None
    updated_at_hk: Optional[str] = None
    created_at_hk: Optional[str] = None
    posted_relative: Optional[str] = None
    scraped_at: Optional[str] = None

    class Config:
        extra = "ignore"
