"""Performance agent for measuring web page load metrics."""

import logging
from typing import List, TypedDict, Dict, Any, Optional

from langgraph.graph import StateGraph, END

from agents.base_agent import BaseAgent
from utils.browser_utils import BrowserSession
from utils.validation_utils import validate_url

logger = logging.getLogger(__name__)

_PERF_SCRIPT = """
() => {
    const nav = performance.getEntriesByType('navigation')[0] || {};
    const resources = performance.getEntriesByType('resource');
    const totalSize = resources.reduce((sum, r) => sum + (r.transferSize || 0), 0);
    return {
        dns:                Math.round((nav.domainLookupEnd  || 0) - (nav.domainLookupStart || 0)),
        tcp:                Math.round((nav.connectEnd       || 0) - (nav.connectStart      || 0)),
        ttfb:               Math.round((nav.responseStart   || 0) - (nav.requestStart      || 0)),
        dom_interactive:    Math.round(nav.domInteractive              || 0),
        dom_content_loaded: Math.round(nav.domContentLoadedEventEnd   || 0),
        load_event:         Math.round(nav.loadEventEnd                || 0),
        resource_count:     resources.length,
        total_transfer_kb:  Math.round(totalSize / 1024),
        large_resources:    resources
            .filter(r => r.transferSize > 500 * 1024)
            .map(r => ({ name: r.name.split('/').pop(), size_kb: Math.round(r.transferSize / 1024) }))
            .slice(0, 10)
    };
}
"""

_THRESHOLDS = [
    ("ttfb",               "Time to First Byte",  600,  "high",   "Optimize server response time, use a CDN or add server-side caching"),
    ("dom_content_loaded", "DOMContentLoaded",    3000, "medium", "Reduce render-blocking resources (CSS/JS in <head>)"),
    ("load_event",         "Page Load Time",      5000, "high",   "Reduce page weight, lazy-load non-critical resources"),
]


class PerformanceState(TypedDict):
    """State structure for performance agent."""

    url: str
    metrics: Dict[str, Any]
    issues: List[dict]
    report: str
    auth: Optional[Dict[str, Any]]


class PerformanceAgent(BaseAgent):
    """Agent for measuring and reporting web page performance metrics."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        temperature: float = 0,
        wait_time: int = 5000,
        provider: str = "gemini",
        **kwargs,
    ):
        super().__init__(model=model, temperature=temperature, provider=provider, **kwargs)
        self.wait_time = wait_time

    def get_state_class(self) -> type:
        return PerformanceState

    def create_initial_state(self, url: str, **kwargs) -> Dict[str, Any]:
        url = validate_url(url)
        return {
            "url": url,
            "metrics": {},
            "issues": [],
            "report": "",
            "auth": kwargs.get("auth"),
        }

    def measure_node(self, state: PerformanceState) -> Dict[str, Any]:
        """Collect browser navigation and resource timing metrics."""
        logger.info(f"Measuring performance for: {state['url']}")
        self._update_progress("Measuring page performance", advance=1)

        with BrowserSession(auth=state.get("auth")) as browser:
            browser.navigate(state["url"])
            browser.page.wait_for_timeout(self.wait_time)
            metrics = browser.page.evaluate(_PERF_SCRIPT)

        logger.debug(f"Performance metrics: {metrics}")
        return {"metrics": metrics}

    def analyze_node(self, state: PerformanceState) -> Dict[str, List[dict]]:
        """Apply rule-based thresholds to collected metrics."""
        logger.info("Analyzing performance metrics")
        self._update_progress("Analyzing metrics", advance=1)

        m = state["metrics"]
        issues = []

        for key, label, threshold, severity, fix in _THRESHOLDS:
            value = m.get(key, 0)
            if value > threshold:
                issues.append({
                    "type": "timing",
                    "metric": label,
                    "value_ms": value,
                    "threshold_ms": threshold,
                    "severity": severity,
                    "recommendation": fix,
                })

        if m.get("resource_count", 0) > 100:
            issues.append({
                "type": "resource_count",
                "metric": "Total Resources",
                "value": m["resource_count"],
                "severity": "medium",
                "recommendation": "Bundle assets, use HTTP/2 multiplexing, or reduce third-party scripts",
            })

        if m.get("total_transfer_kb", 0) > 3000:
            issues.append({
                "type": "page_weight",
                "metric": "Total Transfer Size",
                "value_kb": m["total_transfer_kb"],
                "severity": "high",
                "recommendation": "Enable gzip/brotli compression, optimize images, minify JS/CSS",
            })

        for res in m.get("large_resources", []):
            issues.append({
                "type": "large_resource",
                "metric": f"Large resource: {res['name']}",
                "value_kb": res["size_kb"],
                "severity": "medium",
                "recommendation": f"Optimize or lazy-load {res['name']} ({res['size_kb']} KB)",
            })

        return {"issues": issues}

    def generate_report_node(self, state: PerformanceState) -> Dict[str, str]:
        """Generate human-readable performance report."""
        logger.debug("Generating performance report")
        self._update_progress("Generating report", advance=1)

        m = state["metrics"]
        report = f"PERFORMANCE REPORT for {state['url']}\n{'='*60}\n"
        report += f"DNS Lookup:          {m.get('dns', 0):>6} ms\n"
        report += f"TCP Connect:         {m.get('tcp', 0):>6} ms\n"
        report += f"Time to First Byte:  {m.get('ttfb', 0):>6} ms\n"
        report += f"DOM Interactive:     {m.get('dom_interactive', 0):>6} ms\n"
        report += f"DOMContentLoaded:    {m.get('dom_content_loaded', 0):>6} ms\n"
        report += f"Page Load:           {m.get('load_event', 0):>6} ms\n"
        report += f"Total Resources:     {m.get('resource_count', 0):>6}\n"
        report += f"Total Transfer:      {m.get('total_transfer_kb', 0):>6} KB\n"

        if not state["issues"]:
            report += "\n✓ SUCCESS: All performance metrics within acceptable thresholds\n"
        else:
            report += f"\n✗ {len(state['issues'])} PERFORMANCE ISSUES DETECTED\n"
            for i, issue in enumerate(state["issues"], 1):
                report += f"\n{i}. [{issue['type'].upper()}] {issue['metric']}\n"
                if "value_ms" in issue:
                    report += f"   Value: {issue['value_ms']} ms (threshold: {issue['threshold_ms']} ms)\n"
                elif "value_kb" in issue:
                    report += f"   Value: {issue['value_kb']} KB\n"
                elif "value" in issue:
                    report += f"   Value: {issue['value']}\n"
                report += f"   Fix: {issue['recommendation']}\n"

        return {"report": report}

    def build_workflow(self) -> StateGraph:
        """Build the performance measurement workflow."""
        workflow = StateGraph(PerformanceState)
        workflow.add_node("measure", self.measure_node)
        workflow.add_node("analyzer", self.analyze_node)
        workflow.add_node("reporter", self.generate_report_node)
        workflow.set_entry_point("measure")
        workflow.add_edge("measure", "analyzer")
        workflow.add_edge("analyzer", "reporter")
        workflow.add_edge("reporter", END)
        return workflow
