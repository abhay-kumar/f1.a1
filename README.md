# F1.ai

Automated pipeline for creating F1-themed YouTube Shorts. Generates 60-second vertical videos with professional voiceovers, dynamic captions, and background music.

## Features

- **AI Voiceovers** - ElevenLabs TTS with expressive British narrator
- **Smart Footage Search** - YouTube search and download via yt-dlp
- **F1 Branding** - Official team colors, Formula1 font, styled captions
- **Blur-Pad Effect** - No cropping; blurred background with centered footage
- **One-Click Upload** - YouTube API integration with auto-generated metadata

## Pipeline

```
Script → Voiceover → Footage → Preview → Assemble → Upload
```

## Requirements

- Python 3.10+
- ffmpeg/ffprobe
- yt-dlp
- ElevenLabs API key
- YouTube OAuth credentials (for upload)

## Installation

```bash
# Clone the repository
git clone https://github.com/abhay-kumar/f1.a1.git
cd f1.a1

# Install Python dependencies
pip install requests google-auth-oauthlib google-api-python-client

# Install system dependencies (macOS)
brew install ffmpeg yt-dlp

# Set up credentials
mkdir -p shared/creds
echo "your-elevenlabs-api-key" > shared/creds/elevenlabs
# Place youtube_client_secrets.json in shared/creds/
```

## Quick Start

1. **Create a project directory and script:**
   ```bash
   mkdir -p projects/my-video
   # Create projects/my-video/script.json (see format below)
   ```

2. **Generate voiceovers:**
   ```bash
   python3 src/audio_generator.py --project my-video
   ```

3. **Download footage:**
   ```bash
   python3 src/footage_downloader.py --project my-video
   ```

4. **Verify footage (important!):**
   ```bash
   python3 src/preview_extractor.py --project my-video
   # Check previews/ folder and adjust footage_start in script.json
   ```

5. **Assemble video:**
   ```bash
   python3 src/video_assembler.py --project my-video
   ```

6. **Upload to YouTube:**
   ```bash
   python3 src/youtube_uploader.py --project my-video
   ```

## Script Format

```json
{
  "title": "The Untold Story",
  "duration_target": 60,
  "segments": [
    {
      "id": 1,
      "text": "Narration text for voiceover",
      "context": "Editorial note (not rendered)",
      "footage_query": "F1 Monaco 2024 highlights",
      "footage_start": 30
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `text` | Voiceover narration (sent to TTS) |
| `context` | Internal note for documentation |
| `footage_query` | YouTube search terms |
| `footage_start` | Start timestamp in source footage (seconds) |

## Output Specs

- Resolution: 1080x1920 (9:16 vertical)
- Framerate: 30fps
- Video: H.264, 8Mbps
- Audio: AAC, 192kbps
- Duration: ~60 seconds

## Project Structure

```
f1.ai/
├── src/                    # Core modules
│   ├── config.py           # Settings and F1 colors
│   ├── audio_generator.py  # ElevenLabs TTS
│   ├── footage_downloader.py
│   ├── preview_extractor.py
│   ├── video_assembler.py  # FFmpeg composition
│   └── youtube_uploader.py
├── projects/               # Video projects (gitignored)
├── shared/
│   ├── creds/              # API credentials (gitignored)
│   ├── fonts/              # F1 branding fonts
│   └── music/              # Background track
└── CLAUDE.md               # AI assistant guidance
```

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
