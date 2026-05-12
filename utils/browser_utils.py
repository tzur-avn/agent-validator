"""Browser automation utilities using Playwright."""

import base64
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urlunparse
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from core.exceptions import BrowserError

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize URL for comparison by handling common redirects.

    Args:
        url: URL to normalize

    Returns:
        Normalized URL string
    """
    parsed = urlparse(url)

    # Normalize scheme to https if http (common redirect)
    scheme = "https" if parsed.scheme == "http" else parsed.scheme

    # Normalize netloc by removing/adding www consistently
    netloc = parsed.netloc.lower()
    # Remove www. for comparison
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # Remove trailing slash from path
    path = parsed.path.rstrip("/")
    if not path:
        path = "/"

    # Reconstruct without query/fragment for comparison
    normalized = urlunparse((scheme, netloc, path, "", "", ""))

    return normalized


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
        self._context = None
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
                    "username": self.auth.get("username", ""),
                    "password": self.auth.get("password", ""),
                }
                logger.debug("Configured HTTP Basic Authentication")

            self._context = self.browser.new_context(**context_options)
            self.page = self._context.new_page()
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
            if self._context:
                self._context.close()
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

            # Get the current URL after navigation - it might have redirected to login
            current_url = self.page.url
            logger.info(f"Page loaded at: {current_url}")

            # Check if we need to authenticate (first time only)
            if (
                self.auth
                and self.auth.get("type") == "form"
                and not self._authenticated
            ):
                # Perform authentication
                self.authenticate()

            # After authentication (or if already authenticated), check if we're at the target URL
            # This handles the case where the site redirects to login even after auth cookie is set
            # (e.g., when opening a new browser session)
            post_nav_url = self.page.url
            logger.info(f"After navigation/auth, at: {post_nav_url}")

            # Compare URLs properly - normalize and check if we're at the target
            target_normalized = normalize_url(url)
            current_normalized = normalize_url(post_nav_url)

            if target_normalized != current_normalized:
                logger.info(f"Not at target URL, re-navigating to: {url}")
                self.page.goto(url, wait_until=wait_until, timeout=self.timeout)

                # Wait for the page to fully load after re-navigation
                # This helps with SPAs that need time to render after URL change
                try:
                    self.page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    # If networkidle times out, give it a bit more time
                    self.page.wait_for_timeout(2000)

                # For SPAs: Wait for login form to actually disappear from DOM
                # This is crucial because URL can change before React re-renders
                if self.auth and self.auth.get("type") == "form":
                    self._wait_for_login_form_to_disappear()

                # Check again if we made it to the target
                final_url = self.page.url
                final_normalized = normalize_url(final_url)

                if target_normalized != final_normalized:
                    logger.warning(
                        f"Still not at target URL after re-navigation. "
                        f"Target: {url}, Current: {final_url}. "
                        f"This might indicate authentication issues."
                    )
                else:
                    logger.info(f"Now at target URL: {final_url}")
            else:
                logger.info("Already at target URL")
                # Even if URL is correct, for SPAs we need to wait for content to render
                # after authentication completes
                if self.auth and self.auth.get("type") == "form":
                    self._wait_for_login_form_to_disappear()

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
                    logger.debug(f"Element not found: {selector}")
                    return None
            elif clip_region:
                # Screenshot specific region
                screenshot_bytes = self.page.screenshot(clip=clip_region)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                logger.debug(f"Region screenshot captured")
                return screenshot_b64
            else:
                logger.debug("No selector or clip region provided")
                return None
        except Exception as e:
            logger.debug(f"Failed to take element screenshot: {e}")
            return None

    def get_viewport_size(self) -> Dict[str, int]:
        """Get current viewport size."""
        return self.viewport.copy()

    def _wait_for_login_form_to_disappear(self, timeout: int = 5000) -> None:
        """
        Wait for login form elements to disappear from the DOM.

        This is crucial for SPAs where URL changes before React/Vue re-renders.
        We check for password fields specifically since they're unique to login forms.

        Args:
            timeout: Maximum time to wait in milliseconds
        """
        if not self.page:
            return

        selectors = self.auth.get("selectors", {}) if self.auth else {}
        password_selector = selectors.get(
            "password", selectors.get("password_field", "input[type='password']")
        )

        try:
            # Wait for password field to be hidden/detached - this is the most
            # reliable indicator we've left the login page (other pages rarely have password fields)
            self.page.wait_for_selector(
                password_selector, state="hidden", timeout=timeout
            )
            logger.info("Login form no longer visible - page content ready")
        except Exception:
            # Check if password field still exists
            if self.page.query_selector(password_selector):
                logger.warning(
                    "Login form (password field) still visible - page may not have rendered correctly"
                )
            else:
                logger.info("Login form not found - page content ready")

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

            # Get credentials (already resolved by config_loader)
            username = auth_config.get("username", "")
            password = auth_config.get("password", "")

            # Selectors for form fields
            username_selector = selectors.get(
                "username", selectors.get("username_field", "input[name='username']")
            )
            password_selector = selectors.get(
                "password", selectors.get("password_field", "input[name='password']")
            )
            submit_selector = selectors.get(
                "submit", selectors.get("submit_button", "button[type='submit']")
            )

            logger.info("Waiting for login form to appear...")

            # Wait for the username field to be visible (indicates we're on login page)
            # Use a shorter timeout - if form doesn't appear, we might already be logged in
            try:
                self.page.wait_for_selector(
                    username_selector, timeout=5000, state="visible"
                )
            except Exception as e:
                logger.info(
                    f"Login form not found - assuming already authenticated: {e}"
                )
                self._authenticated = True
                # Don't return here - the navigate method will handle re-navigation
                # to the target URL if needed
                return

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

            # Wait for navigation to complete after login
            wait_time = auth_config.get("wait_after_login", 5000)
            try:
                # Wait for URL to change away from auth page
                self.page.wait_for_url(
                    lambda url: "/auth" not in url, timeout=wait_time
                )
                logger.info("Login successful - redirected away from auth page")
            except Exception:
                # URL didn't change - login might have failed
                logger.warning(
                    f"URL did not change after login - still at {self.page.url}"
                )
                # Wait a bit more and check for error messages
                self.page.wait_for_timeout(1000)

                # Check if there's an error message on the page
                page_text = self.page.inner_text("body").lower()
                if (
                    "error" in page_text
                    or "invalid" in page_text
                    or "incorrect" in page_text
                    or "failed" in page_text
                ):
                    logger.error("Login failed - error message detected on page")
                    raise BrowserError(
                        "Authentication failed - invalid credentials or login error"
                    )

            self._authenticated = True
            logger.info("Authentication successful")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise BrowserError(f"Failed to authenticate: {e}")
