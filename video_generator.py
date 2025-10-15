import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os

def create_animated_video(transcript_segments, speaker_photos, audio_file_path, output_path):
    """
    Create animated video with uploaded photos speaking the dialogue
    """
    try:
        # Video settings
        width, height = 1920, 1080
        fps = 30
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Background color (white)
        background_color = (255, 255, 255)
        
        # Process each segment
        for i, segment in enumerate(transcript_segments):
            speaker_num = (i % 2) + 1
            speaker_key = f"speaker{speaker_num}"
            
            # Load speaker photo
            if speaker_key in speaker_photos:
                # Convert uploaded file to image
                speaker_img = Image.open(speaker_photos[speaker_key])
                speaker_img = speaker_img.resize((400, 400))
            else:
                # Create default avatar
                speaker_img = create_default_avatar(400, 400, speaker_num)
            
            # Calculate duration in frames
            duration = segment["end"] - segment["start"]
            total_frames = int(duration * fps)
            
            # Get dialogue text
            dialogue_text = segment["text"].strip()
            
            # Create frames for this segment
            for frame_num in range(total_frames):
                # Create frame
                frame = create_dialogue_frame(
                    width, height, 
                    speaker_img, 
                    dialogue_text, 
                    speaker_num,
                    frame_num, 
                    total_frames,
                    background_color
                )
                
                # Convert PIL to OpenCV format
                frame_cv = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
                video_writer.write(frame_cv)
        
        video_writer.release()
        return True
        
    except Exception as e:
        print(f"Error creating animated video: {str(e)}")
        return False

def create_dialogue_frame(width, height, speaker_img, dialogue_text, speaker_num, frame_num, total_frames, bg_color):
    """Create a single frame of the dialogue video"""
    
    # Create blank frame
    frame = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(frame)
    
    # Position elements
    speaker_x = 100 if speaker_num == 1 else width - 500
    speaker_y = 200
    
    # Add speaker image with simple "talking" animation
    animation_offset = int(5 * np.sin(frame_num * 0.3))  # Simple mouth movement
    speaker_pos = (speaker_x, speaker_y + animation_offset)
    
    # Resize and paste speaker image
    frame.paste(speaker_img, speaker_pos)
    
    # Add speech bubble
    bubble_x = speaker_x + 450 if speaker_num == 1 else speaker_x - 450
    bubble_y = speaker_y + 50
    
    # Draw speech bubble background
    bubble_width = 600
    bubble_height = 200
    draw.rounded_rectangle(
        [bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height],
        radius=20,
        fill=(240, 240, 240),
        outline=(200, 200, 200),
        width=2
    )
    
    # Add dialogue text
    try:
        # Try to load a font
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Wrap text to fit in bubble
    wrapped_text = wrap_text(dialogue_text, font, bubble_width - 40)
    
    # Draw text
    text_x = bubble_x + 20
    text_y = bubble_y + 20
    
    for line in wrapped_text.split('\n'):
        draw.text((text_x, text_y), line, fill=(50, 50, 50), font=font)
        text_y += 30
    
    # Add speaker label
    label_text = f"Speaker {speaker_num}"
    draw.text((speaker_x, speaker_y - 30), label_text, fill=(100, 100, 100), font=font)
    
    # Add timestamp
    current_time = frame_num / 30  # Assuming 30 FPS
    timestamp = f"{int(current_time//60):02d}:{int(current_time%60):02d}"
    draw.text((50, 50), timestamp, fill=(150, 150, 150), font=font)
    
    return frame

def wrap_text(text, font, max_width):
    """Wrap text to fit within specified width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        # Approximate text width (rough calculation)
        if len(test_line) * 12 < max_width:  # Rough character width estimation
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def create_default_avatar(width, height, speaker_num):
    """Create a default avatar when no photo is uploaded"""
    avatar = Image.new('RGB', (width, height), (200, 200, 200))
    draw = ImageDraw.Draw(avatar)
    
    # Draw simple face
    face_color = (255, 220, 177) if speaker_num == 1 else (255, 200, 160)
    
    # Face circle
    margin = 50
    draw.ellipse([margin, margin, width-margin, height-margin], fill=face_color, outline=(150, 150, 150))
    
    # Eyes
    eye_size = 20
    left_eye = (width//3, height//3)
    right_eye = (2*width//3, height//3)
    
    draw.ellipse([left_eye[0]-eye_size, left_eye[1]-eye_size, 
                  left_eye[0]+eye_size, left_eye[1]+eye_size], fill=(50, 50, 50))
    draw.ellipse([right_eye[0]-eye_size, right_eye[1]-eye_size, 
                  right_eye[0]+eye_size, right_eye[1]+eye_size], fill=(50, 50, 50))
    
    # Mouth
    mouth_y = 2*height//3
    draw.arc([width//3, mouth_y-20, 2*width//3, mouth_y+20], 0, 180, fill=(150, 50, 50), width=3)
    
    return avatar