# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

F1.ai is an automated pipeline for creating F1-themed YouTube videos. It supports two formats:

1. **Shorts** (60-second vertical videos, 9:16) - Quick, engaging content for mobile
2. **Long-form** (~10-minute horizontal videos, 16:9, up to 4K) - In-depth content with references

Both formats orchestrate: script creation → fact checking → voiceover generation (ElevenLabs) → footage acquisition (yt-dlp) → video assembly (FFmpeg with GPU acceleration) → YouTube upload.

## Common Commands

### Shared Commands (Both Formats)

```bash
# Fact-check script content
python3 src/fact_checker.py --project {name}
python3 src/fact_checker.py --project {name} --web-search --api-key YOUR_KEY
python3 src/fact_checker.py --project {name} --validate-refs  # Check reference coverage (long-form)
python3 src/fact_checker.py --project {name} --suggest-refs --web-search  # Get source suggestions

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
```

### Shorts Commands (9:16 Vertical)

```bash
# Assemble short video (1080x1920)
python3 src/video_assembler.py --project {name}
python3 src/video_assembler.py --project {name} --encoder nvenc  # NVIDIA GPU
python3 src/video_assembler.py --project {name} --encoder cpu    # CPU fallback

# Upload short to YouTube
python3 src/youtube_uploader.py --project {name} --dry-run      # Preview metadata
python3 src/youtube_uploader.py --project {name}                 # Upload
```

### Long-Form Commands (16:9 Horizontal, 4K/HD)

```bash
# RECOMMENDED: Advanced visual assembler with intelligent routing
python3 src/image_video_assembler.py --project {name}                     # HD default
python3 src/image_video_assembler.py --project {name} --resolution 4k     # 4K output
python3 src/image_video_assembler.py --project {name} --no-talking-head   # Disable talking head
python3 src/image_video_assembler.py --project {name} --veo3              # Enable Veo3 AI video
python3 src/image_video_assembler.py --project {name} --analyze           # Preview visual routing
python3 src/image_video_assembler.py --project {name} --no-music          # Skip background music

# Visual types (automatically routed based on script content):
# - f1_image: High-quality F1 photos from Pexels/Unsplash with Ken Burns effects
# - youtube_clip: Official F1 footage for action sequences
# - talking_head: AI presenter for concept explanations
# - quote_overlay: Speaker image + quote text
# - veo3_video: AI-generated video for abstract concepts (requires --veo3 flag)

# Alternative: Footage-based assembly (downloads YouTube videos)
python3 src/video_assembler_longform.py --project {name}                    # 4K default
python3 src/video_assembler_longform.py --project {name} --resolution hd    # 1080p
python3 src/video_assembler_longform.py --project {name} --with-text        # Add burned-in captions

# Upload long-form video to YouTube (includes references in description)
python3 src/youtube_uploader_longform.py --project {name} --dry-run  # Preview metadata
python3 src/youtube_uploader_longform.py --project {name}             # Upload
```

## Architecture

**Pipeline Flow:**
```
script.json → fact_check → audio/*.mp3 → footage/*.mp4 → previews/*.jpg → output/final.mp4 → YouTube
```

**Core Modules (`src/`):**
- `config.py` - Centralized settings, API keys, F1 team colors, video specs (shorts + long-form)
- `fact_checker.py` - Script validation with knowledge base, web search, and **reference validation**
- `audio_generator.py` - ElevenLabs TTS with caching and **concurrent processing**
- `footage_downloader.py` - yt-dlp YouTube search/download with **concurrent downloads** (shorts only)
- `stock_image_fetcher.py` - Pexels/Unsplash API for stock photos (long-form)
- `image_video_assembler.py` - **Long-form**: Intelligent visual routing with images, talking head, YouTube clips, quotes, and Veo3
- `veo3_generator.py` - Google Veo3 AI video generation for abstract concepts
- `video_assembler.py` - Shorts: 9:16 vertical FFmpeg composition with GPU acceleration
- `video_assembler_longform.py` - Long-form: 16:9 horizontal with YouTube footage (legacy)
- `youtube_uploader.py` - Shorts: OAuth upload with #Shorts hashtag
- `youtube_uploader_longform.py` - Long-form: Standard video upload with **references in description**

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
- yt-dlp (YouTube download - for shorts)
- ElevenLabs API (TTS)
- Pexels API (stock images - for long-form)
- Unsplash API (fallback stock images - optional)
- YouTube Data API v3 (upload)
- SerpAPI (fact checking web search, optional)
- OpenAI API (DALL-E graphics - optional)

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

## script.json Format

### Shorts Format (Basic)

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

### Long-Form Format (With References)

```json
{
  "title": "The Rise of Max Verstappen",
  "format": "longform",
  "resolution": "4k",
  "duration_target": 600,
  "segments": [
    {
      "id": 1,
      "section": "intro",
      "text": "At just seventeen years old, Max Verstappen became the youngest driver ever to compete in Formula One.",
      "context": "Opening hook",
      "footage_query": "Verstappen F1 debut 2015",
      "footage_start": 45,
      "references": [
        {
          "claim": "Youngest driver ever to compete in F1 at seventeen",
          "source": "Formula 1 Official",
          "url": "https://www.formula1.com/en/drivers/max-verstappen.html",
          "date": "2024-01-15"
        }
      ]
    }
  ],
  "references_summary": [
    {
      "source": "Formula 1 Official",
      "url": "https://www.formula1.com",
      "claims_supported": [1, 3, 5]
    }
  ]
}
```

**Key Fields:**
- `footage_start`: Timestamp (seconds) in source footage to begin extraction
- `section`: Organize segments (intro, main, conclusion) - used for YouTube chapters
- `references`: Sources for factual claims - displayed in end credits and description
- `references_summary`: Consolidated source list for the entire video

## Long-Form Video Features

- **Stock Image Approach**: Uses Pexels/Unsplash photos instead of YouTube footage
- **Ken Burns Effects**: zoom_in, zoom_out, pan_left, pan_right for engaging motion
- **Quote Overlays**: Auto-detects quotes and displays with speaker images
- **4K/HD Resolution**: 3840x2160 or 1920x1080, 16:9 horizontal
- **Higher Bitrate**: 20Mbps (4K) or 12Mbps (HD) for quality
- **End Credits**: Auto-generated with sources/references
- **Image Attributions**: Auto-generated file with stock photo credits
- **No Text Overlay**: Clean footage with separate SRT for YouTube captions
- **Reference Tracking**: Every factual claim should have a source
- **YouTube Chapters**: Generated from section names
- **Description with Sources**: All references included in upload

## API Keys Setup

Store API keys in `shared/creds/`:
- `elevenlabs` - ElevenLabs TTS API key
- `pexels` - Pexels stock image API (free at https://www.pexels.com/api/)
- `unsplash` - Unsplash fallback (free at https://unsplash.com/developers)
- `openai` - OpenAI for DALL-E graphics (optional)
- `google_ai` - Google AI API key for Veo3 video generation (optional)
- `d-id` - D-ID API key for AI talking head (optional, uses simple animation if not set)
- `youtube_client_secrets.json` - YouTube OAuth credentials

### Veo3 Setup (Optional - AI Video Generation)

Veo3 generates cinematic AI videos for abstract concepts (fuel production, chemistry, etc.):

1. **Install library**: `pip install google-genai`
2. **Get API key**: Visit https://aistudio.google.com/apikey
3. **Save key**: `echo "YOUR_KEY" > shared/creds/google_ai`
4. **Enable**: Use `--veo3` flag with image_video_assembler.py

**Pricing** (as of 2025):
- Veo 3 Fast: $0.15/second (~$1.20 per 8s clip)
- Veo 3 Standard: $0.40/second (~$3.20 per 8s clip)

**When Veo3 is used**:
- Abstract concepts without specific F1 imagery (fuel chemistry, carbon capture, etc.)
- Technical visualizations (wind tunnel, molecular processes)
- When other visual sources fail to find relevant content
