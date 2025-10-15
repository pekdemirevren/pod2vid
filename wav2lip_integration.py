import os
import sys
import tempfile
import subprocess
from pathlib import Path
import streamlit as st

# Add Wav2Lip to path
wav2lip_path = Path(__file__).parent / "Wav2Lip"
sys.path.append(str(wav2lip_path))

def generate_wav2lip_video(face_image, audio_file, output_path):
    """
    Generate lip-synced video using Wav2Lip
    """
    try:
        # Check if checkpoint exists
        checkpoint_path = wav2lip_path / "checkpoints" / "wav2lip.pth"
        if not checkpoint_path.exists():
            # Try alternative checkpoint
            checkpoint_path = wav2lip_path / "wav2lip_gan.pth"
            if not checkpoint_path.exists():
                st.error("❌ Wav2Lip checkpoint not found!")
                return False
        
        # Save uploaded face image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as face_tmp:
            face_tmp.write(face_image.read())
            face_tmp_path = face_tmp.name
        
        # Save audio file temporarily  
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as audio_tmp:
            audio_tmp.write(audio_file.read())
            audio_tmp_path = audio_tmp.name
        
        # Prepare Wav2Lip command
        cmd = [
            sys.executable,
            str(wav2lip_path / "inference.py"),
            "--checkpoint_path", str(checkpoint_path),
            "--face", face_tmp_path,
            "--audio", audio_tmp_path,
            "--outfile", output_path,
            "--static", "True",  # Use static image
            "--face_det_batch_size", "1",  # Small batch for cloud
            "--wav2lip_batch_size", "32",  # Optimized for cloud
            "--resize_factor", "2"  # Reduce resolution for speed
        ]
        
        # Run Wav2Lip inference
        st.info("🎭 Running Wav2Lip neural network...")
        
        # Change to Wav2Lip directory
        original_cwd = os.getcwd()
        os.chdir(wav2lip_path)
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0:
                st.success("✅ Wav2Lip generation successful!")
                return True
            else:
                st.error(f"❌ Wav2Lip error: {result.stderr}")
                return False
                
        finally:
            # Restore original directory
            os.chdir(original_cwd)
            
            # Cleanup temp files
            try:
                os.unlink(face_tmp_path)
                os.unlink(audio_tmp_path)
            except:
                pass
        
    except subprocess.TimeoutExpired:
        st.error("❌ Wav2Lip generation timeout (>2 minutes)")
        return False
    except Exception as e:
        st.error(f"❌ Wav2Lip generation failed: {str(e)}")
        return False

def check_wav2lip_available():
    """Check if Wav2Lip is properly set up"""
    try:
        # Check if inference.py exists
        inference_path = wav2lip_path / "inference.py"
        if not inference_path.exists():
            return False, "inference.py not found"
        
        # Check if any checkpoint exists
        checkpoint_dir = wav2lip_path / "checkpoints"
        gan_checkpoint = wav2lip_path / "wav2lip_gan.pth"
        
        if checkpoint_dir.exists():
            checkpoints = list(checkpoint_dir.glob("*.pth"))
            if checkpoints:
                return True, f"Found checkpoint: {checkpoints[0].name}"
        
        if gan_checkpoint.exists():
            return True, f"Found checkpoint: {gan_checkpoint.name}"
        
        return False, "No checkpoints found"
        
    except Exception as e:
        return False, f"Error checking Wav2Lip: {str(e)}"

def create_dialogue_video_with_wav2lip(transcript_segments, speaker_photos, audio_bytes):
    """
    Create dialogue video using real Wav2Lip for each speaker
    """
    if not speaker_photos:
        return None, "No speaker photos uploaded"
    
    try:
        generated_videos = []
        
        # Process each speaker
        for speaker_key, photo_file in speaker_photos.items():
            st.info(f"🎭 Processing {speaker_key} with Wav2Lip...")
            
            # Create temporary output
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_video:
                output_path = tmp_video.name
            
            # Reset file pointer
            photo_file.seek(0)
            
            # Create audio file from bytes
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_audio:
                tmp_audio.write(audio_bytes)
                audio_file = tmp_audio
            
            # Generate lip-synced video
            success = generate_wav2lip_video(photo_file, audio_file, output_path)
            
            if success and os.path.exists(output_path):
                generated_videos.append({
                    'speaker': speaker_key,
                    'video_path': output_path
                })
                st.success(f"✅ {speaker_key} video generated!")
            else:
                st.warning(f"⚠️ Failed to generate video for {speaker_key}")
        
        return generated_videos, "Success"
        
    except Exception as e:
        return None, f"Error: {str(e)}"