"""Asynchronous HTTP Client with rate limiting, retries and Cloudflare detection."""

import asyncio
from typing import Any
import httpx
from app.config import settings
from app.logging import logger

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


class HttpClient:
    """Robust Async HTTP Client managing connection pooling, concurrency and retries."""

    def __init__(
        self,
        concurrency: int = settings.FAST_SCRAPE_CONCURRENCY,
        timeout: float = settings.REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.semaphore = asyncio.Semaphore(concurrency)
        self.timeout = httpx.Timeout(timeout, connect=10.0)
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Lazily initialize and return shared httpx AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=self.timeout,
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
            )
        return self._client

    async def close(self) -> None:
        """Close underlying client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def is_cloudflare_challenge(status_code: int, body_text: str) -> bool:
        """Detect Cloudflare bot challenge or Turnstile verification pages."""
        if status_code in (403, 503):
            cf_signatures = [
                "cf-browser-verification",
                "challenge-running",
                "cf-turnstile",
                "just a moment...",
                "please turn javascript on and reload",
                "cloudflare ray id",
            ]
            lower_body = body_text.lower()
            return any(sig in lower_body for sig in cf_signatures)
        return False

    async def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json: Any = None,
        max_retries: int = 3,
    ) -> httpx.Response:
        """Execute async HTTP request with concurrency control and exponential backoff retry."""
        client = await self.get_client()
        req_headers = {**DEFAULT_HEADERS, **(headers or {})}

        if cookies:
            cookie_str = "; ".join(f"{k}={v}" for k, v in sorted(cookies.items()))
            if "Cookie" in req_headers:
                req_headers["Cookie"] = f"{req_headers['Cookie']}; {cookie_str}"
            else:
                req_headers["Cookie"] = cookie_str

        async with self.semaphore:
            for attempt in range(1, max_retries + 1):
                try:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=req_headers,
                        params=params,
                        data=data,
                        json=json,
                    )

                    # If Cloudflare Challenge detected, trigger headless fallback if enabled
                    if self.is_cloudflare_challenge(response.status_code, response.text):
                        logger.warning(
                            f"Cloudflare challenge detected on {url} (status {response.status_code})"
                        )
                        if settings.ENABLE_PLAYWRIGHT_FALLBACK and method.upper() == "GET":
                            try:
                                from app.fetcher.headless import headless_scraper
                                logger.info(f"Triggering Playwright stealth headless fallback for {url}...")
                                rendered_html = await headless_scraper.fetch_page(url)
                                return httpx.Response(
                                    status_code=200,
                                    text=rendered_html,
                                    request=response.request,
                                    headers={"content-type": "text/html; charset=utf-8"},
                                )
                            except Exception as headless_err:
                                logger.error(f"Headless fallback failed for {url}: {headless_err}")
                        return response

                    if response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                        delay = attempt * 1.5
                        logger.warning(
                            f"HTTP {response.status_code} for {url}. Retrying in {delay}s (attempt {attempt}/{max_retries})..."
                        )
                        await asyncio.sleep(delay)
                        continue

                    return response

                except (httpx.TransportError, httpx.TimeoutException) as exc:
                    if attempt == max_retries:
                        logger.error(f"Request failed for {url} after {max_retries} attempts: {exc}")
                        raise
                    delay = attempt * 1.5
                    logger.warning(f"Request error: {exc}. Retrying in {delay}s ({attempt}/{max_retries})...")
                    await asyncio.sleep(delay)

            raise httpx.HTTPError(f"Failed to fetch {url} after {max_retries} attempts")

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Convenience GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Convenience POST request."""
        return await self.request("POST", url, **kwargs)


http_client = HttpClient()
