"""Base agent class for all validators."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from core.exceptions import LLMError
from utils.retry_utils import retry_with_exponential_backoff
from utils.text_utils import extract_json_from_markdown

logger = logging.getLogger(__name__)


class BaseAgentState(TypedDict):
    """Base state structure for all agents."""

    url: str
    report: str


class BaseAgent(ABC):
    """Abstract base class for all validation agents."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        temperature: float = 0,
        max_retries: int = 3,
        **kwargs,
    ):
        """
        Initialize base agent.

        Args:
            model: LLM model name
            temperature: LLM temperature parameter
            max_retries: Maximum retry attempts for LLM calls
            **kwargs: Additional agent-specific parameters
        """
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.config = kwargs
        self._llm: Optional[ChatGoogleGenerativeAI] = None
        self._workflow: Optional[StateGraph] = None
        self._app = None

        logger.info(f"Initialized {self.__class__.__name__} with model {model}")

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        """Lazy-load LLM instance."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm

    def _create_llm(self) -> ChatGoogleGenerativeAI:
        """Create LLM instance."""
        try:
            return ChatGoogleGenerativeAI(
                model=self.model, temperature=self.temperature
            )
        except Exception as e:
            raise LLMError(f"Failed to initialize LLM: {e}")

    @retry_with_exponential_backoff(
        max_retries=3, initial_delay=1.0, exceptions=(Exception,)
    )
    def invoke_llm(self, prompt: str) -> str:
        """
        Invoke LLM with retry logic.

        Args:
            prompt: Prompt to send to LLM

        Returns:
            LLM response content
        """
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise LLMError(f"LLM invocation failed: {e}")

    @staticmethod
    def parse_json_response(content: str) -> Any:
        """
        Parse JSON from LLM response.

        Args:
            content: Response content that may contain JSON

        Returns:
            Parsed JSON object
        """
        # Extract JSON from markdown code blocks
        content = extract_json_from_markdown(content)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Content: {content[:500]}")
            return []

    @abstractmethod
    def build_workflow(self) -> StateGraph:
        """
        Build the agent workflow graph.

        Returns:
            Configured StateGraph
        """
        pass

    @abstractmethod
    def get_state_class(self) -> type:
        """
        Get the state TypedDict class for this agent.

        Returns:
            State class
        """
        pass

    def compile(self):
        """Compile the workflow into an executable app."""
        if self._workflow is None:
            self._workflow = self.build_workflow()

        if self._app is None:
            self._app = self._workflow.compile()
            logger.debug(f"{self.__class__.__name__} workflow compiled")

        return self._app

    def run(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Run the agent on a URL.

        Args:
            url: URL to validate
            **kwargs: Additional state parameters

        Returns:
            Final state after execution
        """
        app = self.compile()

        # Create initial state
        initial_state = self.create_initial_state(url, **kwargs)

        logger.info(f"Running {self.__class__.__name__} on {url}")

        try:
            final_state = app.invoke(initial_state)
            logger.info(f"{self.__class__.__name__} completed successfully")
            return final_state
        except Exception as e:
            logger.error(f"{self.__class__.__name__} failed: {e}")
            raise

    @abstractmethod
    def create_initial_state(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Create initial state for the workflow.

        Args:
            url: URL to validate
            **kwargs: Additional state parameters

        Returns:
            Initial state dictionary
        """
        pass

    def get_report(self, result: Dict[str, Any]) -> str:
        """
        Extract report from result.

        Args:
            result: Result dictionary from workflow execution

        Returns:
            Report string
        """
        return result.get("report", "No report generated")

    @property
    def name(self) -> str:
        """Get agent name."""
        return self.__class__.__name__.replace("Agent", "")
