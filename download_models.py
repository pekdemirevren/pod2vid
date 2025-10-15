#!/usr/bin/env python3
"""
Runtime model downloader for Streamlit Cloud deployment
Downloads Wav2Lip model if not present
"""

import os
import sys
from pathlib import Path
import subprocess

def download_model():
    """Download Wav2Lip model if not exists"""
    
    # Model paths to check
    current_dir = Path(__file__).parent
    model_paths = [
        current_dir / "models" / "wav2lip_gan.pth",
        current_dir / "Wav2Lip" / "checkpoints" / "Wav2Lip_gan.pth",
        current_dir / "Wav2Lip" / "wav2lip_gan.pth"
    ]
    
    # Check if any model exists
    for model_path in model_paths:
        if model_path.exists() and model_path.stat().st_size > 100_000_000:  # > 100MB
            print(f"✅ Model found: {model_path}")
            return True
    
    print("🔄 Downloading Wav2Lip model...")
    
    # Create models directory
    models_dir = current_dir / "models"
    models_dir.mkdir(exist_ok=True)
    
    # Try multiple download methods
    model_url = "https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0.0/wav2lip_gan.pth"
    alternative_urls = [
        "https://huggingface.co/spaces/Rudrabha/Wav2Lip/resolve/main/checkpoints/wav2lip_gan.pth",
        "https://github.com/justinjohn0306/Wav2Lip/releases/download/models/wav2lip_gan.pth"
    ]
    
    target_path = models_dir / "wav2lip_gan.pth"
    
    # Method 1: wget (if available)
    try:
        result = subprocess.run([
            "wget", "-O", str(target_path), model_url
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and target_path.exists():
            print(f"✅ Downloaded with wget: {target_path}")
            return True
    except Exception as e:
        print(f"wget failed: {e}")
    
    # Method 2: curl
    try:
        result = subprocess.run([
            "curl", "-L", "-o", str(target_path), model_url
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and target_path.exists():
            print(f"✅ Downloaded with curl: {target_path}")
            return True
    except Exception as e:
        print(f"curl failed: {e}")
    
    # Method 3: Python requests (fallback)
    try:
        import requests
        
        print(f"📥 Downloading from {model_url}")
        response = requests.get(model_url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if target_path.exists() and target_path.stat().st_size > 100_000_000:
            print(f"✅ Downloaded with requests: {target_path}")
            return True
    except Exception as e:
        print(f"requests failed: {e}")
    
    print("❌ Failed to download model from all methods")
    return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)