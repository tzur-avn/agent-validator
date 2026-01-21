# OpenAI Integration Guide

This guide explains how to use OpenAI models with the Agent Validator instead of (or in addition to) Google Gemini.

## Prerequisites

- OpenAI API Key from [OpenAI Platform](https://platform.openai.com/api-keys)
- `langchain-openai` package (automatically installed via Pipfile)

## Setup

1. **Add your OpenAI API key to `.env`:**

```bash
# In your .env file
OPENAI_API_KEY=sk-your-openai-api-key-here
```

You can use both Gemini and OpenAI in the same project:

```bash
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=sk-your-openai-api-key-here
```

2. **Configure agents to use OpenAI in `config.yaml`:**

```yaml
agents:
  spell_checker:
    enabled: true
    provider: "openai"  # Switch to OpenAI
    model: "gpt-4o"     # OpenAI model
    temperature: 0
    max_text_length: 10000
  
  visual_qa:
    enabled: true
    provider: "openai"
    model: "gpt-4o"  # Vision-capable model
    temperature: 0
    viewports:
      - width: 1920
        height: 1080
        name: "Desktop"
```

## Supported Models

### OpenAI Models

**For Text Analysis (Spell Checker):**
- `gpt-4o` - Latest multimodal model (recommended)
- `gpt-4-turbo` - Fast, high-quality
- `gpt-3.5-turbo` - Faster, more economical

**For Visual QA (with Vision):**
- `gpt-4o` - Latest with vision support (recommended)
- `gpt-4-turbo` - Vision capabilities
- `gpt-4-vision-preview` - Legacy vision model

### Gemini Models

**For Text Analysis:**
- `gemini-2.5-flash` - Fast and efficient (default)
- `gemini-2.5-pro` - Higher quality
- `gemini-1.5-flash` - Legacy

**For Visual QA:**
- `gemini-2.5-flash` - Vision support (default)
- `gemini-2.5-pro` - Higher quality vision

## Usage Examples

### Using OpenAI for All Agents

```bash
# Run with OpenAI configuration
pipenv run python main.py --config examples/openai_config.yaml --url https://example.com
```

### Mixed Configuration (Gemini + OpenAI)

You can use different providers for different agents:

```yaml
agents:
  spell_checker:
    provider: "gemini"
    model: "gemini-2.5-flash"  # Use Gemini for text
  
  visual_qa:
    provider: "openai"
    model: "gpt-4o"  # Use OpenAI for vision
```

### Command Line Usage

```bash
# Using default config (Gemini)
pipenv run python main.py --url https://example.com

# Using OpenAI config
pipenv run python main.py --config examples/openai_config.yaml --url https://example.com

# Generate HTML report with OpenAI
pipenv run python main.py --config examples/openai_config.yaml \
  --url https://example.com \
  --format html \
  --output reports/
```

## Cost Comparison

### Gemini Pricing (as of 2024)
- **Flash**: Free tier available, very low cost
- **Pro**: Higher cost but better quality

### OpenAI Pricing (as of 2024)
- **GPT-4o**: ~$0.005/1K input tokens, ~$0.015/1K output tokens
- **GPT-4-Turbo**: ~$0.01/1K input tokens, ~$0.03/1K output tokens
- **GPT-3.5-Turbo**: ~$0.0005/1K input tokens, ~$0.0015/1K output tokens

**Note:** Check [OpenAI Pricing](https://openai.com/pricing) and [Google AI Pricing](https://ai.google.dev/pricing) for current rates.

## Performance Considerations

### When to Use Gemini:
- Free tier requirements
- Lower cost at scale
- Prefer Google's AI ecosystem
- Good default choice

### When to Use OpenAI:
- Require GPT-4's reasoning capabilities
- Already using OpenAI in your stack
- Need specific OpenAI features
- Want to compare results between providers

## Troubleshooting

### "OpenAI API key not found"

Make sure your `.env` file contains:
```bash
OPENAI_API_KEY=sk-...
```

And that you're loading environment variables:
```bash
pipenv run python main.py  # Automatically loads .env
```

### "Unsupported provider"

Supported providers are:
- `gemini` (default)
- `openai`

Check your `config.yaml`:
```yaml
agents:
  spell_checker:
    provider: "openai"  # Must be lowercase
```

### Rate Limits

Both providers have rate limits:
- **OpenAI**: Varies by tier (free/paid)
- **Gemini**: 60 requests per minute (free tier)

The agent validator includes automatic retry logic with exponential backoff.

## Example Configuration Files

See the `examples/` directory:
- `config.example.yaml` - Default Gemini configuration
- `openai_config.yaml` - OpenAI configuration
- `multi_site_check.yaml` - Multi-site with provider selection

## Advanced: Per-Target Provider Override

You can't currently override the provider per-target, but you can run multiple validation passes with different configs:

```bash
# Pass 1: Gemini
pipenv run python main.py --config config_gemini.yaml --url https://example.com

# Pass 2: OpenAI
pipenv run python main.py --config config_openai.yaml --url https://example.com
```

## Support

For issues or questions:
1. Check this guide
2. Review example configs in `examples/`
3. Check provider documentation:
   - [OpenAI API Docs](https://platform.openai.com/docs)
   - [Google AI Studio](https://ai.google.dev)
