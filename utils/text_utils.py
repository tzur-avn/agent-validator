"""Text processing utilities."""

import re
from typing import Optional
from bidi.algorithm import get_display


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean and normalize text for processing.

    Args:
        text: Text to clean
        max_length: Optional maximum length to truncate to

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = " ".join(text.split())

    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def format_bidi_text(text: str) -> str:
    """
    Format bidirectional text (Hebrew, Arabic, etc.) for display.

    Args:
        text: Text to format

    Returns:
        Formatted text suitable for console display
    """
    if not text:
        return ""

    try:
        return get_display(text)
    except Exception:
        # Fallback to original text if bidi processing fails
        return text


def extract_json_from_markdown(content: str) -> str:
    """
    Extract JSON from markdown code blocks.

    Args:
        content: Content that may contain JSON in markdown code blocks

    Returns:
        Extracted JSON string
    """
    content = content.strip()

    # Try to extract from ```json blocks
    if "```json" in content:
        parts = content.split("```json")
        if len(parts) > 1:
            json_part = parts[1].split("```")[0].strip()
            return json_part

    # Try to extract from generic ``` blocks
    if "```" in content:
        parts = content.split("```")
        if len(parts) >= 3:
            return parts[1].strip()

    return content


def truncate_with_ellipsis(text: str, max_length: int = 100) -> str:
    """
    Truncate text with ellipsis if it exceeds max_length.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with ellipsis if needed
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."
