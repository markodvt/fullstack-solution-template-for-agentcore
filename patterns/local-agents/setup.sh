#!/bin/bash
set -e

echo "🚀 Setting up local agents environment..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo "📦 Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv is installed"

# Create virtual environment
echo "📦 Creating virtual environment..."
uv venv

# Activate and install
echo "📦 Installing dependencies..."
source .venv/bin/activate
uv pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Then test imports with:"
echo "  python test_imports.py"
echo ""
