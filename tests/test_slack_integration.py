"""Tests for Slack integration components."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from integrations.conversation_manager import ConversationManager
from integrations.slack_formatter import SlackFormatter


class TestConversationManager:
    """Test ConversationManager class."""

    def test_start_conversation(self):
        """Test starting a new conversation."""
        manager = ConversationManager(timeout_minutes=30)

        conversation = manager.start_conversation(
            user_id="U123", agent_name="spell_checker", step="url"
        )

        assert conversation["user_id"] == "U123"
        assert conversation["agent_name"] == "spell_checker"
        assert conversation["step"] == "url"
        assert "started_at" in conversation
        assert "last_activity" in conversation

    def test_get_conversation(self):
        """Test getting an active conversation."""
        manager = ConversationManager(timeout_minutes=30)

        manager.start_conversation(user_id="U123", agent_name="spell_checker")

        conversation = manager.get_conversation("U123")
        assert conversation is not None
        assert conversation["user_id"] == "U123"

    def test_get_nonexistent_conversation(self):
        """Test getting a conversation that doesn't exist."""
        manager = ConversationManager()

        conversation = manager.get_conversation("U999")
        assert conversation is None

    def test_update_conversation(self):
        """Test updating conversation data."""
        manager = ConversationManager()

        manager.start_conversation(user_id="U123", agent_name="spell_checker")

        updated = manager.update_conversation("U123", {"url": "https://example.com"})

        assert updated is not None
        assert updated["data"]["url"] == "https://example.com"

    def test_end_conversation(self):
        """Test ending a conversation."""
        manager = ConversationManager()

        manager.start_conversation(user_id="U123", agent_name="spell_checker")

        manager.end_conversation("U123")

        conversation = manager.get_conversation("U123")
        assert conversation is None

    def test_conversation_timeout(self):
        """Test conversation timeout."""
        manager = ConversationManager(timeout_minutes=1)

        # Start conversation
        manager.start_conversation(user_id="U123", agent_name="spell_checker")

        # Manually set last_activity to past
        manager.conversations["U123"]["last_activity"] = datetime.now() - timedelta(
            minutes=2
        )

        # Should return None due to timeout
        conversation = manager.get_conversation("U123")
        assert conversation is None

    def test_has_active_conversation(self):
        """Test checking for active conversation."""
        manager = ConversationManager()

        assert not manager.has_active_conversation("U123")

        manager.start_conversation(user_id="U123", agent_name="spell_checker")

        assert manager.has_active_conversation("U123")


class TestSlackFormatter:
    """Test SlackFormatter class."""

    def test_format_spell_checker_result_with_errors(self):
        """Test formatting spell checker result with errors."""
        formatter = SlackFormatter()

        result = {
            "agent": "SpellChecker",
            "url": "https://example.com",
            "errors": [
                {
                    "original": "teh",
                    "correction": "the",
                    "context": "This is teh main page",
                }
            ],
        }

        formatted = formatter.format_agent_result(result)

        assert "blocks" in formatted
        assert len(formatted["blocks"]) > 0
        # Check header
        assert formatted["blocks"][0]["type"] == "header"
        assert "Spell Checker Report" in formatted["blocks"][0]["text"]["text"]

    def test_format_spell_checker_result_no_errors(self):
        """Test formatting spell checker result with no errors."""
        formatter = SlackFormatter()

        result = {"agent": "SpellChecker", "url": "https://example.com", "errors": []}

        formatted = formatter.format_agent_result(result)

        assert "blocks" in formatted
        # Should contain success message
        blocks_text = str(formatted["blocks"])
        assert "No spelling or grammar issues found" in blocks_text

    def test_format_visual_qa_result_with_issues(self):
        """Test formatting visual QA result with issues."""
        formatter = SlackFormatter()

        result = {
            "agent": "VisualQA",
            "url": "https://example.com",
            "issues": [
                {
                    "severity": "high",
                    "description": "Button cut off",
                    "element": ".button",
                }
            ],
        }

        formatted = formatter.format_agent_result(result)

        assert "blocks" in formatted
        assert len(formatted["blocks"]) > 0
        # Check header
        assert formatted["blocks"][0]["type"] == "header"
        assert "Visual QA Report" in formatted["blocks"][0]["text"]["text"]

    def test_format_visual_qa_result_no_issues(self):
        """Test formatting visual QA result with no issues."""
        formatter = SlackFormatter()

        result = {"agent": "VisualQA", "url": "https://example.com", "issues": []}

        formatted = formatter.format_agent_result(result)

        assert "blocks" in formatted
        # Should contain success message
        blocks_text = str(formatted["blocks"])
        assert "No visual issues found" in blocks_text

    def test_format_generic_result(self):
        """Test formatting generic result."""
        formatter = SlackFormatter()

        result = {
            "agent": "CustomAgent",
            "url": "https://example.com",
            "report": "Test report",
        }

        formatted = formatter.format_agent_result(result)

        # Should return string for unknown agent type
        assert isinstance(formatted, str)
        assert "CustomAgent" in formatted
        assert "https://example.com" in formatted

    def test_format_error(self):
        """Test formatting error message."""
        error_msg = SlackFormatter.format_error("Something went wrong")

        assert "❌" in error_msg
        assert "Error" in error_msg
        assert "Something went wrong" in error_msg

    def test_format_success(self):
        """Test formatting success message."""
        success_msg = SlackFormatter.format_success("Operation completed")

        assert "✅" in success_msg
        assert "Operation completed" in success_msg


# Note: SlackBot tests would require mocking the Slack SDK extensively
# These should be integration tests in a separate test suite
