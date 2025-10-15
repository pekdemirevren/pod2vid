"""
Distributed Wav2Lip Processing with Cloud APIs
High-performance GPU inference through external services
"""

import streamlit as st
import requests
import io
import time
import json
import base64
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

class CloudInferenceClient:
    """
    Multi-provider cloud inference client for Wav2Lip
    Priority: Hugging Face → Replicate → Local fallback
    """
    
    def __init__(self):
        self.hf_api_url = "https://api-inference.huggingface.co/models/vinthony/wav2lip-hq"
        self.hf_token = st.secrets.get("HF_TOKEN", None)
        self.replicate_token = st.secrets.get("REPLICATE_API_TOKEN", None)
        
    def _encode_image(self, image_bytes: bytes) -> str:
        """Convert image to base64 for API"""
        return base64.b64encode(image_bytes).decode('utf-8')
        
    def _encode_audio(self, audio_bytes: bytes) -> str:
        """Convert audio to base64 for API"""
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    def huggingface_inference(self, face_image: bytes, audio: bytes) -> Tuple[bool, str]:
        """
        Hugging Face Inference API for Wav2Lip
        """
        if not self.hf_token:
            return False, "HF_TOKEN not configured"
            
        try:
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": {
                    "face_image": self._encode_image(face_image),
                    "audio": self._encode_audio(audio)
                },
                "parameters": {
                    "resize_factor": 1,
                    "nosmooth": True
                }
            }
            
            response = requests.post(
                self.hf_api_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                # Save result video
                output_path = Path("outputs") / f"hf_result_{int(time.time())}.mp4"
                output_path.parent.mkdir(exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                    
                return True, str(output_path)
            else:
                return False, f"HF API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"HF API exception: {str(e)}"
    
    def replicate_inference(self, face_image: bytes, audio: bytes) -> Tuple[bool, str]:
        """
        Replicate API for Wav2Lip (fallback)
        """
        if not self.replicate_token:
            return False, "REPLICATE_API_TOKEN not configured"
            
        try:
            import replicate
            
            # Upload files to temporary URLs
            face_url = self._upload_to_temp_storage(face_image, "image.jpg")
            audio_url = self._upload_to_temp_storage(audio, "audio.wav")
            
            output = replicate.run(
                "devxpy/codeformer:7de2ea26c616d5bf2245ad0d5e24f0ff9a6204578a5c876db53142edd9d2cd56",
                input={
                    "face": face_url,
                    "audio": audio_url,
                    "resize_factor": 1
                }
            )
            
            if output:
                # Download result
                result_response = requests.get(output, timeout=60)
                if result_response.status_code == 200:
                    output_path = Path("outputs") / f"replicate_result_{int(time.time())}.mp4"
                    output_path.parent.mkdir(exist_ok=True)
                    
                    with open(output_path, 'wb') as f:
                        f.write(result_response.content)
                        
                    return True, str(output_path)
                    
            return False, "Replicate processing failed"
            
        except Exception as e:
            return False, f"Replicate API exception: {str(e)}"
    
    def _upload_to_temp_storage(self, data: bytes, filename: str) -> str:
        """Upload to temporary storage (could be S3, Cloudinary, etc.)"""
        # For now, use a simple base64 data URL
        import mimetypes
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        b64_data = base64.b64encode(data).decode('utf-8')
        return f"data:{mime_type};base64,{b64_data}"
    
    def local_fallback(self, face_image: bytes, audio: bytes) -> Tuple[bool, str]:
        """
        Local processing fallback (original simple_wav2lip.py)
        """
        try:
            from simple_wav2lip import simple_wav2lip_generation
            
            # Create temporary files
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as face_tmp:
                face_tmp.write(face_image)
                face_tmp.flush()
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_tmp:
                    audio_tmp.write(audio)
                    audio_tmp.flush()
                    
                    # Create file-like objects for the function
                    class FileWrapper:
                        def __init__(self, path):
                            self.path = path
                        def read(self):
                            with open(self.path, 'rb') as f:
                                return f.read()
                    
                    success, result = simple_wav2lip_generation(
                        FileWrapper(face_tmp.name),
                        FileWrapper(audio_tmp.name)
                    )
                    
                    # Cleanup
                    Path(face_tmp.name).unlink(missing_ok=True)
                    Path(audio_tmp.name).unlink(missing_ok=True)
                    
                    return success, result
                    
        except Exception as e:
            return False, f"Local fallback failed: {str(e)}"
    
    def generate_video(self, face_image: bytes, audio: bytes) -> Tuple[bool, str]:
        """
        Main generation function with provider fallback
        Priority: HuggingFace → Replicate → Local
        """
        
        providers = [
            ("Hugging Face GPU", self.huggingface_inference),
            ("Replicate GPU", self.replicate_inference),
            ("Local CPU", self.local_fallback)
        ]
        
        for provider_name, provider_func in providers:
            st.info(f"🔄 Trying {provider_name}...")
            
            success, result = provider_func(face_image, audio)
            
            if success:
                st.success(f"✅ Generated with {provider_name}")
                return True, result
            else:
                st.warning(f"❌ {provider_name} failed: {result}")
                
        return False, "All providers failed"

# Streamlit interface for cloud processing
def streamlit_cloud_wav2lip_interface():
    """
    Advanced cloud-powered Wav2Lip interface
    """
    st.subheader("🚀 Cloud-Powered Wav2Lip Neural Lip-Sync")
    st.markdown("Professional GPU-accelerated video generation")
    
    # API status indicators
    col_status1, col_status2, col_status3 = st.columns(3)
    
    client = CloudInferenceClient()
    
    with col_status1:
        hf_status = "🟢" if client.hf_token else "🔴"
        st.caption(f"{hf_status} Hugging Face GPU")
        
    with col_status2:
        rep_status = "🟢" if client.replicate_token else "🔴"
        st.caption(f"{rep_status} Replicate GPU")
        
    with col_status3:
        st.caption("🟡 Local CPU Fallback")
    
    # Cloud optimization info
    st.info("""
    ⚡ **Cloud Architecture Benefits:**
    • GPU-accelerated processing (10x faster)
    • No local memory limits
    • Professional quality results
    • Automatic fallback system
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_face = st.file_uploader(
            "📷 Face Image", 
            type=["jpg", "png", "jpeg"],
            key="cloud_face"
        )
        if uploaded_face:
            st.image(uploaded_face, caption="Face", width=200)
    
    with col2:
        uploaded_audio = st.file_uploader(
            "🎵 Audio File", 
            type=["wav", "mp3", "m4a"],
            key="cloud_audio"
        )
        if uploaded_audio:
            st.audio(uploaded_audio, format="audio/wav")
    
    if uploaded_face and uploaded_audio:
        if st.button("🎭 Generate Cloud Video", type="primary"):
            
            with st.spinner("🚀 Processing on cloud GPU..."):
                face_bytes = uploaded_face.read()
                audio_bytes = uploaded_audio.read()
                
                success, result = client.generate_video(face_bytes, audio_bytes)
                
                if success and Path(result).exists():
                    st.success("🎉 Video generated successfully!")
                    
                    # Display result
                    with open(result, 'rb') as video_file:
                        video_bytes = video_file.read()
                        st.video(video_bytes)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Video",
                        data=video_bytes,
                        file_name=f"cloud_lipsync_{int(time.time())}.mp4",
                        mime="video/mp4"
                    )
                else:
                    st.error(f"❌ Generation failed: {result}")

# Usage check function
def check_cloud_inference():
    """Check cloud API availability"""
    client = CloudInferenceClient()
    
    available_providers = []
    if client.hf_token:
        available_providers.append("Hugging Face")
    if client.replicate_token:
        available_providers.append("Replicate")
    available_providers.append("Local Fallback")
    
    return len(available_providers) > 1, f"Available: {', '.join(available_providers)}"