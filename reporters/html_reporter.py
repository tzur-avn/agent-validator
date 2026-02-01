"""HTML reporter for interactive dashboards."""

import hashlib
from typing import Dict, Any, List
from reporters.base_reporter import BaseReporter


class HTMLReporter(BaseReporter):
    """Reporter that formats output as HTML."""

    def format_report(self, results: List[Dict[str, Any]]) -> str:
        """Format results as HTML."""
        html_parts = [self._get_html_header()]

        # Summary section
        html_parts.append(self._generate_summary_html(results))

        # Group results by URL
        results_by_url = self._group_results_by_url(results)

        # Detailed results organized by URL
        html_parts.append('<div class="results">')
        for url, url_results in results_by_url.items():
            html_parts.append(self._format_url_section_html(url, url_results))
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
        .url-section {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .url-header {{
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .url-header h2 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 24px;
        }}
        .url-header .url-link {{
            color: #667eea;
            text-decoration: none;
            font-size: 16px;
            word-break: break-all;
        }}
        .url-header .url-link:hover {{
            text-decoration: underline;
        }}
        .agent-results {{
            margin-top: 15px;
        }}
        .result-card {{
            background: #f9fafb;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 15px;
            border-left: 4px solid #6366f1;
        }}
        .result-header {{
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        .result-header h3 {{
            margin: 0;
            color: #4b5563;
            font-size: 18px;
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
        .page-screenshot {{
            margin: 20px 0;
            padding: 15px;
            background: #f0f0f0;
            border-radius: 8px;
        }}
        .page-screenshot h4 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .page-screenshot img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .screenshot-toggle {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .screenshot-toggle:hover {{
            background: #5a6fd6;
        }}
        .screenshot-content {{
            display: none;
        }}
        .screenshot-content.expanded {{
            display: block;
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

    def _group_results_by_url(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group results by URL."""
        grouped = {}
        for result in results:
            url = result.get("url", "Unknown")
            if url not in grouped:
                grouped[url] = []
            grouped[url].append(result)
        return grouped

    def _format_url_section_html(self, url: str, url_results: List[Dict[str, Any]]) -> str:
        """Format a URL section with all its agent results."""
        # Calculate overall status for this URL
        all_passed = all(r.get("success", False) for r in url_results)
        total_issues = 0
        for result in url_results:
            if result.get("errors"):
                total_issues += len(result["errors"])
            if result.get("issues"):
                total_issues += len(result["issues"])

        status_class = "status-pass" if all_passed else "status-fail"
        status_text = "✓ ALL CHECKS PASSED" if all_passed else f"✗ {total_issues} ISSUE(S) FOUND"

        # Generate unique ID for screenshot toggle
        screenshot_id = hashlib.md5(url.encode()).hexdigest()[:8]

        html = f"""
    <div class="url-section">
        <div class="url-header">
            <h2>📄 Page Analysis</h2>
            <p><strong>URL:</strong> <a href="{url}" target="_blank" class="url-link">{url}</a></p>
            <p class="{status_class}">{status_text}</p>
        </div>
"""

        # Add full page screenshot if available (from first result that has one)
        for result in url_results:
            screenshot = result.get("screenshot", "")
            if screenshot:
                html += f"""
        <div class="page-screenshot">
            <button class="screenshot-toggle" onclick="toggleScreenshot('screenshot-{screenshot_id}')">📷 Show Page Screenshot</button>
            <div id="screenshot-{screenshot_id}" class="screenshot-content">
                <img src="data:image/png;base64,{screenshot}" alt="Full page screenshot of {url}">
            </div>
        </div>
"""
                break  # Only show one page screenshot per URL

        # Add agent results
        html += '        <div class="agent-results">\n'
        for result in url_results:
            html += self._format_result_html(result, include_url=False)
        html += "        </div>\n"
        html += "    </div>\n"

        return html

    def _format_result_html(self, result: Dict[str, Any], include_url: bool = True) -> str:
        """Format a single result as HTML."""
        agent_name = result.get("agent", "Unknown")
        url = result.get("url", "Unknown")
        success = result.get("success", False)
        status_class = "status-pass" if success else "status-fail"
        status_text = "✓ PASSED" if success else "✗ FAILED"

        html = f"""
        <div class="result-card">
            <div class="result-header">
                <h3>{agent_name}</h3>
                <p class="{status_class}">{status_text}</p>
            </div>
"""

        if result.get("error"):
            html += (
                f'    <div class="error"><strong>Error:</strong> {result["error"]}</div>\n'
            )

        # Format agent-specific data
        if result.get("errors"):
            html += self._format_spelling_errors_html(result["errors"])

        if result.get("issues"):
            element_screenshots = result.get("element_screenshots", {})
            html += self._format_visual_issues_html(
                result["issues"], element_screenshots
            )

        html += "        </div>\n"
        return html

    def _format_spelling_errors_html(self, errors: List[Dict[str, Any]]) -> str:
        """Format spelling errors as HTML."""
        html = f"    <h4>Spelling Errors ({len(errors)})</h4>\n"

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

    def _format_visual_issues_html(
        self, issues: List[Dict[str, Any]], element_screenshots: Dict[int, str] | None = None
    ) -> str:
        """Format visual issues as HTML."""
        if element_screenshots is None:
            element_screenshots = {}

        # Group by severity
        by_severity = {"critical": [], "high": [], "medium": [], "low": []}
        for idx, issue in enumerate(issues):
            severity = issue.get("severity", "low")
            if severity in by_severity:
                by_severity[severity].append((idx, issue))

        html = f"    <h4>Visual Issues ({len(issues)})</h4>\n"

        for severity in ["critical", "high", "medium", "low"]:
            issues_list = by_severity[severity]
            if not issues_list:
                continue

            html += f'    <h5 class="severity-{severity}">{severity.upper()} ({len(issues_list)})</h5>\n'

            for idx, issue in issues_list:
                issue_type = issue.get("type", "unknown").upper()
                issue_desc = issue.get("issue", "")
                location = issue.get("location", "")
                recommendation = issue.get("recommendation", "")

                html += f"""
            <div class="issue">
                <strong>[{issue_type}]</strong> {issue_desc}<br>
                <strong>Location:</strong> {location}<br>
                <strong>Fix:</strong> {recommendation}"""

                # Add element screenshot if available
                if idx in element_screenshots:
                    screenshot_b64 = element_screenshots[idx]
                    html += f"""
                <div style="margin-top: 10px; padding: 10px; background: white; border: 1px solid #ddd; border-radius: 4px;">
                    <strong>Screenshot:</strong><br>
                    <img src="data:image/png;base64,{screenshot_b64}" 
                         style="max-width: 100%; height: auto; border: 1px solid #ccc; margin-top: 5px; border-radius: 4px;" 
                         alt="Issue screenshot">
                </div>"""

                html += """
            </div>
"""

        return html

    def _get_html_footer(self) -> str:
        """Get HTML footer."""
        return """
    <script>
        function toggleScreenshot(id) {
            const content = document.getElementById(id);
            const button = content.previousElementSibling;
            if (content.classList.contains('expanded')) {
                content.classList.remove('expanded');
                button.textContent = '📷 Show Page Screenshot';
            } else {
                content.classList.add('expanded');
                button.textContent = '📷 Hide Page Screenshot';
            }
        }
    </script>
</body>
</html>
"""
