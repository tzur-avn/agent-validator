"""Text reporter for console output."""

from typing import Dict, Any, List
from reporters.base_reporter import BaseReporter


class TextReporter(BaseReporter):
    """Reporter that formats output as plain text."""

    def format_report(self, results: List[Dict[str, Any]]) -> str:
        """Format results as plain text."""
        lines = []

        if self.timestamp:
            lines.append(f"Report generated: {self.get_timestamp()}")
            lines.append("=" * 80)
            lines.append("")

        for result in results:
            agent_name = result.get("agent", "Unknown Agent")
            url = result.get("url", "Unknown URL")
            report = result.get("report", "No report available")
            success = result.get("success", False)
            error = result.get("error")

            lines.append(f"Agent: {agent_name}")
            lines.append(f"URL: {url}")
            lines.append(f"Status: {'✓ PASSED' if success else '✗ FAILED'}")

            if error:
                lines.append(f"Error: {error}")
            else:
                lines.append("")
                lines.append(report)

            lines.append("")
            lines.append("=" * 80)
            lines.append("")

        return "\n".join(lines)
