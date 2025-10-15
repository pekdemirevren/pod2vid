import streamlit as st
import os
import tempfile
from pathlib import Path
import shutil
import subprocess

# Check FFmpeg availability
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except:
        return False

# Lightweight imports
try:
    import whisper
    WHISPER_AVAILABLE = True
except:
    WHISPER_AVAILABLE = False
    st.error("Whisper not available in cloud environment")

# Audio loading fallback without FFmpeg
def load_audio_fallback(file_path):
    """Load audio without FFmpeg using librosa or soundfile"""
    try:
        import librosa
        audio, sr = librosa.load(file_path, sr=16000)
        return audio
    except:
        try:
            import soundfile as sf
            audio, sr = sf.read(file_path)
            # Resample if needed
            if sr != 16000:
                import librosa
                audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            return audio
        except Exception as e:
            st.error(f"Audio loading failed: {e}")
            return None

def main():
    st.title("🎙️ Audio Transcript Generator (Cloud)")
    st.write("Lightweight version for cloud deployment")
    
    # Check system dependencies
    if not check_ffmpeg():
        st.warning("⚠️ FFmpeg not detected. Using fallback audio loading.")
    
    # File upload
    audio_file = st.file_uploader(
        "Upload audio file", 
        type=["wav", "mp3", "m4a", "ogg"],
        help="Upload an audio file to generate transcript"
    )
    
    if audio_file and WHISPER_AVAILABLE:
        st.success(f"Uploaded: {audio_file.name}")
        
        if st.button("🎯 Generate Transcript"):
            with st.spinner("Processing audio..."):
                try:
                    # Save uploaded file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_file.read())
                        temp_path = tmp_file.name
                    
                    # Load model
                    model = whisper.load_model("base")
                    
                    # Try standard transcription first
                    try:
                        result = model.transcribe(temp_path)
                        transcript = result["text"]
                    except Exception as e:
                        st.warning("Standard transcription failed, trying fallback method...")
                        # Use fallback audio loading
                        audio_data = load_audio_fallback(temp_path)
                        if audio_data is not None:
                            result = model.transcribe(audio_data)
                            transcript = result["text"]
                        else:
                            raise e
                    
                    # Display results
                    st.subheader("📝 Transcript")
                    st.text_area("Generated Transcript", transcript, height=200)
                    
                    # Cleanup
                    os.unlink(temp_path)
                    
                except Exception as e:
                    st.error(f"Error processing audio: {str(e)}")
                    st.info("💡 Try uploading a different audio format (WAV recommended)")
                    
                    # Cleanup on error
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

if __name__ == "__main__":
    main()