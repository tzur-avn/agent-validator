# AI Agent Web Validator

A comprehensive, AI-powered web validation framework that automatically detects spelling errors, grammar issues, and visual/UI problems on websites. Built with a modular architecture using LangGraph, Playwright, and support for Google's Gemini AI and OpenAI models.

## ✨ Features

### Dual Agent System
- **Spell Checker Agent**: Detects spelling errors, grammar issues, and unclear phrasing in text content
- **Visual QA Agent**: Identifies layout issues, accessibility problems, responsive design flaws, and UI inconsistencies

### Advanced Capabilities
- **Real Browser Automation**: Uses Playwright for accurate rendering of JavaScript-heavy sites
- **AI-Powered Analysis**: Leverages Google's Gemini 2.5 Flash or OpenAI models (GPT-4o, GPT-4 Turbo) with vision capabilities
- **Multi-Language Support**: Handles bidirectional text (Hebrew, Arabic, etc.)
- **Flexible Configuration**: YAML-based config for agents, targets, and output formats
- **Multiple Output Formats**: Text, JSON, and HTML reports with interactive dashboards
- **Parallel Execution**: Run multiple agents concurrently for faster validation
- **Robust Error Handling**: Retry logic with exponential backoff for reliability
- **Slack Integration**: Interact with agents directly from Slack (see [Slack Integration Guide](docs/SLACK_INTEGRATION.md))
- **LangSmith Observability**: Monitor and debug agent runs with LangSmith integration (see [LangSmith Guide](docs/LANGSMITH_INTEGRATION.md))

## 🏗️ Architecture

The project uses a modular, extensible architecture:

```
agent-validator/
├── agents/           # Validation agents (spell_checker, visual_qa)
├── core/             # Core framework (orchestrator, config, exceptions)
├── reporters/        # Output formatters (text, JSON, HTML)
├── utils/            # Utilities (browser, validation, text processing)
├── tests/            # Unit tests
├── examples/         # Example configurations
└── main.py           # CLI entry point
```

For detailed architecture documentation, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 📋 Requirements

- Python 3.10+
- API Key from one of:
  - Google AI API Key (free tier available at [Google AI Studio](https://makersuite.google.com/app/apikey))
  - OpenAI API Key (get it at [OpenAI Platform](https://platform.openai.com/api-keys))

## 🚀 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-validator
```

2. Install dependencies with pipenv:
```bash
pipenv install
```

3. Install Playwright browsers:
```bash
pipenv run install-playwright
```

4. Set up your API key:
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY or OPENAI_API_KEY (or both)
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with your API key(s):
```bash
# For Google Gemini (default)
GOOGLE_API_KEY=your_google_api_key_here

# For OpenAI (optional)
OPENAI_API_KEY=your_openai_api_key_here
```

### Configuration File

Create or edit `config.yaml` to customize agents and targets:

```yaml
agents:
  spell_checker:
    enabled: true
    provider: "gemini"  # Options: gemini, openai
    model: "gemini-2.5-flash"  # For OpenAI: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
    temperature: 0
    max_text_length: 10000
  
  visual_qa:
    enabled: true
    provider: "gemini"  # Options: gemini, openai
    model: "gemini-2.5-flash"  # For OpenAI: gpt-4o, gpt-4-turbo (vision models)
    temperature: 0
    viewports:
      - width: 1920
        height: 1080
        name: "Desktop"

targets:
  - url: "https://example.com"
    agents: ["spell_checker", "visual_qa"]

output:
  format: "html"  # Options: text, json, html
  path: "./reports"
  timestamp: true
```

See [examples/](examples/) for more configuration examples.

## 🎯 Usage

### Command Line Interface

#### Basic Usage

```bash
# Run all agents on a URL
pipenv run python main.py --url https://example.com

# Run specific agent
pipenv run python main.py --url https://example.com --agents spell_checker

# Run with custom config
pipenv run python main.py --config examples/multi_site_check.yaml

# Output as HTML
pipenv run python main.py --url https://example.com --format html --output reports/

# Verbose logging
pipenv run python main.py --url https://example.com -v
```

#### Using pipenv scripts

```bash
# Main CLI using validate script
pipenv run validate --url https://example.com

# With options
pipenv run validate --url https://example.com --format html --output reports/
```

### Programmatic Usage

```python
from core.config_loader import ConfigLoader
from core.orchestrator import Orchestrator
from reporters import get_reporter

# Load configuration
config = ConfigLoader.load("config.yaml")

# Create orchestrator
orchestrator = Orchestrator(config._config)

# Run agents on a URL
results = orchestrator.run_multiple_agents(
    url="https://example.com",
    agent_names=["spell_checker", "visual_qa"]
)

# Generate report
reporter = get_reporter("html", timestamp=True)
report = reporter.format_report(results)
print(report)
```

### Running Legacy Agents (Backward Compatibility)

The original standalone agents are still available:

```bash
pipenv run spell-check   # Run spell checker only
pipenv run visual-check  # Run visual QA only
```

### Slack Integration

Run validation agents directly from Slack! See the [Slack Integration Guide](docs/SLACK_INTEGRATION.md) for setup instructions.

```bash
# Start the Slack bot
pipenv run slack-bot

# With verbose logging
pipenv run slack-bot -v
```

**Key Features:**
- Chat with agents directly in Slack
- Interactive conversations to gather required arguments
- Formatted reports delivered to Slack channels
- Support for both direct messages and channel mentions

**Example Slack conversation:**
```
You: @Agent Validator Bot check spelling on https://example.com
Bot: 🚀 Starting spell_checker validation for: https://example.com
Bot: [Formatted report with spelling errors]
```

## 📊 Output Formats

### Text Output
Console-friendly plain text reports.

### JSON Output
Machine-readable format for integration with other tools:
```json
{
  "timestamp": "2026-01-05 10:30:00",
  "results": [...],
  "summary": {
    "total_validations": 2,
    "passed": 1,
    "failed": 1
  }
}
```

### HTML Output
Interactive dashboard with:
- Summary statistics
- Severity-based filtering
- Color-coded issues
- Responsive design

## 🧪 Testing

Run the test suite:
```bash
pipenv run test
```

## 📚 Examples

### Multi-Site Validation
```bash
pipenv run python main.py --config examples/multi_site_check.yaml
```

### Mobile Responsive Testing
```bash
pipenv run python main.py --config examples/mobile_responsive.yaml
```

### Single Agent Quick Check
```bash
pipenv run python main.py --url https://example.com --agents spell_checker --format text
```

## 🛠️ Development

### Project Structure
- `agents/` - Validation agents
- `core/` - Framework core (orchestrator, config, exceptions)
- `reporters/` - Output formatters
- `utils/` - Helper utilities
- `tests/` - Unit tests
- `examples/` - Example configurations

### Adding a New Agent

1. Create agent class in `agents/`:
```python
from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def build_workflow(self):
        # Define your workflow
        pass
```

2. Register in orchestrator:
```python
# In core/orchestrator.py
AGENT_REGISTRY = {
    "my_agent": MyAgent,
}
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

[Your License Here]

## 🔗 Links

- [Google AI Studio](https://makersuite.google.com/app/apikey) - Get your API key
- [Playwright Documentation](https://playwright.dev/python/) - Browser automation
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) - Agent framework

## 📧 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

Built with ❤️ using LangGraph, Playwright, and Google Gemini AI
   - Applies bidirectional text reordering for proper display of Hebrew/Arabic text
   - Returns success or failure status with detailed error information

## Example Output

```
--- Launching browser and scraping: https://www.example.com ---
--- Gemini analyzing 8542 characters of live text ---
--- Summarizing findings ---

==============================
FAILED: Found 3 errors on page https://www.example.com:
1. Error: 'recieve' -> Correction: 'receive'
   Context: "You will recieve an email confirmation within 24 hours."
2. Error: 'their' -> Correction: 'there'
   Context: "Their are many options available for customization."
3. Error: 'alot' -> Correction: 'a lot'
   Context: "We offer alot of features for our users."
```

## Architecture

- **LangGraph**: Orchestrates the multi-node agent workflow
- **Playwright**: Provides real browser automation for accurate content scraping
- **AI Models**: Supports both Google Gemini AI and OpenAI for intelligent analysis
- **python-bidi**: Handles bidirectional text rendering for RTL languages

## Customization

### Switch Between Providers

In your `config.yaml`, change the provider and model:
```yaml
agents:
  spell_checker:
    provider: "openai"  # Switch to OpenAI
    model: "gpt-4o"     # Use GPT-4o model
```

Or use Gemini:
```yaml
agents:
  spell_checker:
    provider: "gemini"
    model: "gemini-2.5-pro"  # Use Pro model for higher quality
```

### Supported Models

**Gemini Models:**
- `gemini-2.5-flash` (default, fast and efficient)
- `gemini-2.5-pro` (higher quality)
- `gemini-1.5-flash` (legacy)

**OpenAI Models:**
- `gpt-4o` (latest multimodal model)
- `gpt-4-turbo` (vision support)
- `gpt-3.5-turbo` (text-only, faster)

### Adjust Content Limit

Modify the character limit in the scraper node:
```python
return {"raw_text": clean_text[:20000]}  # Increase to 20,000 characters
```

### Target Specific Elements

Refine the scraping to specific page sections:
```python
visible_text = page.inner_text("main")  # Only scrape main content area
# or
visible_text = page.inner_text("article")  # Only scrape article content
```

## 🌟 Credits

Built with ❤️ using LangGraph, Playwright, Google Gemini AI, and OpenAI

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
