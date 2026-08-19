"""Playwright Headless browser fallback for bypassing Cloudflare and JavaScript challenges."""

from app.config import settings
from app.logging import logger


class HeadlessScraper:
    """Manages Headless Chromium instances to fetch JavaScript-protected pages."""

    def __init__(self, enabled: bool = settings.ENABLE_PLAYWRIGHT_FALLBACK) -> None:
        self.enabled = enabled

    async def fetch_page(self, url: str, wait_selector: str | None = None, timeout_ms: int = 30000) -> str:
        """Render a page using headless Chromium and return resolved HTML."""
        if not self.enabled:
            raise RuntimeError("Playwright headless fallback is disabled in settings.")

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright is not installed. Please run `playwright install chromium`.")
            raise RuntimeError("Playwright is not installed.")

        logger.info(f"[Headless] Launching stealth browser to bypass challenge on: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="vi-VN",
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=timeout_ms)
                else:
                    # Give JS/Cloudflare Turnstile 3 seconds to resolve
                    await page.wait_for_timeout(3000)

                html = await page.content()
                return html
            finally:
                await browser.close()


headless_scraper = HeadlessScraper()
