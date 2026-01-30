#!/bin/bash

# Slack Integration Quick Start Script
# This script helps you get started with the Slack integration

set -e

echo "=========================================="
echo "Agent Validator - Slack Integration Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "📝 Please edit .env and add your tokens:"
    echo "   - SLACK_BOT_TOKEN (from Slack App OAuth & Permissions)"
    echo "   - SLACK_APP_TOKEN (from Slack App Basic Information)"
    echo "   - GOOGLE_API_KEY (from Google AI Studio)"
    echo ""
    echo "See docs/SLACK_INTEGRATION.md for detailed instructions"
    echo ""
    exit 1
fi

# Check if pipenv is installed
if ! command -v pipenv &> /dev/null; then
    echo "❌ pipenv is not installed"
    echo "Install it with: pip install pipenv"
    exit 1
fi

echo "✅ pipenv found"
echo ""

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! pipenv --venv &> /dev/null; then
    echo "Installing dependencies..."
    pipenv install
else
    echo "✅ Dependencies already installed"
fi
echo ""

# Check for Playwright browsers
echo "🌐 Checking Playwright browsers..."
if pipenv run python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch()" 2>/dev/null; then
    echo "✅ Playwright browsers installed"
else
    echo "⚠️  Installing Playwright browsers..."
    pipenv run install-playwright
    echo "✅ Playwright browsers installed"
fi
echo ""

# Check environment variables
echo "🔑 Checking environment variables..."
source .env

if [ -z "$SLACK_BOT_TOKEN" ] || [ "$SLACK_BOT_TOKEN" == "xoxb-your-bot-token-here" ]; then
    echo "❌ SLACK_BOT_TOKEN not set in .env"
    echo "   Get it from: https://api.slack.com/apps → OAuth & Permissions"
    exit 1
fi

if [ -z "$SLACK_APP_TOKEN" ] || [ "$SLACK_APP_TOKEN" == "xapp-your-app-token-here" ]; then
    echo "❌ SLACK_APP_TOKEN not set in .env"
    echo "   Get it from: https://api.slack.com/apps → Basic Information → App-Level Tokens"
    exit 1
fi

if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" == "your_google_api_key_here" ]; then
    echo "❌ GOOGLE_API_KEY not set in .env"
    echo "   Get it from: https://makersuite.google.com/app/apikey"
    exit 1
fi

echo "✅ All required environment variables set"
echo ""

# Run example to verify setup
echo "🧪 Running setup verification..."
pipenv run python examples/slack_integration_example.py
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the Slack bot, run:"
echo "  pipenv run slack-bot"
echo ""
echo "Or with verbose logging:"
echo "  pipenv run slack-bot -v"
echo ""
echo "For more information:"
echo "  - Setup Guide: docs/SLACK_INTEGRATION.md"
echo "  - Commands: docs/SLACK_COMMANDS.md"
echo "  - Implementation: docs/SLACK_IMPLEMENTATION_SUMMARY.md"
echo ""
