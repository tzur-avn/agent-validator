"""Unit tests for configuration loader."""

import pytest
import yaml
from pathlib import Path
from core.config_loader import Config, ConfigLoader
from core.exceptions import ConfigurationError


def test_config_initialization():
    """Test config initialization."""
    config_dict = {
        "agents": {"spell_checker": {"enabled": True, "model": "gemini-2.5-flash"}}
    }

    config = Config(config_dict)
    assert config.get_agent_config("spell_checker")["enabled"] is True


def test_config_get_agent_config():
    """Test getting agent configuration."""
    config_dict = {
        "agents": {"spell_checker": {"model": "test"}, "visual_qa": {"model": "test2"}}
    }

    config = Config(config_dict)
    assert config.get_agent_config("spell_checker")["model"] == "test"
    assert config.get_agent_config("nonexistent") == {}


def test_config_is_agent_enabled():
    """Test agent enabled check."""
    config_dict = {
        "agents": {"spell_checker": {"enabled": True}, "visual_qa": {"enabled": False}}
    }

    config = Config(config_dict)
    assert config.is_agent_enabled("spell_checker") is True
    assert config.is_agent_enabled("visual_qa") is False
    assert config.is_agent_enabled("nonexistent") is True  # Default


def test_config_validation_invalid_model():
    """Test config validation with invalid model."""
    config_dict = {"agents": {"spell_checker": {"model": ""}}}

    with pytest.raises(ConfigurationError):
        Config(config_dict)


def test_config_loader_default():
    """Test config loader with defaults."""
    config = ConfigLoader._get_default_config()

    assert "agents" in config
    assert "spell_checker" in config["agents"]
    assert "visual_qa" in config["agents"]
