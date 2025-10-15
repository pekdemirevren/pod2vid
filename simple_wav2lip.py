import streamlit as st
import subprocess
import os
from tempfile import NamedTemporaryFile
import tempfile
from pathlib import Path

def simple_wav2lip_generation(face_file, audio_file, output_path):
    """
    Simple and efficient Wav2Lip generation
    """
    try:
        # Get current directory and Wav2Lip path
        current_dir = Path(__file__).parent
        wav2lip_dir = current_dir / "Wav2Lip"
        
        # Check checkpoint
        checkpoint_path = wav2lip_dir / "checkpoints" / "wav2lip.pth"
        if not checkpoint_path.exists():
            checkpoint_path = wav2lip_dir / "Wav2Lip_gan.pth"
            if not checkpoint_path.exists():
                return False, "No checkpoint found"
        
        # Create temporary files
        with NamedTemporaryFile(delete=False, suffix=".jpg") as face_tmp:
            face_tmp.write(face_file.read())
            face_path = face_tmp.name

        with NamedTemporaryFile(delete=False, suffix=".wav") as audio_tmp:
            audio_tmp.write(audio_file.read())
            audio_path = audio_tmp.name

        # Build command
        cmd = [
            "python", str(wav2lip_dir / "inference.py"),
            "--checkpoint_path", str(checkpoint_path),
            "--face", face_path,
            "--audio", audio_path,
            "--outfile", output_path,
            "--static", "True",  # Use static image for efficiency
            "--face_det_batch_size", "1",  # Minimal batch size
            "--wav2lip_batch_size", "16"   # Small batch for CPU
        ]
        
        # Change to Wav2Lip directory
        original_cwd = os.getcwd()
        os.chdir(wav2lip_dir)
        
        try:
            # Run inference
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=180  # 3 minute timeout
            )
            
            success = result.returncode == 0 and os.path.exists(output_path)
            
            if not success:
                return False, f"Generation failed: {result.stderr}"
            
            return True, "Success"
            
        finally:
            # Cleanup
            os.chdir(original_cwd)
            try:
                os.unlink(face_path)
                os.unlink(audio_path)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        return False, "Timeout (>3 minutes)"
    except Exception as e:
        return False, f"Error: {str(e)}"

def streamlit_wav2lip_interface():
    """
    Clean Wav2Lip interface for Streamlit
    """
    st.subheader("🎭 Wav2Lip Neural Lip-Sync")
    st.markdown("Upload a **face photo** and **audio** to generate talking video")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_face = st.file_uploader(
            "📷 Upload face image", 
            type=["jpg", "png", "jpeg"],
            key="wav2lip_face"
        )
        if uploaded_face:
            st.image(uploaded_face, caption="Face Image", width=200)
    
    with col2:
        uploaded_audio = st.file_uploader(
            "🎵 Upload audio file", 
            type=["wav", "mp3", "m4a"],
            key="wav2lip_audio"
        )
        if uploaded_audio:
            st.audio(uploaded_audio)
    
    if uploaded_face and uploaded_audio:
        if st.button("🧠 Generate Lip-Sync Video", type="primary"):
            with st.spinner("🎬 Running Wav2Lip neural network... (~2-3 minutes)"):
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Create output path
                result_path = tempfile.mktemp(suffix=".mp4")
                
                # Update progress
                progress_bar.progress(25)
                status_text.text("🔍 Preprocessing face and audio...")
                
                # Reset file pointers
                uploaded_face.seek(0)
                uploaded_audio.seek(0)
                
                # Generate video
                progress_bar.progress(50)
                status_text.text("🧠 Running neural lip-sync inference...")
                
                success, message = simple_wav2lip_generation(
                    uploaded_face, 
                    uploaded_audio, 
                    result_path
                )
                
                progress_bar.progress(90)
                status_text.text("✨ Finalizing video...")
                
                if success and os.path.exists(result_path):
                    progress_bar.progress(100)
                    status_text.text("🎉 Video generation complete!")
                    
                    st.success("✅ Lip-sync video generated successfully!")
                    
                    # Load and display video
                    with open(result_path, 'rb') as video_file:
                        video_bytes = video_file.read()
                    
                    st.video(video_bytes)
                    
                    # Download button
                    st.download_button(
                        "📱 Download Lip-Sync Video",
                        data=video_bytes,
                        file_name=f"wav2lip_output_{uploaded_face.name}_{uploaded_audio.name}.mp4",
                        mime="video/mp4"
                    )
                    
                    # Cleanup
                    try:
                        os.unlink(result_path)
                    except:
                        pass
                        
                else:
                    st.error(f"❌ Video generation failed: {message}")
                    st.info("💡 Try with:\n• Shorter audio (< 30 seconds)\n• Smaller image (< 1MB)\n• Clear face photo")
    
    else:
        st.info("👆 Upload both face image and audio file to start")

def check_simple_wav2lip():
    """Check if simple Wav2Lip setup is ready"""
    try:
        current_dir = Path(__file__).parent
        wav2lip_dir = current_dir / "Wav2Lip"
        inference_path = wav2lip_dir / "inference.py"
        
        if not inference_path.exists():
            return False, "inference.py not found"
            
        # Check for any checkpoint
        checkpoints = [
            wav2lip_dir / "checkpoints" / "wav2lip.pth",
            wav2lip_dir / "Wav2Lip_gan.pth"
        ]
        
        for checkpoint in checkpoints:
            if checkpoint.exists():
                return True, f"Ready with {checkpoint.name}"
        
        return False, "No checkpoint found"
        
    except Exception as e:
        return False, f"Setup error: {str(e)}"