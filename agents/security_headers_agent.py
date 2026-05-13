"""Security headers agent for checking HTTP security response headers."""

import logging
from typing import List, TypedDict, Dict, Any

from langgraph.graph import StateGraph, END

from agents.base_agent import BaseAgent
from utils.validation_utils import validate_url

logger = logging.getLogger(__name__)

_REQUIRED_HEADERS = {
    "strict-transport-security": {
        "description": "HTTP Strict Transport Security (HSTS)",
        "severity": "high",
        "recommendation": "Add: Strict-Transport-Security: max-age=31536000; includeSubDomains",
    },
    "content-security-policy": {
        "description": "Content Security Policy (CSP)",
        "severity": "high",
        "recommendation": "Add a Content-Security-Policy header to prevent XSS attacks",
    },
    "x-frame-options": {
        "description": "Clickjacking protection",
        "severity": "medium",
        "recommendation": "Add: X-Frame-Options: DENY or SAMEORIGIN",
    },
    "x-content-type-options": {
        "description": "MIME-sniffing protection",
        "severity": "medium",
        "recommendation": "Add: X-Content-Type-Options: nosniff",
    },
    "referrer-policy": {
        "description": "Referrer Policy",
        "severity": "low",
        "recommendation": "Add: Referrer-Policy: strict-origin-when-cross-origin",
    },
    "permissions-policy": {
        "description": "Permissions Policy",
        "severity": "low",
        "recommendation": "Add Permissions-Policy to restrict access to browser APIs",
    },
}


class SecurityHeadersState(TypedDict):
    """State structure for security headers agent."""

    url: str
    headers: Dict[str, str]
    issues: List[dict]
    report: str


class SecurityHeadersAgent(BaseAgent):
    """Agent for checking HTTP security response headers."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        temperature: float = 0,
        provider: str = "gemini",
        **kwargs,
    ):
        super().__init__(model=model, temperature=temperature, provider=provider, **kwargs)

    def get_state_class(self) -> type:
        return SecurityHeadersState

    def create_initial_state(self, url: str, **kwargs) -> Dict[str, Any]:
        url = validate_url(url)
        return {"url": url, "headers": {}, "issues": [], "report": ""}

    def fetch_headers_node(self, state: SecurityHeadersState) -> Dict[str, Dict[str, str]]:
        """Capture HTTP response headers using Playwright's response event."""
        logger.info(f"Fetching security headers for: {state['url']}")
        self._update_progress("Fetching HTTP headers", advance=1)

        from utils.browser_utils import BrowserSession

        captured: Dict[str, str] = {}

        def _on_response(response) -> None:
            target = state["url"].rstrip("/")
            if response.url.rstrip("/") in (target, target.replace("http://", "https://")):
                captured.update({k.lower(): v for k, v in response.headers.items()})

        with BrowserSession() as browser:
            browser.page.on("response", _on_response)
            browser.navigate(state["url"])

        logger.debug(f"Captured {len(captured)} response headers")
        return {"headers": captured}

    def analyze_node(self, state: SecurityHeadersState) -> Dict[str, List[dict]]:
        """Apply rule-based checks against known security header requirements."""
        logger.info("Analyzing security headers")
        self._update_progress("Analyzing security headers", advance=1)

        headers = state["headers"]
        issues = []

        for header_name, meta in _REQUIRED_HEADERS.items():
            if header_name not in headers:
                issues.append({
                    "type": "missing_header",
                    "header": header_name,
                    "description": meta["description"],
                    "severity": meta["severity"],
                    "recommendation": meta["recommendation"],
                })

        cookie_header = headers.get("set-cookie", "")
        if cookie_header:
            if "secure" not in cookie_header.lower():
                issues.append({
                    "type": "insecure_cookie",
                    "header": "set-cookie",
                    "description": "Cookie missing Secure flag",
                    "severity": "high",
                    "recommendation": "Add the Secure flag to all cookies",
                })
            if "httponly" not in cookie_header.lower():
                issues.append({
                    "type": "insecure_cookie",
                    "header": "set-cookie",
                    "description": "Cookie missing HttpOnly flag",
                    "severity": "medium",
                    "recommendation": "Add the HttpOnly flag to prevent JS access to session cookies",
                })

        logger.info(f"Found {len(issues)} security header issues")
        return {"issues": issues}

    def generate_report_node(self, state: SecurityHeadersState) -> Dict[str, str]:
        """Generate security headers report."""
        logger.debug("Generating security headers report")
        self._update_progress("Generating report", advance=1)

        if not state["issues"]:
            return {"report": f"✓ SUCCESS: All security headers present on {state['url']}\n"}

        severity_order = ["high", "medium", "low"]
        grouped: Dict[str, list] = {s: [] for s in severity_order}
        for issue in state["issues"]:
            grouped[issue["severity"]].append(issue)

        report = f"✗ SECURITY HEADER ISSUES on {state['url']}\n"
        report += f"Total Issues: {len(state['issues'])}\n"

        for sev in severity_order:
            issues_list = grouped[sev]
            if not issues_list:
                continue
            report += f"\n{sev.upper()} SEVERITY ({len(issues_list)})\n{'='*40}\n"
            for i, issue in enumerate(issues_list, 1):
                report += f"{i}. {issue['description']}\n"
                report += f"   Header: {issue['header']}\n"
                report += f"   Fix: {issue['recommendation']}\n\n"

        return {"report": report}

    def build_workflow(self) -> StateGraph:
        """Build the security headers check workflow."""
        workflow = StateGraph(SecurityHeadersState)
        workflow.add_node("fetcher", self.fetch_headers_node)
        workflow.add_node("analyzer", self.analyze_node)
        workflow.add_node("reporter", self.generate_report_node)
        workflow.set_entry_point("fetcher")
        workflow.add_edge("fetcher", "analyzer")
        workflow.add_edge("analyzer", "reporter")
        workflow.add_edge("reporter", END)
        return workflow
