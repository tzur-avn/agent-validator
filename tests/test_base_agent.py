"""Unit tests for base agent functionality."""

import pytest
from unittest.mock import Mock, patch
from agents.base_agent import BaseAgent
from core.exceptions import LLMError


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def build_workflow(self):
        return None

    def get_state_class(self):
        return dict

    def create_initial_state(self, url, **kwargs):
        return {"url": url}


def test_base_agent_initialization():
    """Test base agent initialization."""
    agent = MockAgent(model="test-model", temperature=0.5)

    assert agent.model == "test-model"
    assert agent.temperature == 0.5
    assert agent.max_retries == 3


def test_parse_json_response():
    """Test JSON parsing from various formats."""
    agent = MockAgent()

    # Plain JSON
    result = agent.parse_json_response('{"key": "value"}')
    assert result == {"key": "value"}

    # JSON in markdown code block
    result = agent.parse_json_response('```json\n{"key": "value"}\n```')
    assert result == {"key": "value"}

    # Invalid JSON
    result = agent.parse_json_response("not json")
    assert result == []


@patch("agents.base_agent.ChatGoogleGenerativeAI")
def test_invoke_llm_success(mock_llm_class):
    """Test successful LLM invocation."""
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = "test response"
    mock_llm.invoke.return_value = mock_response
    mock_llm_class.return_value = mock_llm

    agent = MockAgent()
    result = agent.invoke_llm("test prompt")

    assert result == "test response"
    mock_llm.invoke.assert_called_once_with("test prompt")


def test_agent_name_property():
    """Test agent name extraction."""
    agent = MockAgent()
    assert agent.name == "Mock"
