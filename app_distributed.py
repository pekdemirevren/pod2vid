"""
Pod2Vid - Production Cloud Architecture
Distributed processing with GPU-powered APIs
"""

import streamlit as st
import os
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Pod2Vid - AI Video Generator", 
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check if we should use cloud architecture
CLOUD_MODE = os.getenv("STREAMLIT_CLOUD", "false").lower() == "true" or "streamlit.app" in os.getenv("SERVER_NAME", "")

def main():
    """Main application entry point"""
    
    # Sidebar for mode selection
    with st.sidebar:
        st.title("🎭 Pod2Vid")
        st.markdown("**AI Video Generation Platform**")
        
        # Mode selection
        mode = st.selectbox(
            "⚙️ Processing Mode",
            [
                "🚀 Cloud Architecture (Recommended)",
                "⚡ Async Processing",
                "🧠 Simple Interface",
                "📊 Analytics Dashboard"
            ]
        )
        
        st.divider()
        
        # System status
        st.subheader("📡 System Status")
        
        if CLOUD_MODE:
            st.success("☁️ Cloud deployment detected")
        else:
            st.info("💻 Local development mode")
        
        # API status indicators
        try:
            from cloud_inference import CloudInferenceClient
            client = CloudInferenceClient()
            
            hf_status = "🟢" if client.hf_token else "🔴"
            rep_status = "🟢" if client.replicate_token else "🔴"
            
            st.markdown(f"""
            **API Status:**
            - {hf_status} Hugging Face GPU
            - {rep_status} Replicate GPU  
            - 🟡 Local CPU Fallback
            """)
            
        except Exception as e:
            st.error(f"Status check failed: {e}")
    
    # Main content area
    if mode == "🚀 Cloud Architecture (Recommended)":
        show_optimized_interface()
        
    elif mode == "⚡ Async Processing":
        show_async_interface()
        
    elif mode == "🧠 Simple Interface":
        show_simple_interface()
        
    elif mode == "📊 Analytics Dashboard":
        show_analytics_dashboard()

def show_optimized_interface():
    """Main optimized cloud interface"""
    try:
        from cost_optimization import streamlit_optimized_interface
        streamlit_optimized_interface()
        
    except ImportError as e:
        st.error(f"Cloud optimization module not available: {e}")
        st.info("Falling back to simple interface...")
        show_simple_interface()

def show_async_interface():
    """Async processing interface"""
    try:
        from async_processing import streamlit_async_interface
        streamlit_async_interface()
        
    except ImportError as e:
        st.error(f"Async processing module not available: {e}")
        show_simple_interface()

def show_simple_interface():
    """Simple cloud inference interface"""
    try:
        from cloud_inference import streamlit_cloud_wav2lip_interface
        streamlit_cloud_wav2lip_interface()
        
    except ImportError as e:
        st.error(f"Cloud inference module not available: {e}")
        show_fallback_interface()

def show_analytics_dashboard():
    """Analytics and monitoring dashboard"""
    try:
        from cost_optimization import streamlit_usage_dashboard
        streamlit_usage_dashboard()
        
    except ImportError as e:
        st.error(f"Analytics module not available: {e}")
        st.info("Dashboard not available in this configuration")

def show_fallback_interface():
    """Fallback interface using original modules"""
    st.title("🎭 Pod2Vid - Fallback Mode")
    st.warning("⚠️ Running in fallback mode - some features may be limited")
    
    try:
        # Try to load original simple wav2lip
        from simple_wav2lip import streamlit_wav2lip_interface
        streamlit_wav2lip_interface()
        
    except ImportError:
        st.error("❌ No video generation modules available")
        st.info("""
        **Troubleshooting:**
        1. Check that all required modules are installed
        2. Verify API tokens are configured
        3. Try refreshing the page
        """)

# Footer
def show_footer():
    """Application footer"""
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🎭 **Pod2Vid** - AI Video Generation")
    
    with col2:
        st.caption("🧠 Powered by Wav2Lip neural networks")
    
    with col3:
        st.caption("☁️ Distributed cloud architecture")

if __name__ == "__main__":
    # Auto-detect cloud environment
    if CLOUD_MODE:
        # Download models if needed (for cloud deployment)
        try:
            from download_models import download_model
            download_model()
        except Exception as e:
            st.sidebar.warning(f"Model download check: {e}")
    
    # Run main app
    main()
    
    # Show footer
    show_footer()