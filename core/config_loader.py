"""Configuration loader and validator."""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from core.exceptions import ConfigurationError
from utils.validation_utils import (
    validate_url,
    validate_viewport,
    validate_model_name,
    validate_temperature,
    validate_provider,
)

logger = logging.getLogger(__name__)


class Config:
    """Configuration container."""

    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize configuration.

        Args:
            config_dict: Configuration dictionary
        """
        self._config = config_dict
        self._validate()

    def _validate(self):
        """Validate configuration structure."""
        # Validate agents section
        if "agents" in self._config:
            for agent_name, agent_config in self._config["agents"].items():
                if not isinstance(agent_config, dict):
                    raise ConfigurationError(
                        f"Agent config for {agent_name} must be a dictionary"
                    )

                # Validate provider if present
                if "provider" in agent_config:
                    validate_provider(agent_config["provider"])

                # Validate model if present
                if "model" in agent_config:
                    validate_model_name(agent_config["model"])

                # Validate temperature if present
                if "temperature" in agent_config:
                    validate_temperature(agent_config["temperature"])

                # Validate viewports for visual_qa agent
                if agent_name == "visual_qa" and "viewports" in agent_config:
                    for viewport in agent_config["viewports"]:
                        validate_viewport(
                            viewport.get("width", 1920), viewport.get("height", 1080)
                        )

        # Validate targets section
        if "targets" in self._config:
            for target in self._config["targets"]:
                if "url" in target:
                    validate_url(target["url"])

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent configuration dictionary
        """
        return self._config.get("agents", {}).get(agent_name, {})

    def get_targets(self) -> List[Dict[str, Any]]:
        """Get list of target configurations."""
        return self._config.get("targets", [])

    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self._config.get("output", {})

    def is_agent_enabled(self, agent_name: str) -> bool:
        """Check if an agent is enabled."""
        agent_config = self.get_agent_config(agent_name)
        return agent_config.get("enabled", True)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Get a configuration value using bracket notation."""
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in configuration."""
        return key in self._config


class ConfigLoader:
    """Load and manage configuration from files and environment."""

    DEFAULT_CONFIG_PATHS = [
        "config.yaml",
        "config.yml",
        ".agent-validator.yaml",
        ".agent-validator.yml",
    ]

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> Config:
        """
        Load configuration from file.

        Args:
            config_path: Optional path to config file. If not provided,
                        searches for default config files.

        Returns:
            Config object

        Raises:
            ConfigurationError: If config file not found or invalid
        """
        # Find config file
        if config_path:
            path = Path(config_path)
            if not path.exists():
                raise ConfigurationError(f"Config file not found: {config_path}")
        else:
            path = cls._find_config_file()
            if path is None:
                logger.warning("No config file found, using defaults")
                return Config(cls._get_default_config())

        # Load YAML
        try:
            with open(path, "r") as f:
                config_dict = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {path}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config file: {e}")

        # Apply environment variable overrides
        config_dict = cls._apply_env_overrides(config_dict)

        return Config(config_dict)

    @classmethod
    def _find_config_file(cls) -> Optional[Path]:
        """Find configuration file in default locations."""
        for config_name in cls.DEFAULT_CONFIG_PATHS:
            path = Path(config_name)
            if path.exists():
                return path
        return None

    @staticmethod
    def _apply_env_overrides(config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        # Override GOOGLE_API_KEY if set
        if "GOOGLE_API_KEY" in os.environ:
            # This is already handled by langchain, but we could add it to config if needed
            pass

        # Override OPENAI_API_KEY if set
        if "OPENAI_API_KEY" in os.environ:
            # This is already handled by langchain-openai
            pass

        # Add support for other env var overrides as needed
        # Example: AGENT_VALIDATOR_MODEL, AGENT_VALIDATOR_TEMPERATURE, etc.

        return config_dict

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Get default configuration when no config file exists."""
        return {
            "agents": {
                "spell_checker": {
                    "enabled": True,
                    "provider": "gemini",
                    "model": "gemini-2.5-flash",
                    "temperature": 0,
                    "max_text_length": 10000,
                },
                "visual_qa": {
                    "enabled": True,
                    "provider": "gemini",
                    "model": "gemini-2.5-flash",
                    "temperature": 0,
                    "viewports": [{"width": 1920, "height": 1080, "name": "Desktop"}],
                },
            },
            "output": {
                "format": "text",
                "path": "./reports",
                "timestamp": True,
            },
        }
