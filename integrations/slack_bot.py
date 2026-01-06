"""Slack bot for interacting with validation agents."""

import logging
import os
from typing import Dict, Any, Optional
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from core.orchestrator import Orchestrator
from integrations.conversation_manager import ConversationManager
from integrations.slack_formatter import SlackFormatter
from core.exceptions import AgentValidatorError

logger = logging.getLogger(__name__)


class SlackBot:
    """Slack bot for agent validator integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Slack bot.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Get Slack credentials from environment
        bot_token = os.getenv("SLACK_BOT_TOKEN")
        app_token = os.getenv("SLACK_APP_TOKEN")

        if not bot_token or not app_token:
            raise ValueError(
                "SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be set in environment variables"
            )

        # Initialize Slack app
        self.app = App(token=bot_token)
        self.socket_handler = SocketModeHandler(self.app, app_token)

        # Initialize components
        self.orchestrator = Orchestrator(config)
        self.conversation_manager = ConversationManager()
        self.formatter = SlackFormatter()

        # Register event handlers
        self._register_handlers()

        logger.info("SlackBot initialized successfully")

    def _register_handlers(self):
        """Register Slack event handlers."""

        @self.app.message("")
        def handle_message(message, say, client):
            """Handle incoming messages."""
            try:
                self._handle_message(message, say, client)
            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)
                say(f"❌ Sorry, I encountered an error: {str(e)}")

        @self.app.event("app_mention")
        def handle_mention(event, say, client):
            """Handle app mentions."""
            try:
                self._handle_message(event, say, client)
            except Exception as e:
                logger.error(f"Error handling mention: {e}", exc_info=True)
                say(f"❌ Sorry, I encountered an error: {str(e)}")

    def _handle_message(self, message: Dict[str, Any], say, client):
        """
        Handle incoming Slack message.

        Args:
            message: Slack message event
            say: Slack say function
            client: Slack client
        """
        user_id = message.get("user")
        channel_id = message.get("channel")
        text = message.get("text", "").strip()

        # Remove bot mention from text
        text = self._clean_message_text(text)

        logger.info(f"Received message from {user_id}: {text}")

        # Check if user has an active conversation
        conversation = self.conversation_manager.get_conversation(user_id)

        if conversation:
            # Continue existing conversation
            self._continue_conversation(user_id, text, say)
        else:
            # Start new conversation
            self._start_new_conversation(user_id, text, say)

    def _clean_message_text(self, text: str) -> str:
        """
        Clean message text by removing bot mentions.

        Args:
            text: Raw message text

        Returns:
            Cleaned text
        """
        import re

        # Remove bot mention (e.g., <@U12345678>)
        text = re.sub(r"<@[A-Z0-9]+>", "", text)
        return text.strip()

    def _start_new_conversation(self, user_id: str, text: str, say):
        """
        Start a new conversation.

        Args:
            user_id: Slack user ID
            text: Message text
            say: Slack say function
        """
        # Parse user intent
        intent = self._parse_intent(text)

        if intent == "help":
            self._show_help(say)
        elif intent == "list_agents":
            self._list_agents(say)
        elif intent.startswith("run_"):
            agent_name = intent.replace("run_", "")
            self._initiate_agent_run(user_id, agent_name, text, say)
        else:
            # General conversation
            say(self._get_welcome_message())

    def _parse_intent(self, text: str) -> str:
        """
        Parse user intent from message.

        Args:
            text: Message text

        Returns:
            Intent string
        """
        text_lower = text.lower()

        if any(
            word in text_lower for word in ["help", "what can you do", "how to use"]
        ):
            return "help"

        if any(
            word in text_lower for word in ["list agents", "show agents", "what agents"]
        ):
            return "list_agents"

        # Check for agent run requests
        if "spell" in text_lower or "spelling" in text_lower or "grammar" in text_lower:
            return "run_spell_checker"

        if (
            "visual" in text_lower
            or "screenshot" in text_lower
            or "ui" in text_lower
            or "layout" in text_lower
        ):
            return "run_visual_qa"

        return "general"

    def _initiate_agent_run(self, user_id: str, agent_name: str, text: str, say):
        """
        Initiate an agent run by collecting required arguments.

        Args:
            user_id: Slack user ID
            agent_name: Name of agent to run
            text: Original message text
            say: Slack say function
        """
        # Check if agent exists
        if agent_name not in self.orchestrator.AGENT_REGISTRY:
            say(
                f"❌ Unknown agent: `{agent_name}`. Use `list agents` to see available agents."
            )
            return

        # Try to extract URL from the message
        import re

        url_pattern = r'https?://[^\s<>"]+'
        urls = re.findall(url_pattern, text)

        if urls:
            # URL found, run the agent directly
            url = urls[0]
            self._run_agent(user_id, agent_name, url, say)
        else:
            # No URL found, ask for it
            self.conversation_manager.start_conversation(
                user_id=user_id, agent_name=agent_name, step="url"
            )
            say(
                f"🔗 Please provide the URL you want to validate with the {agent_name} agent."
            )

    def _continue_conversation(self, user_id: str, text: str, say):
        """
        Continue an existing conversation.

        Args:
            user_id: Slack user ID
            text: Message text
            say: Slack say function
        """
        conversation = self.conversation_manager.get_conversation(user_id)

        if not conversation:
            return

        current_step = conversation.get("step")
        agent_name = conversation.get("agent_name")

        if current_step == "url":
            # Extract URL
            import re

            url_pattern = r'https?://[^\s<>"]+'
            urls = re.findall(url_pattern, text)

            if not urls:
                say(
                    "❌ I couldn't find a valid URL. Please provide a URL starting with http:// or https://"
                )
                return

            url = urls[0]

            # Update conversation with URL
            self.conversation_manager.update_conversation(user_id, {"url": url})

            # Check if we need more parameters
            # For now, we'll just run the agent with the URL
            self._run_agent(user_id, agent_name, url, say)
            self.conversation_manager.end_conversation(user_id)

    def _run_agent(self, user_id: str, agent_name: str, url: str, say):
        """
        Run an agent and return results.

        Args:
            user_id: Slack user ID
            agent_name: Name of agent to run
            url: URL to validate
            say: Slack say function
        """
        say(f"🚀 Starting {agent_name} validation for: {url}")

        try:
            # Get agent config from main config
            agent_config = self.config.get("agents", {}).get(agent_name, {})

            # Run the agent
            result = self.orchestrator.run_agent(
                agent_name=agent_name, url=url, agent_config=agent_config
            )

            # Format and send the result
            formatted_result = self.formatter.format_agent_result(result)
            say(formatted_result)

            logger.info(f"Successfully ran {agent_name} for user {user_id}")

        except AgentValidatorError as e:
            logger.error(f"Agent validation error: {e}")
            say(f"❌ Validation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error running agent: {e}", exc_info=True)
            say(f"❌ An unexpected error occurred: {str(e)}")

    def _show_help(self, say):
        """
        Show help message.

        Args:
            say: Slack say function
        """
        help_text = """
*🤖 Agent Validator Bot - Help*

I can help you validate websites using AI-powered agents!

*Available Commands:*
• `help` - Show this help message
• `list agents` - Show available validation agents
• `run spell checker on <URL>` - Check spelling and grammar
• `run visual qa on <URL>` - Check visual issues and layout

*How to Use:*
1. Mention an agent type and provide a URL
2. I'll ask for any missing information
3. I'll run the validation and send you the report

*Examples:*
• "Check spelling on https://example.com"
• "Run visual QA on https://mysite.com"
• "Validate https://example.com for grammar errors"
"""
        say(help_text)

    def _list_agents(self, say):
        """
        List available agents.

        Args:
            say: Slack say function
        """
        agents_text = """
*📋 Available Agents:*

• *spell_checker* - Detects spelling, grammar, and writing issues
  - Uses AI to analyze text content
  - Identifies errors with context and suggestions
  
• *visual_qa* - Detects visual and layout issues
  - Takes screenshots at different viewports
  - Analyzes UI/UX problems, broken elements, and design issues

*Usage:*
Just mention the agent type and provide a URL to get started!
"""
        say(agents_text)

    def _get_welcome_message(self) -> str:
        """
        Get welcome message.

        Returns:
            Welcome message text
        """
        return """
👋 Hello! I'm the Agent Validator Bot.

I can help you validate websites for:
• Spelling and grammar errors
• Visual and layout issues

Type `help` to see what I can do, or just tell me what you'd like to validate!
"""

    def start(self):
        """Start the Slack bot."""
        logger.info("Starting Slack bot...")
        self.socket_handler.start()

    def stop(self):
        """Stop the Slack bot."""
        logger.info("Stopping Slack bot...")
        self.socket_handler.close()
