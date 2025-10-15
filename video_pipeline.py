import os
import subprocess
try:
    # MoviePy 2.x için doğru import syntax
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    from moviepy.video.VideoClip import ColorClip
    
    # Text clip için alternatif (şimdilik olmadan devam edebiliriz)
    TextClip = None  # Text functionality olmadan devam et
    
    MOVIEPY_AVAILABLE = True
    print("✅ MoviePy imports successful!")
    
except ImportError as e:
    print(f"⚠️ MoviePy not available: {e}")
    print("💡 Please install: pip install moviepy")
    MOVIEPY_AVAILABLE = False

def generate_video(audio_path, transcript_file, face1_path, face2_path, output_dir="outputs"):
    """
    Full video generation pipeline:
    - Uses Wav2Lip + SadTalker for realistic talking head animation
    - Adds subtitles based on transcript
    - Combines with background and audio using MoviePy
    """
    
    if not MOVIEPY_AVAILABLE:
        raise ImportError("MoviePy is required for video generation. Please install: pip install moviepy")
    
    # Input validation
    print(f"🔍 Validating input files...")
    print(f"   📁 Audio: {audio_path}")
    print(f"   📷 Face 1: {face1_path}")
    print(f"   📷 Face 2: {face2_path}")
    print(f"   📄 Transcript: {transcript_file}")
    
    missing_files = []
    if not os.path.exists(audio_path):
        missing_files.append(f"Audio file: {audio_path}")
    if not os.path.exists(face1_path):
        missing_files.append(f"Face 1 image: {face1_path}")
    if not os.path.exists(face2_path):
        missing_files.append(f"Face 2 image: {face2_path}")
    if not os.path.exists(transcript_file):
        missing_files.append(f"Transcript file: {transcript_file}")
        
    if missing_files:
        error_msg = "Missing required files:\n" + "\n".join([f"  - {f}" for f in missing_files])
        print(f"❌ {error_msg}")
        raise FileNotFoundError(error_msg)
    
    print("✅ All input files validated")
    
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    final_video_path = os.path.join(output_dir, f"{base_name}_final.mp4")

    # 1️⃣ Select character (face_1 / face_2) based on speaker lines
    with open(transcript_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"📄 Transcript content preview:")
    for i, line in enumerate(lines[:5]):  # Show first 5 lines
        print(f"   Line {i+1}: {repr(line[:100])}")

    segments = []
    current_speaker = None
    segment_audio_files = []

    # Example parsing (Speaker 1 / Speaker 2 / Speaker_1 / Speaker_2)
    for line_num, line in enumerate(lines):
        if "Speaker 1:" in line or "speaker 1:" in line.lower() or "Speaker_1:" in line:
            current_speaker = face1_path
            segments.append((current_speaker, line.strip()))
            print(f"✅ Found Speaker 1 at line {line_num+1}")
        elif "Speaker 2:" in line or "speaker 2:" in line.lower() or "Speaker_2:" in line:
            current_speaker = face2_path
            segments.append((current_speaker, line.strip()))
            print(f"✅ Found Speaker 2 at line {line_num+1}")
        elif "SPEAKER_" in line:  # pyannote format
            if "SPEAKER_00" in line:
                current_speaker = face1_path
                segments.append((current_speaker, line.strip()))
                print(f"✅ Found SPEAKER_00 at line {line_num+1}")
            elif "SPEAKER_01" in line:
                current_speaker = face2_path
                segments.append((current_speaker, line.strip()))
                print(f"✅ Found SPEAKER_01 at line {line_num+1}")

    print(f"📊 Found {len(segments)} speaker segments")
    
    # Fallback: If no speaker segments found, create a single segment with first face
    if not segments:
        print("⚠️ No speaker segments found, using fallback (full audio with face1)")
        segments = [(face1_path, "Full conversation")]

    # 2️⃣ Run Wav2Lip for each segment
    segment_videos = []
    for idx, (face_img, line) in enumerate(segments):
        temp_video = os.path.join(output_dir, f"segment_{idx}.mp4")
        temp_audio = audio_path  # We're using full audio for now (you can later segment timestamps)

        print(f"🎬 Processing segment {idx+1}/{len(segments)}: {os.path.basename(face_img)}")
        print(f"   📁 Face image: {face_img}")
        print(f"   🎵 Audio file: {temp_audio}")
        print(f"   📽️ Output video: {temp_video}")
        
        # Input dosyalarının varlığını kontrol et
        if not os.path.exists(face_img):
            print(f"❌ Face image not found: {face_img}")
            continue
        if not os.path.exists(temp_audio):
            print(f"❌ Audio file not found: {temp_audio}")
            continue
            
        try:
            # Wav2Lip inference command - absolute paths kullan
            cmd = [
                "/Users/evrenpekdemir/audio-transcript-generator/Wav2Lip/venv39/bin/python", 
                "/Users/evrenpekdemir/audio-transcript-generator/Wav2Lip/inference.py",
                "--checkpoint_path", "/Users/evrenpekdemir/audio-transcript-generator/Wav2Lip/checkpoints/wav2lip_gan.pth",
                "--face", face_img,
                "--audio", temp_audio,
                "--outfile", temp_video
            ]
            
            print(f"🔧 Running command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, 
                capture_output=True, 
                text=True, 
                cwd="/Users/evrenpekdemir/audio-transcript-generator",
                timeout=300  # 5 dakika timeout
            )
            
            if result.returncode == 0 and os.path.exists(temp_video):
                segment_videos.append(temp_video)
                print(f"✅ Segment {idx+1} generated successfully")
            else:
                print(f"❌ Segment {idx+1} failed!")
                print(f"   Return code: {result.returncode}")
                print(f"   STDOUT: {result.stdout}")
                print(f"   STDERR: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Segment {idx+1} timed out after 5 minutes")
        except Exception as e:
            print(f"❌ Error processing segment {idx+1}: {e}")

    print(f"📝 Generated {len(segment_videos)} video segments")
    
    # Check if we have any videos to work with
    if not segment_videos:
        raise ValueError("No video segments were generated successfully. Check Wav2Lip setup and input files.")

    # 3️⃣ Merge segments with MoviePy
    print(f"🎬 Starting video merge with {len(segment_videos)} segments")
    
    try:
        clips = []
        for i, v in enumerate(segment_videos):
            if os.path.exists(v):
                print(f"📁 Loading segment {i+1}: {os.path.basename(v)}")
                clip = VideoFileClip(v)
                clips.append(clip)
            else:
                print(f"⚠️ Segment {i+1} file not found: {v}")
        
        if not clips:
            raise ValueError("No valid video clips loaded!")
        
        print(f"✅ Loaded {len(clips)} video clips successfully")
        
        # Safe concatenation for MoviePy 2.x
        if len(clips) == 1:
            final_clip = clips[0]
            print("✅ Single video segment, using as-is")
        else:
            # MoviePy 2.x için manuel concatenation
            print(f"🔗 Concatenating {len(clips)} video segments...")
            
            # İlk clip'i al
            final_clip = clips[0]
            
            # Diğer clipleri sırayla ekle (basit approach)
            current_duration = final_clip.duration
            
            for i, clip in enumerate(clips[1:], 1):
                try:
                    # Clip'i zaman offset'i ile composite et
                    clip_with_offset = clip.set_start(current_duration)
                    final_clip = CompositeVideoClip([final_clip, clip_with_offset])
                    current_duration += clip.duration
                    print(f"✅ Added segment {i+1}")
                except Exception as e:
                    print(f"⚠️ Could not add segment {i+1}: {e}, stopping concatenation")
                    break

        # 4️⃣ Add subtitles (şimdilik atla - TextClip mevcut değil)
        print("⚠️ Subtitle functionality temporarily disabled (TextClip not available)")
        
        # Audio'yu ekle
        final_audio = AudioFileClip(audio_path)
        final_clip = final_clip.set_audio(final_audio)
        
    except Exception as e:
        print(f"❌ Error during video merge: {e}")
        raise

    # 5️⃣ Export final video
    print(f"💾 Exporting final video to: {final_video_path}")
    final_clip.write_videofile(final_video_path, fps=24)
    
    # Cleanup temporary files
    for temp_video in segment_videos:
        if os.path.exists(temp_video):
            os.remove(temp_video)
    
    print(f"✅ Video generation complete: {final_video_path}")
    return final_video_path