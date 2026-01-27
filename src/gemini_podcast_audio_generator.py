#!/usr/bin/env python3
"""
Gemini Podcast Audio Generator - Creates podcast audio using Google Gemini TTS

Uses Gemini 2.5 Pro/Flash TTS models for high-quality, expressive speech synthesis.
Supports SSML markup and emotion markers for immersive podcast experiences.

Free tier: Gemini 2.5 Flash TTS (lower quality but free)
Pro tier: Gemini 2.5 Pro TTS (highest quality)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import SHARED_DIR, get_project_dir
from src.ssml_generator import generate_ssml

# Lower concurrency for Gemini free tier (10 RPM limit)
# Using 2 workers with rate limiting is optimal
GEMINI_MAX_CONCURRENT = 2

# Gemini TTS Configuration
GEMINI_KEY_FILE = f"{SHARED_DIR}/creds/google_ai"
GEMINI_MODEL_PRO = "gemini-2.5-pro-preview-tts"
GEMINI_MODEL_FLASH = "gemini-2.5-flash-preview-tts"

# Voice options for Gemini TTS
# Each voice has a distinctive characteristic
GEMINI_VOICES = {
    # Bright/Energetic voices
    "zephyr": "Zephyr",  # Bright
    "puck": "Puck",  # Upbeat
    "fenrir": "Fenrir",  # Excitable
    # Warm/Conversational voices
    "kore": "Kore",  # Firm
    "aoede": "Aoede",  # Breezy
    "leda": "Leda",  # Youthful
    # Deep/Authoritative voices
    "charon": "Charon",  # Informative
    "orus": "Orus",  # Firm
    # Soft/Calm voices
    "enceladus": "Enceladus",  # Breathy
    "vale": "Vale",  # Mellow
}

# Default voice for F1 Burnouts podcast (conversational, engaging)
DEFAULT_VOICE = "Charon"  # Informative tone, good for podcast hosting

# Rate limiting for free tier (10 requests per minute)
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60  # seconds
MAX_RETRIES = 3
RETRY_BASE_DELAY = 10  # seconds

# Global rate limiter state
_rate_limiter_lock = Lock()
_request_timestamps: list = []


def _rate_limit_wait():
    """Wait if necessary to respect rate limits"""
    global _request_timestamps

    with _rate_limiter_lock:
        now = time.time()

        # Remove timestamps older than the window
        _request_timestamps = [
            ts for ts in _request_timestamps if now - ts < RATE_LIMIT_WINDOW
        ]

        # If we've hit the limit, wait
        if len(_request_timestamps) >= RATE_LIMIT_REQUESTS:
            oldest = min(_request_timestamps)
            wait_time = RATE_LIMIT_WINDOW - (now - oldest) + 1
            if wait_time > 0:
                print(f"  [Rate limit] Waiting {wait_time:.1f}s...", flush=True)
                time.sleep(wait_time)

        # Record this request
        _request_timestamps.append(time.time())


def get_gemini_key() -> str:
    """Read Gemini API key from credentials file"""
    if not os.path.exists(GEMINI_KEY_FILE):
        raise FileNotFoundError(
            f"Gemini API key not found at {GEMINI_KEY_FILE}\n"
            "Get your free API key at: https://aistudio.google.com/apikey\n"
            f"Then save it: echo 'YOUR_KEY' > {GEMINI_KEY_FILE}"
        )
    with open(GEMINI_KEY_FILE) as f:
        return f.read().strip()


def wave_file_write(
    filename: str,
    pcm_data: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2,
) -> None:
    """Write PCM data to a WAV file"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def convert_wav_to_mp3(wav_path: str, mp3_path: str, bitrate: str = "256k") -> bool:
    """Convert WAV to MP3 using FFmpeg"""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        wav_path,
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        mp3_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up WAV file
    if result.returncode == 0 and os.path.exists(wav_path):
        os.remove(wav_path)

    return result.returncode == 0


def get_duration(file_path: str) -> float:
    """Get audio duration in seconds using ffprobe"""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0


def generate_audio_gemini(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    model: str = GEMINI_MODEL_FLASH,
    use_ssml: bool = True,
    emotion: str = "energetic",
) -> Tuple[bool, Optional[str]]:
    """
    Generate audio using Google Gemini TTS

    Args:
        text: Text to synthesize (plain or SSML-enhanced)
        output_path: Path for output MP3 file
        voice: Gemini voice name (e.g., "Charon", "Kore")
        model: Gemini model to use (flash or pro)
        use_ssml: Whether to enhance text with SSML
        emotion: Emotion for SSML generation

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return False, "google-genai not installed. Run: pip install google-genai"

    # Get API key
    try:
        api_key = get_gemini_key()
    except FileNotFoundError as e:
        return False, str(e)

    # Initialize client
    client = genai.Client(api_key=api_key)

    # Enhance text with SSML if requested
    if use_ssml:
        enhanced_text = generate_ssml(text, emotion)
    else:
        enhanced_text = text

    # Retry loop with exponential backoff
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            # Apply rate limiting before each request
            _rate_limit_wait()

            # Generate audio
            response = client.models.generate_content(
                model=model,
                contents=enhanced_text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice,
                            )
                        )
                    ),
                ),
            )

            # Extract audio data
            if not response.candidates:
                return False, "No audio generated - empty response"

            audio_data = response.candidates[0].content.parts[0].inline_data.data

            if not audio_data:
                return False, "No audio data in response"

            # Write to WAV file first (Gemini outputs PCM)
            wav_path = output_path.replace(".mp3", ".wav")
            wave_file_write(wav_path, audio_data)

            # Convert to MP3
            if not convert_wav_to_mp3(wav_path, output_path):
                return False, "Failed to convert WAV to MP3"

            return True, None

        except Exception as e:
            error_str = str(e)
            last_error = error_str

            # Check if it's a rate limit error
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                # Extract retry delay if provided
                retry_match = re.search(r"retry in (\d+(?:\.\d+)?)", error_str.lower())
                if retry_match:
                    wait_time = float(retry_match.group(1)) + 1
                else:
                    wait_time = RETRY_BASE_DELAY * (2**attempt)

                if attempt < MAX_RETRIES - 1:
                    print(
                        f"  [Retry {attempt + 1}/{MAX_RETRIES}] Rate limited, waiting {wait_time:.0f}s...",
                        flush=True,
                    )
                    time.sleep(wait_time)
                    continue
            else:
                # Non-rate-limit error, don't retry
                return False, f"Gemini TTS error: {error_str}"

    return False, f"Max retries exceeded. Last error: {last_error}"


def process_segment(args: Tuple) -> Tuple[int, bool, float, Optional[str]]:
    """Process a single segment (for concurrent execution)"""
    idx, segment, audio_path, voice, model, use_ssml = args

    # Check cache
    if os.path.exists(audio_path):
        duration = get_duration(audio_path)
        return idx, True, duration, "cached"

    text = segment["text"]
    emotion = segment.get("emotion", "energetic")

    success, error = generate_audio_gemini(
        text=text,
        output_path=audio_path,
        voice=voice,
        model=model,
        use_ssml=use_ssml,
        emotion=emotion,
    )

    if success:
        duration = get_duration(audio_path)
        return idx, True, duration, None
    else:
        return idx, False, 0, error


def concatenate_audio(audio_files: list, output_path: str) -> bool:
    """Concatenate all audio segments into final podcast"""
    # Create file list for ffmpeg
    list_file = output_path.replace(".mp3", "_list.txt")
    with open(list_file, "w") as f:
        for audio_file in audio_files:
            f.write(f"file '{audio_file}'\n")

    # Concatenate with ffmpeg
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_file,
        "-c:a",
        "libmp3lame",
        "-b:a",
        "256k",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up list file
    if os.path.exists(list_file):
        os.remove(list_file)

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate podcast audio using Google Gemini TTS"
    )
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument(
        "--model",
        choices=["flash", "pro"],
        default="flash",
        help="Gemini model: flash (free, fast) or pro (paid, highest quality)",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Voice name (default: {DEFAULT_VOICE}). Options: {', '.join(GEMINI_VOICES.values())}",
    )
    parser.add_argument(
        "--no-ssml",
        action="store_true",
        help="Disable SSML enhancement (use plain text)",
    )
    parser.add_argument(
        "--sequential", action="store_true", help="Disable concurrent processing"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=GEMINI_MAX_CONCURRENT,
        help=f"Max concurrent workers (default: {GEMINI_MAX_CONCURRENT}, optimized for free tier)",
    )
    parser.add_argument(
        "--skip-concat",
        action="store_true",
        help="Skip final concatenation (segments only)",
    )
    parser.add_argument(
        "--segment", type=int, help="Only generate specific segment (0-indexed)"
    )
    parser.add_argument(
        "--list-voices", action="store_true", help="List available voices and exit"
    )
    args = parser.parse_args()

    # List voices and exit
    if args.list_voices:
        print("Available Gemini TTS Voices:")
        print("-" * 40)
        for key, name in GEMINI_VOICES.items():
            print(f"  {name}")
        print(f"\nDefault: {DEFAULT_VOICE}")
        sys.exit(0)

    # Setup paths
    project_dir = get_project_dir(args.project)
    audio_dir = f"{project_dir}/audio"
    output_dir = f"{project_dir}/output"
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Load script
    with open(script_file) as f:
        script = json.load(f)

    # Select model
    model = GEMINI_MODEL_PRO if args.model == "pro" else GEMINI_MODEL_FLASH
    use_ssml = not args.no_ssml
    voice = args.voice

    print("=" * 60)
    print(f"Gemini Podcast Audio Generator - Project: {args.project}")
    print(f"Model: {args.model.upper()} ({model})")
    print(f"Voice: {voice}")
    print(f"SSML Enhancement: {'Enabled' if use_ssml else 'Disabled'}")
    print(
        f"Concurrency: {'Sequential' if args.sequential else f'{args.workers} workers'}"
    )
    print("=" * 60)

    segments = script["segments"]

    # Single segment mode
    if args.segment is not None:
        if args.segment >= len(segments):
            print(f"Error: Segment {args.segment} not found (max: {len(segments) - 1})")
            sys.exit(1)

        segment = segments[args.segment]
        audio_path = f"{audio_dir}/segment_{args.segment:02d}.mp3"

        print(f"\nGenerating segment {args.segment}...")
        print(f"Context: {segment.get('context', 'N/A')}")
        print(f"Emotion: {segment.get('emotion', 'energetic')}")

        # Remove cached version to force regeneration
        if os.path.exists(audio_path):
            os.remove(audio_path)

        success, error = generate_audio_gemini(
            text=segment["text"],
            output_path=audio_path,
            voice=voice,
            model=model,
            use_ssml=use_ssml,
            emotion=segment.get("emotion", "energetic"),
        )

        if success:
            duration = get_duration(audio_path)
            print(f"Success! Duration: {duration:.1f}s")
            print(f"Output: {audio_path}")
        else:
            print(f"Failed: {error}")
            sys.exit(1)

        sys.exit(0)

    # Prepare all tasks
    tasks = []
    for i, segment in enumerate(segments):
        audio_path = f"{audio_dir}/segment_{i:02d}.mp3"
        tasks.append((i, segment, audio_path, voice, model, use_ssml))

    generated = 0
    cached = 0
    failed = 0
    results = {}

    if args.sequential:
        # Sequential processing
        for task in tasks:
            idx = task[0]
            segment = task[1]
            context = segment.get("context", "Segment")[:30]
            emotion = segment.get("emotion", "energetic")

            print(
                f"[{idx + 1}/{len(segments)}] {context} ({emotion})...",
                end=" ",
                flush=True,
            )

            idx, success, duration, status = process_segment(task)

            if status == "cached":
                print(f"Cached ({duration:.1f}s)")
                cached += 1
            elif success:
                print(f"Done ({duration:.1f}s)")
                generated += 1
            else:
                print(f"Failed: {status}")
                failed += 1

            results[idx] = (success, duration)
    else:
        # Concurrent processing
        print(f"\nProcessing {len(segments)} segments concurrently...")

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_idx = {
                executor.submit(process_segment, task): task[0] for task in tasks
            }

            for future in as_completed(future_to_idx):
                idx, success, duration, status = future.result()
                segment = segments[idx]
                context = segment.get("context", "Segment")[:30]
                emotion = segment.get("emotion", "energetic")

                if status == "cached":
                    print(
                        f"[{idx + 1}/{len(segments)}] Cached ({duration:.1f}s) - {context}"
                    )
                    cached += 1
                elif success:
                    print(
                        f"[{idx + 1}/{len(segments)}] Generated ({duration:.1f}s) - {context}"
                    )
                    generated += 1
                else:
                    print(f"[{idx + 1}/{len(segments)}] Failed - {status} - {context}")
                    failed += 1

                results[idx] = (success, duration)

    # Calculate total duration
    total_duration = sum(
        get_duration(f"{audio_dir}/segment_{i:02d}.mp3")
        for i in range(len(segments))
        if os.path.exists(f"{audio_dir}/segment_{i:02d}.mp3")
    )

    print(f"\n{'=' * 60}")
    print("Segment Generation Complete")
    print(f"Generated: {generated} | Cached: {cached} | Failed: {failed}")
    print(
        f"Total segment duration: {total_duration:.1f}s ({total_duration / 60:.1f} min)"
    )

    if failed > 0:
        print(f"\nWarning: {failed} segments failed. Fix errors and re-run.")
        sys.exit(1)

    # Concatenate all segments
    if not args.skip_concat:
        print(f"\n{'=' * 60}")
        print("Concatenating segments into final podcast...")

        audio_files = [f"{audio_dir}/segment_{i:02d}.mp3" for i in range(len(segments))]
        output_path = f"{output_dir}/final.mp3"

        if concatenate_audio(audio_files, output_path):
            final_duration = get_duration(output_path)
            print(f"Success! Final podcast: {output_path}")
            print(f"Duration: {final_duration:.1f}s ({final_duration / 60:.1f} min)")
        else:
            print("Error: Failed to concatenate audio segments")
            sys.exit(1)
    else:
        print(f"\nSkipped concatenation. Segments saved to: {audio_dir}/")

    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
