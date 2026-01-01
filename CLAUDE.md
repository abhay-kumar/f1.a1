# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

F1.ai is an automated pipeline for creating F1-themed YouTube Shorts (60-second vertical videos). It orchestrates: script creation → voiceover generation (ElevenLabs) → footage acquisition (yt-dlp) → video assembly (FFmpeg) → YouTube upload.

## Common Commands

```bash
# Generate voiceovers for all segments
python3 src/audio_generator.py --project {name}

# Download footage (batch mode)
python3 src/footage_downloader.py --project {name}

# Download footage for specific segment with custom query
python3 src/footage_downloader.py --project {name} --segment 0 --query "F1 race highlights"

# Check footage status
python3 src/footage_downloader.py --project {name} --list

# Extract preview frames for verification
python3 src/preview_extractor.py --project {name}

# Assemble final video
python3 src/video_assembler.py --project {name}

# Preview upload metadata (dry run)
python3 src/youtube_uploader.py --project {name} --dry-run

# Upload to YouTube
python3 src/youtube_uploader.py --project {name}
```

## Architecture

**Pipeline Flow:**
```
script.json → audio/*.mp3 → footage/*.mp4 → previews/*.jpg → output/final.mp4 → YouTube
```

**Core Modules (`src/`):**
- `config.py` - Centralized settings, API keys, F1 team colors, video specs (1080x1920, 30fps)
- `audio_generator.py` - ElevenLabs TTS with caching (Bradford voice)
- `footage_downloader.py` - yt-dlp YouTube search/download with multiple modes
- `preview_extractor.py` - Frame extraction for footage verification before assembly
- `video_assembler.py` - FFmpeg composition with blur-pad effect, captions, background music
- `youtube_uploader.py` - OAuth upload with auto-generated metadata

**Project Structure:**
```
projects/{name}/
├── script.json      # Segments with text, footage_query, footage_start
├── audio/           # Generated voiceovers (segment_00.mp3, ...)
├── footage/         # Downloaded clips (segment_00.mp4, ...)
├── previews/        # Frame extractions for QA
├── output/          # Final video (final.mp4)
└── upload_info.json # YouTube video ID and URL after upload
```

**External Dependencies:**
- ffmpeg/ffprobe (video processing)
- yt-dlp (YouTube download)
- ElevenLabs API (TTS)
- YouTube Data API v3 (upload)

## Critical Technical Notes

1. **Always verify footage with previews** - YouTube search often returns incorrect videos; run preview_extractor and visually check before assembly
2. **30fps is mandatory** - Mixed framerates cause audio/video desync; video_assembler enforces this
3. **FFmpeg split filter required** - Cannot consume the same stream twice in filter graphs
4. **Re-encode during concat** - Stream copy corrupts timestamps with mixed source formats
5. **Cache awareness** - Audio files are cached; delete segment MP3 to regenerate
6. **Duration validation** - Assembly verifies video/audio durations match within 1 second

## script.json Format

```json
{
  "title": "Video Title",
  "duration_target": 60,
  "segments": [
    {
      "id": 1,
      "text": "Voiceover narration text",
      "context": "Editorial note (not rendered)",
      "footage_query": "YouTube search terms",
      "footage_start": 55,
      "footage": "segment_00.mp4"
    }
  ]
}
```

The `footage_start` field specifies the timestamp (seconds) in the source footage to begin extraction.
