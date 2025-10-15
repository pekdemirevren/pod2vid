import streamlit as st
import os
import tempfile
from pathlib import Path

# Lightweight imports
try:
    import whisper
    WHISPER_AVAILABLE = True
except:
    WHISPER_AVAILABLE = False
    st.error("Whisper not available in cloud environment")

def main():
    st.title("🎙️ Audio Transcript Generator (Cloud)")
    st.write("Lightweight version for cloud deployment")
    
    # File upload
    audio_file = st.file_uploader(
        "Upload audio file", 
        type=['mp3', 'wav', 'm4a'],
        help="Max 200MB for cloud deployment"
    )
    
    if audio_file:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            tmp.write(audio_file.read())
            temp_path = tmp.name
        
        if st.button("Generate Transcript"):
            if WHISPER_AVAILABLE:
                with st.spinner("Processing..."):
                    model = whisper.load_model("tiny")  # Use tiny model for cloud
                    result = model.transcribe(temp_path)
                    
                    # Display results
                    st.success("Transcript generated!")
                    st.text_area("Transcript", result["text"], height=300)
                    
                    # Download option
                    transcript_data = result["text"]
                    st.download_button(
                        "Download Transcript",
                        transcript_data,
                        file_name="transcript.txt",
                        mime="text/plain"
                    )
            else:
                st.error("Whisper model not available")
        
        # Cleanup
        os.unlink(temp_path)

if __name__ == "__main__":
    main()