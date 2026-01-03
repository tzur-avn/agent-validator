import operator
import json
import base64
from typing import Annotated, List, TypedDict
from playwright.sync_api import sync_playwright
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv


load_dotenv()

# --- Define State Structure ---
class AgentState(TypedDict):
    url: str
    screenshot: str  # Base64 encoded screenshot
    viewport_width: int
    viewport_height: int
    issues: Annotated[List[dict], operator.add]
    report: str

# --- Node 1: Capture Screenshot and Page Metrics ---
def capture_visual_node(state: AgentState):
    print(f"--- Capturing visual data from: {state['url']} ---")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': state.get('viewport_width', 1920), 
                     'height': state.get('viewport_height', 1080)}
        )
        page = context.new_page()
        
        # Navigate and wait for page to be fully loaded
        page.goto(state['url'])
        page.wait_for_timeout(5000)  # Additional wait for animations
        
        # Take full-page screenshot
        screenshot_bytes = page.screenshot(full_page=True)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        browser.close()
        
    return {"screenshot": screenshot_b64}

# --- Node 2: AI Visual Analysis with Gemini Vision ---
def analyze_visual_node(state: AgentState):
    print(f"--- Gemini analyzing visual elements ---")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0
    )
    
    # Prepare the message with image
    from langchain_core.messages import HumanMessage
    
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": """You are a UI/UX expert and QA specialist. Analyze this website screenshot for visual issues.

Check for:
1. **Layout Issues**: Overlapping elements, misaligned content, broken grids
2. **Readability**: Poor color contrast, text too small, hard-to-read fonts
3. **Responsive Design**: Elements cut off, horizontal scrolling issues
4. **Visual Hierarchy**: Confusing layouts, poor spacing, cluttered UI
5. **Accessibility**: Missing alt text indicators, poor focus states, contrast issues
6. **Broken UI**: Missing images (broken image icons), distorted graphics
7. **Consistency**: Inconsistent spacing, mixed font sizes, mismatched styles

Return ONLY a JSON list of issues found:
[
  {
    "type": "layout|readability|responsive|hierarchy|accessibility|broken|consistency",
    "severity": "critical|high|medium|low",
    "location": "describe where on the page",
    "issue": "brief description of the problem",
    "recommendation": "suggested fix"
  }
]

If no issues are found, return an empty array: []
"""
            },
            {
                "type": "image_url",
                "image_url": f"data:image/png;base64,{state['screenshot']}"
            }
        ]
    )
    
    response = llm.invoke([message])
    
    # Clean output and convert to JSON
    content = response.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    try:
        found_issues = json.loads(content)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {content[:500]}")
        found_issues = []
        
    return {"issues": found_issues}

# --- Node 3: Generate Detailed Report ---
def generate_report_node(state: AgentState):
    print("--- Generating visual QA report ---")
    
    if not state['issues']:
        report = f"✓ SUCCESS: No visual issues detected on {state['url']}\n"
        report += f"Viewport: {state.get('viewport_width', 1920)}x{state.get('viewport_height', 1080)}"
    else:
        # Group issues by severity
        critical = [i for i in state['issues'] if i.get('severity') == 'critical']
        high = [i for i in state['issues'] if i.get('severity') == 'high']
        medium = [i for i in state['issues'] if i.get('severity') == 'medium']
        low = [i for i in state['issues'] if i.get('severity') == 'low']
        
        report = f"✗ VISUAL ISSUES DETECTED on {state['url']}\n"
        report += f"Viewport: {state.get('viewport_width', 1920)}x{state.get('viewport_height', 1080)}\n"
        report += f"Total Issues: {len(state['issues'])} "
        report += f"(Critical: {len(critical)}, High: {len(high)}, Medium: {len(medium)}, Low: {len(low)})\n\n"
        
        # Report by severity
        for severity_name, issues_list in [
            ("CRITICAL", critical),
            ("HIGH", high),
            ("MEDIUM", medium),
            ("LOW", low)
        ]:
            if issues_list:
                report += f"\n{'='*60}\n"
                report += f"{severity_name} SEVERITY ISSUES ({len(issues_list)})\n"
                report += f"{'='*60}\n"
                
                for i, issue in enumerate(issues_list, 1):
                    report += f"\n{i}. [{issue.get('type', 'unknown').upper()}] {issue.get('issue', 'No description')}\n"
                    report += f"   Location: {issue.get('location', 'Not specified')}\n"
                    report += f"   Fix: {issue.get('recommendation', 'No recommendation')}\n"
    
    return {"report": report}

# --- Build the Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("capture", capture_visual_node)
workflow.add_node("analyzer", analyze_visual_node)
workflow.add_node("reporter", generate_report_node)

workflow.set_entry_point("capture")
workflow.add_edge("capture", "analyzer")
workflow.add_edge("analyzer", "reporter")
workflow.add_edge("reporter", END)

app = workflow.compile()

# --- Run Visual QA Test ---
if __name__ == "__main__":
    # Test on different viewport sizes
    test_configs = [
        {"url": "https://www.walla.co.il", "viewport_width": 1920, "viewport_height": 1080},
        # Uncomment to test mobile view:
        # {"url": "https://www.walla.co.il", "viewport_width": 375, "viewport_height": 667},
    ]
    
    for config in test_configs:
        print(f"\n{'#'*80}")
        print(f"# Testing: {config['url']} at {config['viewport_width']}x{config['viewport_height']}")
        print(f"{'#'*80}\n")
        
        final_output = app.invoke({
            "url": config['url'],
            "viewport_width": config['viewport_width'],
            "viewport_height": config['viewport_height'],
            "issues": []
        })
        
        print("\n" + "="*80)
        print(final_output['report'])
        print("="*80)
