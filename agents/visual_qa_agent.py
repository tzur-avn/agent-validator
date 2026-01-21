"""Visual QA agent for detecting UI/UX issues."""

import operator
import logging
from pathlib import Path
from typing import Annotated, List, TypedDict, Dict, Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from agents.base_agent import BaseAgent
from utils.browser_utils import BrowserSession
from utils.validation_utils import validate_url, validate_viewport

logger = logging.getLogger(__name__)


class VisualQAState(TypedDict):
    """State structure for visual QA agent."""

    url: str
    screenshot: str
    viewport_width: int
    viewport_height: int
    issues: Annotated[List[dict], operator.add]
    report: str
    element_screenshots: Dict[int, str]  # index -> base64 screenshot


class VisualQAAgent(BaseAgent):
    """Agent for detecting visual and UI/UX issues on web pages."""

    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        temperature: float = 0,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        wait_time: int = 5000,
        provider: str = "gemini",
        **kwargs,
    ):
        """
        Initialize visual QA agent.

        Args:
            model: LLM model name (must support vision)
            temperature: LLM temperature parameter
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            wait_time: Time to wait before screenshot (milliseconds)
            provider: LLM provider ("gemini" or "openai")
            **kwargs: Additional parameters
        """
        super().__init__(
            model=model, temperature=temperature, provider=provider, **kwargs
        )
        self.viewport_width, self.viewport_height = validate_viewport(
            viewport_width, viewport_height
        )
        self.wait_time = wait_time
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the prompt template from markdown file."""
        prompt_file = self.PROMPTS_DIR / "visual_qa.md"
        return prompt_file.read_text(encoding="utf-8")

    def get_state_class(self) -> type:
        """Get the state class for this agent."""
        return VisualQAState

    def create_initial_state(self, url: str, **kwargs) -> Dict[str, Any]:
        """Create initial state for visual QA."""
        url = validate_url(url)

        # Allow override of viewport from kwargs
        viewport_width = kwargs.get("viewport_width", self.viewport_width)
        viewport_height = kwargs.get("viewport_height", self.viewport_height)
        viewport_width, viewport_height = validate_viewport(
            viewport_width, viewport_height
        )

        return {
            "url": url,
            "screenshot": "",
            "viewport_width": viewport_width,
            "viewport_height": viewport_height,
            "issues": [],
            "report": "",
            "element_screenshots": {},
        }

    def capture_visual_node(self, state: VisualQAState) -> Dict[str, str]:
        """Capture screenshot of the web page."""
        logger.info(
            f"Capturing screenshot of {state['url']} "
            f"at {state['viewport_width']}x{state['viewport_height']}"
        )
        self._update_progress("Capturing screenshot", advance=1)

        with BrowserSession(
            viewport={
                "width": state["viewport_width"],
                "height": state["viewport_height"],
            }
        ) as browser:
            browser.navigate(state["url"])
            screenshot_b64 = browser.take_screenshot(wait_time=self.wait_time)

        logger.debug("Screenshot captured successfully")
        return {"screenshot": screenshot_b64}

    def analyze_visual_node(self, state: VisualQAState) -> Dict[str, List[dict]]:
        """Analyze screenshot for visual issues."""
        logger.info("Analyzing visual elements with AI")
        self._update_progress("Analyzing visuals with AI", advance=1)

        # Format image URL based on provider
        if self.provider == "openai":
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{state['screenshot']}"},
            }
        else:  # gemini
            image_content = {
                "type": "image_url",
                "image_url": f"data:image/png;base64,{state['screenshot']}",
            }

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": self._prompt_template,
                },
                image_content,
            ]
        )

        response = self.llm.invoke([message])
        found_issues = self.parse_json_response(response.content)

        if not isinstance(found_issues, list):
            found_issues = []

        logger.info(f"Found {len(found_issues)} potential issues")
        return {"issues": found_issues}

    def capture_element_screenshots_node(
        self, state: VisualQAState
    ) -> Dict[str, Dict[int, str]]:
        """Capture screenshots of specific issue elements/regions."""
        if not state["issues"]:
            logger.debug("No issues to capture screenshots for")
            return {"element_screenshots": {}}

        logger.info(f"Capturing screenshots for {len(state['issues'])} issues")
        self._update_progress("Capturing element screenshots", advance=1)

        element_screenshots = {}

        with BrowserSession(
            viewport={
                "width": state["viewport_width"],
                "height": state["viewport_height"],
            }
        ) as browser:
            browser.navigate(state["url"])
            browser.page.wait_for_timeout(self.wait_time)

            for idx, issue in enumerate(state["issues"]):
                try:
                    # Try selector first if available
                    selector = issue.get("selector")
                    if selector and selector.strip() and selector != "null":
                        screenshot_b64 = browser.take_element_screenshot(
                            selector=selector
                        )
                        if screenshot_b64:
                            element_screenshots[idx] = screenshot_b64
                            logger.debug(
                                f"Captured screenshot for issue {idx} using selector"
                            )
                            continue

                    # Fall back to coordinates if available
                    coordinates = issue.get("coordinates")
                    if coordinates and isinstance(coordinates, dict):
                        x = coordinates.get("x", 0)
                        y = coordinates.get("y", 0)
                        width = coordinates.get("width", 0)
                        height = coordinates.get("height", 0)

                        if width > 0 and height > 0:
                            clip_region = {
                                "x": int(x),
                                "y": int(y),
                                "width": int(width),
                                "height": int(height),
                            }
                            screenshot_b64 = browser.take_element_screenshot(
                                clip_region=clip_region
                            )
                            if screenshot_b64:
                                element_screenshots[idx] = screenshot_b64
                                logger.debug(
                                    f"Captured screenshot for issue {idx} using coordinates"
                                )

                except Exception as e:
                    logger.warning(f"Failed to capture screenshot for issue {idx}: {e}")

        logger.info(
            f"Captured {len(element_screenshots)} element screenshots out of {len(state['issues'])} issues"
        )
        return {"element_screenshots": element_screenshots}

    def generate_report_node(self, state: VisualQAState) -> Dict[str, str]:
        """Generate detailed visual QA report."""
        logger.debug("Generating visual QA report")
        self._update_progress("Generating report", advance=1)

        viewport_info = f"{state['viewport_width']}x{state['viewport_height']}"

        if not state["issues"]:
            report = f"✓ SUCCESS: No visual issues detected on {state['url']}\n"
            report += f"Viewport: {viewport_info}"
        else:
            # Group by severity
            severity_groups = {"critical": [], "high": [], "medium": [], "low": []}

            for issue in state["issues"]:
                severity = issue.get("severity", "low")
                if severity in severity_groups:
                    severity_groups[severity].append(issue)

            report = f"✗ VISUAL ISSUES DETECTED on {state['url']}\n"
            report += f"Viewport: {viewport_info}\n"
            report += f"Total Issues: {len(state['issues'])} "
            report += f"(Critical: {len(severity_groups['critical'])}, "
            report += f"High: {len(severity_groups['high'])}, "
            report += f"Medium: {len(severity_groups['medium'])}, "
            report += f"Low: {len(severity_groups['low'])})\n\n"

            # Report by severity
            for severity_name in ["critical", "high", "medium", "low"]:
                issues_list = severity_groups[severity_name]
                if issues_list:
                    report += f"\n{'='*60}\n"
                    report += f"{severity_name.upper()} SEVERITY ISSUES ({len(issues_list)})\n"
                    report += f"{'='*60}\n"

                    for i, issue in enumerate(issues_list, 1):
                        issue_type = issue.get("type", "unknown").upper()
                        issue_desc = issue.get("issue", "No description")
                        location = issue.get("location", "Not specified")
                        recommendation = issue.get(
                            "recommendation", "No recommendation"
                        )

                        report += f"\n{i}. [{issue_type}] {issue_desc}\n"
                        report += f"   Location: {location}\n"
                        report += f"   Fix: {recommendation}\n"

        return {"report": report}

    def build_workflow(self) -> StateGraph:
        """Build the visual QA workflow."""
        workflow = StateGraph(VisualQAState)

        workflow.add_node("capture", self.capture_visual_node)
        workflow.add_node("analyzer", self.analyze_visual_node)
        workflow.add_node("capture_elements", self.capture_element_screenshots_node)
        workflow.add_node("reporter", self.generate_report_node)

        workflow.set_entry_point("capture")
        workflow.add_edge("capture", "analyzer")
        workflow.add_edge("analyzer", "capture_elements")
        workflow.add_edge("capture_elements", "reporter")
        workflow.add_edge("reporter", END)

        return workflow
