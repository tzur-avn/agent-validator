"""Browser automation utilities using Playwright."""

import base64
import logging
import os
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
        auth: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize browser session.

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
            viewport: Optional viewport dimensions {'width': int, 'height': int}
            auth: Optional authentication configuration
        """
        self.headless = headless
        self.timeout = timeout
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.auth = auth
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._authenticated = False

    def __enter__(self):
        """Start browser session."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)

            # Configure HTTP Basic Auth if specified
            context_options = {"viewport": self.viewport}
            if self.auth and self.auth.get("type") == "basic":
                context_options["http_credentials"] = {
                    "username": self._resolve_env_var(self.auth.get("username", "")),
                    "password": self._resolve_env_var(self.auth.get("password", "")),
                }
                logger.debug("Configured HTTP Basic Authentication")

            context = self.browser.new_context(**context_options)
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

            # Perform form-based authentication if configured and not already authenticated
            if (
                self.auth
                and self.auth.get("type") == "form"
                and not self._authenticated
            ):
                self.authenticate()

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

    def take_element_screenshot(
        self, selector: str = None, clip_region: Dict[str, int] = None
    ) -> Optional[str]:
        """
        Take a screenshot of a specific element or region.

        Args:
            selector: CSS selector for element to screenshot
            clip_region: Dict with x, y, width, height for clipping region

        Returns:
            Base64-encoded screenshot or None if element not found
        """
        if not self.page:
            raise BrowserError("Browser session not initialized")

        try:
            if selector:
                # Screenshot specific element
                element = self.page.query_selector(selector)
                if element:
                    screenshot_bytes = element.screenshot()
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                    logger.debug(f"Element screenshot captured for {selector}")
                    return screenshot_b64
                else:
                    logger.warning(f"Element not found: {selector}")
                    return None
            elif clip_region:
                # Screenshot specific region
                screenshot_bytes = self.page.screenshot(clip=clip_region)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                logger.debug(f"Region screenshot captured")
                return screenshot_b64
            else:
                logger.warning("No selector or clip region provided")
                return None
        except Exception as e:
            logger.warning(f"Failed to take element screenshot: {e}")
            return None

    def get_viewport_size(self) -> Dict[str, int]:
        """Get current viewport size."""
        return self.viewport.copy()

    def authenticate(self) -> None:
        """
        Perform form-based authentication.

        Raises:
            BrowserError: If authentication fails
        """
        if not self.auth or self.auth.get("type") != "form":
            logger.warning("No form-based authentication configured")
            return

        if self._authenticated:
            logger.debug("Already authenticated, skipping login")
            return

        if not self.page:
            raise BrowserError("Browser session not initialized")

        try:
            auth_config = self.auth
            selectors = auth_config.get("selectors", {})

            # Navigate to login page if specified
            login_url = auth_config.get("login_url")
            if login_url and self.page.url != login_url:
                logger.info(f"Navigating to login page: {login_url}")
                self.page.goto(
                    login_url, wait_until="domcontentloaded", timeout=self.timeout
                )

            # Get credentials (resolve environment variables)
            username = self._resolve_env_var(auth_config.get("username", ""))
            password = self._resolve_env_var(auth_config.get("password", ""))

            # Default selectors if not provided
            username_selector = selectors.get(
                "username_field",
                "input[name='username'], input[type='email'], input[name='email']",
            )
            password_selector = selectors.get(
                "password_field", "input[name='password'], input[type='password']"
            )
            submit_selector = selectors.get(
                "submit_button", "button[type='submit'], input[type='submit']"
            )

            logger.info("Filling login form")

            # Fill username
            self.page.fill(username_selector, username)
            logger.debug(f"Filled username field: {username_selector}")

            # Fill password
            self.page.fill(password_selector, password)
            logger.debug("Filled password field")

            # Click submit button
            self.page.click(submit_selector)
            logger.debug(f"Clicked submit button: {submit_selector}")

            # Wait for navigation or specified time
            wait_time = auth_config.get("wait_after_login", 2000)
            try:
                self.page.wait_for_load_state("domcontentloaded", timeout=wait_time)
            except:
                # If navigation doesn't happen, just wait the specified time
                self.page.wait_for_timeout(wait_time)

            self._authenticated = True
            logger.info("Authentication successful")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise BrowserError(f"Failed to authenticate: {e}")

    def _resolve_env_var(self, value: str) -> str:
        """
        Resolve environment variable in string format ${VAR_NAME}.

        Args:
            value: String that may contain ${VAR_NAME}

        Returns:
            Resolved string
        """
        if not value or not isinstance(value, str):
            return value

        # Check if value is in format ${VAR_NAME}
        if value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            resolved = os.getenv(var_name)
            if resolved is None:
                logger.warning(
                    f"Environment variable {var_name} not found, using empty string"
                )
                return ""
            return resolved

        return value
