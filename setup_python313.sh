#!/bin/bash
# Setup script for fixOpenclaw with Homebrew Python 3.13

set -e

echo "🐍 Setting up fixOpenclaw with Python 3.13..."

# Python 3.13 path
PYTHON_313="/opt/homebrew/bin/python3.13"

# Check if Python 3.13 is available
if [ ! -f "$PYTHON_313" ]; then
    echo "❌ Python 3.13 not found at $PYTHON_313"
    echo "Please install it with: brew install python@3.13"
    exit 1
fi

echo "✅ Found Python 3.13: $($PYTHON_313 --version)"

# Remove old virtual environment if exists
if [ -d "venv" ]; then
    echo "🗑️  Removing old virtual environment..."
    rm -rf venv
fi

# Create new virtual environment with Python 3.13
echo "📦 Creating virtual environment with Python 3.13..."
$PYTHON_313 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Verify Python version
echo "✅ Virtual environment Python: $(python --version)"
echo "✅ Virtual environment location: $(which python)"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel -q

# Install dependencies
echo "📦 Installing project dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  python quick_test.py"
echo ""
echo "To run the application:"
echo "  python main.py --mode once --log-file logs/openclaw.log"
