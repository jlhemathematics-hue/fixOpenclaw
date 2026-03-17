#!/bin/bash
# Quick activation script for Python 3.13 virtual environment

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run ./setup_python313.sh first to create it."
    exit 1
fi

echo "🔌 Activating Python 3.13 virtual environment..."
source venv/bin/activate

echo "✅ Virtual environment activated!"
echo "Python version: $(python --version)"
echo "Python path: $(which python)"
echo ""
echo "You can now run:"
echo "  python quick_test.py"
echo "  python main.py --mode once --log-file logs/openclaw.log"
