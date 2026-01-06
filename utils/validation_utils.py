"""Input validation utilities."""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse
from core.exceptions import ValidationError


def validate_url(url: str) -> str:
    """
    Validate and normalize a URL.

    Args:
        url: URL string to validate

    Returns:
        Normalized URL

    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValidationError(f"Invalid URL: {url}")
        return url
    except Exception as e:
        raise ValidationError(f"Invalid URL: {url} - {str(e)}")


def validate_viewport(width: int, height: int) -> Tuple[int, int]:
    """
    Validate viewport dimensions.

    Args:
        width: Viewport width in pixels
        height: Viewport height in pixels

    Returns:
        Tuple of validated (width, height)

    Raises:
        ValidationError: If dimensions are invalid
    """
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValidationError("Viewport dimensions must be integers")

    if width < 320 or width > 7680:
        raise ValidationError(
            f"Viewport width must be between 320 and 7680, got {width}"
        )

    if height < 240 or height > 4320:
        raise ValidationError(
            f"Viewport height must be between 240 and 4320, got {height}"
        )

    return width, height


def validate_model_name(model: str) -> str:
    """
    Validate LLM model name.

    Args:
        model: Model name to validate

    Returns:
        Validated model name

    Raises:
        ValidationError: If model name is invalid
    """
    if not model or not isinstance(model, str):
        raise ValidationError("Model name must be a non-empty string")

    # Basic validation - model names should be alphanumeric with hyphens, dots, slashes
    if not re.match(r"^[a-zA-Z0-9\-\.\/]+$", model):
        raise ValidationError(f"Invalid model name format: {model}")

    return model


def validate_temperature(temp: float) -> float:
    """
    Validate LLM temperature parameter.

    Args:
        temp: Temperature value

    Returns:
        Validated temperature

    Raises:
        ValidationError: If temperature is invalid
    """
    if not isinstance(temp, (int, float)):
        raise ValidationError("Temperature must be a number")

    if temp < 0 or temp > 2:
        raise ValidationError(f"Temperature must be between 0 and 2, got {temp}")

    return float(temp)
