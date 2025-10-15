"""
Cost Optimization & Usage Monitoring
Smart caching, rate limiting, and resource management
"""

import streamlit as st
import hashlib
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pickle

class UsageTracker:
    """
    Track API usage, costs, and implement rate limiting
    """
    
    def __init__(self):
        self.usage_file = Path("usage_stats.json")
        self.cache_dir = Path("video_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Load existing stats
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict[str, Any]:
        """Load usage statistics"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "cache_hits": 0,
            "provider_usage": {
                "huggingface": 0,
                "replicate": 0,
                "local": 0
            },
            "daily_usage": {},
            "costs": {
                "estimated_total": 0.0,
                "huggingface": 0.0,
                "replicate": 0.0
            }
        }
    
    def _save_stats(self):
        """Save usage statistics"""
        with open(self.usage_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def _get_file_hash(self, face_data: bytes, audio_data: bytes) -> str:
        """Generate unique hash for caching"""
        combined = face_data + audio_data
        return hashlib.md5(combined).hexdigest()[:16]
    
    def check_rate_limit(self, user_id: str = "default") -> Tuple[bool, str]:
        """
        Check if user has exceeded rate limits
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.stats["daily_usage"]:
            self.stats["daily_usage"][today] = {"requests": 0, "users": {}}
        
        daily_stats = self.stats["daily_usage"][today]
        
        if user_id not in daily_stats["users"]:
            daily_stats["users"][user_id] = 0
        
        user_requests_today = daily_stats["users"][user_id]
        total_requests_today = daily_stats["requests"]
        
        # Rate limits
        MAX_REQUESTS_PER_USER_PER_DAY = 10
        MAX_TOTAL_REQUESTS_PER_DAY = 100
        
        if user_requests_today >= MAX_REQUESTS_PER_USER_PER_DAY:
            return False, f"Daily limit reached ({MAX_REQUESTS_PER_USER_PER_DAY} requests/day)"
        
        if total_requests_today >= MAX_TOTAL_REQUESTS_PER_DAY:
            return False, "System daily limit reached. Try again tomorrow."
        
        return True, "OK"
    
    def check_cache(self, face_data: bytes, audio_data: bytes) -> Optional[str]:
        """
        Check if result exists in cache
        """
        file_hash = self._get_file_hash(face_data, audio_data)
        cache_file = self.cache_dir / f"result_{file_hash}.mp4"
        
        if cache_file.exists():
            # Check if cache is recent (within 7 days)
            if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).days < 7:
                self.stats["cache_hits"] += 1
                self._save_stats()
                return str(cache_file)
        
        return None
    
    def cache_result(self, face_data: bytes, audio_data: bytes, result_path: str):
        """
        Cache successful result
        """
        try:
            file_hash = self._get_file_hash(face_data, audio_data)
            cache_file = self.cache_dir / f"result_{file_hash}.mp4"
            
            # Copy result to cache
            import shutil
            shutil.copy2(result_path, cache_file)
            
        except Exception as e:
            st.warning(f"Cache save failed: {e}")
    
    def record_usage(self, provider: str, success: bool, cost: float = 0.0, user_id: str = "default"):
        """
        Record API usage and costs
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Update totals
        self.stats["total_requests"] += 1
        
        if success:
            self.stats["successful_generations"] += 1
        else:
            self.stats["failed_generations"] += 1
        
        # Update provider usage
        if provider in self.stats["provider_usage"]:
            self.stats["provider_usage"][provider] += 1
        
        # Update costs
        if provider in self.stats["costs"]:
            self.stats["costs"][provider] += cost
            self.stats["costs"]["estimated_total"] += cost
        
        # Update daily usage
        if today not in self.stats["daily_usage"]:
            self.stats["daily_usage"][today] = {"requests": 0, "users": {}}
        
        self.stats["daily_usage"][today]["requests"] += 1
        
        if user_id not in self.stats["daily_usage"][today]["users"]:
            self.stats["daily_usage"][today]["users"][user_id] = 0
        
        self.stats["daily_usage"][today]["users"][user_id] += 1
        
        self._save_stats()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return self.stats.copy()
    
    def estimate_cost(self, provider: str) -> float:
        """
        Estimate cost per request by provider
        """
        cost_estimates = {
            "huggingface": 0.01,  # $0.01 per request (estimated)
            "replicate": 0.05,    # $0.05 per request (estimated)
            "local": 0.0          # Free but uses compute resources
        }
        
        return cost_estimates.get(provider, 0.0)

class OptimizedInferenceClient:
    """
    Cost-optimized inference client with caching and monitoring
    """
    
    def __init__(self):
        self.tracker = UsageTracker()
        
        # Load original client
        from cloud_inference import CloudInferenceClient
        self.client = CloudInferenceClient()
    
    def generate_video_optimized(self, face_image: bytes, audio: bytes, user_id: str = "default") -> Tuple[bool, str]:
        """
        Optimized generation with caching and rate limiting
        """
        
        # 1. Check rate limits
        rate_ok, rate_message = self.tracker.check_rate_limit(user_id)
        if not rate_ok:
            return False, f"Rate limit: {rate_message}"
        
        # 2. Check cache first
        cached_result = self.tracker.check_cache(face_image, audio)
        if cached_result:
            st.success("⚡ Found in cache - instant result!")
            return True, cached_result
        
        # 3. Validate file sizes
        if len(face_image) > 10 * 1024 * 1024:  # 10MB limit
            return False, "Face image too large (max 10MB)"
        
        if len(audio) > 50 * 1024 * 1024:  # 50MB limit
            return False, "Audio file too large (max 50MB)"
        
        # 4. Process with cost tracking
        providers = [
            ("huggingface", self.client.huggingface_inference),
            ("replicate", self.client.replicate_inference),
            ("local", self.client.local_fallback)
        ]
        
        for provider_name, provider_func in providers:
            estimated_cost = self.tracker.estimate_cost(provider_name)
            
            st.info(f"🔄 Trying {provider_name} (est. cost: ${estimated_cost:.3f})")
            
            start_time = time.time()
            success, result = provider_func(face_image, audio)
            duration = time.time() - start_time
            
            # Record usage
            self.tracker.record_usage(provider_name, success, estimated_cost if success else 0, user_id)
            
            if success:
                st.success(f"✅ Generated with {provider_name} in {duration:.1f}s")
                
                # Cache successful result
                self.tracker.cache_result(face_image, audio, result)
                
                return True, result
            else:
                st.warning(f"❌ {provider_name} failed: {result}")
        
        return False, "All providers failed"

def streamlit_usage_dashboard():
    """
    Usage monitoring dashboard
    """
    st.subheader("📊 Usage & Cost Dashboard")
    
    tracker = UsageTracker()
    stats = tracker.get_usage_stats()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", stats["total_requests"])
    
    with col2:
        success_rate = 0
        if stats["total_requests"] > 0:
            success_rate = stats["successful_generations"] / stats["total_requests"] * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        st.metric("Cache Hits", stats["cache_hits"])
    
    with col4:
        st.metric("Est. Total Cost", f"${stats['costs']['estimated_total']:.2f}")
    
    # Provider usage
    st.subheader("🔧 Provider Usage")
    
    provider_cols = st.columns(3)
    providers = ["huggingface", "replicate", "local"]
    
    for i, provider in enumerate(providers):
        with provider_cols[i]:
            usage_count = stats["provider_usage"].get(provider, 0)
            cost = stats["costs"].get(provider, 0.0)
            
            st.metric(
                provider.title(),
                f"{usage_count} requests",
                f"${cost:.2f}"
            )
    
    # Daily usage chart
    st.subheader("📈 Daily Usage")
    
    if stats["daily_usage"]:
        dates = list(stats["daily_usage"].keys())[-7:]  # Last 7 days
        requests = [stats["daily_usage"][date]["requests"] for date in dates]
        
        import pandas as pd
        df = pd.DataFrame({"Date": dates, "Requests": requests})
        st.bar_chart(df.set_index("Date"))
    else:
        st.info("No usage data yet")
    
    # Rate limiting info
    st.subheader("⚡ Rate Limits")
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_usage = stats["daily_usage"].get(today, {"requests": 0})
    
    st.info(f"""
    **Current Limits:**
    • Per user: 10 requests/day
    • System total: 100 requests/day
    • Today's usage: {today_usage['requests']} requests
    """)
    
    # Cache management
    st.subheader("💾 Cache Management")
    
    cache_dir = Path("video_cache")
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.mp4"))
        cache_size = sum(f.stat().st_size for f in cache_files) / (1024*1024)  # MB
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Cached Videos", len(cache_files))
        
        with col2:
            st.metric("Cache Size", f"{cache_size:.1f} MB")
        
        if st.button("🗑️ Clear Cache"):
            for cache_file in cache_files:
                cache_file.unlink()
            st.success("Cache cleared!")
            st.rerun()

def streamlit_optimized_interface():
    """
    Main optimized interface combining all features
    """
    st.title("🚀 Pod2Vid - Optimized Cloud Architecture")
    st.markdown("**Professional AI video generation with intelligent cost optimization**")
    
    # Tabs for different features
    tab1, tab2, tab3 = st.tabs(["🎭 Generate Video", "📊 Usage Dashboard", "⚙️ System Status"])
    
    with tab1:
        st.subheader("🎬 Cloud Video Generation")
        
        # Quick info
        st.info("""
        **Smart Features Active:**
        • 🧠 Intelligent caching (instant results for repeated requests)
        • ⚡ Multi-provider fallback (HuggingFace → Replicate → Local)
        • 📊 Cost tracking and optimization
        • 🛡️ Rate limiting and file size validation
        """)
        
        # File uploads
        col1, col2 = st.columns(2)
        
        with col1:
            face_file = st.file_uploader("📷 Face Image", type=["jpg", "png", "jpeg"])
            if face_file:
                st.image(face_file, caption="Face", width=200)
                st.caption(f"Size: {len(face_file.read()) / 1024:.1f} KB")
                face_file.seek(0)  # Reset file pointer
        
        with col2:
            audio_file = st.file_uploader("🎵 Audio File", type=["wav", "mp3", "m4a"])
            if audio_file:
                st.audio(audio_file)
                st.caption(f"Size: {len(audio_file.read()) / 1024:.1f} KB")
                audio_file.seek(0)  # Reset file pointer
        
        # Generation button
        if face_file and audio_file:
            user_id = st.text_input("👤 User ID (optional)", value="anonymous")
            
            if st.button("🎭 Generate Video (Optimized)", type="primary"):
                
                with st.spinner("🧠 Optimizing and processing..."):
                    
                    face_bytes = face_file.read()
                    audio_bytes = audio_file.read()
                    
                    client = OptimizedInferenceClient()
                    success, result = client.generate_video_optimized(face_bytes, audio_bytes, user_id)
                    
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
                            file_name=f"optimized_lipsync_{int(time.time())}.mp4",
                            mime="video/mp4"
                        )
                    else:
                        st.error(f"❌ Generation failed: {result}")
    
    with tab2:
        streamlit_usage_dashboard()
    
    with tab3:
        st.subheader("⚙️ System Status")
        
        # API status check
        from cloud_inference import CloudInferenceClient
        client = CloudInferenceClient()
        
        status_cols = st.columns(3)
        
        with status_cols[0]:
            hf_status = "🟢 Active" if client.hf_token else "🔴 No Token"
            st.metric("Hugging Face API", hf_status)
        
        with status_cols[1]:
            rep_status = "🟢 Active" if client.replicate_token else "🔴 No Token"
            st.metric("Replicate API", rep_status)
        
        with status_cols[2]:
            st.metric("Local Fallback", "🟡 Available")
        
        # System resources
        st.subheader("💻 Resources")
        
        import psutil
        
        resource_cols = st.columns(3)
        
        with resource_cols[0]:
            cpu_percent = psutil.cpu_percent()
            st.metric("CPU Usage", f"{cpu_percent:.1f}%")
        
        with resource_cols[1]:
            memory = psutil.virtual_memory()
            st.metric("Memory Usage", f"{memory.percent:.1f}%")
        
        with resource_cols[2]:
            disk = psutil.disk_usage('/')
            st.metric("Disk Usage", f"{disk.percent:.1f}%")