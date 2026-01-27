# Create Short Video

Create an F1 short video based on user's prompt. This command handles the entire pipeline from script to final video.

## User Input

**Synopsis** (required): $ARGUMENTS

The synopsis is the topic/story idea for the short video. This argument is mandatory.

## Instructions

You are creating a short-form vertical video (9:16, ~60 seconds) for mobile consumption.

### Project Structure
```
f1.ai/
├── projects/           # Each short gets its own folder
│   └── {project-name}/
│       ├── script.json     # Video script with segments
│       ├── audio/          # Generated voiceovers (cached)
│       ├── footage/        # Downloaded source clips
│       ├── temp/           # Intermediate files
│       └── output/         # Final video
├── shared/
│   ├── music/              # Reusable background music
│   └── creds/              # API keys
├── src/                    # Core modules
│   ├── audio_generator.py
│   ├── footage_downloader.py
│   ├── video_assembler.py
│   └── preview_extractor.py
└── .claude/commands/
```

### Workflow

1. **Understand the Prompt**: Analyze what story/narrative the user wants
2. **Research** (if needed): Search web for facts, quotes, sources
3. **Create Script**: Generate `script.json` with segments containing:
   - `text`: Voiceover text (keep each segment to 1-2 sentences; if text exceeds 8 wrapped lines, the assembler auto-splits into two timed parts at a natural break point, but shorter segments are always better for short-form)
   - `context`: Segment purpose
   - `footage_query`: YouTube search query for relevant footage
   - `footage_start`: Timestamp in source video (verify with previews!)

4. **REVIEW CHECKPOINT**: Present the script to the user for review before proceeding:
   - Display the complete script with all segments
   - Show title, segment texts, and footage queries
   - **STOP and wait for user approval** before continuing
   - User may request changes to the script before proceeding
   - Only continue to step 5 after explicit user approval

5. **Download Footage**: Use yt-dlp to find and download clips
6. **Verify Footage via `--list`**: CRITICAL - After downloading, run `--list` to check the actual YouTube video titles match the intended content. Fan channels often have screen recordings or wrong content.
7. **Fix Mismatched Footage**: If a title doesn't match:
   - Prefer official F1 channel footage over fan channels
   - For team-specific footage, download a broad official video (e.g., shakedown highlights) and use subtitle search to find the right timestamp:
     ```bash
     yt-dlp --write-auto-sub --sub-lang en --skip-download --sub-format vtt -o /tmp/subs "https://youtube.com/watch?v=VIDEO_ID"
     grep -i "team name" /tmp/subs*.vtt
     ```
   - Delete old previews (`rm previews/segNN_*.jpg`) before re-extracting
8. **Extract Previews**: Generate thumbnail frames and visually verify:
   - Footage matches the narrative (not wrong era/drivers)
   - Timestamp shows the actual moment needed
   - Update `footage_start` based on visual verification

9. **Generate Audio**: Use Gemini TTS with Alnilam voice (caches to avoid re-generation)
10. **Assemble Video**: Run video assembler with:
   - Consistent 30fps (avoids timestamp issues)
   - Blur-pad effect (no cropping)
   - Background music mixed at 15%
   - GPU encoding (VideoToolbox)

11. **Verify Final Output**: Check that:
    - Video and audio durations match
    - Video plays correctly throughout
    - Content syncs with narration

### Critical Lessons Learned

1. **Always prefer official F1 channel footage** - Fan channels often have screen recordings with cursors, news anchors, or low-quality re-uploads
2. **Use `--list` after downloading to verify titles** - Catches mismatches instantly without opening preview images
3. **Use subtitle search for team-specific timestamps** - Download subtitles with `yt-dlp --write-auto-sub` and grep for team/driver names instead of scanning preview frames
4. **Delete old previews before re-extracting** - Preview images are cached; stale images will show after footage replacement
5. **Force consistent framerate (30fps)** - Mixed framerates cause audio/video desync
6. **Use `split` filter in FFmpeg** - Can't consume same stream twice without splitting
7. **Re-encode during concat** - Stream copy causes timestamp corruption with mixed sources
8. **Cache audio files** - Don't regenerate voiceovers during video editing iterations
9. **Check video/audio stream durations** - They must match in final output

### API Keys Location
- Gemini: `shared/creds/google_ai` (free at https://aistudio.google.com/apikey)
- ElevenLabs (fallback): `shared/creds/elevenlabs`

### Voice Settings
- Engine: Google Gemini TTS (free)
- Voice: Alnilam (Male, friendly, clean American voice)
- Model: gemini-2.5-flash-preview-tts

### Commands to Use
```bash
# Generate audio with Gemini TTS (run once, caches results)
python3 src/audio_generator.py --project {name}

# Or use ElevenLabs as fallback
# python3 src/audio_generator.py --project {name} --engine elevenlabs

# Download all footage
python3 src/footage_downloader.py --project {name}

# Verify downloaded footage titles
python3 src/footage_downloader.py --project {name} --list

# Re-download a specific segment (auto-downloads top result)
python3 src/footage_downloader.py --project {name} --segment {id} --query "search terms"

# Preview candidates without downloading
python3 src/footage_downloader.py --project {name} --segment {id} --query "search terms" --dry-run

# Download specific YouTube video by URL
python3 src/footage_downloader.py --project {name} --segment {id} --url "https://youtube.com/watch?v=VIDEO_ID"

# Extract preview frames
python3 src/preview_extractor.py --project {name}

# Assemble final video
python3 src/video_assembler.py --project {name}
```

### Video Features
- **Blur-pad effect**: Full footage shown centered, blurred version as background (no cropping)
- **Text captions**: Team-colored text always at the bottom (auto-wrapped). If text exceeds 8 lines, it is automatically split into two timed parts at a natural break point (period, comma, semicolon) — part 1 shows first, then gets replaced by part 2
- **Background music**: Epic cinematic track mixed at 15% volume
- **GPU encoding**: VideoToolbox for fast processing

### Output
Final video: `projects/{name}/output/final.mp4`
- Format: 1080x1920 (9:16 vertical)
- Duration: ~60 seconds
- Framerate: 30fps
- Audio: Voiceover + background music
- Captions: Auto-generated from script text

### Next Step
After the video is created, suggest the user run `/f1-upload-short` to upload to YouTube.
