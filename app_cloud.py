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

def format_timestamp(seconds):
    """Convert seconds to MM:SS format"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def display_timestamped_transcript(segments):
    """Display transcript with timestamps"""
    st.subheader("📝 Timestamped Transcript")
    
    # Create columns for better layout
    col1, col2 = st.columns([1, 4])
    
    for segment in segments:
        with col1:
            start_time = format_timestamp(segment["start"])
            end_time = format_timestamp(segment["end"])
            st.write(f"**{start_time}-{end_time}**")
        
        with col2:
            st.write(segment["text"].strip())
        
        st.divider()

def main():
    st.title("🎙️ AI Podcast Video Generator 2025")
    st.write("🤖 No-code AI automation: Audio → Transcript → Video")
    
    # Check system dependencies
    if not check_ffmpeg():
        st.warning("⚠️ FFmpeg not detected. Using fallback audio loading.")
    
    # Sidebar for options
    with st.sidebar:
        st.header("🎛️ Settings")
        model_size = st.selectbox("Whisper Model", ["tiny", "base", "small"], index=1)
        show_timestamps = st.checkbox("Show timestamps", value=True)
        generate_video = st.checkbox("Enable video generation", value=False)
        
        if generate_video:
            st.info("🎬 Video generation will be available after transcript")
    
    # File uploads
    st.header("📁 Upload Files")
    col1, col2 = st.columns(2)
    
    with col1:
        audio_file = st.file_uploader(
            "🎵 Upload audio file", 
            type=["wav", "mp3", "m4a", "ogg"],
            help="Upload podcast or audio file"
        )
    
    with col2:
        if generate_video:
            face_image = st.file_uploader(
                "👤 Upload speaker photo",
                type=["jpg", "png", "jpeg"],
                help="Photo of the speaker for video generation"
            )
    
    if audio_file and WHISPER_AVAILABLE:
        st.success(f"✅ Uploaded: {audio_file.name}")
        
        if st.button("🎯 Generate Transcript", type="primary"):
            with st.spinner("🤖 AI processing your audio..."):
                try:
                    # Save uploaded file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_file.read())
                        temp_path = tmp_file.name
                    
                    # Load model
                    st.info(f"Loading {model_size} model...")
                    model = whisper.load_model(model_size)
                    
                    # Try standard transcription first
                    try:
                        result = model.transcribe(temp_path, verbose=True)
                        
                        if show_timestamps:
                            # Display timestamped transcript
                            display_timestamped_transcript(result["segments"])
                            
                            # Download options
                            st.subheader("💾 Download Options")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Simple transcript
                                simple_transcript = result["text"]
                                st.download_button(
                                    "📄 Download Simple Transcript",
                                    simple_transcript,
                                    file_name=f"transcript_{audio_file.name}.txt",
                                    mime="text/plain"
                                )
                            
                            with col2:
                                # Timestamped transcript
                                timestamped_text = ""
                                for segment in result["segments"]:
                                    start = format_timestamp(segment["start"])
                                    end = format_timestamp(segment["end"])
                                    text = segment["text"].strip()
                                    timestamped_text += f"[{start}-{end}] {text}\n\n"
                                
                                st.download_button(
                                    "⏰ Download Timestamped Transcript",
                                    timestamped_text,
                                    file_name=f"timestamped_{audio_file.name}.txt",
                                    mime="text/plain"
                                )
                        else:
                            # Simple transcript display
                            st.subheader("📝 Transcript")
                            st.text_area("Generated Transcript", result["text"], height=300)
                        
                        # Video generation section
                        if generate_video and 'face_image' in locals() and face_image:
                            st.header("🎬 Video Generation")
                            st.info("🚧 Video generation feature coming soon in 2025!")
                            st.write("Features will include:")
                            st.write("• 🎭 AI avatar animation")
                            st.write("• 🎨 Auto background generation") 
                            st.write("• 🎵 Lip-sync technology")
                            st.write("• 📱 Social media formats")
                            
                            if st.button("🎥 Generate Video (Demo)", disabled=True):
                                st.balloons()
                                st.success("🎉 Video generation will be available soon!")
                    
                    except Exception as e:
                        st.warning("Standard transcription failed, trying fallback method...")
                        # Use fallback audio loading
                        audio_data = load_audio_fallback(temp_path)
                        if audio_data is not None:
                            result = model.transcribe(audio_data)
                            st.text_area("Generated Transcript", result["text"], height=200)
                        else:
                            raise e
                    
                    # Cleanup
                    os.unlink(temp_path)
                    
                except Exception as e:
                    st.error(f"❌ Error processing audio: {str(e)}")
                    st.info("💡 Try uploading a different audio format (WAV recommended)")
                    
                    # Cleanup on error
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

    # About section
    st.header("🤖 About This AI Tool")
    st.write("""
    **Welcome to 2025's no-code AI revolution!** 🚀
    
    This tool demonstrates how anyone can build powerful AI applications without coding:
    
    🎯 **What it does:**
    • Converts audio to text using OpenAI's Whisper
    • Creates timestamped transcripts automatically
    • Prepares content for video generation
    
    🔮 **Coming in 2025:**
    • AI avatar video generation
    • Multi-language support
    • Real-time processing
    • Social media integration
    """)
    
    st.divider()
    st.markdown("Made with ❤️ using AI automation tools • 2025")

if __name__ == "__main__":
    main()