"""Spell checker agent for validating text content."""

import operator
import logging
from pathlib import Path
from typing import Annotated, List, TypedDict, Dict, Any

from langgraph.graph import StateGraph, END

from agents.base_agent import BaseAgent
from utils.browser_utils import BrowserSession
from utils.text_utils import clean_text, format_bidi_text
from utils.validation_utils import validate_url

logger = logging.getLogger(__name__)


class SpellCheckerState(TypedDict):
    """State structure for spell checker agent."""

    url: str
    raw_text: str
    errors: Annotated[List[dict], operator.add]
    report: str


class SpellCheckerAgent(BaseAgent):
    """Agent for detecting spelling and grammar errors on web pages."""

    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        temperature: float = 0,
        max_text_length: int = 10000,
        wait_time: int = 2000,
        provider: str = "gemini",
        **kwargs,
    ):
        """
        Initialize spell checker agent.

        Args:
            model: LLM model name
            temperature: LLM temperature parameter
            max_text_length: Maximum text length to analyze
            wait_time: Time to wait for dynamic content (milliseconds)
            provider: LLM provider ("gemini" or "openai")
            **kwargs: Additional parameters
        """
        super().__init__(
            model=model, temperature=temperature, provider=provider, **kwargs
        )
        self.max_text_length = max_text_length
        self.wait_time = wait_time
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the prompt template from markdown file."""
        prompt_file = self.PROMPTS_DIR / "spell_checker.md"
        return prompt_file.read_text(encoding="utf-8")

    def get_state_class(self) -> type:
        """Get the state class for this agent."""
        return SpellCheckerState

    def create_initial_state(self, url: str, **kwargs) -> Dict[str, Any]:
        """Create initial state for spell checking."""
        url = validate_url(url)
        return {
            "url": url,
            "raw_text": "",
            "errors": [],
            "report": "",
            "auth": kwargs.get("auth"),  # Pass auth config to state
        }

    def scrape_web_node(self, state: SpellCheckerState) -> Dict[str, str]:
        """Scrape text content from web page."""
        logger.info(f"Scraping text from: {state['url']}")
        self._update_progress("Scraping web page", advance=1)

        # Pass auth config to browser session
        auth_config = state.get("auth")
        with BrowserSession(auth=auth_config) as browser:
            browser.navigate(state["url"])
            visible_text = browser.get_text(wait_time=self.wait_time)

        # Clean and limit text
        clean = clean_text(visible_text, max_length=self.max_text_length)
        logger.debug(f"Extracted {len(clean)} characters")

        return {"raw_text": clean}

    def analyze_text_node(self, state: SpellCheckerState) -> Dict[str, List[dict]]:
        """Analyze text for spelling and grammar errors."""
        logger.info(f"Analyzing {len(state['raw_text'])} characters")
        self._update_progress("Analyzing text with AI", advance=1)

        prompt = self._prompt_template.replace("{text}", state["raw_text"])

        response = self.invoke_llm(prompt)
        found_errors = self.parse_json_response(response)

        if not isinstance(found_errors, list):
            found_errors = []

        logger.info(f"Found {len(found_errors)} potential errors")
        return {"errors": found_errors}

    def generate_report_node(self, state: SpellCheckerState) -> Dict[str, str]:
        """Generate report from findings."""
        logger.debug("Generating spell check report")
        self._update_progress("Generating report", advance=1)

        if not state["errors"]:
            report = f"✓ SUCCESS: No spelling errors found on {state['url']}"
        else:
            report = f"✗ SPELLING ERRORS DETECTED on {state['url']}\n"
            report += f"Total Errors: {len(state['errors'])}\n\n"

            for i, err in enumerate(state["errors"], 1):
                original = format_bidi_text(err.get("original", ""))
                correction = format_bidi_text(err.get("correction", ""))
                context = format_bidi_text(err.get("context", ""))

                report += f"{i}. Error: '{original}' → Correction: '{correction}'\n"
                report += f'   Context: "{context}"\n\n'

        return {"report": report}

    def build_workflow(self) -> StateGraph:
        """Build the spell checker workflow."""
        workflow = StateGraph(SpellCheckerState)

        workflow.add_node("scraper", self.scrape_web_node)
        workflow.add_node("analyzer", self.analyze_text_node)
        workflow.add_node("reporter", self.generate_report_node)

        workflow.set_entry_point("scraper")
        workflow.add_edge("scraper", "analyzer")
        workflow.add_edge("analyzer", "reporter")
        workflow.add_edge("reporter", END)

        return workflow
