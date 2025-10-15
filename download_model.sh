#!/bin/bash

# Wav2Lip Model Download Script
# Bu script model dosyasını indirmek için farklı yöntemler dener

echo "🔄 Wav2Lip Model İndirme Script'i"
echo "=================================="

MODEL_DIR="/Users/evrenpekdemir/audio-transcript-generator/Wav2Lip/checkpoints"
MODEL_FILE="$MODEL_DIR/wav2lip_gan.pth"

# Create directory if it doesn't exist
mkdir -p "$MODEL_DIR"

echo "📍 Hedef dizin: $MODEL_DIR"
echo "📄 Hedef dosya: wav2lip_gan.pth"
echo "🎯 Beklenen boyut: ~170MB"
echo ""

# Function to check file size
check_size() {
    if [ -f "$MODEL_FILE" ]; then
        SIZE=$(stat -f%z "$MODEL_FILE" 2>/dev/null || stat -c%s "$MODEL_FILE" 2>/dev/null || echo "0")
        SIZE_MB=$((SIZE / 1024 / 1024))
        echo "📁 Dosya boyutu: ${SIZE_MB}MB"
        
        if [ $SIZE_MB -gt 150 ]; then
            echo "✅ İndirme başarılı!"
            return 0
        elif [ $SIZE_MB -gt 10 ]; then
            echo "⚠️ Kısmi indirme (${SIZE_MB}MB)"
            return 1
        else
            echo "❌ Dosya çok küçük (${SIZE_MB}MB)"
            return 2
        fi
    else
        echo "❌ Dosya bulunamadı"
        return 3
    fi
}

# Remove existing file if it exists
if [ -f "$MODEL_FILE" ]; then
    echo "🗑️ Mevcut dosya siliniyor..."
    rm "$MODEL_FILE"
fi

echo "📥 İndirme başlatılıyor..."

# Method 1: Try direct GitHub download
echo ""
echo "🌐 Yöntem 1: GitHub Direct"
curl -L --progress-bar -o "$MODEL_FILE" \
    "https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth" \
    --connect-timeout 30 --max-time 600

check_size
if [ $? -eq 0 ]; then
    echo "🎉 GitHub'dan başarıyla indirildi!"
    exit 0
fi

# Method 2: Try wget if available
if command -v wget &> /dev/null; then
    echo ""
    echo "🌐 Yöntem 2: Wget ile GitHub"
    rm -f "$MODEL_FILE"
    
    wget --progress=bar:force:noscroll -O "$MODEL_FILE" \
        "https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth" \
        --timeout=30 --tries=3
    
    check_size
    if [ $? -eq 0 ]; then
        echo "🎉 Wget ile başarıyla indirildi!"
        exit 0
    fi
fi

# Method 3: Try alternative mirror
echo ""
echo "🌐 Yöntem 3: Alternatif Mirror"
rm -f "$MODEL_FILE"

curl -L --progress-bar -o "$MODEL_FILE" \
    "https://huggingface.co/spaces/Rudrabha/Wav2Lip/resolve/main/checkpoints/wav2lip_gan.pth" \
    --connect-timeout 30 --max-time 600

check_size
if [ $? -eq 0 ]; then
    echo "🎉 Alternatif kaynaktan başarıyla indirildi!"
    exit 0
fi

# If all methods fail
echo ""
echo "❌ Otomatik indirme başarısız oldu"
echo ""
echo "🔧 MANUEL İNDİRME TALİMATLARI:"
echo "1. Web browser'da şu adresi açın:"
echo "   https://github.com/Rudrabha/Wav2Lip/releases"
echo ""
echo "2. 'Assets' bölümünden 'wav2lip_gan.pth' dosyasını indirin"
echo "   (Boyut: yaklaşık 170MB)"
echo ""
echo "3. İndirilen dosyayı şu konuma taşıyın:"
echo "   $MODEL_FILE"
echo ""
echo "4. Dosya boyutunu kontrol edin:"
echo "   ls -lh '$MODEL_FILE'"
echo ""
echo "💡 Not: Dosya boyutu 150MB'dan büyük olmalı"

exit 1