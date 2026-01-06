# What You Need to Do - LangSmith Integration

## Quick Answer

You have your LangSmith API key already. Here's exactly what to do:

### 1. Add to `.env` file (create if it doesn't exist):

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_actual_api_key_here
LANGCHAIN_PROJECT=agent-validator
```

### 2. Install the package:

```bash
pipenv install
```

### 3. Done! Test it:

```bash
pipenv run validate --url https://example.com
```

Then check [smith.langchain.com](https://smith.langchain.com) to see your run!

---

## Detailed Steps

### Step 1: Edit Your `.env` File

Open `.env` (or create it from `.env.example`):

```bash
# If .env doesn't exist:
cp .env.example .env
```

Then add these lines:

```bash
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__your_actual_key_here  # Replace with your key
LANGCHAIN_PROJECT=agent-validator
```

**Important:** Replace `ls__your_actual_key_here` with your actual LangSmith API key!

### Step 2: Install Dependencies

The `langsmith` package has been added to your `Pipfile`. Install it:

```bash
cd /Users/tzur.avner/projects/private/agent-validator
pipenv install
```

This will install the `langsmith` package along with any other dependencies.

### Step 3: Verify Setup (Optional)

Run the automated setup check:

```bash
./setup_langsmith.sh
```

This will verify:
- ✅ `.env` file exists
- ✅ API key is set
- ✅ Package is installed
- ✅ Connection to LangSmith works

### Step 4: Run a Test Validation

```bash
pipenv run validate --url https://example.com
```

### Step 5: Check LangSmith Dashboard

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Look for project `agent-validator`
3. You should see your validation run with all the details!

---

## What Gets Tracked Automatically

Once set up, LangSmith will automatically track:

- ✅ **All LLM calls** to Gemini
- ✅ **Agent workflows** (every step)
- ✅ **Performance metrics** (duration, tokens)
- ✅ **Costs** (estimated API costs)
- ✅ **Errors** (if any occur)
- ✅ **Inputs/outputs** (prompts and responses)

**No code changes needed!** It just works with your existing agents.

---

## Troubleshooting

### Problem: "No runs showing up"

**Solution:**
1. Check `.env` has all three variables
2. Make sure `LANGCHAIN_TRACING_V2=true` (not `false`)
3. Verify your API key is correct
4. Run with verbose logging: `pipenv run validate --url https://example.com -v`

### Problem: "API key invalid"

**Solution:**
1. Check your API key starts with `ls__`
2. Make sure there are no extra spaces or quotes in `.env`
3. Regenerate the key at [smith.langchain.com/settings](https://smith.langchain.com/settings)

### Problem: Package not found

**Solution:**
```bash
pipenv install langsmith
```

---

## Example `.env` File

Here's a complete example:

```bash
# Google AI (required)
GOOGLE_API_KEY=AIzaSyA_your_google_key_here

# LangSmith (optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__your_langsmith_key_here
LANGCHAIN_PROJECT=agent-validator

# Slack (optional - only if using Slack bot)
# SLACK_BOT_TOKEN=xoxb-your-token
# SLACK_APP_TOKEN=xapp-your-token
```

---

## What You'll See in LangSmith

After running a validation, you'll see something like:

```
Project: agent-validator
├── Run: SpellChecker validation (https://example.com)
│   Duration: 4.2s
│   Status: ✅ Success
│   
│   Steps:
│   ├── Scrape Web Node (1.2s)
│   ├── Analyze Text Node (2.5s)
│   │   └── Gemini LLM Call
│   │       Input: "Check this text for errors..."
│   │       Output: [{"original": "teh", "correction": "the"}]
│   │       Tokens: 1,200 in / 150 out
│   │       Cost: $0.0002
│   └── Generate Report Node (0.5s)
```

Click on any step to see full details!

---

## Benefits You Get

### 1. **Debugging**
See exactly what prompts are sent to the LLM and what responses come back.

### 2. **Performance Monitoring**
Track which steps are slow and optimize them.

### 3. **Cost Tracking**
Monitor API costs across all validations.

### 4. **Error Analysis**
When something fails, see the full trace to debug faster.

### 5. **Comparison**
Compare different runs to see how changes affect results.

---

## Optional: Different Projects for Different Environments

If you want separate tracking for development vs production:

**Development:**
```bash
LANGCHAIN_PROJECT=agent-validator-dev
```

**Production:**
```bash
LANGCHAIN_PROJECT=agent-validator-prod
```

---

## Documentation

- **Quick Start**: [docs/LANGSMITH_QUICKSTART.md](docs/LANGSMITH_QUICKSTART.md)
- **Full Guide**: [docs/LANGSMITH_INTEGRATION.md](docs/LANGSMITH_INTEGRATION.md)
- **LangSmith Docs**: [docs.smith.langchain.com](https://docs.smith.langchain.com)

---

## Summary Checklist

- [ ] Added `LANGCHAIN_TRACING_V2=true` to `.env`
- [ ] Added `LANGCHAIN_API_KEY=your_key` to `.env`
- [ ] Added `LANGCHAIN_PROJECT=agent-validator` to `.env`
- [ ] Ran `pipenv install`
- [ ] Tested with `pipenv run validate --url https://example.com`
- [ ] Checked [smith.langchain.com](https://smith.langchain.com) for the run

---

**That's it!** You're all set. LangSmith is now tracking your agent runs automatically. 🎉
