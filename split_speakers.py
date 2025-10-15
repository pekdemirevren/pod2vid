import os
from pydub import AudioSegment
from pyannote.core import Annotation

# Girdi dosyaları
audio_path = "podcast.wav"       # podcast ses dosyan
rttm_path = "diarization.rttm"   # pyannote çıktısı

# Çıktı klasörü
output_dir = "split_speakers"
os.makedirs(output_dir, exist_ok=True)

# RTTM'i yükle
annotation = Annotation.from_rttm(open(rttm_path).readlines())

# Orijinal ses dosyasını yükle
audio = AudioSegment.from_wav(audio_path)

# Her konuşmacının sesini ayır
for speaker in annotation.labels():
    segments = annotation.label_timeline(speaker)
    combined = AudioSegment.empty()
    for segment in segments:
        start_ms = int(segment.start * 1000)
        end_ms = int(segment.end * 1000)
        combined += audio[start_ms:end_ms]
    
    # Her konuşmacıyı ayrı kaydet
    output_file = os.path.join(output_dir, f"{speaker}.wav")
    combined.export(output_file, format="wav")
    print(f"✔ {output_file} kaydedildi ({len(segments)} segment).")

print("\n✅ Tüm konuşmacılar ayrı dosyalar halinde 'split_speakers/' klasörüne kaydedildi.")