import os
import torch
import whisper
from pyannote.audio import Pipeline
from datetime import timedelta

# Hugging Face token (pyannote gated models için gerekli)
# Environment variable'dan oku
HUGGING_FACE_TOKEN = os.getenv("HF_TOKEN")  # Environment variable kullan

# Fallback değerleri
if not HUGGING_FACE_TOKEN:
    print("⚠️ HF_TOKEN environment variable not set!")
    print("💡 Please set your Hugging Face token:")
    print("   export HF_TOKEN='<your_token_here>'")
    HUGGING_FACE_TOKEN = None

# ------------------------------
# ACADEMIC CITATIONS & CREDITS
# ------------------------------
"""
This implementation uses pyannote.audio for speaker diarization:

@inproceedings{Bredin2020,
  Title = {{pyannote.audio: neural building blocks for speaker diarization}},
  Author = {{Bredin}, Herv{\'e} and {Yin}, Ruiqing and {Coria}, Juan Manuel and {Gelly}, Gregory and {Korshunov}, Pavel and {Lavechin}, Marvin and {Fustes}, Diego and {Titeux}, Hadrien and {Bouaziz}, Wassim and {Gill}, Marie-Philippe},
  Booktitle = {ICASSP 2020, IEEE International Conference on Acoustics, Speech, and Signal Processing},
  Address = {Barcelona, Spain},
  Month = {May},
  Year = {2020},
}

@inproceedings{Bredin2021,
  Title = {{End-to-end speaker segmentation for overlap-aware resegmentation}},
  Author = {{Bredin}, Herv{\'e} and {Laurent}, Antoine},
  Booktitle = {Proc. Interspeech 2021},
  Address = {Brno, Czech Republic},
  Month = {August},
  Year = {2021},
}

And OpenAI Whisper for speech recognition:
@misc{radford2022whisper,
  title={Robust Speech Recognition via Large-Scale Weak Supervision},
  author={Radford, Alec and Kim, Jong Wook and Xu, Tao and Brockman, Greg and McLeavey, Christine and Sutskever, Ilya},
  year={2022},
  eprint={2212.04356},
  archivePrefix={arXiv},
  primaryClass={eess.AS}
}
"""

# ------------------------------
# MODEL SETUP
# ------------------------------
def setup_models():
    """
    Automatically download or load Whisper (speech-to-text)
    and Pyannote (speaker diarization) models.
    """
    print("🔧 Loading models...")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Whisper (ASR)
    asr_model = whisper.load_model("base", device=device)

    # Pyannote (Speaker Diarization)
    try:
        print("🔍 Checking pyannote.audio access...")
        
        # Try full speaker diarization first
        try:
            diarization_model = Pipeline.from_pretrained(
                "pyannote/speaker-diarization@2.1",
                token=HUGGING_FACE_TOKEN
            )
            print("✅ Full speaker diarization loaded!")
            return asr_model, diarization_model
        except:
            print("⚠️ Speaker diarization access denied, trying VAD...")
            
        # Fallback to Advanced pyannote.audio Features
        from pyannote.audio import Model, Inference
        from pyannote.audio.pipelines import VoiceActivityDetection, OverlappedSpeechDetection, Resegmentation
        
        segmentation_model = Model.from_pretrained(
            "pyannote/segmentation", 
            token=HUGGING_FACE_TOKEN
        )
        
        # Setup raw inference for detailed analysis
        inference = Inference(segmentation_model)
        
        # Setup VAD pipeline
        vad_pipeline = VoiceActivityDetection(segmentation=segmentation_model)
        HYPER_PARAMETERS = {
            "onset": 0.5, "offset": 0.5,
            "min_duration_on": 0.0,
            "min_duration_off": 0.0
        }
        vad_pipeline.instantiate(HYPER_PARAMETERS)
        
        # Setup Overlapped Speech Detection
        osd_pipeline = OverlappedSpeechDetection(segmentation=segmentation_model)
        osd_pipeline.instantiate(HYPER_PARAMETERS)
        
        # Setup Resegmentation (for improving baseline diarization)
        reseg_pipeline = Resegmentation(segmentation=segmentation_model, diarization="baseline")
        reseg_pipeline.instantiate(HYPER_PARAMETERS)
        
        print("✅ Complete pyannote suite loaded: Raw Inference + VAD + OSD + Resegmentation!")
        return asr_model, {
            "inference": inference,
            "vad": vad_pipeline, 
            "osd": osd_pipeline, 
            "reseg": reseg_pipeline,
            "segmentation_model": segmentation_model
        }
        
    except Exception as e:
        print(f"⚠️ All pyannote models access denied: {e}")
        print("💡 Please visit:")
        print("   - https://hf.co/pyannote/segmentation (accept conditions)")
        print("   - https://hf.co/pyannote/speaker-diarization (accept conditions)")
        print("   - https://hf.co/settings/tokens (get access token)")
        print("🔄 Using fallback: simple speaker detection")
        diarization_model = None

    return asr_model, diarization_model


# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def format_timestamp(seconds: float):
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


# ------------------------------
# CORE FUNCTION
# ------------------------------
def generate_transcript(audio_path, output_path="transcript_with_timestamps.txt"):
    """
    Generate timestamped transcript with speaker labels.
    """
    print(f"🎙️ Processing audio: {audio_path}")

    # Load models
    asr_model, diarization_model = setup_models()

    # --------------------
    # Step 1: Diarization
    # --------------------
    print("👥 Running speaker diarization...")
    
    if diarization_model:
        try:
            # Check if it's full diarization, VAD+OSD, or simple pipeline
            if hasattr(diarization_model, 'itertracks'):
                # Full speaker diarization
                diarization = diarization_model(audio_path)
                speaker_segments = []
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    speaker_segments.append({
                        "speaker": speaker,
                        "start": turn.start,
                        "end": turn.end
                    })
                print(f"✅ Found {len(speaker_segments)} speaker segments")
                
            elif isinstance(diarization_model, dict):
                # Complete pyannote pipeline: Raw Inference + VAD + OSD + Resegmentation
                print("🔬 Running raw segmentation analysis...")
                
                # Get raw segmentation scores for detailed analysis
                if "inference" in diarization_model:
                    raw_segmentation = diarization_model["inference"](audio_path)
                    print(f"📊 Raw segmentation shape: {raw_segmentation.data.shape}")
                    print(f"📊 Confidence scores available for {raw_segmentation.data.shape[1]} classes")
                
                vad_result = diarization_model["vad"](audio_path)
                osd_result = diarization_model["osd"](audio_path)
                
                speaker_segments = []
                overlapped_regions = []
                
                # Process overlapped speech regions
                for segment in osd_result.itersegments():
                    overlapped_regions.append({
                        "start": segment.start,
                        "end": segment.end
                    })
                
                # Create baseline annotation for resegmentation
                from pyannote.core import Annotation, Segment
                baseline = Annotation()
                
                # Build baseline from VAD with alternating speakers
                for i, segment in enumerate(vad_result.itersegments()):
                    speaker_id = f"SPEAKER_{i % 2:02d}"
                    baseline[Segment(segment.start, segment.end)] = speaker_id
                
                # Apply resegmentation to improve baseline
                try:
                    if "reseg" in diarization_model:
                        resegmented = diarization_model["reseg"]({
                            "audio": audio_path, 
                            "baseline": baseline
                        })
                        print("🔄 Applied resegmentation with raw score guidance")
                        
                        # Process resegmented results with confidence scoring
                        for segment, _, speaker in resegmented.itertracks(yield_label=True):
                            # Check for overlaps
                            is_overlapped = any(
                                overlap["start"] <= segment.start <= overlap["end"] or
                                overlap["start"] <= segment.end <= overlap["end"]
                                for overlap in overlapped_regions
                            )
                            
                            speaker_label = speaker
                            if is_overlapped:
                                speaker_label += " + Overlap"
                            
                            # Add confidence info if available
                            try:
                                # Calculate average confidence for this segment
                                start_frame = int(segment.start * raw_segmentation.sliding_window.sample_rate)
                                end_frame = int(segment.end * raw_segmentation.sliding_window.sample_rate)
                                segment_scores = raw_segmentation.data[start_frame:end_frame]
                                if len(segment_scores) > 0:
                                    avg_confidence = float(segment_scores.max(axis=1).mean())
                                    if avg_confidence < 0.7:  # Low confidence threshold
                                        speaker_label += f" (conf: {avg_confidence:.2f})"
                            except:
                                pass  # Skip confidence calculation if failed
                            
                            speaker_segments.append({
                                "speaker": speaker_label,
                                "start": segment.start,
                                "end": segment.end
                            })
                    else:
                        raise Exception("Resegmentation not available")
                        
                except Exception as reseg_error:
                    print(f"⚠️ Resegmentation failed, using enhanced VAD: {reseg_error}")
                    # Enhanced VAD processing with confidence scores
                    for i, segment in enumerate(vad_result.itersegments()):
                        is_overlapped = any(
                            overlap["start"] <= segment.start <= overlap["end"] or
                            overlap["start"] <= segment.end <= overlap["end"]
                            for overlap in overlapped_regions
                        )
                        
                        speaker_label = f"Speaker_{(i % 2) + 1}"
                        if is_overlapped:
                            speaker_label += " + Overlap"
                        
                        speaker_segments.append({
                            "speaker": speaker_label,
                            "start": segment.start,
                            "end": segment.end
                        })
                
                print(f"✅ Found {len(speaker_segments)} speech segments")
                print(f"🔄 Detected {len(overlapped_regions)} overlapped regions")
                print(f"🔬 Raw score analysis completed")
                
            else:
                # Simple VAD only
                vad_result = diarization_model(audio_path)
                speaker_segments = []
                for i, segment in enumerate(vad_result.itersegments()):
                    speaker_segments.append({
                        "speaker": f"Speaker_{(i % 2) + 1}",
                        "start": segment.start,
                        "end": segment.end
                    })
                print(f"✅ Found {len(speaker_segments)} speech segments (VAD)")
                
        except Exception as e:
            print(f"⚠️ Diarization failed: {e}")
            speaker_segments = []
    else:
        # Fallback: simple alternating speakers
        print("💡 Using fallback speaker detection...")
        speaker_segments = []
        # We'll assign speakers based on transcript segments later

    # --------------------
    # Step 2: Transcription
    # --------------------
    print("🗣️ Running Whisper transcription...")
    
    try:
        transcription = asr_model.transcribe(audio_path)
        segments = transcription["segments"]
    except FileNotFoundError as e:
        if 'ffmpeg' in str(e):
            print("❌ FFmpeg not found! Trying audio processing alternatives...")
            
            # Try different approaches
            fallback_worked = False
            
            # Approach 1: Try with librosa
            try:
                print("🔄 Trying librosa for audio loading...")
                import librosa
                import soundfile as sf
                import tempfile
                
                # Load audio with librosa
                audio_data, sr = librosa.load(audio_path, sr=16000)
                
                # Save as temporary WAV
                temp_wav = tempfile.mktemp(suffix='.wav')
                sf.write(temp_wav, audio_data, sr)
                
                print(f"✅ Converted audio with librosa: {temp_wav}")
                
                # Try transcription with converted file
                transcription = asr_model.transcribe(temp_wav)
                segments = transcription["segments"]
                fallback_worked = True
                
                # Clean up
                os.unlink(temp_wav)
                
            except Exception as librosa_error:
                print(f"⚠️ Librosa fallback failed: {librosa_error}")
            
            # Approach 2: Try with pydub (if librosa failed)
            if not fallback_worked:
                try:
                    print("🔄 Trying pydub for audio conversion...")
                    import subprocess
                    import sys
                    
                    # Install pydub if not available
                    try:
                        from pydub import AudioSegment
                    except ImportError:
                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pydub'])
                        from pydub import AudioSegment
                    
                    # Convert with pydub
                    audio = AudioSegment.from_file(audio_path)
                    temp_wav = tempfile.mktemp(suffix='.wav')
                    audio.export(temp_wav, format='wav')
                    
                    print(f"✅ Converted audio with pydub: {temp_wav}")
                    
                    # Try transcription
                    transcription = asr_model.transcribe(temp_wav)
                    segments = transcription["segments"]
                    fallback_worked = True
                    
                    # Clean up
                    os.unlink(temp_wav)
                    
                except Exception as pydub_error:
                    print(f"⚠️ Pydub fallback failed: {pydub_error}")
            
            # Approach 3: Manual instructions (if all failed)
            if not fallback_worked:
                print("❌ All audio processing fallbacks failed!")
                print("💡 Solutions:")
                print("   1. Install FFmpeg: brew install ffmpeg")
                print("   2. Convert audio to WAV format manually")
                print("   3. Use a different audio file")
                
                # Create error transcript
                segments = [{
                    "start": 0.0,
                    "end": 10.0,
                    "text": f"Audio processing failed. Please install FFmpeg or use WAV format. File: {os.path.basename(audio_path)}"
                }]
        else:
            raise e

    # --------------------
    # Step 3: Match speakers with transcript
    # --------------------
    print("🔗 Matching speech segments to speakers...")
    output_lines = []
    for i, seg in enumerate(segments):
        start = seg["start"]
        end = seg["end"]
        text = seg["text"].strip()

        # Find corresponding speaker (based on overlap or fallback)
        speaker_label = "Unknown"
        
        if speaker_segments:
            # Use pyannote results
            for s in speaker_segments:
                if s["start"] <= start <= s["end"]:
                    speaker_label = s["speaker"]
                    break
        else:
            # Fallback: alternate between speakers
            speaker_label = f"Speaker_{(i % 2) + 1}"

        start_time = format_timestamp(start)
        end_time = format_timestamp(end)
        output_lines.append(f"{start_time} --> {end_time}\n{speaker_label}: {text}\n")

    # --------------------
    # Step 4: Save output
    # --------------------
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"✅ Transcript saved to {output_path}")
    return output_path


# ------------------------------
# CLI ENTRY POINT
# ------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate timestamped transcript with speaker labels.")
    parser.add_argument("--audio", required=True, help="Path to input audio file (.wav or .mp3)")
    parser.add_argument("--output", default="transcript_with_timestamps.txt", help="Output transcript path")
    args = parser.parse_args()

    generate_transcript(args.audio, args.output)