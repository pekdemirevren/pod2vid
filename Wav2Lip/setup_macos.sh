#!/bin/bash
# Wav2Lip setup script for macOS (Apple Silicon) with Python 3.9

echo "🚀 Wav2Lip Setup Script"
echo "======================="

# Check if we're in the right directory
if [ ! -f "requirements_39.txt" ]; then
    echo "❌ Error: requirements_39.txt not found. Please run from Wav2Lip directory."
    exit 1
fi

# 1. Virtual environment oluştur
echo "📦 Creating virtual environment 'venv39'..."
python3 -m venv venv39
source venv39/bin/activate

# 2. pip, setuptools ve wheel güncelle
echo "⬆️ Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# 3. Paketleri yükle
echo "📥 Installing Python packages..."
pip install -r requirements_39.txt

echo "✅ Setup completed successfully!"
echo "🎯 Activate the environment with: source venv39/bin/activate"