import streamlit as st
import os
from main import generate_transcript

# ------------------------------
# Streamlit UI Setup
# ------------------------------
st.set_page_config(page_title="Podcast Video Generator", layout="centered")
st.title("🎙️ Podcast Video Generator")
st.write("Upload a podcast audio file, select character photos, and generate transcript + animated video.")

# ------------------------------
# File Upload
# ------------------------------
uploaded_audio = st.file_uploader("Upload your audio file (.wav or .mp3)", type=["wav", "mp3"])
uploaded_face1 = st.file_uploader("Upload Speaker 1 photo (face_1.jpg)", type=["jpg", "png"])
uploaded_face2 = st.file_uploader("Upload Speaker 2 photo (face_2.jpg)", type=["jpg", "png"])

audio_path = None
face1_path = None
face2_path = None

if uploaded_audio:
    audio_path = f"temp_{uploaded_audio.name}"
    with open(audio_path, "wb") as f:
        f.write(uploaded_audio.getbuffer())
    st.audio(audio_path)
    st.success("✅ Audio uploaded!")

if uploaded_face1:
    face1_path = f"temp_face1_{uploaded_face1.name}"
    with open(face1_path, "wb") as f:
        f.write(uploaded_face1.getbuffer())
    st.image(face1_path, caption="Speaker 1", width=150)

if uploaded_face2:
    face2_path = f"temp_face2_{uploaded_face2.name}"
    with open(face2_path, "wb") as f:
        f.write(uploaded_face2.getbuffer())
    st.image(face2_path, caption="Speaker 2", width=150)

# ------------------------------
# Generate Transcript
# ------------------------------
if audio_path:
    if st.button("Generate Transcript"):
        with st.spinner("Processing transcript... ⏳"):
            transcript_file = generate_transcript(audio_path)
            # Session state'e kaydet
            st.session_state.transcript_file = transcript_file
            st.success("✅ Transcript generated!")
            
            with open(transcript_file, "r", encoding="utf-8") as f:
                transcript_content = f.read()
            
            st.text_area("📝 Generated Transcript", transcript_content, height=400)
            
            # Download button
            with open(transcript_file, "rb") as f:
                st.download_button(
                    "💾 Download Transcript",
                    data=f,
                    file_name="transcript.txt",
                    mime="text/plain"
                )

# ------------------------------
# Generate Video
# ------------------------------
if audio_path and face1_path and face2_path:
    # Transcript dosyasının var olup olmadığını kontrol et
    if 'transcript_file' not in st.session_state:
        st.warning("⚠️ Please generate transcript first!")
    else:
        if st.button("Generate Animated Video"):
            with st.spinner("Generating video... this may take a few minutes ⏳"):
                try:
                    # Session state'ten transcript dosyasını al
                    transcript_file = st.session_state.transcript_file
                    
                    # Check if Wav2Lip model exists
                    wav2lip_model_path = "Wav2Lip/checkpoints/wav2lip_gan.pth"
                    if not os.path.exists(wav2lip_model_path):
                        st.error("❌ Wav2Lip model not found!")
                        st.info("📥 Download the model from: https://github.com/Rudrabha/Wav2Lip/releases")
                        st.code(f"Expected location: {wav2lip_model_path}")
                        st.stop()
                    
                    # Check model file size
                    model_size = os.path.getsize(wav2lip_model_path) / (1024*1024)  # MB
                    if model_size < 100:  # Less than 100MB
                        st.error(f"❌ Wav2Lip model file is too small ({model_size:.1f}MB)")
                        st.info("📥 Please download the complete model (~170MB)")
                        st.stop()
                    
                    # Burada main.py veya ayrı video_pipeline.py içindeki fonksiyon çağrılır
                    # Örnek:
                    from video_pipeline import generate_video
                    video_file = generate_video(audio_path, transcript_file, face1_path, face2_path)
                    
                    st.video(video_file)
                    with open(video_file, "rb") as f:
                        st.download_button(
                            "💾 Download Video",
                            data=f,
                            file_name="podcast_video.mp4",
                            mime="video/mp4"
                        )
                    st.success("✅ Video generated successfully!")
                except Exception as e:
                    st.error(f"❌ Error during video generation: {e}")

# ------------------------------
# Footer
# ------------------------------
st.markdown("---")
st.caption("Powered by Whisper + Pyannote + Wav2Lip + SadTalker • Built for Podcast Automation 🎧")

# Academic Credits
with st.expander("📚 Academic Citations & Credits"):
    st.markdown("""
    ### 🎙️ **Speaker Diarization: pyannote.audio**
    
    **Main Framework (2020):**
    ```
    @inproceedings{Bredin2020,
      Title = {{pyannote.audio: neural building blocks for speaker diarization}},
      Author = {{Bredin}, Hervé and {Yin}, Ruiqing and {Coria}, Juan Manuel 
                and {Gelly}, Gregory and {Korshunov}, Pavel and {Lavechin}, Marvin 
                and {Fustes}, Diego and {Titeux}, Hadrien and {Bouaziz}, Wassim 
                and {Gill}, Marie-Philippe},
      Booktitle = {ICASSP 2020, IEEE International Conference on Acoustics, Speech, and Signal Processing},
      Address = {Barcelona, Spain},
      Month = {May},
      Year = {2020},
    }
    ```
    
    **Overlap-Aware Resegmentation (2021):**
    ```
    @inproceedings{Bredin2021,
      Title = {{End-to-end speaker segmentation for overlap-aware resegmentation}},
      Author = {{Bredin}, Hervé and {Laurent}, Antoine},
      Booktitle = {Proc. Interspeech 2021},
      Address = {Brno, Czech Republic},
      Month = {August},
      Year = {2021},
    }
    ```
    
    ### 🗣️ **Speech Recognition: OpenAI Whisper**  
    ```
    @misc{radford2022whisper,
      title={Robust Speech Recognition via Large-Scale Weak Supervision},
      author={Radford, Alec and Kim, Jong Wook and Xu, Tao and others},
      year={2022},
      eprint={2212.04356},
      archivePrefix={arXiv},
    }
    ```
    
    ### 🎬 **Lip Sync: Wav2Lip**
    ```
    @inproceedings{prajwal2020lip,
      title={A Lip Sync Expert Is All You Need for Speech to Lip Generation In The Wild},
      author={Prajwal, K R and Mukhopadhyay, Rudrabha and Namboodiri, Vinay P. and Jawahar, C.V.},
      booktitle={Proceedings of the 28th ACM International Conference on Multimedia},
      year={2020}
    }
    ```
    
    **Special thanks to the open-source AI research community! 🙏**
    """)

st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em; margin-top: 20px;'>
    <p>🔬 Built with state-of-the-art AI models • Research meets Production</p>
</div>
""", unsafe_allow_html=True)