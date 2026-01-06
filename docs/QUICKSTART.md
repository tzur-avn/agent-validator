# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```bash
pipenv install
pipenv run install-playwright
```

### 2. Set Up API Key

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

Get your free API key at [Google AI Studio](https://makersuite.google.com/app/apikey)

### 3. Run Your First Validation

```bash
pipenv run python main.py --url https://example.com
```

That's it! You'll see a text report in your console.

## 📋 Next Steps

### Try Different Agents

```bash
# Spell check only
pipenv run python main.py --url https://example.com --agents spell_checker

# Visual QA only
pipenv run python main.py --url https://example.com --agents visual_qa
```

### Generate HTML Report

```bash
pipenv run python main.py --url https://example.com --format html --output reports/
```

Open the generated HTML file in your browser for an interactive dashboard!

### Use a Configuration File

1. Copy the example config:
```bash
cp examples/config.example.yaml my-config.yaml
```

2. Edit `my-config.yaml` with your URLs:
```yaml
targets:
  - url: "https://your-site.com"
    agents: ["spell_checker", "visual_qa"]
```

3. Run with config:
```bash
pipenv run python main.py --config my-config.yaml
```

### Test Multiple Viewports

```bash
pipenv run python main.py --config examples/mobile_responsive.yaml --format html
```

## 🎯 Common Use Cases

### 1. Check Blog Post for Spelling Errors
```bash
pipenv run python main.py --url https://your-blog.com/post --agents spell_checker
```

### 2. Validate Landing Page UI
```bash
pipenv run python main.py --url https://your-landing-page.com --agents visual_qa --format html
```

### 3. Full Site Audit
```yaml
# audit.yaml
targets:
  - url: "https://your-site.com"
  - url: "https://your-site.com/about"
  - url: "https://your-site.com/contact"
```

```bash
pipenv run python main.py --config audit.yaml --format html --output reports/audit/
```

### 4. CI/CD Integration
```bash
# Exit with error code if issues found
pipenv run python main.py --url https://staging.your-site.com --quiet
if [ $? -eq 0 ]; then
  echo "✓ Validation passed"
else
  echo "✗ Validation failed"
  exit 1
fi
```

## 🔧 Troubleshooting

### "No module named 'playwright'"
```bash
pipenv install
pipenv run install-playwright
```

### "GOOGLE_API_KEY not set"
Make sure you have a `.env` file with:
```
GOOGLE_API_KEY=your_actual_api_key_here
```

### Browser not launching
```bash
# Reinstall Playwright browsers
pipenv run install-playwright
```

### For more help
```bash
pipenv run python main.py --help
```

Or enable verbose logging:
```bash
pipenv run python main.py --url https://example.com -v
```

## 📚 Learn More

- [Full Documentation](../README.md)
- [Architecture Details](ARCHITECTURE.md)
- [Migration Guide](MIGRATION.md)
- [Configuration Examples](../examples/)
