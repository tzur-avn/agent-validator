"""Unit tests for utilities."""

import pytest
from utils.validation_utils import (
    validate_url,
    validate_viewport,
    validate_model_name,
    validate_temperature,
)
from utils.text_utils import (
    clean_text,
    extract_json_from_markdown,
    truncate_with_ellipsis,
)
from core.exceptions import ValidationError


class TestValidation:
    """Test validation utilities."""

    def test_validate_url_valid(self):
        """Test valid URL validation."""
        assert validate_url("https://example.com") == "https://example.com"
        assert validate_url("http://example.com") == "http://example.com"
        assert validate_url("example.com") == "https://example.com"

    def test_validate_url_invalid(self):
        """Test invalid URL validation."""
        with pytest.raises(ValidationError):
            validate_url("")

        with pytest.raises(ValidationError):
            validate_url(None)

    def test_validate_viewport_valid(self):
        """Test valid viewport validation."""
        assert validate_viewport(1920, 1080) == (1920, 1080)
        assert validate_viewport(375, 667) == (375, 667)

    def test_validate_viewport_invalid(self):
        """Test invalid viewport validation."""
        with pytest.raises(ValidationError):
            validate_viewport(100, 1080)  # Too small

        with pytest.raises(ValidationError):
            validate_viewport(1920, 10000)  # Too large

    def test_validate_model_name(self):
        """Test model name validation."""
        assert validate_model_name("gemini-2.5-flash") == "gemini-2.5-flash"
        assert validate_model_name("gpt-4") == "gpt-4"

        with pytest.raises(ValidationError):
            validate_model_name("")

    def test_validate_temperature(self):
        """Test temperature validation."""
        assert validate_temperature(0) == 0.0
        assert validate_temperature(1.0) == 1.0
        assert validate_temperature(2) == 2.0

        with pytest.raises(ValidationError):
            validate_temperature(-1)

        with pytest.raises(ValidationError):
            validate_temperature(3)


class TestTextUtils:
    """Test text utilities."""

    def test_clean_text(self):
        """Test text cleaning."""
        text = "  Hello   World  \n\n  Test  "
        assert clean_text(text) == "Hello World Test"

    def test_clean_text_with_max_length(self):
        """Test text cleaning with max length."""
        text = "Hello World"
        assert clean_text(text, max_length=5) == "Hello"

    def test_extract_json_from_markdown(self):
        """Test JSON extraction from markdown."""
        # JSON code block
        content = '```json\n{"key": "value"}\n```'
        assert extract_json_from_markdown(content) == '{"key": "value"}'

        # Generic code block
        content = '```\n{"key": "value"}\n```'
        assert extract_json_from_markdown(content) == '{"key": "value"}'

        # Plain JSON
        content = '{"key": "value"}'
        assert extract_json_from_markdown(content) == '{"key": "value"}'

    def test_truncate_with_ellipsis(self):
        """Test text truncation."""
        text = "Hello World"
        assert truncate_with_ellipsis(text, 5) == "He..."
        assert truncate_with_ellipsis(text, 20) == "Hello World"
