"""Tests for authentication configuration and env var resolution."""

import os
import pytest
from unittest.mock import patch
from core.config_loader import ConfigLoader
from utils.browser_utils import BrowserSession


def test_form_auth_browser_session_creation():
    """BrowserSession accepts form auth config without raising."""
    auth_config = {
        "type": "form",
        "username": "test_user",
        "password": "test_pass",
        "selectors": {
            "username": 'input[name="username"]',
            "password": 'input[name="password"]',
            "submit": 'button[type="submit"]',
        },
    }
    bs = BrowserSession(auth=auth_config)
    assert bs.auth == auth_config
    assert bs.auth["type"] == "form"


def test_basic_auth_browser_session_creation():
    """BrowserSession accepts basic auth config without raising."""
    auth_config = {"type": "basic", "username": "admin", "password": "secret"}
    bs = BrowserSession(auth=auth_config)
    assert bs.auth == auth_config
    assert bs.auth["type"] == "basic"


def test_no_auth_browser_session_creation():
    """BrowserSession can be created without auth."""
    bs = BrowserSession()
    assert bs.auth is None


def test_env_var_resolution_in_auth_config():
    """ConfigLoader resolves ${VAR} placeholders in auth credentials."""
    with patch.dict(os.environ, {"AUTH_USER": "myuser", "AUTH_PASS": "mypass"}):
        raw = {
            "targets": [
                {
                    "url": "https://example.com",
                    "auth": {
                        "type": "form",
                        "username": "${AUTH_USER}",
                        "password": "${AUTH_PASS}",
                    },
                }
            ]
        }
        resolved = ConfigLoader._resolve_env_vars(raw)
        auth = resolved["targets"][0]["auth"]
        assert auth["username"] == "myuser"
        assert auth["password"] == "mypass"


def test_env_var_resolution_missing_var(caplog):
    """ConfigLoader logs a warning for unset environment variables."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("MISSING_VAR", None)
        result = ConfigLoader._resolve_env_vars({"key": "${MISSING_VAR}"})
        assert result["key"] == ""


def test_env_var_resolution_leaves_non_placeholders_unchanged():
    """ConfigLoader does not modify strings without ${} patterns."""
    result = ConfigLoader._resolve_env_vars({"key": "plain_value"})
    assert result["key"] == "plain_value"


def test_env_var_resolution_nested():
    """ConfigLoader resolves placeholders at any nesting depth."""
    with patch.dict(os.environ, {"SECRET": "s3cr3t"}):
        raw = {"a": {"b": [{"c": "${SECRET}"}]}}
        resolved = ConfigLoader._resolve_env_vars(raw)
        assert resolved["a"]["b"][0]["c"] == "s3cr3t"
