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
            f"<p class='timestamp'>Generated: {self.get_timestamp()}</p>"
            if self.timestamp
            else ""
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Validator Report</title>
    <style>
        :root {{
            --primary: #667eea;
            --primary-dark: #5a67d8;
            --secondary: #764ba2;
            --success: #10b981;
            --success-light: #d1fae5;
            --error: #ef4444;
            --error-light: #fee2e2;
            --warning: #f59e0b;
            --warning-light: #fef3c7;
            --info: #3b82f6;
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-tertiary: #f3f4f6;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --text-tertiary: #9ca3af;
            --border: #e5e7eb;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}

        body.dark-mode {{
            --bg-primary: #1f2937;
            --bg-secondary: #111827;
            --bg-tertiary: #374151;
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --text-tertiary: #9ca3af;
            --border: #374151;
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            transition: background 0.3s ease, color 0.3s ease;
        }}

        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: var(--shadow-lg);
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 15s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.5; }}
            50% {{ transform: scale(1.1); opacity: 0.8; }}
        }}

        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5rem;
            font-weight: 700;
            position: relative;
            z-index: 1;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .timestamp {{
            margin: 0;
            opacity: 0.9;
            font-size: 0.95rem;
            position: relative;
            z-index: 1;
        }}

        .dark-mode-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--bg-primary);
            color: var(--text-primary);
            border: 2px solid var(--border);
            padding: 10px 16px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 1.2rem;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
            z-index: 1000;
        }}

        .dark-mode-toggle:hover {{
            transform: scale(1.1);
            box-shadow: var(--shadow-lg);
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: var(--bg-primary);
            padding: 25px;
            border-radius: 12px;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }}

        .summary-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
        }}

        .summary-card:hover {{
            transform: translateY(-5px);
            box-shadow: var(--shadow-xl);
        }}

        .summary-card h3 {{
            margin: 0 0 15px 0;
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}

        .summary-card .value {{
            font-size: 3rem;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .summary-card .icon {{
            font-size: 2rem;
        }}

        .url-section {{
            background: var(--bg-primary);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }}

        .url-section:hover {{
            box-shadow: var(--shadow-lg);
        }}

        .url-header {{
            border-bottom: 3px solid var(--primary);
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}

        .url-header h2 {{
            margin: 0 0 15px 0;
            color: var(--text-primary);
            font-size: 1.75rem;
            font-weight: 700;
        }}

        .url-header .url-link {{
            color: var(--primary);
            text-decoration: none;
            font-size: 1rem;
            word-break: break-all;
            transition: color 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }}

        .url-header .url-link:hover {{
            color: var(--primary-dark);
            text-decoration: underline;
        }}

        .url-header .url-link::before {{
            content: '🔗';
            font-size: 0.9rem;
        }}

        .agent-results {{
            margin-top: 20px;
        }}

        .result-card {{
            background: var(--bg-secondary);
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 5px solid var(--info);
            transition: all 0.3s ease;
            box-shadow: var(--shadow-sm);
        }}

        .result-card:hover {{
            box-shadow: var(--shadow-md);
            transform: translateX(5px);
        }}

        .result-header {{
            border-bottom: 2px solid var(--border);
            padding-bottom: 15px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .result-header h3 {{
            margin: 0;
            color: var(--text-primary);
            font-size: 1.25rem;
            font-weight: 600;
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
        }}

        .status-pass {{
            background: var(--success-light);
            color: var(--success);
        }}

        .status-fail {{
            background: var(--error-light);
            color: var(--error);
        }}

        .severity-critical {{
            color: #dc2626;
            font-weight: bold;
            padding: 8px 12px;
            background: #fee2e2;
            border-radius: 6px;
            display: inline-block;
        }}

        .severity-high {{
            color: #ea580c;
            font-weight: 600;
            padding: 8px 12px;
            background: #ffedd5;
            border-radius: 6px;
            display: inline-block;
        }}

        .severity-medium {{
            color: #f59e0b;
            font-weight: 600;
            padding: 8px 12px;
            background: var(--warning-light);
            border-radius: 6px;
            display: inline-block;
        }}

        .severity-low {{
            color: #84cc16;
            font-weight: 600;
            padding: 8px 12px;
            background: #ecfccb;
            border-radius: 6px;
            display: inline-block;
        }}

        .issue {{
            padding: 18px;
            background: var(--bg-primary);
            border-left: 4px solid var(--info);
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
        }}

        .issue:hover {{
            box-shadow: var(--shadow-md);
            transform: translateX(3px);
        }}

        .error {{
            padding: 18px;
            background: var(--error-light);
            border-left: 4px solid var(--error);
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: var(--shadow-sm);
        }}

        pre {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.875rem;
            line-height: 1.5;
        }}

        .page-screenshot {{
            margin: 25px 0;
            padding: 20px;
            background: var(--bg-secondary);
            border-radius: 12px;
            border: 1px solid var(--border);
        }}

        .page-screenshot h4 {{
            margin: 0 0 15px 0;
            color: var(--text-primary);
            font-weight: 600;
        }}

        .page-screenshot img {{
            max-width: 100%;
            height: auto;
            border: 2px solid var(--border);
            border-radius: 8px;
            box-shadow: var(--shadow-lg);
            transition: transform 0.3s ease;
        }}

        .page-screenshot img:hover {{
            transform: scale(1.02);
        }}

        .screenshot-toggle {{
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-md);
        }}

        .screenshot-toggle:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}

        .screenshot-toggle:active {{
            transform: translateY(0);
        }}

        .screenshot-content {{
            display: none;
            animation: slideDown 0.3s ease;
        }}

        .screenshot-content.expanded {{
            display: block;
        }}

        @keyframes slideDown {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .collapsible-section {{
            margin: 20px 0;
        }}

        .collapsible-header {{
            background: var(--bg-secondary);
            padding: 15px 20px;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid var(--border);
            transition: all 0.2s ease;
        }}

        .collapsible-header:hover {{
            background: var(--bg-tertiary);
        }}

        .collapsible-arrow {{
            transition: transform 0.3s ease;
            font-size: 1.2rem;
        }}

        .collapsible-arrow.expanded {{
            transform: rotate(180deg);
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            .header {{
                padding: 25px;
            }}

            .header h1 {{
                font-size: 1.75rem;
            }}

            .summary {{
                grid-template-columns: 1fr;
            }}

            .url-section {{
                padding: 20px;
            }}

            .result-header {{
                flex-direction: column;
                align-items: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <button class="dark-mode-toggle" onclick="toggleDarkMode()" title="Toggle dark mode">🌓</button>
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
            <h3>📊 Total Validations</h3>
            <div class="value"><span class="icon">🔍</span>{total}</div>
        </div>
        <div class="summary-card">
            <h3>✅ Passed</h3>
            <div class="value" style="color: #10b981;"><span class="icon">✓</span>{passed}</div>
        </div>
        <div class="summary-card">
            <h3>❌ Failed</h3>
            <div class="value" style="color: #ef4444;"><span class="icon">✗</span>{failed}</div>
        </div>
        <div class="summary-card">
            <h3>⚠️ Total Issues</h3>
            <div class="value" style="color: #f59e0b;"><span class="icon">🐛</span>{total_issues}</div>
        </div>
    </div>
"""

    def _group_results_by_url(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group results by URL."""
        grouped = {}
        for result in results:
            url = result.get("url", "Unknown")
            if url not in grouped:
                grouped[url] = []
            grouped[url].append(result)
        return grouped

    def _format_url_section_html(
        self, url: str, url_results: List[Dict[str, Any]]
    ) -> str:
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
        status_icon = "✓" if all_passed else "✗"
        status_text = (
            "ALL CHECKS PASSED" if all_passed else f"{total_issues} ISSUE(S) FOUND"
        )

        # Generate unique ID for screenshot toggle
        screenshot_id = hashlib.md5(url.encode()).hexdigest()[:8]

        html = f"""
    <div class="url-section">
        <div class="url-header">
            <h2>📄 Page Analysis</h2>
            <p><strong>URL:</strong> <a href="{url}" target="_blank" class="url-link">{url}</a></p>
            <p><span class="status-badge {status_class}">{status_icon} {status_text}</span></p>
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

    def _format_result_html(
        self, result: Dict[str, Any], include_url: bool = True
    ) -> str:
        """Format a single result as HTML."""
        agent_name = result.get("agent", "Unknown")
        success = result.get("success", False)
        status_class = "status-pass" if success else "status-fail"
        status_icon = "✓" if success else "✗"
        status_text = "PASSED" if success else "FAILED"

        html = f"""
        <div class="result-card">
            <div class="result-header">
                <h3>🔬 {agent_name}</h3>
                <span class="status-badge {status_class}">{status_icon} {status_text}</span>
            </div>
"""

        if result.get("error"):
            html += f'    <div class="error"><strong>⚠️ Error:</strong> {result["error"]}</div>\n'

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
        html = f"    <h4 style='color: var(--text-primary); margin: 20px 0 15px 0;'>📝 Spelling Errors ({len(errors)})</h4>\n"

        for error in errors:
            original = error.get("original", "")
            correction = error.get("correction", "")
            context = error.get("context", "")

            html += f"""
            <div class="error">
                <strong>Error:</strong> <code style="background: #fca5a5; padding: 2px 6px; border-radius: 3px; color: #7f1d1d;">"{original}"</code> 
                → <strong>Correction:</strong> <code style="background: #86efac; padding: 2px 6px; border-radius: 3px; color: #14532d;">"{correction}"</code><br>
                <em style="color: var(--text-secondary);">Context:</em> "{context}"
            </div>
"""

        return html

    def _format_visual_issues_html(
        self,
        issues: List[Dict[str, Any]],
        element_screenshots: Dict[int, str] | None = None,
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

        html = f"    <h4 style='color: var(--text-primary); margin: 20px 0 15px 0;'>👁️ Visual Issues ({len(issues)})</h4>\n"

        for severity in ["critical", "high", "medium", "low"]:
            issues_list = by_severity[severity]
            if not issues_list:
                continue

            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }[severity]
            html += f'    <h5 style="margin: 15px 0;"><span class="severity-{severity}">{severity_emoji} {severity.upper()} ({len(issues_list)})</span></h5>\n'

            for idx, issue in issues_list:
                issue_type = issue.get("type", "unknown").upper()
                issue_desc = issue.get("issue", "")
                location = issue.get("location", "")
                recommendation = issue.get("recommendation", "")

                html += f"""
            <div class="issue">
                <div style="margin-bottom: 10px;">
                    <strong style="color: var(--primary);">[{issue_type}]</strong> 
                    <span style="color: var(--text-primary);">{issue_desc}</span>
                </div>
                <div style="color: var(--text-secondary); margin-bottom: 8px;">
                    <strong>📍 Location:</strong> {location}
                </div>
                <div style="color: var(--text-secondary);">
                    <strong>💡 Fix:</strong> {recommendation}
                </div>"""

                # Add element screenshot if available
                if idx in element_screenshots:
                    screenshot_b64 = element_screenshots[idx]
                    html += f"""
                <div style="margin-top: 15px; padding: 15px; background: var(--bg-primary); border: 2px solid var(--border); border-radius: 8px;">
                    <strong style="color: var(--text-primary);">📸 Screenshot:</strong><br>
                    <img src="data:image/png;base64,{screenshot_b64}" 
                         style="max-width: 100%; height: auto; border: 2px solid var(--border); margin-top: 10px; border-radius: 8px; box-shadow: var(--shadow-md);" 
                         alt="Issue screenshot">
                </div>"""

                html += """
            </div>
"""

        return html

    def _get_html_footer(self) -> str:
        """Get HTML footer."""
        return """
    <footer style="text-align: center; padding: 40px 20px; color: var(--text-tertiary); margin-top: 40px; border-top: 2px solid var(--border);">
        <p style="margin: 0 0 10px 0; font-size: 0.875rem;">Generated by <strong>Agent Validator</strong></p>
        <p style="margin: 0; font-size: 0.75rem;">🤖 Powered by AI-driven website validation</p>
    </footer>
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

        function toggleDarkMode() {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');
        }

        // Load dark mode preference
        if (localStorage.getItem('darkMode') === 'enabled') {
            document.body.classList.add('dark-mode');
        }

        // Add smooth scroll behavior
        document.documentElement.style.scrollBehavior = 'smooth';

        // Add intersection observer for fade-in animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.url-section, .result-card').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(el);
        });
    </script>
</body>
</html>
"""
