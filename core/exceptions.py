"""Custom exceptions for the agent validator framework."""


class AgentValidatorError(Exception):
    """Base exception for all agent validator errors."""

    pass


class ConfigurationError(AgentValidatorError):
    """Raised when configuration is invalid or missing."""

    pass


class BrowserError(AgentValidatorError):
    """Raised when browser operations fail."""

    pass


class LLMError(AgentValidatorError):
    """Raised when LLM operations fail."""

    pass


class ValidationError(AgentValidatorError):
    """Raised when input validation fails."""

    pass


class ReportGenerationError(AgentValidatorError):
    """Raised when report generation fails."""

    pass
