#!/bin/bash

# LangSmith Integration Quick Check
# This script verifies your LangSmith setup

set -e

echo "=========================================="
echo "LangSmith Integration - Setup Check"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ No .env file found"
    echo ""
    echo "Create one from .env.example:"
    echo "  cp .env.example .env"
    echo ""
    exit 1
fi

echo "✅ .env file found"
echo ""

# Source .env
source .env

# Check for required variables
echo "🔑 Checking LangSmith configuration..."
echo ""

if [ -z "$LANGCHAIN_API_KEY" ] || [ "$LANGCHAIN_API_KEY" == "your_langsmith_api_key_here" ]; then
    echo "❌ LANGCHAIN_API_KEY not set in .env"
    echo ""
    echo "To get your API key:"
    echo "  1. Go to https://smith.langchain.com"
    echo "  2. Sign in or create account"
    echo "  3. Go to Settings → API Keys"
    echo "  4. Create new key and copy it"
    echo "  5. Add to .env:"
    echo "     LANGCHAIN_API_KEY=ls__your_key_here"
    echo ""
    exit 1
fi

echo "✅ LANGCHAIN_API_KEY is set"

if [ -z "$LANGCHAIN_TRACING_V2" ]; then
    echo "⚠️  LANGCHAIN_TRACING_V2 not set"
    echo "   Add to .env: LANGCHAIN_TRACING_V2=true"
    echo ""
elif [ "$LANGCHAIN_TRACING_V2" != "true" ]; then
    echo "⚠️  LANGCHAIN_TRACING_V2 is set to '$LANGCHAIN_TRACING_V2'"
    echo "   Should be: LANGCHAIN_TRACING_V2=true"
    echo ""
else
    echo "✅ LANGCHAIN_TRACING_V2 is enabled"
fi

if [ -z "$LANGCHAIN_PROJECT" ] || [ "$LANGCHAIN_PROJECT" == "agent-validator" ]; then
    echo "✅ LANGCHAIN_PROJECT is set to '${LANGCHAIN_PROJECT:-agent-validator}'"
else
    echo "ℹ️  LANGCHAIN_PROJECT is set to '$LANGCHAIN_PROJECT'"
fi

echo ""

# Check if langsmith package is installed
echo "📦 Checking langsmith package..."
if pipenv run python -c "import langsmith" 2>/dev/null; then
    echo "✅ langsmith package is installed"
else
    echo "❌ langsmith package not installed"
    echo ""
    echo "Install it with:"
    echo "  pipenv install"
    echo ""
    exit 1
fi

echo ""

# Test API key validity
echo "🧪 Testing LangSmith connection..."
echo ""

TEST_RESULT=$(pipenv run python -c "
import os
from langsmith import Client

try:
    client = Client()
    # Try to list projects (this will validate the API key)
    projects = list(client.list_projects(limit=1))
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if [[ "$TEST_RESULT" == "SUCCESS" ]]; then
    echo "✅ LangSmith API key is valid!"
    echo "✅ Successfully connected to LangSmith"
else
    echo "❌ LangSmith connection failed"
    echo ""
    echo "Error: $TEST_RESULT"
    echo ""
    echo "Possible issues:"
    echo "  - API key is invalid or expired"
    echo "  - Network connectivity issues"
    echo "  - LangSmith service is down"
    echo ""
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ LangSmith Setup Complete!"
echo "=========================================="
echo ""
echo "Your configuration:"
echo "  API Key: ${LANGCHAIN_API_KEY:0:10}..."
echo "  Tracing: $LANGCHAIN_TRACING_V2"
echo "  Project: ${LANGCHAIN_PROJECT:-agent-validator}"
echo ""
echo "Next steps:"
echo "  1. Run a validation:"
echo "     pipenv run validate --url https://example.com"
echo ""
echo "  2. Check your dashboard:"
echo "     https://smith.langchain.com"
echo ""
echo "  3. View traces in project: ${LANGCHAIN_PROJECT:-agent-validator}"
echo ""
echo "Documentation:"
echo "  - Quick Start: docs/LANGSMITH_QUICKSTART.md"
echo "  - Full Guide: docs/LANGSMITH_INTEGRATION.md"
echo ""
