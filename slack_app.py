"""Slack app entry point for agent validator integration."""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from core.config_loader import ConfigLoader
from core.logging_config import setup_logging
from integrations.slack_bot import SlackBot

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Slack bot for AI-powered web validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables Required:
  SLACK_BOT_TOKEN     - Your Slack bot token (xoxb-...)
  SLACK_APP_TOKEN     - Your Slack app token (xapp-...)
  GOOGLE_API_KEY      - Google Gemini API key (for agents)

Examples:
  # Run with default config
  %(prog)s
  
  # Run with custom config file
  %(prog)s --config config.yaml
  
  # Enable verbose logging
  %(prog)s -v
""",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file",
    )

    return parser.parse_args()


def main():
    """Main entry point for Slack bot."""
    # Load environment variables
    load_dotenv()

    args = parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level, log_file=args.log_file)

    logger.info("Starting Agent Validator Slack Bot")

    try:
        # Load configuration
        config_path = Path(args.config)
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            config = {}
        else:
            config_loader = ConfigLoader(config_path)
            config = config_loader.load()
            logger.info(f"Loaded configuration from {config_path}")

        # Initialize and start Slack bot
        bot = SlackBot(config=config)

        logger.info("Slack bot initialized successfully")
        logger.info("Connecting to Slack...")

        # Start the bot (this blocks)
        bot.start()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping bot...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
