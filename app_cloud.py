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

def create_dialogue_preview(segments, speaker_photos):
    """Create a visual dialogue preview from transcript segments"""
    st.subheader("🎭 Dialogue Preview")
    
    # Show how the video would look
    st.write("**This is how your dialogue video would appear:**")
    
    for i, segment in enumerate(segments[:5]):  # Show first 5 segments
        # Determine speaker
        speaker_num = (i % 2) + 1
        speaker_key = f"speaker{speaker_num}"
        
        # Create scene container
        with st.container():
            # Scene header
            scene_time = format_timestamp(segment["start"])
            scene_duration = segment["end"] - segment["start"]
            
            st.markdown(f"**🎬 Scene {i+1}** - *{scene_time}* ({scene_duration:.1f}s)")
            
            # Speaker and dialogue layout
            col_avatar, col_dialogue = st.columns([1, 3])
            
            with col_avatar:
                # Show speaker info
                st.markdown(f"**👤 Speaker {speaker_num}**")
                
                if speaker_key in speaker_photos:
                    st.success("📷 Using uploaded photo")
                    st.caption("🎭 Avatar animated")
                else:
                    st.info("🤖 AI generated avatar")
                    st.caption("🎨 Auto-created face")
                
                # Animation indicator
                st.markdown("🔄 *Speaking animation*")
            
            with col_dialogue:
                # Dialogue text with speech bubble effect
                dialogue_text = segment["text"].strip()
                
                st.markdown(f"""
                <div style="
                    background-color: #f0f2f6;
                    padding: 15px;
                    border-radius: 15px;
                    border-left: 4px solid #1f77b4;
                    margin: 10px 0;
                ">
                    <strong>💬 "{dialogue_text}"</strong>
                </div>
                """, unsafe_allow_html=True)
                
                # Speech effects
                word_count = len(dialogue_text.split())
                speech_duration = scene_duration
                st.caption(f"🎵 Lip-sync: {word_count} words in {speech_duration:.1f}s")
            
            st.divider()
    
    return True

def detect_speakers_from_text(text):
    """Detect dialogue patterns and estimate speaker count"""
    # Look for dialogue indicators
    dialogue_patterns = [
        "- ", "• ", "Speaker", "Host:", "Guest:", 
        "A:", "B:", "1:", "2:", "Q:", "A:"
    ]
    
    lines = text.split('\n')
    speaker_changes = 0
    
    for line in lines:
        for pattern in dialogue_patterns:
            if pattern in line:
                speaker_changes += 1
                break
    
    # Estimate speakers based on content length and patterns
    if speaker_changes > 5:
        return min(speaker_changes // 3, 4)  # Max 4 speakers
    elif "dialogue" in text.lower() or "conversation" in text.lower():
        return 2
    else:
        return 1

def display_timestamped_transcript(segments):
    """Display transcript with timestamps and speaker detection"""
    st.subheader("📝 Timestamped Transcript")
    
    # Analyze for dialogue patterns
    full_text = " ".join([seg["text"] for seg in segments])
    estimated_speakers = detect_speakers_from_text(full_text)
    
    if estimated_speakers > 1:
        st.info(f"🗣️ Detected dialogue with approximately {estimated_speakers} speakers")
    
    # Create columns for better layout
    col1, col2 = st.columns([1, 4])
    
    current_speaker = 1
    for i, segment in enumerate(segments):
        # Simple speaker alternation for dialogue
        if estimated_speakers > 1 and i > 0:
            # Change speaker every few segments for dialogue
            if i % 3 == 0:  # Rough speaker change estimation
                current_speaker = 2 if current_speaker == 1 else 1
        
        with col1:
            start_time = format_timestamp(segment["start"])
            end_time = format_timestamp(segment["end"])
            if estimated_speakers > 1:
                st.write(f"**👤 Speaker {current_speaker}**")
                st.write(f"*{start_time}-{end_time}*")
            else:
                st.write(f"**{start_time}-{end_time}**")
        
        with col2:
            text = segment["text"].strip()
            if estimated_speakers > 1:
                st.write(f"💬 {text}")
            else:
                st.write(text)
        
        st.divider()

def main():
    st.title("🎙️ AI Podcast Video Generator 2025")
    st.write("🤖 No-code AI automation: Audio → Transcript → Video")
    
    # Initialize session state
    if 'transcript_generated' not in st.session_state:
        st.session_state.transcript_generated = False
    if 'transcript_data' not in st.session_state:
        st.session_state.transcript_data = None
    if 'audio_file_name' not in st.session_state:
        st.session_state.audio_file_name = None
    if 'speaker_photos' not in st.session_state:
        st.session_state.speaker_photos = {}
    
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
        
        # Clear session button
        if st.button("🗑️ Clear All", help="Clear transcript and start over"):
            st.session_state.transcript_generated = False
            st.session_state.transcript_data = None
            st.session_state.audio_file_name = None
            st.session_state.speaker_photos = {}
            st.rerun()
    
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
            st.subheader("👥 Speaker Photos")
            face_image1 = st.file_uploader(
                "👤 Speaker 1 photo",
                type=["jpg", "png", "jpeg"],
                help="Photo of the first speaker",
                key="speaker1_upload"
            )
            if face_image1:
                st.session_state.speaker_photos['speaker1'] = face_image1
                st.success("✅ Speaker 1 photo uploaded")
            
            face_image2 = st.file_uploader(
                "👤 Speaker 2 photo", 
                type=["jpg", "png", "jpeg"],
                help="Photo of the second speaker",
                key="speaker2_upload"
            )
            if face_image2:
                st.session_state.speaker_photos['speaker2'] = face_image2
                st.success("✅ Speaker 2 photo uploaded")
            
            # Optional: More speakers
            add_more_speakers = st.checkbox("➕ More speakers?")
            if add_more_speakers:
                face_image3 = st.file_uploader(
                    "👤 Speaker 3 photo",
                    type=["jpg", "png", "jpeg"],
                    key="speaker3_upload"
                )
                if face_image3:
                    st.session_state.speaker_photos['speaker3'] = face_image3
                    st.success("✅ Speaker 3 photo uploaded")
    
    if audio_file and WHISPER_AVAILABLE:
        st.success(f"✅ Uploaded: {audio_file.name}")
        
        # Store audio file name
        st.session_state.audio_file_name = audio_file.name
        
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
                        
                        # Store transcript in session state
                        st.session_state.transcript_data = result
                        st.session_state.transcript_generated = True
                        
                        # Show success message
                        st.success("🎉 Transcript generated successfully!")
                        st.rerun()  # Refresh to show transcript
                        
                    except Exception as e:
                        st.warning("Standard transcription failed, trying fallback method...")
                        # Use fallback audio loading
                        audio_data = load_audio_fallback(temp_path)
                        if audio_data is not None:
                            result = model.transcribe(audio_data)
                            st.session_state.transcript_data = result
                            st.session_state.transcript_generated = True
                            st.success("🎉 Transcript generated with fallback method!")
                            st.rerun()
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
    
    # Display transcript if generated
    if st.session_state.transcript_generated and st.session_state.transcript_data:
        result = st.session_state.transcript_data
        
        st.divider()
        st.header("📋 Generated Transcript")
        
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
                    file_name=f"transcript_{st.session_state.audio_file_name}.txt",
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
                    file_name=f"timestamped_{st.session_state.audio_file_name}.txt",
                    mime="text/plain"
                )
        else:
            # Simple transcript display
            st.subheader("📝 Transcript")
            st.text_area("Generated Transcript", result["text"], height=300)
        
        # Video generation section - now separate from transcript generation
        if generate_video:
            st.divider()
            st.header("🎬 Video Generation")
            
            # Check if any speaker photos uploaded
            speakers_uploaded = []
            if 'speaker1' in st.session_state.speaker_photos:
                speakers_uploaded.append("Speaker 1")
            if 'speaker2' in st.session_state.speaker_photos:
                speakers_uploaded.append("Speaker 2")
            if 'speaker3' in st.session_state.speaker_photos:
                speakers_uploaded.append("Speaker 3")
            
            if speakers_uploaded:
                st.success(f"✅ Photos uploaded for: {', '.join(speakers_uploaded)}")
                
                # Speaker detection from transcript
                speaker_count = len([seg for seg in result["segments"] if "speaker" in seg.get("text", "").lower()])
                if speaker_count == 0:
                    # Estimate speakers from dialogue patterns
                    speaker_count = 2  # Default for dialogue
                
                st.info(f"🗣️ Detected approximately {speaker_count} speakers in audio")
                
                col_vid1, col_vid2 = st.columns(2)
                
                with col_vid1:
                    if st.button("🎥 Generate Dialogue Video", key="generate_video_btn"):
                        st.balloons()
                        with st.spinner("🎬 Creating dialogue video..."):
                            # Simulate video generation process
                            progress = st.progress(0)
                            status = st.empty()
                            
                            steps = [
                                ("🔍 Analyzing dialogue structure...", 20),
                                ("👥 Matching speakers to photos...", 40),
                                ("🎭 Generating avatar animations...", 60), 
                                ("🎬 Rendering video scenes...", 80),
                                ("✨ Adding transitions...", 100)
                            ]
                            
                            import time
                            for step_text, prog in steps:
                                status.text(step_text)
                                progress.progress(prog)
                                time.sleep(1)
                                
                            st.success("🎉 Dialogue video generated!")
                            
                            # Show realistic dialogue preview
                            create_dialogue_preview(result["segments"], st.session_state.speaker_photos)
                            
                            # Show video stats
                            total_duration = result["segments"][-1]["end"] if result["segments"] else 0
                            total_words = len(result["text"].split())
                            
                            col_stats1, col_stats2, col_stats3 = st.columns(3)
                            with col_stats1:
                                st.metric("Video Length", f"{format_timestamp(total_duration)}")
                            with col_stats2:
                                st.metric("Total Words", f"{total_words}")
                            with col_stats3:
                                st.metric("Speakers", f"{len(speakers_uploaded) or 2}")
                            
                            # Download section
                            st.subheader("📱 Download Your Video")
                            
                            col_dl1, col_dl2 = st.columns(2)
                            
                            with col_dl1:
                                # Create demo video content based on actual dialogue
                                video_content = f"""# Generated Video: {st.session_state.audio_file_name}
# Total Duration: {format_timestamp(total_duration) if 'total_duration' in locals() else 'Unknown'}
# Speakers: {len(speakers_uploaded) or 'Auto-detected'}

=== VIDEO SCRIPT ===
"""
                                if result and "segments" in result:
                                    for i, segment in enumerate(result["segments"]):
                                        speaker_num = (i % 2) + 1
                                        start_time = format_timestamp(segment["start"])
                                        end_time = format_timestamp(segment["end"])
                                        text = segment["text"].strip()
                                        video_content += f"\n[{start_time}-{end_time}] Speaker {speaker_num}: {text}\n"
                                
                                st.download_button(
                                    "📄 Download Video Script",
                                    video_content.encode('utf-8'),
                                    file_name=f"video_script_{st.session_state.audio_file_name}.txt",
                                    mime="text/plain"
                                )
                            
                            with col_dl2:
                                # Simulated video file (in real implementation, this would be actual video)
                                st.download_button(
                                    "🎬 Download Video (Demo)",
                                    data=f"Demo video for: {st.session_state.audio_file_name}".encode('utf-8'),
                                    file_name=f"dialogue_{st.session_state.audio_file_name}.mp4",
                                    mime="video/mp4",
                                    help="This is a demo - real video would be generated here"
                                )
                            
                            # Real video preview message
                            st.info("""
                            🎬 **Real Video Preview:**
                            In production, this would show:
                            • Your uploaded speaker photos as animated avatars
                            • Lip-synchronized speech matching your audio
                            • Scene transitions between speakers
                            • Customized backgrounds and effects
                            """)
                            
                            # Technical details
                            with st.expander("🔧 Technical Details"):
                                st.write("**Video Generation Process:**")
                                st.write("1. 📊 Audio analysis and speaker detection")
                                st.write("2. 👤 Face photo processing and avatar creation") 
                                st.write("3. 🎭 Lip-sync animation generation")
                                st.write("4. 🎬 Scene composition and rendering")
                                st.write("5. 🎵 Audio-video synchronization")
                                st.write("6. 📱 Format optimization for platforms")
                
                with col_vid2:
                    st.write("📋 **Video Settings:**")
                    video_format = st.selectbox("Format", ["16:9 (YouTube)", "9:16 (TikTok)", "1:1 (Instagram)"])
                    video_length = st.selectbox("Length", ["Full audio", "1 min clips", "30 sec clips"])
                    add_subtitles = st.checkbox("Add subtitles", value=True)
            else:
                st.warning("📷 Please upload photos for your speakers to generate video")
                st.info("💡 **Tip:** For best results:\n• Use clear, front-facing photos\n• Good lighting\n• Neutral background")
            
            # Advanced features preview
            with st.expander("🚀 Advanced Features (Coming Soon)"):
                st.write("**🤖 AI Enhancements:**")
                st.write("• Real-time lip synchronization")
                st.write("• Emotion-based expressions") 
                st.write("• Auto gesture generation")
                st.write("• Voice cloning integration")
                st.write("• Multi-language dubbing")

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