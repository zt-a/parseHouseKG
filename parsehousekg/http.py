from __future__ import annotations

import time
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import CFG, LIST_HEADERS, random_delay


class HttpError(Exception):
    pass


def build_client(headers: Optional[dict] = None, timeout: float = CFG.request_timeout) -> httpx.Client:
    h = {**LIST_HEADERS, **(headers or {})}
    client = httpx.Client(
        base_url=CFG.base_url,
        headers=h,
        timeout=timeout,
        follow_redirects=True,
        http2=False,
    )
    return client


@retry(
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, HttpError)),
    stop=stop_after_attempt(CFG.max_retries),
    wait=wait_exponential(multiplier=CFG.retry_backoff_min, min=CFG.retry_backoff_min, max=CFG.retry_backoff_max),
    reraise=True,
)
def fetch_html(client: httpx.Client, path: str, *, delay: bool = True) -> BeautifulSoup:
    if delay:
        time.sleep(random_delay())
    url = path if path.startswith("http") else f"{CFG.base_url}{path}"
    resp = client.get(url)
    if resp.status_code >= 400:
        raise HttpError(f"HTTP {resp.status_code} for {url}")
    soup = BeautifulSoup(resp.text, "lxml")
    return soup
