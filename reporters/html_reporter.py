"""HTML reporter for interactive dashboards."""

from typing import Dict, Any, List
from reporters.base_reporter import BaseReporter


class HTMLReporter(BaseReporter):
    """Reporter that formats output as HTML."""

    def format_report(self, results: List[Dict[str, Any]]) -> str:
        """Format results as HTML."""
        html_parts = [self._get_html_header()]

        # Summary section
        html_parts.append(self._generate_summary_html(results))

        # Detailed results
        html_parts.append('<div class="results">')
        for result in results:
            html_parts.append(self._format_result_html(result))
        html_parts.append("</div>")

        html_parts.append(self._get_html_footer())

        return "\n".join(html_parts)

    def _get_html_header(self) -> str:
        """Get HTML header with styles."""
        timestamp = (
            f"<p>Generated: {self.get_timestamp()}</p>" if self.timestamp else ""
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Validator Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .result-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .result-header {{
            border-bottom: 2px solid #eee;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }}
        .status-pass {{
            color: #22c55e;
            font-weight: bold;
        }}
        .status-fail {{
            color: #ef4444;
            font-weight: bold;
        }}
        .severity-critical {{
            color: #dc2626;
            font-weight: bold;
        }}
        .severity-high {{
            color: #ea580c;
        }}
        .severity-medium {{
            color: #f59e0b;
        }}
        .severity-low {{
            color: #84cc16;
        }}
        .issue {{
            padding: 15px;
            background: #f9fafb;
            border-left: 4px solid #6366f1;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .error {{
            padding: 15px;
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            margin: 10px 0;
            border-radius: 4px;
        }}
        pre {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Agent Validator Report</h1>
        {timestamp}
    </div>
"""

    def _generate_summary_html(self, results: List[Dict[str, Any]]) -> str:
        """Generate summary statistics HTML."""
        total = len(results)
        passed = sum(1 for r in results if r.get("success", False))
        failed = total - passed

        total_issues = 0
        for result in results:
            if result.get("errors"):
                total_issues += len(result["errors"])
            if result.get("issues"):
                total_issues += len(result["issues"])

        return f"""
    <div class="summary">
        <div class="summary-card">
            <h3>Total Validations</h3>
            <div class="value">{total}</div>
        </div>
        <div class="summary-card">
            <h3>Passed</h3>
            <div class="value" style="color: #22c55e;">{passed}</div>
        </div>
        <div class="summary-card">
            <h3>Failed</h3>
            <div class="value" style="color: #ef4444;">{failed}</div>
        </div>
        <div class="summary-card">
            <h3>Total Issues</h3>
            <div class="value" style="color: #f59e0b;">{total_issues}</div>
        </div>
    </div>
"""

    def _format_result_html(self, result: Dict[str, Any]) -> str:
        """Format a single result as HTML."""
        agent_name = result.get("agent", "Unknown")
        url = result.get("url", "Unknown")
        success = result.get("success", False)
        status_class = "status-pass" if success else "status-fail"
        status_text = "✓ PASSED" if success else "✗ FAILED"

        html = f"""
    <div class="result-card">
        <div class="result-header">
            <h2>{agent_name}</h2>
            <p><strong>URL:</strong> <a href="{url}" target="_blank">{url}</a></p>
            <p class="{status_class}">{status_text}</p>
        </div>
"""

        if result.get("error"):
            html += (
                f'<div class="error"><strong>Error:</strong> {result["error"]}</div>'
            )

        # Format agent-specific data
        if result.get("errors"):
            html += self._format_spelling_errors_html(result["errors"])

        if result.get("issues"):
            html += self._format_visual_issues_html(result["issues"])

        html += "    </div>\n"
        return html

    def _format_spelling_errors_html(self, errors: List[Dict[str, Any]]) -> str:
        """Format spelling errors as HTML."""
        html = f"<h3>Spelling Errors ({len(errors)})</h3>\n"

        for error in errors:
            original = error.get("original", "")
            correction = error.get("correction", "")
            context = error.get("context", "")

            html += f"""
        <div class="error">
            <strong>Error:</strong> "{original}" → <strong>Correction:</strong> "{correction}"<br>
            <em>Context:</em> "{context}"
        </div>
"""

        return html

    def _format_visual_issues_html(self, issues: List[Dict[str, Any]]) -> str:
        """Format visual issues as HTML."""
        # Group by severity
        by_severity = {"critical": [], "high": [], "medium": [], "low": []}
        for issue in issues:
            severity = issue.get("severity", "low")
            if severity in by_severity:
                by_severity[severity].append(issue)

        html = f"<h3>Visual Issues ({len(issues)})</h3>\n"

        for severity in ["critical", "high", "medium", "low"]:
            issues_list = by_severity[severity]
            if not issues_list:
                continue

            html += f'<h4 class="severity-{severity}">{severity.upper()} ({len(issues_list)})</h4>\n'

            for issue in issues_list:
                issue_type = issue.get("type", "unknown").upper()
                issue_desc = issue.get("issue", "")
                location = issue.get("location", "")
                recommendation = issue.get("recommendation", "")

                html += f"""
        <div class="issue">
            <strong>[{issue_type}]</strong> {issue_desc}<br>
            <strong>Location:</strong> {location}<br>
            <strong>Fix:</strong> {recommendation}
        </div>
"""

        return html

    def _get_html_footer(self) -> str:
        """Get HTML footer."""
        return """
</body>
</html>
"""
