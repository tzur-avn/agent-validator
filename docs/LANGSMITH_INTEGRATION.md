# LangSmith Integration Guide

## Overview

LangSmith is LangChain's observability platform that helps you monitor, debug, and improve your AI agents. This guide will help you integrate LangSmith with your agent-validator project.

## What You'll Get

With LangSmith integration, you can:

- 📊 **Monitor all LLM calls** - See every request and response
- 🐛 **Debug agent behavior** - Trace through agent workflows step-by-step
- ⚡ **Track performance** - Measure latency and token usage
- 📈 **Analyze patterns** - Identify common issues and improvements
- 🔍 **Search and filter** - Find specific runs across all validations
- 💰 **Cost tracking** - Monitor API usage and costs

## Setup Instructions

### Step 1: Get Your LangSmith API Key

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Sign in or create a free account
3. Navigate to **Settings** → **API Keys**
4. Click **Create API Key**
5. Copy your API key (starts with `ls__...`)

### Step 2: Configure Environment Variables

Add these to your `.env` file:

```bash
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__your_api_key_here
LANGCHAIN_PROJECT=agent-validator
```

**Example `.env` file:**
```bash
# Google AI
GOOGLE_API_KEY=your_google_api_key

# LangSmith (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__abc123xyz789
LANGCHAIN_PROJECT=agent-validator

# Slack (Optional)
# SLACK_BOT_TOKEN=xoxb-...
# SLACK_APP_TOKEN=xapp-...
```

### Step 3: Enable in Configuration

Edit `config.yaml`:

```yaml
langsmith:
  enabled: true  # Changed from false to true
```

### Step 4: Install Dependencies

```bash
pipenv install
```

This will install the `langsmith` package.

### Step 5: Verify Setup

Run a validation to test:

```bash
pipenv run validate --url https://example.com
```

Then check [smith.langchain.com](https://smith.langchain.com) - you should see your run!

## That's It! 🎉

LangSmith is now automatically tracking all your agent runs. No code changes needed!

---

## Understanding LangSmith Dashboard

### Projects

Your runs are organized by project. The default project is `agent-validator`. You can change this in the environment variable `LANGCHAIN_PROJECT`.

### Runs View

Each validation creates a "run" in LangSmith:

```
agent-validator/
├── Spell Checker Run (https://example.com)
│   ├── Scrape Web Node
│   ├── Analyze Text Node
│   │   └── LLM Call (Gemini)
│   └── Generate Report Node
└── Visual QA Run (https://example.com)
    ├── Screenshot Node
    ├── Analyze Visual Node
    │   └── LLM Call (Gemini Vision)
    └── Generate Report Node
```

### Key Metrics Tracked

- **Duration**: How long each step took
- **Tokens**: Input/output token counts
- **Cost**: Estimated API costs
- **Status**: Success, error, or pending
- **Inputs/Outputs**: Full request and response data

### Filtering and Search

You can filter runs by:
- Date range
- Status (success/error)
- Agent type
- URL validated
- Duration
- Cost

## Advanced Usage

### Custom Project Names

Set different projects for different environments:

```bash
# Development
LANGCHAIN_PROJECT=agent-validator-dev

# Production
LANGCHAIN_PROJECT=agent-validator-prod

# Per-user (for Slack bot)
LANGCHAIN_PROJECT=agent-validator-user-123
```

### Adding Custom Metadata

You can add metadata to runs for better organization (requires code changes - see Advanced section below).

### Dataset Creation

LangSmith allows you to create test datasets from your runs:

1. Find a good validation run
2. Click **"Add to Dataset"**
3. Create test cases for regression testing

## Troubleshooting

### "No runs appearing in LangSmith"

**Check:**
1. ✅ `LANGCHAIN_TRACING_V2=true` is set
2. ✅ `LANGCHAIN_API_KEY` is correct
3. ✅ API key is valid (not expired)
4. ✅ You're logged into the correct LangSmith account
5. ✅ Check the correct project name

**Debug:**
```bash
# Run with verbose logging
pipenv run validate --url https://example.com -v
```

Look for LangSmith-related log messages.

### "API Key Invalid"

- Verify your API key starts with `ls__`
- Check for extra spaces or quotes in `.env`
- Regenerate the API key if needed

### "Tracing Disabled"

Ensure `LANGCHAIN_TRACING_V2=true` (not `false` or `1`)

### Performance Impact

LangSmith adds minimal overhead (typically <100ms per run). If you need to disable it temporarily:

```bash
# In .env, set:
LANGCHAIN_TRACING_V2=false
```

Or remove the environment variable entirely.

## Best Practices

### 1. Use Descriptive Project Names

```bash
# Good
LANGCHAIN_PROJECT=agent-validator-production
LANGCHAIN_PROJECT=agent-validator-staging

# Less helpful
LANGCHAIN_PROJECT=test
```

### 2. Review Runs Regularly

Check your LangSmith dashboard weekly to:
- Identify performance bottlenecks
- Find common error patterns
- Track cost trends

### 3. Create Datasets for Testing

Convert good validation runs into test cases:
1. Find a representative run
2. Add to dataset
3. Use for regression testing

### 4. Set Up Alerts (LangSmith Pro)

Configure alerts for:
- High error rates
- Slow response times
- Cost spikes

### 5. Use Tags and Metadata

Tag runs by:
- Environment (dev/staging/prod)
- User (for Slack bot)
- Validation type
- Website category

## Cost Considerations

### LangSmith Pricing

- **Free Tier**: 5,000 traces/month
- **Plus**: $39/month for 100,000 traces
- **Enterprise**: Custom pricing

Your validation runs count as traces. Estimate:
- Each spell check ≈ 2-5 traces
- Each visual QA ≈ 3-7 traces

### Optimizing Trace Usage

To reduce traces if you hit limits:

1. **Disable in development:**
   ```bash
   LANGCHAIN_TRACING_V2=false  # for local testing
   ```

2. **Enable only for production:**
   Set environment variable only on production servers

3. **Sample traces:**
   Only trace a percentage of runs (requires code changes)

## Security & Privacy

### API Key Security

- ✅ Store in `.env` (never commit to git)
- ✅ Use different keys for dev/prod
- ✅ Rotate keys periodically
- ✅ Limit access to keys

### Data Privacy

**What gets sent to LangSmith:**
- All LLM prompts
- All LLM responses
- URLs validated
- Validation results
- Metadata and timing

**Considerations:**
- Don't use on sensitive/private websites in development
- Review LangSmith's privacy policy
- Consider data retention settings
- Use self-hosted LangSmith for sensitive data (Enterprise)

## Advanced Configuration (Optional)

### Custom Run Names

For better organization, you can customize run names. Create a utility file:

**`utils/langsmith_utils.py`:**
```python
"""LangSmith utility functions."""

import os
from typing import Optional, Dict, Any
from langsmith import Client
from langsmith.run_helpers import traceable

def is_langsmith_enabled() -> bool:
    """Check if LangSmith tracing is enabled."""
    return os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

def get_langsmith_client() -> Optional[Client]:
    """Get LangSmith client if enabled."""
    if not is_langsmith_enabled():
        return None
    return Client()

@traceable(name="agent_validation")
def trace_agent_run(
    agent_name: str,
    url: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Decorator for tracing agent runs.
    
    Usage:
        with trace_agent_run("spell_checker", url, {"user": "john"}):
            # Your agent code
            pass
    """
    pass
```

Then wrap your agent executions with this decorator for better organization.

## Integration with Slack Bot

When using the Slack bot, you can track which user requested which validation:

```python
# In slack_bot.py, add metadata
metadata = {
    "user_id": user_id,
    "channel_id": channel_id,
    "source": "slack"
}
```

This helps you see which users are using the bot most frequently.

## Comparing Runs

LangSmith allows you to compare runs side-by-side:

1. Select multiple runs
2. Click **"Compare"**
3. See differences in:
   - Performance
   - Outputs
   - Errors
   - Token usage

Useful for:
- A/B testing different prompts
- Comparing agent versions
- Identifying regressions

## Exporting Data

Export run data for external analysis:

1. Select runs
2. Click **"Export"**
3. Choose format (CSV, JSON)
4. Analyze in your preferred tool

## LangSmith + CI/CD

Integrate LangSmith with your testing pipeline:

```bash
# In your test script
export LANGCHAIN_PROJECT=agent-validator-ci
export LANGCHAIN_TRACING_V2=true

pipenv run test
```

This creates a separate project for CI runs, keeping them isolated from production.

## Resources

- **LangSmith Docs**: [docs.smith.langchain.com](https://docs.smith.langchain.com)
- **LangSmith Dashboard**: [smith.langchain.com](https://smith.langchain.com)
- **LangChain Discord**: Community support
- **API Reference**: [api.python.langchain.com](https://api.python.langchain.com)

## FAQ

**Q: Does LangSmith slow down my validations?**  
A: Minimal impact, typically <100ms overhead per run.

**Q: Can I use LangSmith with the Slack bot?**  
A: Yes! It works automatically with no changes needed.

**Q: What if I exceed the free tier?**  
A: You can disable tracing or upgrade to a paid plan.

**Q: Can I self-host LangSmith?**  
A: Yes, with Enterprise plan.

**Q: Is my data secure?**  
A: LangSmith uses industry-standard encryption. Review their security policy.

**Q: Can I delete runs?**  
A: Yes, you can delete individual runs or entire projects.

## Summary

To get started with LangSmith right now:

1. **Add to `.env`:**
   ```bash
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_key_here
   LANGCHAIN_PROJECT=agent-validator
   ```

2. **Install:**
   ```bash
   pipenv install
   ```

3. **Run a validation:**
   ```bash
   pipenv run validate --url https://example.com
   ```

4. **Check dashboard:**
   Visit [smith.langchain.com](https://smith.langchain.com)

That's it! You're now tracking all your agent runs. 🎉

---

**Need Help?**  
Check the [main documentation](../README.md) or LangSmith's support.
