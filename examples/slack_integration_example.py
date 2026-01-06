"""Example script demonstrating Slack integration usage."""

import os
from pathlib import Path
from dotenv import load_dotenv

from core.config_loader import ConfigLoader
from integrations.slack_bot import SlackBot
from integrations.conversation_manager import ConversationManager
from integrations.slack_formatter import SlackFormatter

# Load environment variables
load_dotenv()


def example_conversation_manager():
    """Example of using the conversation manager."""
    print("=== Conversation Manager Example ===\n")

    manager = ConversationManager(timeout_minutes=30)

    # Start a conversation
    user_id = "U12345"
    conversation = manager.start_conversation(
        user_id=user_id, agent_name="spell_checker", step="url"
    )
    print(f"Started conversation: {conversation}")

    # Update conversation with data
    manager.update_conversation(user_id, {"url": "https://example.com"})
    print(f"Updated conversation with URL")

    # Get conversation
    current = manager.get_conversation(user_id)
    print(f"Current conversation: {current}")

    # End conversation
    manager.end_conversation(user_id)
    print(f"Ended conversation\n")


def example_formatter():
    """Example of using the Slack formatter."""
    print("=== Slack Formatter Example ===\n")

    formatter = SlackFormatter()

    # Example spell checker result
    spell_result = {
        "agent": "SpellChecker",
        "url": "https://example.com",
        "errors": [
            {
                "original": "teh",
                "correction": "the",
                "context": "This is teh main page of our website.",
            },
            {
                "original": "recieve",
                "correction": "receive",
                "context": "You will recieve updates via email.",
            },
        ],
        "report": "Found 2 spelling errors",
    }

    formatted = formatter.format_agent_result(spell_result)
    print("Formatted spell checker result:")
    print(formatted)
    print()

    # Example visual QA result
    visual_result = {
        "agent": "VisualQA",
        "url": "https://example.com",
        "issues": [
            {
                "severity": "high",
                "description": "Button text is cut off on mobile viewport",
                "element": ".submit-button",
            },
            {
                "severity": "medium",
                "description": "Image aspect ratio distorted",
                "element": ".hero-image",
            },
        ],
        "report": "Found 2 visual issues",
    }

    formatted = formatter.format_agent_result(visual_result)
    print("Formatted visual QA result:")
    print(formatted)
    print()


def example_slack_bot_config():
    """Example of Slack bot configuration."""
    print("=== Slack Bot Configuration Example ===\n")

    # Check if tokens are set
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    app_token = os.getenv("SLACK_APP_TOKEN")

    if not bot_token or not app_token:
        print("⚠️  Slack tokens not found in environment!")
        print("To use the Slack bot:")
        print("1. Create a Slack app at https://api.slack.com/apps")
        print("2. Set SLACK_BOT_TOKEN and SLACK_APP_TOKEN in .env")
        print("3. See docs/SLACK_INTEGRATION.md for detailed setup\n")
        return

    print("✅ Slack tokens found!")
    print(f"Bot Token: {bot_token[:20]}...")
    print(f"App Token: {app_token[:20]}...")

    # Load config
    config_path = Path("config.yaml")
    if config_path.exists():
        config_loader = ConfigLoader(config_path)
        config = config_loader.load()
        print(f"\n✅ Configuration loaded from {config_path}")

        # Show Slack config
        slack_config = config.get("slack", {})
        print(f"Slack enabled: {slack_config.get('enabled', False)}")
        print(
            f"Conversation timeout: {slack_config.get('conversation_timeout_minutes', 30)} minutes"
        )
    else:
        print(f"\n⚠️  Config file not found: {config_path}")

    print("\nTo start the Slack bot, run:")
    print("  pipenv run slack-bot")
    print("\nOr with verbose logging:")
    print("  pipenv run slack-bot -v\n")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Slack Integration Examples")
    print("=" * 60 + "\n")

    example_conversation_manager()
    example_formatter()
    example_slack_bot_config()

    print("=" * 60)
    print("For more information, see docs/SLACK_INTEGRATION.md")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
