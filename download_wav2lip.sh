#!/bin/bash

# Download Wav2Lip checkpoint
CHECKPOINT_URL="https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip.pth"
CHECKPOINT_DIR="Wav2Lip/checkpoints"
CHECKPOINT_FILE="$CHECKPOINT_DIR/wav2lip.pth"

echo "🔽 Downloading Wav2Lip checkpoint..."

# Create checkpoints directory if it doesn't exist
mkdir -p "$CHECKPOINT_DIR"

# Download if not exists
if [ ! -f "$CHECKPOINT_FILE" ]; then
    echo "📦 Downloading wav2lip.pth (416MB)..."
    curl -L "$CHECKPOINT_URL" -o "$CHECKPOINT_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Checkpoint downloaded successfully!"
    else
        echo "❌ Failed to download checkpoint"
        exit 1
    fi
else
    echo "✅ Checkpoint already exists"
fi

echo "🎉 Wav2Lip setup complete!"