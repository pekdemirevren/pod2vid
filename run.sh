#!/bin/bash

# Quick run script for the Multi-Speaker Audio Transcript Generator

echo "🚀 Starting Multi-Speaker Audio Transcript Generator..."

# Check if virtual environment exists
if [ ! -d "transcript_env" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source transcript_env/bin/activate

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Please run setup.sh first."
    exit 1
fi

# Run the application
echo "🌐 Opening Streamlit application..."
streamlit run app.py