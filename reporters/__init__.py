"""Reporter modules for formatting validation results."""

from .base_reporter import BaseReporter
from .text_reporter import TextReporter
from .json_reporter import JSONReporter
from .html_reporter import HTMLReporter

__all__ = [
    "BaseReporter",
    "TextReporter",
    "JSONReporter",
    "HTMLReporter",
]


def get_reporter(format_type: str, **kwargs) -> BaseReporter:
    """
    Get a reporter instance by format type.

    Args:
        format_type: Type of reporter ('text', 'json', 'html')
        **kwargs: Additional reporter options

    Returns:
        Reporter instance

    Raises:
        ValueError: If format type is unknown
    """
    reporters = {
        "text": TextReporter,
        "json": JSONReporter,
        "html": HTMLReporter,
    }

    reporter_class = reporters.get(format_type.lower())
    if not reporter_class:
        raise ValueError(
            f"Unknown reporter format: {format_type}. "
            f"Available formats: {', '.join(reporters.keys())}"
        )

    return reporter_class(**kwargs)
