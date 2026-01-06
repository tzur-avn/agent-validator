"""JSON reporter for machine-readable output."""

import json
from typing import Dict, Any, List
from reporters.base_reporter import BaseReporter


class JSONReporter(BaseReporter):
    """Reporter that formats output as JSON."""

    def format_report(self, results: List[Dict[str, Any]]) -> str:
        """Format results as JSON."""
        report_data = {"results": results, "summary": self._generate_summary(results)}

        if self.timestamp:
            report_data["timestamp"] = self.get_timestamp()

        return json.dumps(report_data, indent=2, ensure_ascii=False)

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics."""
        total = len(results)
        passed = sum(1 for r in results if r.get("success", False))
        failed = total - passed

        # Count issues by agent
        issues_by_agent = {}
        for result in results:
            agent = result.get("agent", "unknown")

            # Extract issue counts based on agent type
            if agent == "SpellChecker":
                errors = result.get("errors", [])
                issues_by_agent[agent] = len(errors)
            elif agent == "VisualQA":
                issues = result.get("issues", [])
                issues_by_agent[agent] = len(issues)

        return {
            "total_validations": total,
            "passed": passed,
            "failed": failed,
            "issues_by_agent": issues_by_agent,
        }
