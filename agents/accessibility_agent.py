"""Accessibility QA agent for detecting WCAG/a11y issues."""

import operator
import logging
from pathlib import Path
from typing import Annotated, List, TypedDict, Dict, Any, Optional

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from agents.base_agent import BaseAgent
from utils.browser_utils import BrowserSession
from utils.validation_utils import validate_url, validate_viewport

logger = logging.getLogger(__name__)


class AccessibilityState(TypedDict):
    """State structure for accessibility agent."""

    url: str
    screenshot: str
    html_content: str
    viewport_width: int
    viewport_height: int
    issues: Annotated[List[dict], operator.add]
    report: str
    auth: Optional[Dict[str, Any]]


class AccessibilityAgent(BaseAgent):
    """Agent for detecting WCAG 2.1 accessibility issues on web pages."""

    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        temperature: float = 0,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        wait_time: int = 3000,
        provider: str = "gemini",
        **kwargs,
    ):
        super().__init__(model=model, temperature=temperature, provider=provider, **kwargs)
        self.viewport_width, self.viewport_height = validate_viewport(viewport_width, viewport_height)
        self.wait_time = wait_time
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        prompt_file = self.PROMPTS_DIR / "accessibility.md"
        return prompt_file.read_text(encoding="utf-8")

    def get_state_class(self) -> type:
        return AccessibilityState

    def create_initial_state(self, url: str, **kwargs) -> Dict[str, Any]:
        url = validate_url(url)
        viewport_width = kwargs.get("viewport_width", self.viewport_width)
        viewport_height = kwargs.get("viewport_height", self.viewport_height)
        viewport_width, viewport_height = validate_viewport(viewport_width, viewport_height)
        return {
            "url": url,
            "screenshot": "",
            "html_content": "",
            "viewport_width": viewport_width,
            "viewport_height": viewport_height,
            "issues": [],
            "report": "",
            "auth": kwargs.get("auth"),
        }

    def capture_node(self, state: AccessibilityState) -> Dict[str, Any]:
        """Capture screenshot and HTML for accessibility analysis."""
        logger.info(f"Capturing page for accessibility analysis: {state['url']}")
        self._update_progress("Capturing page", advance=1)

        with BrowserSession(
            viewport={"width": state["viewport_width"], "height": state["viewport_height"]},
            auth=state.get("auth"),
        ) as browser:
            browser.navigate(state["url"])
            screenshot_b64 = browser.take_screenshot(wait_time=self.wait_time)
            html_content = browser.page.content()

        return {"screenshot": screenshot_b64, "html_content": html_content[:50000]}

    def analyze_node(self, state: AccessibilityState) -> Dict[str, List[dict]]:
        """Analyze page for WCAG accessibility issues using vision LLM."""
        logger.info("Analyzing accessibility issues with AI")
        self._update_progress("Analyzing accessibility with AI", advance=1)

        if self.provider == "openai":
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{state['screenshot']}"},
            }
        else:
            image_content = {
                "type": "image_url",
                "image_url": f"data:image/png;base64,{state['screenshot']}",
            }

        prompt_text = self._prompt_template.replace("{html}", state["html_content"][:20000])
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                image_content,
            ]
        )

        response = self.llm.invoke([message])
        found_issues = self.parse_json_response(response.content)

        if not isinstance(found_issues, list):
            found_issues = []

        logger.info(f"Found {len(found_issues)} accessibility issues")
        return {"issues": found_issues}

    def generate_report_node(self, state: AccessibilityState) -> Dict[str, str]:
        """Generate accessibility report grouped by WCAG level."""
        logger.debug("Generating accessibility report")
        self._update_progress("Generating report", advance=1)

        if not state["issues"]:
            return {"report": f"✓ SUCCESS: No accessibility issues detected on {state['url']}"}

        level_groups: Dict[str, list] = {"A": [], "AA": [], "AAA": [], "best_practice": []}
        for issue in state["issues"]:
            level = issue.get("wcag_level", "best_practice").upper()
            target = level if level in level_groups else "best_practice"
            level_groups[target].append(issue)

        report = f"✗ ACCESSIBILITY ISSUES DETECTED on {state['url']}\n"
        report += (
            f"Total Issues: {len(state['issues'])} "
            f"(A: {len(level_groups['A'])}, AA: {len(level_groups['AA'])}, "
            f"AAA: {len(level_groups['AAA'])}, Best Practice: {len(level_groups['best_practice'])})\n"
        )

        for level_name in ["A", "AA", "AAA", "best_practice"]:
            issues_list = level_groups[level_name]
            if not issues_list:
                continue
            label = f"WCAG {level_name}" if level_name != "best_practice" else "BEST PRACTICE"
            report += f"\n{'='*60}\n{label} ({len(issues_list)})\n{'='*60}\n"
            for i, issue in enumerate(issues_list, 1):
                report += f"\n{i}. [{issue.get('type', 'unknown').upper()}] {issue.get('issue', 'No description')}\n"
                report += f"   Element: {issue.get('element', 'Not specified')}\n"
                report += f"   Fix: {issue.get('recommendation', 'No recommendation')}\n"

        return {"report": report}

    def build_workflow(self) -> StateGraph:
        """Build the accessibility QA workflow."""
        workflow = StateGraph(AccessibilityState)
        workflow.add_node("capture", self.capture_node)
        workflow.add_node("analyzer", self.analyze_node)
        workflow.add_node("reporter", self.generate_report_node)
        workflow.set_entry_point("capture")
        workflow.add_edge("capture", "analyzer")
        workflow.add_edge("analyzer", "reporter")
        workflow.add_edge("reporter", END)
        return workflow
