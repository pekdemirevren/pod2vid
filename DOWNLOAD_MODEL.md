# 🎬 Wav2Lip Model Download Instructions

## ⚠️ Critical Step Required for Video Generation

The Wav2Lip model file is required for video generation but needs to be downloaded manually.

## 📥 Download Steps

### Option 1: Direct Download (Recommended)
1. **Visit GitHub Releases**: https://github.com/Rudrabha/Wav2Lip/releases
2. **Download**: Look for `wav2lip_gan.pth` (approximately 170MB)
3. **Place file at**: `/Users/evrenpekdemir/audio-transcript-generator/Wav2Lip/checkpoints/wav2lip_gan.pth`

### Option 2: Terminal Download
```bash
# Navigate to project directory
cd /Users/evrenpekdemir/audio-transcript-generator

# Download using curl
curl -L -o Wav2Lip/checkpoints/wav2lip_gan.pth "https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth"

# OR download using wget (if available)
wget -O Wav2Lip/checkpoints/wav2lip_gan.pth "https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth"
```

### Option 3: Alternative Sources
If GitHub releases are not available, try:
- **Hugging Face**: https://huggingface.co/spaces/Rudrabha/Wav2Lip
- **Author's Google Drive**: Look for alternative links in the original Wav2Lip repository

## ✅ Verification

After download, verify the file:
```bash
# Check file size (should be ~170MB)
ls -lh Wav2Lip/checkpoints/wav2lip_gan.pth

# Expected output: ~170M wav2lip_gan.pth
```

## 🚀 What Works Without The Model

✅ **Currently Working**:
- Audio transcription with speaker detection
- Multi-speaker transcript generation
- Streamlit web interface
- File uploads and processing

❌ **Requires Model**:
- Video generation with lip-sync
- Face animation
- Final video output

## 🔧 Quick Test

Once downloaded, test the application:
```bash
cd /Users/evrenpekdemir/audio-transcript-generator
source venv/bin/activate
streamlit run app.py
```

Upload an audio file and speaker photos to test the complete pipeline!

---

**Model File Location**: `Wav2Lip/checkpoints/wav2lip_gan.pth`  
**Expected Size**: ~170MB  
**File Type**: PyTorch model checkpoint (.pth)