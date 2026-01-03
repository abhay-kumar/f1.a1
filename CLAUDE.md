# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

F1.ai is an automated pipeline for creating F1-themed YouTube Shorts (60-second vertical videos). It orchestrates: script creation → fact checking → voiceover generation (ElevenLabs) → footage acquisition (yt-dlp) → video assembly (FFmpeg with GPU acceleration) → YouTube upload.

## Common Commands

```bash
# Fact-check script content
python3 src/fact_checker.py --project {name}
python3 src/fact_checker.py --project {name} --web-search --api-key YOUR_KEY

# Check/apply phonetic pronunciation corrections
python3 src/phonetics.py --project {name} --mode analyze
python3 src/phonetics.py --project {name} --mode phonetic --apply

# Generate voiceovers (concurrent by default)
python3 src/audio_generator.py --project {name}
python3 src/audio_generator.py --project {name} --sequential  # disable concurrency

# Download footage (concurrent by default)
python3 src/footage_downloader.py --project {name}
python3 src/footage_downloader.py --project {name} --workers 5  # custom concurrency
python3 src/footage_downloader.py --project {name} --sequential  # disable concurrency

# Download footage for specific segment with custom query
python3 src/footage_downloader.py --project {name} --segment 0 --query "F1 race highlights"

# Check footage status
python3 src/footage_downloader.py --project {name} --list

# Extract preview frames (concurrent by default)
python3 src/preview_extractor.py --project {name}

# Assemble final video (concurrent + GPU acceleration by default)
python3 src/video_assembler.py --project {name}
python3 src/video_assembler.py --project {name} --encoder nvenc  # NVIDIA GPU
python3 src/video_assembler.py --project {name} --encoder cpu    # CPU fallback
python3 src/video_assembler.py --project {name} --workers 8      # custom concurrency

# Preview upload metadata (dry run)
python3 src/youtube_uploader.py --project {name} --dry-run

# Upload to YouTube
python3 src/youtube_uploader.py --project {name}
```

## Architecture

**Pipeline Flow:**
```
script.json → fact_check → phonetics → audio/*.mp3 → footage/*.mp4 → previews/*.jpg → output/final.mp4 → YouTube
```

**Core Modules (`src/`):**
- `config.py` - Centralized settings, API keys, F1 team colors, video specs, concurrency settings
- `fact_checker.py` - **NEW** Script validation against F1 knowledge base + optional web search
- `phonetics.py` - **NEW** Pronunciation correction for F1 proper nouns (drivers, teams, circuits)
- `audio_generator.py` - ElevenLabs TTS with caching and **concurrent processing**
- `footage_downloader.py` - yt-dlp YouTube search/download with **concurrent downloads**
- `preview_extractor.py` - Frame extraction with **concurrent processing**
- `video_assembler.py` - FFmpeg composition with **GPU acceleration** and **concurrent segment processing**
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
- SerpAPI (fact checking web search, optional)

## Critical Technical Notes

1. **Always verify footage with previews** - YouTube search often returns incorrect videos; run preview_extractor and visually check before assembly
2. **30fps is mandatory** - Mixed framerates cause audio/video desync; video_assembler enforces this
3. **FFmpeg split filter required** - Cannot consume the same stream twice in filter graphs
4. **Re-encode during concat** - Stream copy corrupts timestamps with mixed source formats
5. **Cache awareness** - Audio files are cached; delete segment MP3 to regenerate
6. **Duration validation** - Assembly verifies video/audio durations match within 1 second

## Performance Features

### Concurrency
All pipeline stages support concurrent processing by default:
- **Audio generation**: 4 concurrent API calls (ElevenLabs rate-limit friendly)
- **Footage download**: 3 concurrent downloads (YouTube respectful)
- **Video assembly**: CPU core count workers for parallel segment encoding
- **Preview extraction**: 4 concurrent frame extractions

Use `--sequential` flag on any command to disable concurrency for debugging.
Use `--workers N` to customize the concurrency level.

### GPU Acceleration
Video encoding automatically detects and uses GPU acceleration:
- **macOS**: VideoToolbox (Metal) - `h264_videotoolbox`
- **Linux/Windows with NVIDIA**: NVENC (CUDA) - `h264_nvenc`
- **Fallback**: CPU encoding with libx264

Force a specific encoder with `--encoder [auto|videotoolbox|nvenc|cpu]`

## Quality Assurance Features

### Fact Checking (`fact_checker.py`)
Validates F1 script content against:
- Built-in F1 knowledge base (champions, teams, records, famous moments)
- Optional web search verification (requires SerpAPI key)

```bash
python3 src/fact_checker.py --project {name} --strict  # Exit non-zero if unverified claims
```

### Phonetics (`phonetics.py`)
Ensures correct pronunciation of F1 proper nouns:
- 60+ driver pronunciations (Verstappen → "Fur-STAH-pn")
- Team names (Ferrari → "feh-RAH-ree")
- Circuits (Spa-Francorchamps → "SPAH fron-kor-SHOM")
- F1 terminology (Eau Rouge → "oh ROOZH")

```bash
python3 src/phonetics.py --list  # Show all pronunciations
```

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
