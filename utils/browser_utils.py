"""Browser automation utilities using Playwright."""

import base64
import logging
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from core.exceptions import BrowserError

logger = logging.getLogger(__name__)


class BrowserSession:
    """Context manager for browser sessions."""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 60000,
        viewport: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize browser session.

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
            viewport: Optional viewport dimensions {'width': int, 'height': int}
        """
        self.headless = headless
        self.timeout = timeout
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """Start browser session."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            context = self.browser.new_context(viewport=self.viewport)
            self.page = context.new_page()
            self.page.set_default_timeout(self.timeout)
            logger.debug(f"Browser session started with viewport {self.viewport}")
            return self
        except Exception as e:
            self._cleanup()
            raise BrowserError(f"Failed to start browser session: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser session."""
        self._cleanup()

    def _cleanup(self):
        """Clean up browser resources."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.debug("Browser session closed")
        except Exception as e:
            logger.warning(f"Error during browser cleanup: {e}")

    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """
        Navigate to URL.

        Args:
            url: URL to navigate to
            wait_until: Wait condition ('domcontentloaded', 'load', 'networkidle')
        """
        if not self.page:
            raise BrowserError("Browser session not initialized")

        try:
            logger.info(f"Navigating to {url}")
            self.page.goto(url, wait_until=wait_until, timeout=self.timeout)
        except Exception as e:
            raise BrowserError(f"Failed to navigate to {url}: {e}")

    def get_text(self, selector: str = "body", wait_time: int = 2000) -> str:
        """
        Extract text from page.

        Args:
            selector: CSS selector to extract text from
            wait_time: Time to wait for dynamic content (milliseconds)

        Returns:
            Extracted text
        """
        if not self.page:
            raise BrowserError("Browser session not initialized")

        try:
            self.page.wait_for_timeout(wait_time)
            text = self.page.inner_text(selector)
            logger.debug(f"Extracted {len(text)} characters from {selector}")
            return text
        except Exception as e:
            raise BrowserError(f"Failed to extract text from {selector}: {e}")

    def take_screenshot(self, full_page: bool = True, wait_time: int = 5000) -> str:
        """
        Take a screenshot of the page.

        Args:
            full_page: Capture full page or just viewport
            wait_time: Time to wait before screenshot (milliseconds)

        Returns:
            Base64-encoded screenshot
        """
        if not self.page:
            raise BrowserError("Browser session not initialized")

        try:
            self.page.wait_for_timeout(wait_time)
            screenshot_bytes = self.page.screenshot(full_page=full_page)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            logger.debug(f"Screenshot captured ({len(screenshot_b64)} bytes)")
            return screenshot_b64
        except Exception as e:
            raise BrowserError(f"Failed to take screenshot: {e}")

    def get_viewport_size(self) -> Dict[str, int]:
        """Get current viewport size."""
        return self.viewport.copy()
