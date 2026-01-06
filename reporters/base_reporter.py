"""Base reporter interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime


class BaseReporter(ABC):
    """Abstract base class for all reporters."""

    def __init__(self, timestamp: bool = True, **kwargs):
        """
        Initialize reporter.

        Args:
            timestamp: Include timestamp in report
            **kwargs: Additional reporter-specific options
        """
        self.timestamp = timestamp
        self.config = kwargs

    @abstractmethod
    def format_report(self, results: List[Dict[str, Any]]) -> str:
        """
        Format validation results into a report.

        Args:
            results: List of validation results from agents

        Returns:
            Formatted report string
        """
        pass

    def get_timestamp(self) -> str:
        """Get formatted timestamp."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_report(self, content: str, filepath: str) -> None:
        """
        Save report to file.

        Args:
            content: Report content
            filepath: Path to save report
        """
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
