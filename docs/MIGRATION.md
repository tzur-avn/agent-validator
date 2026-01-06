# Migration Guide

## Upgrading from Legacy Agents

If you were using the original `agent_web_speller.py` or `agent_web_visual_issues.py`, here's how to migrate to the new architecture.

### Quick Start

The legacy agents still work! But we recommend migrating to the new unified CLI:

#### Old Way
```bash
pipenv run spell-check
pipenv run visual-check
```

#### New Way
```bash
# Run both agents
pipenv run python main.py --url https://example.com

# Run specific agent
pipenv run python main.py --url https://example.com --agents spell_checker
pipenv run python main.py --url https://example.com --agents visual_qa
```

### Configuration Migration

#### Old Way (Hardcoded)
```python
# In agent_web_speller.py
url_to_test = "https://www.walla.co.il"
```

#### New Way (Config File)
```yaml
# config.yaml
targets:
  - url: "https://www.walla.co.il"
    agents: ["spell_checker", "visual_qa"]
```

Then run:
```bash
pipenv run python main.py --config config.yaml
```

### Code Migration

#### Old Way
```python
from agent_web_speller import app

final_output = app.invoke({"url": url_to_test, "errors": []})
print(final_output['report'])
```

#### New Way
```python
from core.orchestrator import Orchestrator
from reporters import get_reporter

orchestrator = Orchestrator()
results = orchestrator.run_multiple_agents(
    url="https://example.com",
    agent_names=["spell_checker"]
)

reporter = get_reporter("text")
print(reporter.format_report(results))
```

### Benefits of Migrating

1. **Unified Interface**: One CLI for all agents
2. **Configuration Files**: Reusable configs for different scenarios
3. **Multiple Formats**: Output as text, JSON, or HTML
4. **Parallel Execution**: Run agents concurrently
5. **Better Error Handling**: Automatic retries and detailed logging
6. **Extensibility**: Easy to add custom agents

### Backward Compatibility

The original agents remain in the project root and continue to work. They will be maintained for backward compatibility but new features will only be added to the new architecture.

### Common Patterns

#### Pattern 1: Single Site, Multiple Agents
```bash
pipenv run python main.py --url https://example.com --format html --output reports/
```

#### Pattern 2: Multiple Sites from Config
```yaml
# multi-sites.yaml
targets:
  - url: "https://site1.com"
    agents: ["spell_checker", "visual_qa"]
  - url: "https://site2.com"
    agents: ["spell_checker"]
```

```bash
pipenv run python main.py --config multi-sites.yaml
```

#### Pattern 3: Mobile Testing
```yaml
# mobile.yaml
agents:
  visual_qa:
    viewports:
      - width: 375
        height: 667
        name: "iPhone"
      - width: 1920
        height: 1080
        name: "Desktop"

targets:
  - url: "https://example.com"
    agents: ["visual_qa"]
```

```bash
pipenv run python main.py --config mobile.yaml --format html
```

### Getting Help

Run with `--help` to see all options:
```bash
pipenv run python main.py --help
```

For verbose output during migration:
```bash
pipenv run python main.py --url https://example.com -v
```
