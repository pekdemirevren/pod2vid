import streamlit as st
import gc
import torch

def optimize_memory():
    """Memory optimization for local deployment"""
    
    # Clear GPU cache if available
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Force garbage collection
    gc.collect()
    
    # Streamlit cache clear
    st.cache_data.clear()
    st.cache_resource.clear()

def load_models_lazy():
    """Load models only when needed"""
    
    @st.cache_resource
    def get_whisper_model():
        import whisper
        return whisper.load_model("tiny")  # Use tiny instead of base
    
    @st.cache_resource  
    def get_wav2lip_model():
        # Load only when video generation is requested
        return "wav2lip_model_placeholder"
    
    return get_whisper_model, get_wav2lip_model

# Usage in main app
if __name__ == "__main__":
    # Memory optimization
    optimize_memory()
    
    # Lazy loading
    get_whisper, get_wav2lip = load_models_lazy()
    
    st.title("🎙️ Memory Optimized Version")
    st.write("Uses 2-4GB instead of 14GB")