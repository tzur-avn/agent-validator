"""Broken links agent for finding dead links on web pages."""

import logging
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, TypedDict, Dict, Any, Optional

from langgraph.graph import StateGraph, END

from agents.base_agent import BaseAgent
from utils.browser_utils import BrowserSession
from utils.validation_utils import validate_url

logger = logging.getLogger(__name__)


class BrokenLinksState(TypedDict):
    """State structure for broken links agent."""

    url: str
    all_links: List[str]
    broken_links: List[dict]
    report: str
    auth: Optional[Dict[str, Any]]


class BrokenLinksAgent(BaseAgent):
    """Agent for detecting broken links on web pages."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        temperature: float = 0,
        max_links: int = 100,
        link_timeout: int = 10,
        provider: str = "gemini",
        **kwargs,
    ):
        super().__init__(model=model, temperature=temperature, provider=provider, **kwargs)
        self.max_links = max_links
        self.link_timeout = link_timeout

    def get_state_class(self) -> type:
        return BrokenLinksState

    def create_initial_state(self, url: str, **kwargs) -> Dict[str, Any]:
        url = validate_url(url)
        return {
            "url": url,
            "all_links": [],
            "broken_links": [],
            "report": "",
            "auth": kwargs.get("auth"),
        }

    def extract_links_node(self, state: BrokenLinksState) -> Dict[str, List[str]]:
        """Extract all HTTP/HTTPS anchor links from the page."""
        logger.info(f"Extracting links from: {state['url']}")
        self._update_progress("Extracting links", advance=1)

        with BrowserSession(auth=state.get("auth")) as browser:
            browser.navigate(state["url"])
            browser.page.wait_for_timeout(2000)
            hrefs: List[str] = browser.page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(h => h.startsWith('http'))
            """)

        unique_links = list(dict.fromkeys(hrefs))[: self.max_links]
        logger.info(f"Found {len(unique_links)} unique links to check")
        return {"all_links": unique_links}

    def _check_link(self, url: str) -> Optional[dict]:
        """Return a broken-link entry if the URL is unreachable, else None."""
        try:
            req = urllib.request.Request(
                url, method="HEAD", headers={"User-Agent": "agent-validator/1.0"}
            )
            with urllib.request.urlopen(req, timeout=self.link_timeout) as resp:
                if resp.status >= 400:
                    return {"url": url, "status": resp.status, "error": f"HTTP {resp.status}"}
                return None
        except urllib.error.HTTPError as e:
            return {"url": url, "status": e.code, "error": f"HTTP {e.code}"}
        except urllib.error.URLError as e:
            return {"url": url, "status": 0, "error": str(e.reason)}
        except Exception as e:
            return {"url": url, "status": 0, "error": str(e)}

    def check_links_node(self, state: BrokenLinksState) -> Dict[str, List[dict]]:
        """Check each link concurrently for HTTP errors."""
        logger.info(f"Checking {len(state['all_links'])} links")
        self._update_progress("Checking links", advance=1)

        broken = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self._check_link, url): url
                for url in state["all_links"]
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    broken.append(result)

        broken.sort(key=lambda x: x["status"])
        logger.info(f"Found {len(broken)} broken links")
        return {"broken_links": broken}

    def generate_report_node(self, state: BrokenLinksState) -> Dict[str, str]:
        """Generate broken links report."""
        logger.debug("Generating broken links report")
        self._update_progress("Generating report", advance=1)

        total = len(state["all_links"])
        broken = state["broken_links"]

        if not broken:
            report = f"✓ SUCCESS: All {total} links are reachable on {state['url']}\n"
        else:
            report = f"✗ BROKEN LINKS DETECTED on {state['url']}\n"
            report += f"Checked: {total} | Broken: {len(broken)}\n\n"
            for i, link in enumerate(broken, 1):
                report += f"{i}. [{link['status']}] {link['url']}\n"
                report += f"   Error: {link['error']}\n"

        return {"report": report}

    def build_workflow(self) -> StateGraph:
        """Build the broken links detection workflow."""
        workflow = StateGraph(BrokenLinksState)
        workflow.add_node("extractor", self.extract_links_node)
        workflow.add_node("checker", self.check_links_node)
        workflow.add_node("reporter", self.generate_report_node)
        workflow.set_entry_point("extractor")
        workflow.add_edge("extractor", "checker")
        workflow.add_edge("checker", "reporter")
        workflow.add_edge("reporter", END)
        return workflow
