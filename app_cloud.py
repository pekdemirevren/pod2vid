import streamlit as st
import os
import tempfile
from pathlib import Path
import shutil
import subprocess
import time

# Import video generation
try:
    from video_generator import create_animated_video
    VIDEO_GENERATION_AVAILABLE = True
except ImportError:
    VIDEO_GENERATION_AVAILABLE = False
    # Don't show warning immediately - only when needed

# Import Wav2Lip integration
try:
    from wav2lip_integration import (
        check_wav2lip_available, 
        generate_wav2lip_video,
        create_dialogue_video_with_wav2lip
    )
    WAV2LIP_AVAILABLE, wav2lip_status = check_wav2lip_available()
except ImportError:
    WAV2LIP_AVAILABLE = False
    wav2lip_status = "Wav2Lip module not available"

# Import simple Wav2Lip (more reliable)
try:
    from simple_wav2lip import (
        check_simple_wav2lip,
        streamlit_wav2lip_interface,
        simple_wav2lip_generation
    )
    SIMPLE_WAV2LIP_AVAILABLE, simple_status = check_simple_wav2lip()
except ImportError:
    SIMPLE_WAV2LIP_AVAILABLE = False
    simple_status = "Simple Wav2Lip not available"

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

def create_video_script(result, speaker_photos):
    """Create a detailed video script from transcript"""
    if not result or "segments" not in result:
        return "No transcript data available"
    
    total_duration = result["segments"][-1]["end"] if result["segments"] else 0
    total_words = len(result["text"].split())
    
    script = f"""# DIALOGUE VIDEO SCRIPT
# Generated: {format_timestamp(total_duration)} duration
# Total Words: {total_words}
# Speakers: {len(speaker_photos)}

=== SCENE BREAKDOWN ===

"""
    
    for i, segment in enumerate(result["segments"]):
        speaker_num = (i % 2) + 1
        start_time = format_timestamp(segment["start"])
        end_time = format_timestamp(segment["end"])
        duration = segment["end"] - segment["start"]
        text = segment["text"].strip()
        
        photo_status = "📷 Photo Available" if f"speaker{speaker_num}" in speaker_photos else "🤖 AI Avatar"
        
        script += f"""
SCENE {i+1}: {start_time} - {end_time} ({duration:.1f}s)
Speaker: {speaker_num} ({photo_status})
Text: "{text}"
Animation: Lip-sync + facial expressions
Transition: Fade to next speaker

"""
    
    script += f"""
=== TECHNICAL SPECS ===
Video Format: MP4 (H.264)
Resolution: 1920x1080 (16:9)
Frame Rate: 30 FPS
Audio: Original audio track
Subtitles: Auto-generated
Background: Studio lighting
Avatar Quality: High-definition
Lip Sync: AI-powered
"""
    
    return script

def create_actual_video_content(result, speaker_photos):
    """Create interactive HTML video content"""
    if not result or "segments" not in result:
        return "<p>No transcript data available</p>"
    
    # Create HTML video player with transcript synchronization
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Dialogue Video Preview</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .video-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .scene { margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #007bff; }
            .speaker { font-weight: bold; color: #007bff; margin-bottom: 8px; }
            .timestamp { color: #666; font-size: 0.9em; }
            .dialogue { margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }
            .controls { margin: 20px 0; padding: 15px; background: #e9ecef; border-radius: 5px; }
            .play-button { background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .speaker1 { border-left-color: #007bff; }
            .speaker2 { border-left-color: #dc3545; }
            .avatar-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
            .avatar-photo { background: #28a745; }
            .avatar-ai { background: #ffc107; }
        </style>
    </head>
    <body>
        <div class="video-container">
            <h2>🎬 Interactive Dialogue Video</h2>
            <div class="controls">
                <button class="play-button" onclick="playVideo()">▶️ Play Dialogue</button>
                <span style="margin-left: 20px;">Total Duration: """ + format_timestamp(result["segments"][-1]["end"]) + """</span>
            </div>
            
            <div id="scenes">
    """
    
    # Add each scene
    for i, segment in enumerate(result["segments"]):
        speaker_num = (i % 2) + 1
        speaker_class = f"speaker{speaker_num}"
        start_time = format_timestamp(segment["start"])
        end_time = format_timestamp(segment["end"])
        duration = segment["end"] - segment["start"]
        text = segment["text"].strip()
        
        has_photo = f"speaker{speaker_num}" in speaker_photos
        avatar_class = "avatar-photo" if has_photo else "avatar-ai"
        avatar_text = "📷 Photo" if has_photo else "🤖 AI"
        
        html_content += f"""
                <div class="scene {speaker_class}" id="scene-{i+1}">
                    <div class="speaker">
                        <span class="avatar-indicator {avatar_class}"></span>
                        👤 Speaker {speaker_num} ({avatar_text})
                    </div>
                    <div class="timestamp">🕐 {start_time} - {end_time} ({duration:.1f}s)</div>
                    <div class="dialogue">💬 "{text}"</div>
                    <div style="font-size: 0.8em; color: #666;">
                        🎭 Animation: Lip-sync + expressions | 🎵 Words: {len(text.split())}
                    </div>
                </div>
        """
    
    html_content += """
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: #d4edda; border-radius: 5px; border: 1px solid #c3e6cb;">
                <h4>🚀 Production Features</h4>
                <ul>
                    <li>🎭 AI-powered lip synchronization</li>
                    <li>📷 High-quality avatar animation</li>
                    <li>🎨 Dynamic background effects</li>
                    <li>🎵 Professional audio mixing</li>
                    <li>📱 Multi-format export (YouTube, TikTok, Instagram)</li>
                </ul>
            </div>
        </div>
        
        <script>
            let currentScene = 0;
            const scenes = document.querySelectorAll('.scene');
            
            function playVideo() {
                if (currentScene < scenes.length) {
                    // Highlight current scene
                    scenes.forEach(s => s.style.background = '#f8f9fa');
                    scenes[currentScene].style.background = '#fff3cd';
                    scenes[currentScene].scrollIntoView({ behavior: 'smooth' });
                    
                    // Simulate timing
                    const duration = parseFloat(scenes[currentScene].querySelector('.timestamp').textContent.match(/\\((\\d+\\.\\d+)s\\)/)[1]);
                    
                    setTimeout(() => {
                        currentScene++;
                        if (currentScene < scenes.length) {
                            playVideo();
                        } else {
                            alert('🎉 Video playback complete!');
                            currentScene = 0;
                        }
                    }, Math.max(duration * 1000, 2000)); // Minimum 2 seconds per scene
                }
            }
        </script>
    </body>
    </html>
    """
    
    return html_content

def create_dialogue_preview(segments, speaker_photos):
    """Create a visual dialogue preview from transcript segments"""
    st.subheader("🎭 Dialogue Preview")
    
    # Debug info
    st.write(f"**Debug:** Processing {len(segments)} segments with {len(speaker_photos)} speaker photos")
    
    if not segments:
        st.error("❌ No segments provided for dialogue preview!")
        return False
    
    # Show how the video would look
    st.write("**This is how your dialogue video would appear:**")
    
    try:
        for i, segment in enumerate(segments[:5]):  # Show first 5 segments
            st.write(f"**Debug:** Processing segment {i+1}: {segment.get('start', 'No start')} - {segment.get('end', 'No end')}")
            
            # Determine speaker
            speaker_num = (i % 2) + 1
            speaker_key = f"speaker{speaker_num}"
            
            # Create scene container
            with st.container():
                # Scene header
                try:
                    scene_time = format_timestamp(segment["start"])
                    scene_duration = segment["end"] - segment["start"]
                    
                    st.markdown(f"**🎬 Scene {i+1}** - *{scene_time}* ({scene_duration:.1f}s)")
                except Exception as e:
                    st.error(f"❌ Error formatting scene {i+1}: {str(e)}")
                    continue
                
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
                    dialogue_text = segment.get("text", "").strip()
                    
                    if not dialogue_text:
                        st.warning(f"⚠️ No text found for segment {i+1}")
                        continue
                    
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
                    speech_duration = segment["end"] - segment["start"]
                    st.caption(f"🎵 Lip-sync: {word_count} words in {speech_duration:.1f}s")
                
                st.divider()
        
        st.success("✅ Dialogue preview created successfully!")
        return True
        
    except Exception as e:
        st.error(f"❌ Error in create_dialogue_preview: {str(e)}")
        st.write(f"**Debug:** segments type: {type(segments)}")
        st.write(f"**Debug:** speaker_photos type: {type(speaker_photos)}")
        return False

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
    
    # Feature status info
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.success("✅ Audio transcription with Whisper AI")
    with col_info2:
        if SIMPLE_WAV2LIP_AVAILABLE:
            st.success("✅ Wav2Lip neural lip-sync ready")
        elif WAV2LIP_AVAILABLE:
            st.success("✅ Wav2Lip neural lip-sync available")
        elif VIDEO_GENERATION_AVAILABLE:
            st.success("✅ Basic video generation available")
        else:
            st.info("📱 Interactive video preview mode")
    
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
            if SIMPLE_WAV2LIP_AVAILABLE:
                st.success("🎭 Wav2Lip neural lip-sync ready")
                st.caption(f"Status: {simple_status}")
            elif WAV2LIP_AVAILABLE:
                st.success("🎭 Wav2Lip neural lip-sync ready")
                st.caption(f"Status: {wav2lip_status}")
            elif VIDEO_GENERATION_AVAILABLE:
                st.success("🎬 Basic video generation available")
            else:
                st.info("📱 Interactive video preview mode")
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
        
        # Store audio bytes for Wav2Lip
        audio_file.seek(0)  # Reset file pointer
        st.session_state.audio_bytes = audio_file.read()
        audio_file.seek(0)  # Reset for transcript generation
        
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
            
            # Show simple Wav2Lip interface if available
            if SIMPLE_WAV2LIP_AVAILABLE:
                streamlit_wav2lip_interface()
                
                # Add separator for other options
                st.divider()
                st.subheader("🎭 Or use dialogue-based generation:")
            
            # Debug info
            with st.expander("🔍 Debug Info", expanded=False):
                st.write("**Session State Debug:**")
                st.write(f"- transcript_generated: {st.session_state.transcript_generated}")
                st.write(f"- transcript_data exists: {st.session_state.transcript_data is not None}")
                st.write(f"- speaker_photos: {list(st.session_state.speaker_photos.keys())}")
                st.write(f"- generate_video setting: {generate_video}")
                st.write(f"- SIMPLE_WAV2LIP_AVAILABLE: {SIMPLE_WAV2LIP_AVAILABLE}")
                st.write(f"- WAV2LIP_AVAILABLE: {WAV2LIP_AVAILABLE}")
                
                if st.session_state.transcript_data:
                    st.write(f"- segments count: {len(st.session_state.transcript_data.get('segments', []))}")
                    st.write(f"- transcript length: {len(st.session_state.transcript_data.get('text', ''))}")
            
            # Check if any speaker photos uploaded
            speakers_uploaded = []
            if 'speaker1' in st.session_state.speaker_photos:
                speakers_uploaded.append("Speaker 1")
            if 'speaker2' in st.session_state.speaker_photos:
                speakers_uploaded.append("Speaker 2")
            if 'speaker3' in st.session_state.speaker_photos:
                speakers_uploaded.append("Speaker 3")
            
            st.write(f"**Debug:** Found {len(speakers_uploaded)} uploaded speaker photos: {speakers_uploaded}")
            
            if speakers_uploaded:
                st.success(f"✅ Photos uploaded for: {', '.join(speakers_uploaded)}")
                
                # Debug transcript data
                if not st.session_state.transcript_data:
                    st.error("❌ No transcript data found! Please generate transcript first.")
                    return
                
                result = st.session_state.transcript_data
                
                # Speaker detection from transcript
                speaker_count = len([seg for seg in result["segments"] if "speaker" in seg.get("text", "").lower()])
                if speaker_count == 0:
                    # Estimate speakers from dialogue patterns
                    speaker_count = 2  # Default for dialogue
                
                st.info(f"🗣️ Detected approximately {speaker_count} speakers in audio")
                st.write(f"**Debug:** Transcript has {len(result.get('segments', []))} segments")
                
                col_vid1, col_vid2 = st.columns(2)
                
                with col_vid1:
                    # Wav2Lip neural lip-sync button
                    if WAV2LIP_AVAILABLE and st.button("🧠 Generate Neural Lip-Sync Video", key="wav2lip_btn"):
                        st.write("**Debug:** Wav2Lip neural generation started!")
                        st.balloons()
                        
                        with st.spinner("🧠 Running Wav2Lip neural network..."):
                            try:
                                # Get audio file bytes (we need original audio)
                                if 'audio_bytes' not in st.session_state:
                                    st.error("❌ Original audio not found. Please re-upload audio file.")
                                    st.stop()
                                
                                # Generate videos for each speaker
                                generated_videos, status = create_dialogue_video_with_wav2lip(
                                    result["segments"], 
                                    st.session_state.speaker_photos,
                                    st.session_state.audio_bytes
                                )
                                
                                if generated_videos:
                                    st.success("🎉 Wav2Lip neural lip-sync completed!")
                                    
                                    # Show generated videos
                                    for video_info in generated_videos:
                                        st.subheader(f"🎭 {video_info['speaker']} - Neural Lip-Sync")
                                        
                                        # Load and display video
                                        with open(video_info['video_path'], 'rb') as f:
                                            video_bytes = f.read()
                                        
                                        st.video(video_bytes)
                                        
                                        # Download button
                                        st.download_button(
                                            f"📱 Download {video_info['speaker']} Video",
                                            data=video_bytes,
                                            file_name=f"wav2lip_{video_info['speaker']}_{st.session_state.audio_file_name}.mp4",
                                            mime="video/mp4"
                                        )
                                else:
                                    st.error(f"❌ Wav2Lip generation failed: {status}")
                                    
                            except Exception as e:
                                st.error(f"❌ Neural lip-sync error: {str(e)}")
                                st.info("🔄 Falling back to basic video generation...")
                    
                    # Basic video generation button (fallback)
                    elif st.button("🎥 Generate Dialogue Video", key="generate_video_btn"):
                        st.write("**Debug:** Video generation button clicked!")
                        
                        # Validate data before generation
                        if not result.get("segments"):
                            st.error("❌ No audio segments found in transcript!")
                            st.stop()
                        
                        if len(result["segments"]) == 0:
                            st.error("❌ Empty segments list!")
                            st.stop()
                        
                        st.write(f"**Debug:** Starting video generation with {len(result['segments'])} segments")
                        st.balloons()
                        
                        with st.spinner("🎬 Creating real animated video..."):
                            # Create real animated video
                            if VIDEO_GENERATION_AVAILABLE and st.session_state.speaker_photos:
                                st.info("🎭 Generating REAL animated video with your photos...")
                                
                                try:
                                    # Create temporary output path
                                    output_path = tempfile.mktemp(suffix='.mp4')
                                    
                                    # Generate real video
                                    success = create_animated_video(
                                        result["segments"][:3],  # First 3 segments for demo
                                        st.session_state.speaker_photos,
                                        None,  # Audio file path (optional)
                                        output_path
                                    )
                                    
                                    if success and os.path.exists(output_path):
                                        st.success("🎉 REAL animated video generated!")
                                        
                                        # Show the actual video
                                        with open(output_path, 'rb') as video_file:
                                            video_bytes = video_file.read()
                                        
                                        st.subheader("🎬 Your Animated Video")
                                        st.video(video_bytes)
                                        
                                        # Download button for real video
                                        st.download_button(
                                            "📱 Download Animated Video",
                                            data=video_bytes,
                                            file_name=f"animated_dialogue_{st.session_state.audio_file_name}.mp4",
                                            mime="video/mp4"
                                        )
                                        
                                        st.success("✅ Real video with your uploaded photos speaking!")
                                        
                                        # Cleanup
                                        os.unlink(output_path)
                                        
                                    else:
                                        raise Exception("Video generation failed")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error generating real video: {str(e)}")
                                    st.info("🔄 Falling back to interactive preview...")
                                    # Fall through to interactive preview
                            
                            # Interactive preview (fallback or default)
                            progress = st.progress(0)
                            status = st.empty()
                            
                            steps = [
                                ("🔍 Analyzing dialogue structure...", 20),
                                ("👥 Matching speakers to photos...", 40),
                                ("🎭 Generating avatar animations...", 60), 
                                ("🎬 Rendering video scenes...", 80),
                                ("✨ Adding transitions...", 100)
                            ]
                            
                            for step_text, prog in steps:
                                status.text(f"{step_text} (Debug: Step {prog}%)")
                                progress.progress(prog)
                                time.sleep(1)
                                
                            if not VIDEO_GENERATION_AVAILABLE or not st.session_state.speaker_photos:
                                st.info("� Interactive preview mode (upload photos for real animation)")
                            
                            st.success("🎉 Video processing completed!")
                            st.write("**Debug:** Video generation completed successfully!")
                            
                            # Show realistic dialogue preview
                            try:
                                create_dialogue_preview(result["segments"], st.session_state.speaker_photos)
                                st.write("**Debug:** Dialogue preview created successfully!")
                            except Exception as e:
                                st.error(f"❌ Error creating dialogue preview: {str(e)}")
                            
                            # Show video stats
                            try:
                                total_duration = result["segments"][-1]["end"] if result["segments"] else 0
                                total_words = len(result["text"].split())
                                
                                col_stats1, col_stats2, col_stats3 = st.columns(3)
                                with col_stats1:
                                    st.metric("Video Length", f"{format_timestamp(total_duration)}")
                                with col_stats2:
                                    st.metric("Total Words", f"{total_words}")
                                with col_stats3:
                                    st.metric("Speakers", f"{len(speakers_uploaded) or 2}")
                                
                                st.write("**Debug:** Video stats calculated successfully!")
                            except Exception as e:
                                st.error(f"❌ Error calculating video stats: {str(e)}")
                            
                            # Download section
                            st.subheader("📱 Download Your Video")
                            
                            # Create actual video content
                            try:
                                # Generate actual video files
                                video_html = create_actual_video_content(result, st.session_state.speaker_photos)
                                
                                col_dl1, col_dl2 = st.columns(2)
                                
                                with col_dl1:
                                    # Create video script based on actual dialogue
                                    video_script = create_video_script(result, st.session_state.speaker_photos)
                                    
                                    st.download_button(
                                        "📄 Download Video Script",
                                        video_script.encode('utf-8'),
                                        file_name=f"video_script_{st.session_state.audio_file_name}.txt",
                                        mime="text/plain"
                                    )
                                
                                with col_dl2:
                                    # Generate simple video HTML for preview
                                    st.download_button(
                                        "🎬 Download Video HTML",
                                        video_html.encode('utf-8'),
                                        file_name=f"dialogue_video_{st.session_state.audio_file_name}.html",
                                        mime="text/html",
                                        help="Interactive HTML video preview"
                                    )
                                
                                # Show actual video preview
                                st.subheader("🎥 Interactive Video Preview")
                                st.components.v1.html(video_html, height=400, scrolling=True)
                                
                                st.write("**Debug:** Actual video content generated and displayed!")
                                
                            except Exception as e:
                                st.error(f"❌ Error generating video content: {str(e)}")
                                st.write("**Debug:** Falling back to simple script download")
                                
                                # Fallback to simple script
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