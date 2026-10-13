from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    base_url: str = "https://www.house.kg"
    request_timeout: float = 30.0
    max_retries: int = 5
    retry_backoff_min: float = 0.5
    retry_backoff_max: float = 2.0
    delay_min: float = 0.5
    delay_max: float = 1.5
    concurrency: int = 2
    page_size: int = 20
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )


CFG = Config()


CATEGORY_SLUGS = {
    "buy_all": "/kupit",
    "buy_apart": "/kupit-kvartiru",
    "buy_house": "/kupit-dom",
    "buy_commercial": "/kupit-kommercheskaia-nedvijimost",
    "buy_room": "/kupit-komnatu",
    "buy_land": "/kupit-uchastok",
    "buy_dacha": "/kupit-dachu",
    "buy_parking": "/kupit-parking-garaj",
}


LIST_HEADERS = {
    "User-Agent": CFG.user_agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def random_delay() -> float:
    return random.uniform(CFG.delay_min, CFG.delay_max)
