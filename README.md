# AI Agent Web Validator

An intelligent web scraping and validation agent that uses AI to analyze website content for spelling errors, grammar issues, and unclear phrasing. Built with LangGraph, Playwright, and Google's Gemini AI.

## Features

- **Real Browser Scraping**: Uses Playwright to scrape content from live websites, including JavaScript-rendered content
- **AI-Powered Analysis**: Leverages Google's Gemini 2.5 Flash model to intelligently detect spelling and grammar errors
- **Multi-Language Support**: Properly handles bidirectional text (Hebrew, Arabic, etc.) using the python-bidi library
- **Agent Workflow**: Implements a multi-node agent workflow using LangGraph for structured processing

## Requirements

- Python 3.10+
- Google AI API Key (free tier available at [Google AI Studio](https://makersuite.google.com/app/apikey))

## Installation

### Quick Setup (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-validator
```

2. Run the setup script:
```bash
./setup.sh
```

This script will install pipenv, create the virtual environment, install all dependencies, and set up Playwright browsers.

### Manual Setup with pipenv

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-validator
```

2. Install pipenv if you haven't already:
```bash
pip install pipenv
```

3. Install dependencies and create virtual environment:
```bash
pipenv install
```

4. Install Playwright browsers:
```bash
pipenv run install-playwright
```

### Alternative: Manual Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-validator
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install playwright langchain-google-genai langgraph python-dotenv python-bidi
```

4. Install Playwright browser:
```bash
playwright install chromium
```

## Configuration

Create a `.env` file in the project root with your Google API key:

```env
GOOGLE_API_KEY=your_api_key_here
```

Get your free API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

## Usage

1. Edit the `url_to_test` variable in `agent_web_speller.py` to specify the website you want to analyze:
```python
url_to_test = "https://www.example.com"
```

2. Run the scripts using pipenv:

For spell checking:
```bash
pipenv run spell-check
```

For visual issue analysis:
```bash
pipenv run visual-check
```

Or run directly with pipenv shell:
```bash
pipenv shell
python agent_web_speller.py
python agent_web_visual_issues.py
```

3. The agent will:
   - Launch a headless browser
   - Scrape the website content
   - Analyze the text using Gemini AI
   - Generate a detailed report of any errors found

## How It Works

The application uses a three-node agent workflow:

1. **Scraper Node** (`scrape_web_node`):
   - Launches a Chromium browser using Playwright
   - Navigates to the target URL
   - Extracts visible text from the page
   - Returns cleaned text (up to 10,000 characters)

2. **Analyzer Node** (`analyze_text_node`):
   - Sends the scraped text to Google's Gemini 2.5 Flash model
   - Uses a specialized prompt to identify spelling, grammar, and phrasing issues
   - Parses the AI response into structured error objects

3. **Reporter Node** (`generate_report_node`):
   - Formats the findings into a human-readable report
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
- **Google Gemini AI**: Powers intelligent text analysis and error detection
- **python-bidi**: Handles bidirectional text rendering for RTL languages

## Customization

### Change the Model

Edit the `analyze_text_node` function to use a different Gemini model:
```python
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",  # Use Pro model for higher quality
    temperature=0
)
```

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

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
