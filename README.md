# Multi-Speaker Audio Transcript Generator

A Python application that generates timestamped transcripts from audio files with automatic speaker diarization.

## Features

- 🎯 **Automatic Speaker Detection**: Identifies different speakers in the audio
- ⏱️ **Precise Timestamps**: Generates SRT-style timestamps for each segment
- 🔄 **Multiple Formats**: Supports WAV and MP3 input files
- 🤖 **AI-Powered**: Uses Whisper for transcription and PyAnnote for speaker diarization
- 🖥️ **Web Interface**: Easy-to-use Streamlit interface
- 📥 **Download Ready**: Generates downloadable transcript files

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   streamlit run app.py
   ```

3. **Upload your audio file** and click "Generate Transcript"

## Output Format

The generated transcript follows this format:

```
00:00:00,000 --> 00:00:03,500
Speaker_1: Merhaba, hoş geldin.

00:00:03,600 --> 00:00:06,800
Speaker_2: Teşekkürler, seni görmek güzel.
```

## Models Used

- **Whisper**: OpenAI's speech-to-text model (automatically downloaded)
- **PyAnnote**: Speaker diarization pipeline (requires Hugging Face token for full functionality)

## Command Line Usage

You can also use the tool from command line:

```bash
python main.py path/to/your/audio.wav
```

## File Structure

```
audio-transcript-generator/
├── app.py                  # Streamlit web interface
├── main.py                 # Core processing logic
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Requirements

- Python 3.8+
- At least 4GB RAM (for model loading)
- Internet connection (for initial model downloads)

## Notes

- First run may take longer due to automatic model downloads
- For best results with speaker diarization, set up a Hugging Face token
- The application includes a fallback speaker detection method
- Generated files are automatically cleaned up after download

## Troubleshooting

If you encounter issues:

1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check that your audio file is in WAV or MP3 format
3. For speaker diarization issues, try setting up a Hugging Face token
4. Make sure you have sufficient disk space for model downloads

## License

MIT License - feel free to use and modify as needed.