#!/bin/bash

# Multi-Speaker Audio Transcript Generator Setup Script

echo "🎙️ Setting up Multi-Speaker Audio Transcript Generator..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -o "3\.[0-9]\+")
if [[ $? -ne 0 ]]; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment
echo "🔄 Creating virtual environment..."
python3 -m venv transcript_env

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source transcript_env/bin/activate

# Upgrade pip
echo "🔄 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "🔄 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To run the application:"
echo "1. Activate the environment: source transcript_env/bin/activate"
echo "2. Run the app: streamlit run app.py"
echo ""
echo "Or use the quick start script:"
echo "chmod +x run.sh && ./run.sh"