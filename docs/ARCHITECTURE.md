# Architecture Documentation

## Overview

The Agent Validator is built with a modular, extensible architecture that separates concerns and allows easy addition of new validation agents.

## Core Components

### 1. Agents (`agents/`)

The agents module contains all validation agents. Each agent inherits from `BaseAgent` and implements specific validation logic.

#### BaseAgent
- **Purpose**: Abstract base class providing common functionality
- **Key Features**:
  - LLM initialization and invocation with retry logic
  - JSON response parsing
  - Workflow management using LangGraph
  - State management

#### SpellCheckerAgent
- **Purpose**: Detect spelling and grammar errors in text content
- **Workflow**:
  1. Scrape text content from web page
  2. Clean and normalize text
  3. Send to LLM for analysis
  4. Parse errors from response
  5. Generate formatted report
- **State**: `url`, `raw_text`, `errors`, `report`

#### VisualQAAgent
- **Purpose**: Identify visual and UI/UX issues
- **Workflow**:
  1. Capture screenshot at specified viewport
  2. Send screenshot to vision-capable LLM
  3. Parse visual issues from response
  4. Group issues by severity
  5. Generate detailed report
- **State**: `url`, `screenshot`, `viewport_width`, `viewport_height`, `issues`, `report`

### 2. Core Framework (`core/`)

#### Orchestrator
- **Purpose**: Coordinate execution of multiple agents
- **Features**:
  - Run agents sequentially or in parallel
  - Manage agent lifecycle and configuration
  - Aggregate results from multiple agents
  - Generate summary statistics

#### ConfigLoader
- **Purpose**: Load and validate configuration
- **Features**:
  - YAML configuration parsing
  - Environment variable overrides
  - Configuration validation
  - Default configuration fallback

#### Exceptions
Custom exception hierarchy:
- `AgentValidatorError` (base)
  - `ConfigurationError`
  - `BrowserError`
  - `LLMError`
  - `ValidationError`
  - `ReportGenerationError`

#### Logging
- Configurable log levels
- Console and file output
- Third-party logger suppression

### 3. Reporters (`reporters/`)

#### Reporter Architecture
All reporters inherit from `BaseReporter` and implement the `format_report()` method.

#### TextReporter
- Plain text output for console
- Simple, readable format
- Timestamp support

#### JSONReporter
- Machine-readable output
- Includes summary statistics
- Easy integration with other tools

#### HTMLReporter
- Interactive dashboard
- Severity-based styling
- Responsive design
- Summary cards
- Color-coded issues

### 4. Utilities (`utils/`)

#### BrowserSession
- Context manager for Playwright browser sessions
- Automatic resource cleanup
- Navigation and screenshot capabilities
- Configurable viewport and timeout

#### Text Utilities
- Text cleaning and normalization
- Bidirectional text formatting
- JSON extraction from markdown
- Text truncation

#### Validation Utilities
- URL validation and normalization
- Viewport dimension validation
- Model name validation
- Temperature parameter validation

#### Retry Utilities
- Exponential backoff decorator
- Configurable retry attempts
- Exception filtering

## Data Flow

```
User Input (URL or Config)
        ↓
ConfigLoader → Configuration
        ↓
Orchestrator
        ↓
    ┌───┴───┐
    ↓       ↓
SpellChecker  VisualQA
  Agent       Agent
    ↓           ↓
Browser    Browser
Session    Session
    ↓           ↓
  LLM         LLM
(Text)     (Vision)
    ↓           ↓
Results    Results
    └───┬───┘
        ↓
    Reporter
        ↓
Output (Text/JSON/HTML)
```

## State Management

Each agent maintains its own state using TypedDict:

### SpellCheckerState
```python
{
    "url": str,
    "raw_text": str,
    "errors": List[dict],
    "report": str
}
```

### VisualQAState
```python
{
    "url": str,
    "screenshot": str,  # base64
    "viewport_width": int,
    "viewport_height": int,
    "issues": List[dict],
    "report": str
}
```

## Workflow Graphs

Agents use LangGraph to define their execution workflows:

### SpellChecker Workflow
```
START → scraper → analyzer → reporter → END
```

### VisualQA Workflow
```
START → capture → analyzer → reporter → END
```

## Extension Points

### Adding a New Agent

1. Create agent class inheriting from `BaseAgent`
2. Define state TypedDict
3. Implement required methods:
   - `build_workflow()`
   - `get_state_class()`
   - `create_initial_state()`
4. Add workflow nodes
5. Register in `Orchestrator.AGENT_REGISTRY`

### Adding a New Reporter

1. Create reporter class inheriting from `BaseReporter`
2. Implement `format_report(results)` method
3. Add to `reporters/__init__.py`
4. Update `get_reporter()` factory

### Adding Custom Validation

1. Add validation function to `utils/validation_utils.py`
2. Use in configuration loading or agent initialization
3. Raise `ValidationError` on failure

## Configuration Schema

```yaml
agents:
  agent_name:
    enabled: bool
    model: str
    temperature: float
    # Agent-specific options

targets:
  - url: str
    agents: List[str]

output:
  format: str  # text|json|html
  path: str
  timestamp: bool

browser:
  headless: bool
  timeout: int

retry:
  max_retries: int
  initial_delay: float
  exponential_base: float
```

## Error Handling Strategy

1. **Validation Errors**: Fail fast on invalid input
2. **Browser Errors**: Retry with exponential backoff
3. **LLM Errors**: Retry with exponential backoff
4. **Parsing Errors**: Return empty results, log warning
5. **Orchestrator Errors**: Collect per-agent, continue execution

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies (LLM, browser)
- Focus on business logic

### Integration Tests
- Test agent workflows end-to-end
- Use real browser with test pages
- Mock only LLM responses

### Configuration Tests
- Validate configuration loading
- Test environment variable overrides
- Verify validation rules

## Performance Considerations

- **Parallel Execution**: Use ThreadPoolExecutor for concurrent agent runs
- **Browser Reuse**: Potential future optimization (not currently implemented)
- **Response Caching**: Potential future optimization
- **Viewport Batching**: VisualQA can test multiple viewports sequentially

## Security Considerations

- API keys stored in environment variables
- No sensitive data in logs (except debug mode)
- URL validation prevents injection attacks
- Browser runs in sandboxed mode

## Future Enhancements

1. **Agent Chaining**: Output from one agent as input to another
2. **Custom Prompts**: User-configurable LLM prompts
3. **Screenshot Comparison**: Detect visual regressions
4. **Performance Metrics**: Page load time, resource analysis
5. **Accessibility Scoring**: WCAG compliance checking
6. **API Server**: REST API for remote validation
7. **Webhook Support**: Send results to external services
8. **Scheduled Runs**: Cron-like scheduling
