import operator
import json
from typing import Annotated, List, TypedDict
from playwright.sync_api import sync_playwright
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from bidi.algorithm import get_display


load_dotenv()
# --- Define State Structure ---
class AgentState(TypedDict):
    url: str
    raw_text: str
    errors: Annotated[List[dict], operator.add]
    report: str

# --- Node 1: Scrape Real Data from Browser (Scraper Node) ---
def scrape_web_node(state: AgentState):
    print(f"--- Launching browser and scraping: {state['url']} ---")
    
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to site and wait for network to be idle (suitable for React/Angular sites)
        page.goto(state['url'], wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)  # Additional wait for dynamic content
        
        # Extract text from body (can be refined to specific selectors like 'main' or 'article')
        # We extract InnerText so AI doesn't get unnecessary HTML tags
        visible_text = page.inner_text("body")
        
        browser.close()
        
    # Basic cleanup of double spaces to save tokens
    clean_text = " ".join(visible_text.split())
    return {"raw_text": clean_text[:10000]} # Basic limit for demonstration purposes

# --- Node 2: Analysis with Gemini 1.5 ---
def analyze_text_node(state: AgentState):
    print(f"--- Gemini analyzing {len(state['raw_text'])} characters of live text ---")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )
    
    prompt = f"""
    You are a QA expert for the English language. Scan the following text extracted from a website.
    Identify spelling errors, grammar issues, or unclear phrasing.
    
    Return only a JSON list:
    [
      {{"original": "the source", "correction": "the correction", "context": "the full sentence where the error was found"}}
    ]
    
    Text to check:
    {state['raw_text']}
    """
    
    response = llm.invoke(prompt)
    
    # Clean output and convert to JSON
    content = response.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    
    try:
        found_errors = json.loads(content)
    except:
        found_errors = []
        
    return {"errors": found_errors}

# --- Node 3: Generate Report ---
def generate_report_node(state: AgentState):
    print("--- Summarizing findings ---")
    if not state['errors']:
        report = f"SUCCESS: No spelling errors found on page {state['url']}."
    else:
        report = f"FAILED: Found {len(state['errors'])} errors on page {state['url']}:\n"
        for i, err in enumerate(state['errors'], 1):
            original = get_display(err.get('original', ''))
            correction = get_display(err.get('correction', ''))
            context = get_display(err.get('context', ''))
            report += f"{i}. Error: '{original}' -> Correction: '{correction}'\n"
            report += f"   Context: \"{context}\"\n"
    
    return {"report": report}

# --- Build the Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("scraper", scrape_web_node)
workflow.add_node("analyzer", analyze_text_node)
workflow.add_node("reporter", generate_report_node)

workflow.set_entry_point("scraper")
workflow.add_edge("scraper", "analyzer")
workflow.add_edge("analyzer", "reporter")
workflow.add_edge("reporter", END)

app = workflow.compile()

# --- Run on a real website ---
# Make sure you set export GOOGLE_API_KEY='your_key'
url_to_test = "https://www.walla.co.il" # Just an example of a site with lots of content
final_output = app.invoke({"url": url_to_test, "errors": []})

print("\n" + "="*30)
print(final_output['report'])