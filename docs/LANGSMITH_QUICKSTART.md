# LangSmith Quick Setup

## What You Need

- LangSmith API key from [smith.langchain.com](https://smith.langchain.com)

## Setup Steps

### 1. Add to your `.env` file:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__your_api_key_here
LANGCHAIN_PROJECT=agent-validator
```

### 2. Install the package:

```bash
pipenv install
```

### 3. Run a test validation:

```bash
pipenv run validate --url https://example.com
```

### 4. Check your dashboard:

Go to [smith.langchain.com](https://smith.langchain.com) and you'll see your run!

## That's It! 🎉

LangSmith is now automatically tracking:
- ✅ All LLM calls
- ✅ Agent workflow steps
- ✅ Performance metrics
- ✅ Token usage
- ✅ Costs

## What You'll See

In LangSmith dashboard:

```
agent-validator/
├── SpellChecker (https://example.com)
│   ├── Scrape Web - 1.2s
│   ├── Analyze Text - 2.5s
│   │   └── Gemini LLM Call - 2.3s
│   └── Generate Report - 0.3s
│
└── VisualQA (https://example.com)
    ├── Take Screenshot - 2.1s
    ├── Analyze Visual - 3.2s
    │   └── Gemini Vision Call - 3.0s
    └── Generate Report - 0.4s
```

## Optional: Change Project Name

Want different projects for dev/prod?

```bash
# Development
LANGCHAIN_PROJECT=agent-validator-dev

# Production  
LANGCHAIN_PROJECT=agent-validator-prod
```

## Disable Temporarily

To turn off tracing:

```bash
# In .env, change to:
LANGCHAIN_TRACING_V2=false
```

Or just remove/comment out the environment variables.

## Troubleshooting

**Not seeing runs?**

1. Check `.env` has correct variables
2. Make sure `LANGCHAIN_TRACING_V2=true` (not false or 1)
3. Verify API key is correct
4. Check you're viewing the correct project

**Still need help?**

See the full guide: [LANGSMITH_INTEGRATION.md](LANGSMITH_INTEGRATION.md)

---

**Cost:** LangSmith free tier includes 5,000 traces/month  
**Privacy:** All LLM calls and responses are logged to LangSmith  
**Performance:** Adds <100ms overhead per validation
