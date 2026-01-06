"""Main CLI entry point for agent validator."""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from core.config_loader import ConfigLoader
from core.orchestrator import Orchestrator
from core.logging_config import setup_logging
from core.exceptions import AgentValidatorError
from reporters import get_reporter

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI-powered web validation tool for spell checking and visual QA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all agents on a URL
  %(prog)s --url https://example.com
  
  # Run specific agent
  %(prog)s --url https://example.com --agents spell_checker
  
  # Use custom config file
  %(prog)s --config examples/multi_site_check.yaml
  
  # Output as HTML
  %(prog)s --url https://example.com --format html --output reports/
  
  # Verbose mode
  %(prog)s --url https://example.com -v
""",
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--url", type=str, help="URL to validate")
    input_group.add_argument("--config", type=str, help="Path to configuration file")

    # Agent selection
    parser.add_argument(
        "--agents",
        type=str,
        nargs="+",
        choices=["spell_checker", "visual_qa"],
        help="Specific agents to run (default: all enabled)",
    )

    # Output options
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json", "html"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--output", type=str, help="Output directory for reports")

    # Execution options
    parser.add_argument(
        "--parallel", action="store_true", help="Run agents in parallel"
    )

    # Logging options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose (DEBUG) logging"
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress console output except errors",
    )
    parser.add_argument("--log-file", type=str, help="Path to log file")

    return parser.parse_args()


def generate_output_filename(format_type: str, url: Optional[str] = None) -> str:
    """
    Generate output filename based on format and URL.

    Args:
        format_type: Output format type
        url: Optional URL being validated

    Returns:
        Generated filename
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if url:
        # Extract domain from URL
        from urllib.parse import urlparse

        domain = urlparse(url).netloc.replace("www.", "").replace(".", "_")
        filename = f"report_{domain}_{timestamp}"
    else:
        filename = f"report_{timestamp}"

    extensions = {
        "text": ".txt",
        "json": ".json",
        "html": ".html",
    }

    return filename + extensions.get(format_type, ".txt")


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    args = parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose, quiet=args.quiet, log_file=args.log_file)

    try:
        # Load configuration
        if args.config:
            logger.info(f"Loading configuration from {args.config}")
            config = ConfigLoader.load(args.config)
        else:
            logger.info("Using default configuration")
            config = ConfigLoader.load()

        # Create orchestrator
        orchestrator = Orchestrator(config._config)

        # Determine what to run
        if args.url:
            # Single URL mode
            agent_names = args.agents
            if not agent_names:
                # Use all enabled agents
                agent_names = [
                    name
                    for name, agent_config in config._config.get("agents", {}).items()
                    if agent_config.get("enabled", True)
                ]

            logger.info(f"Running {len(agent_names)} agents on {args.url}")
            results = orchestrator.run_multiple_agents(
                args.url, agent_names, parallel=args.parallel
            )
        else:
            # Config file mode with targets
            targets = config.get_targets()
            if not targets:
                logger.error("No targets defined in configuration file")
                sys.exit(1)

            logger.info(f"Running validation on {len(targets)} targets")
            results = orchestrator.run_targets(targets, parallel=args.parallel)

        # Generate report
        output_format = args.format or config.get_output_config().get("format", "text")
        reporter = get_reporter(output_format, timestamp=True)
        report_content = reporter.format_report(results)

        # Output report
        if args.output:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = generate_output_filename(output_format, args.url)
            output_path = output_dir / filename

            reporter.save_report(report_content, str(output_path))
            logger.info(f"Report saved to {output_path}")

            if not args.quiet:
                print(f"\n✓ Report saved to: {output_path}")
        else:
            # Print to console
            if not args.quiet or output_format != "text":
                print("\n" + report_content)

        # Print summary
        if not args.quiet:
            summary = orchestrator.get_summary(results)
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Total Validations: {summary['total_validations']}")
            print(f"Passed: {summary['passed']}")
            print(f"Failed: {summary['failed']}")
            print(f"Total Problems: {summary['total_problems']}")
            print(f"  - Spelling Errors: {summary['total_spelling_errors']}")
            print(f"  - Visual Issues: {summary['total_visual_issues']}")

        # Exit with appropriate code
        if summary["failed"] > 0 or summary["total_problems"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except AgentValidatorError as e:
        logger.error(f"Validation error: {e}")
        if not args.quiet:
            print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        if not args.quiet:
            print("\n\nInterrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        if not args.quiet:
            print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
