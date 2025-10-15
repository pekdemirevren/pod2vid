"""
Async Processing UI for Cloud Inference
Job queue, progress tracking, and real-time updates
"""

import streamlit as st
import time
import threading
import queue
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProcessingJob:
    job_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    provider_used: Optional[str] = None

class AsyncJobManager:
    """
    Manages async video generation jobs with progress tracking
    """
    
    def __init__(self):
        if 'jobs' not in st.session_state:
            st.session_state.jobs = {}
        if 'job_queue' not in st.session_state:
            st.session_state.job_queue = queue.Queue()
            
    def create_job(self, face_image: bytes, audio: bytes) -> str:
        """Create a new processing job"""
        job_id = str(uuid.uuid4())[:8]
        
        job = ProcessingJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.now()
        )
        
        st.session_state.jobs[job_id] = job
        
        # Add to processing queue
        st.session_state.job_queue.put({
            'job_id': job_id,
            'face_image': face_image,
            'audio': audio
        })
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get job by ID"""
        return st.session_state.jobs.get(job_id)
    
    def update_job_progress(self, job_id: str, progress: float, status: JobStatus = None):
        """Update job progress"""
        if job_id in st.session_state.jobs:
            st.session_state.jobs[job_id].progress = progress
            if status:
                st.session_state.jobs[job_id].status = status
    
    def complete_job(self, job_id: str, result_path: str, provider_used: str):
        """Mark job as completed"""
        if job_id in st.session_state.jobs:
            job = st.session_state.jobs[job_id]
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress = 100.0
            job.result_path = result_path
            job.provider_used = provider_used
    
    def fail_job(self, job_id: str, error_message: str):
        """Mark job as failed"""
        if job_id in st.session_state.jobs:
            job = st.session_state.jobs[job_id]
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            job.error_message = error_message

def process_job_async(job_data: Dict[str, Any], job_manager: AsyncJobManager):
    """
    Process a job asynchronously in background thread
    """
    job_id = job_data['job_id']
    face_image = job_data['face_image']
    audio = job_data['audio']
    
    try:
        from cloud_inference import CloudInferenceClient
        
        # Update status
        job_manager.update_job_progress(job_id, 10.0, JobStatus.PROCESSING)
        
        client = CloudInferenceClient()
        
        # Try processing
        job_manager.update_job_progress(job_id, 30.0)
        
        success, result = client.generate_video(face_image, audio)
        
        job_manager.update_job_progress(job_id, 90.0)
        
        if success:
            job_manager.complete_job(job_id, result, "Cloud GPU")
        else:
            job_manager.fail_job(job_id, result)
            
    except Exception as e:
        job_manager.fail_job(job_id, str(e))

def streamlit_async_interface():
    """
    Streamlit interface for async job processing
    """
    st.subheader("⚡ Async Cloud Processing")
    st.markdown("Queue-based video generation with real-time progress")
    
    job_manager = AsyncJobManager()
    
    # Job submission form
    with st.form("async_job_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            face_file = st.file_uploader("📷 Face Image", type=["jpg", "png", "jpeg"])
            
        with col2:
            audio_file = st.file_uploader("🎵 Audio File", type=["wav", "mp3", "m4a"])
        
        submit_button = st.form_submit_button("🚀 Queue Generation Job", type="primary")
        
        if submit_button and face_file and audio_file:
            # Create job
            face_bytes = face_file.read()
            audio_bytes = audio_file.read()
            
            job_id = job_manager.create_job(face_bytes, audio_bytes)
            
            st.success(f"✅ Job queued: `{job_id}`")
            
            # Start background processing
            threading.Thread(
                target=process_job_async,
                args=({'job_id': job_id, 'face_image': face_bytes, 'audio': audio_bytes}, job_manager),
                daemon=True
            ).start()
    
    st.divider()
    
    # Job status dashboard
    st.subheader("📊 Job Dashboard")
    
    jobs = st.session_state.jobs
    
    if not jobs:
        st.info("No jobs yet. Submit your first generation above!")
        return
    
    # Auto-refresh every 2 seconds
    if st.button("🔄 Refresh Status"):
        st.rerun()
    
    # Add auto-refresh for processing jobs
    processing_jobs = [j for j in jobs.values() if j.status == JobStatus.PROCESSING]
    if processing_jobs:
        time.sleep(2)
        st.rerun()
    
    # Display jobs in reverse chronological order
    for job in sorted(jobs.values(), key=lambda x: x.created_at, reverse=True):
        
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
            
            with col1:
                # Status indicator
                status_icons = {
                    JobStatus.PENDING: "⏳",
                    JobStatus.PROCESSING: "🔄",
                    JobStatus.COMPLETED: "✅",
                    JobStatus.FAILED: "❌"
                }
                
                status_colors = {
                    JobStatus.PENDING: "orange",
                    JobStatus.PROCESSING: "blue", 
                    JobStatus.COMPLETED: "green",
                    JobStatus.FAILED: "red"
                }
                
                st.markdown(f"""
                **Job {job.job_id}** {status_icons[job.status]}
                
                :{status_colors[job.status]}[{job.status.value.upper()}]
                """)
            
            with col2:
                # Timing info
                duration = ""
                if job.completed_at:
                    duration = f"Duration: {(job.completed_at - job.created_at).seconds}s"
                elif job.started_at:
                    duration = f"Running: {(datetime.now() - job.started_at).seconds}s"
                else:
                    duration = f"Queued: {(datetime.now() - job.created_at).seconds}s ago"
                
                st.caption(f"Created: {job.created_at.strftime('%H:%M:%S')}")
                st.caption(duration)
            
            with col3:
                # Progress bar
                if job.status == JobStatus.PROCESSING:
                    st.progress(job.progress / 100.0)
                    st.caption(f"{job.progress:.0f}%")
                elif job.status == JobStatus.COMPLETED:
                    st.progress(1.0)
                    st.caption("100%")
            
            with col4:
                # Actions
                if job.status == JobStatus.COMPLETED and job.result_path:
                    try:
                        from pathlib import Path
                        result_file = Path(job.result_path)
                        if result_file.exists():
                            with open(result_file, 'rb') as f:
                                video_bytes = f.read()
                            
                            st.download_button(
                                "📥 Download",
                                data=video_bytes,
                                file_name=f"result_{job.job_id}.mp4",
                                mime="video/mp4",
                                key=f"download_{job.job_id}"
                            )
                            
                            # Preview button
                            if st.button("👁️ Preview", key=f"preview_{job.job_id}"):
                                st.video(video_bytes)
                                
                    except Exception as e:
                        st.error(f"File error: {e}")
                        
                elif job.status == JobStatus.FAILED:
                    st.error(f"Error: {job.error_message}")
        
        st.divider()

# Add to simple UI for testing
def simple_async_test():
    """Simple test interface for async processing"""
    st.title("🔬 Async Processing Test")
    
    if st.button("🧪 Test Async Job"):
        job_manager = AsyncJobManager()
        
        # Create dummy job
        dummy_job_id = job_manager.create_job(b"dummy_face", b"dummy_audio")
        
        # Simulate processing
        def simulate_processing():
            time.sleep(1)
            job_manager.update_job_progress(dummy_job_id, 25.0, JobStatus.PROCESSING)
            time.sleep(1)
            job_manager.update_job_progress(dummy_job_id, 50.0)
            time.sleep(1)
            job_manager.update_job_progress(dummy_job_id, 75.0)
            time.sleep(1)
            job_manager.complete_job(dummy_job_id, "dummy_result.mp4", "Test Provider")
        
        threading.Thread(target=simulate_processing, daemon=True).start()
        st.success(f"Test job created: {dummy_job_id}")
    
    # Show dashboard
    streamlit_async_interface()