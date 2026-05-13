"""SEO agent for analyzing on-page SEO factors."""

import json
import operator
import logging
from pathlib import Path
from typing import Annotated, List, TypedDict, Dict, Any, Optional

from langgraph.graph import StateGraph, END

from agents.base_agent import BaseAgent
from utils.browser_utils import BrowserSession
from utils.validation_utils import validate_url

logger = logging.getLogger(__name__)

_SEO_EXTRACT_SCRIPT = """
() => {
    const getMeta = (name) => {
        const el = document.querySelector(
            `meta[name="${name}"], meta[property="${name}"]`
        );
        return el ? el.getAttribute('content') : null;
    };
    return {
        title:               document.title,
        title_length:        document.title.length,
        description:         getMeta('description'),
        keywords:            getMeta('keywords'),
        canonical:           (document.querySelector('link[rel="canonical"]') || {}).href || null,
        robots:              getMeta('robots'),
        og_title:            getMeta('og:title'),
        og_description:      getMeta('og:description'),
        og_image:            getMeta('og:image'),
        og_type:             getMeta('og:type'),
        twitter_card:        getMeta('twitter:card'),
        twitter_title:       getMeta('twitter:title'),
        h1_count:            document.querySelectorAll('h1').length,
        h1_texts:            Array.from(document.querySelectorAll('h1'))
                                 .map(h => h.innerText.trim()).slice(0, 3),
        images_without_alt:  document.querySelectorAll('img:not([alt]), img[alt=""]').length,
        total_images:        document.querySelectorAll('img').length,
        structured_data:     Array.from(
                                 document.querySelectorAll('script[type="application/ld+json"]')
                             ).map(s => { try { return JSON.parse(s.textContent); } catch(e) { return null; } })
                              .filter(Boolean).length,
        lang:                document.documentElement.lang || null,
        viewport_meta:       (document.querySelector('meta[name="viewport"]') || {}).content || null,
    };
}
"""


class SEOState(TypedDict):
    """State structure for SEO agent."""

    url: str
    seo_data: Dict[str, Any]
    issues: Annotated[List[dict], operator.add]
    report: str
    auth: Optional[Dict[str, Any]]


class SEOAgent(BaseAgent):
    """Agent for analyzing on-page SEO factors."""

    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        temperature: float = 0,
        provider: str = "gemini",
        **kwargs,
    ):
        super().__init__(model=model, temperature=temperature, provider=provider, **kwargs)
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        prompt_file = self.PROMPTS_DIR / "seo.md"
        return prompt_file.read_text(encoding="utf-8")

    def get_state_class(self) -> type:
        return SEOState

    def create_initial_state(self, url: str, **kwargs) -> Dict[str, Any]:
        url = validate_url(url)
        return {
            "url": url,
            "seo_data": {},
            "issues": [],
            "report": "",
            "auth": kwargs.get("auth"),
        }

    def extract_node(self, state: SEOState) -> Dict[str, Any]:
        """Extract SEO metadata from the page via JavaScript."""
        logger.info(f"Extracting SEO data from: {state['url']}")
        self._update_progress("Extracting SEO metadata", advance=1)

        with BrowserSession(auth=state.get("auth")) as browser:
            browser.navigate(state["url"])
            browser.page.wait_for_timeout(2000)
            seo_data = browser.page.evaluate(_SEO_EXTRACT_SCRIPT)

        logger.debug(f"Extracted SEO data: {seo_data}")
        return {"seo_data": seo_data}

    def analyze_node(self, state: SEOState) -> Dict[str, List[dict]]:
        """Send SEO data to LLM for evaluation."""
        logger.info("Analyzing SEO data with AI")
        self._update_progress("Analyzing SEO with AI", advance=1)

        prompt = self._prompt_template.replace(
            "{seo_data}", json.dumps(state["seo_data"], indent=2)
        )
        response = self.invoke_llm(prompt)
        found_issues = self.parse_json_response(response)

        if not isinstance(found_issues, list):
            found_issues = []

        logger.info(f"Found {len(found_issues)} SEO issues")
        return {"issues": found_issues}

    def generate_report_node(self, state: SEOState) -> Dict[str, str]:
        """Generate SEO report."""
        logger.debug("Generating SEO report")
        self._update_progress("Generating report", advance=1)

        d = state["seo_data"]
        report = f"SEO REPORT for {state['url']}\n{'='*60}\n"
        report += f"Title:               {d.get('title') or 'MISSING'} ({d.get('title_length', 0)} chars)\n"
        report += f"Description:         {d.get('description') or 'MISSING'}\n"
        report += f"Canonical:           {d.get('canonical') or 'MISSING'}\n"
        report += f"H1 tags:             {d.get('h1_count', 0)}\n"
        report += f"Open Graph:          {'present' if d.get('og_title') else 'missing'}\n"
        report += f"Structured data:     {d.get('structured_data', 0)} schema(s)\n"
        report += f"Images missing alt:  {d.get('images_without_alt', 0)} / {d.get('total_images', 0)}\n"
        report += f"Lang attribute:      {d.get('lang') or 'MISSING'}\n"

        if not state["issues"]:
            report += "\n✓ SUCCESS: No significant SEO issues detected\n"
        else:
            severity_order = ["critical", "high", "medium", "low"]
            grouped: Dict[str, list] = {s: [] for s in severity_order}
            for issue in state["issues"]:
                grouped.setdefault(issue.get("severity", "low"), []).append(issue)

            report += f"\n✗ {len(state['issues'])} SEO ISSUES DETECTED\n"
            for sev in severity_order:
                issues_list = grouped.get(sev, [])
                if not issues_list:
                    continue
                report += f"\n{sev.upper()} ({len(issues_list)})\n{'-'*40}\n"
                for i, issue in enumerate(issues_list, 1):
                    report += f"{i}. {issue.get('issue', 'No description')}\n"
                    if issue.get("recommendation"):
                        report += f"   Fix: {issue['recommendation']}\n"

        return {"report": report}

    def build_workflow(self) -> StateGraph:
        """Build the SEO analysis workflow."""
        workflow = StateGraph(SEOState)
        workflow.add_node("extractor", self.extract_node)
        workflow.add_node("analyzer", self.analyze_node)
        workflow.add_node("reporter", self.generate_report_node)
        workflow.set_entry_point("extractor")
        workflow.add_edge("extractor", "analyzer")
        workflow.add_edge("analyzer", "reporter")
        workflow.add_edge("reporter", END)
        return workflow
