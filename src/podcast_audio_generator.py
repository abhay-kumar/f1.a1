#!/usr/bin/env python3
"""
Podcast Audio Generator - Creates multi-voice podcast audio
Uses ElevenLabs API with different voices for each host
"""

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional, Tuple

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    MAX_CONCURRENT_AUDIO,
    MODEL_ID,
    get_elevenlabs_key,
    get_project_dir,
)

# Default podcast host voices
DEFAULT_HOSTS = {
    "alex": {
        "voice_id": "TxGEqnHWrfWFTfGW9XjX",  # Josh - deep, young male
        "description": "Racing and drivers enthusiast",
    },
    "sophie": {
        "voice_id": "XrExE9yKIg1WjnnlVkGX",  # Matilda - warm, young female
        "description": "Engineering and technical expert",
    },
}


def get_duration(file_path: str) -> float:
    """Get audio duration in seconds"""
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


def generate_audio(
    text: str, output_path: str, voice_id: str
) -> Tuple[bool, Optional[str]]:
    """Generate audio using ElevenLabs API with specified voice"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": get_elevenlabs_key(),
    }
    data = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=120)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True, None
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)


def process_segment(args: Tuple) -> Tuple[int, bool, float, Optional[str]]:
    """Process a single segment (for concurrent execution)"""
    idx, segment, audio_path, voice_id = args

    if os.path.exists(audio_path):
        duration = get_duration(audio_path)
        return idx, True, duration, "cached"

    success, error = generate_audio(segment["text"], audio_path, voice_id)
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
        description="Generate podcast audio with multiple voices"
    )
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument(
        "--sequential", action="store_true", help="Disable concurrent processing"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=MAX_CONCURRENT_AUDIO,
        help=f"Max concurrent workers (default: {MAX_CONCURRENT_AUDIO})",
    )
    parser.add_argument(
        "--skip-concat",
        action="store_true",
        help="Skip final concatenation (segments only)",
    )
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    audio_dir = f"{project_dir}/audio"
    output_dir = f"{project_dir}/output"
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    with open(script_file) as f:
        script = json.load(f)

    # Determine if single-host or multi-host format
    is_single_host = "host" in script and "hosts" not in script

    if is_single_host:
        # Single host format - use the "host" object
        host_config = script["host"]
        host_name = host_config.get("name", "host").lower()
        hosts = {
            host_name: {
                "voice_id": host_config["voice_id"],
                "description": host_config.get("description", "Podcast host"),
            }
        }
    else:
        # Multi-host format - use "hosts" dictionary or defaults
        hosts = script.get("hosts", DEFAULT_HOSTS)

    print("=" * 60)
    print(f"Podcast Audio Generator - Project: {args.project}")
    print(
        "Engine: ElevenLabs (Multi-voice)"
        if not is_single_host
        else "Engine: ElevenLabs (Single-voice)"
    )
    print(
        f"Concurrency: {'Sequential' if args.sequential else f'{args.workers} workers'}"
    )
    print("-" * 60)
    if is_single_host:
        print(f"Host: {script['host'].get('description', 'Podcast host')}")
    else:
        print("Hosts:")
        for h_name, h_config in hosts.items():
            print(
                f"  {h_name.capitalize()}: {h_config.get('description', 'No description')}"
            )
    print("=" * 60)

    segments = script["segments"]

    # Validate all segments have valid hosts (only for multi-host format)
    if not is_single_host:
        for i, segment in enumerate(segments):
            host = segment.get("host", "").lower()
            if host not in hosts:
                print(
                    f"Error: Segment {i + 1} has unknown host '{host}'. Valid hosts: {list(hosts.keys())}"
                )
                sys.exit(1)

    generated = 0
    cached = 0
    failed = 0

    # Prepare tasks with voice IDs
    tasks = []
    for i, segment in enumerate(segments):
        if is_single_host:
            # Single host - use the host's voice for all segments
            host_name = list(hosts.keys())[0]
            voice_id = hosts[host_name]["voice_id"]
        else:
            # Multi-host - get voice from segment's host field
            host = segment.get("host", "").lower()
            voice_id = hosts[host]["voice_id"]
        audio_path = f"{audio_dir}/segment_{i:02d}.mp3"
        tasks.append((i, segment, audio_path, voice_id))

    results = {}

    if args.sequential:
        # Sequential processing
        for task in tasks:
            idx = task[0]
            segment = task[1]
            if is_single_host:
                label = segment.get("context", "Segment")[:30]
            else:
                host = segment.get("host", "").capitalize()
                label = f"{host}: {segment.get('context', 'Dialogue')[:30]}"
            print(
                f"[{idx + 1}/{len(segments)}] {label}...",
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

                if is_single_host:
                    label = context
                else:
                    host = segment.get("host", "").capitalize()
                    label = f"{host}: {context}"

                if status == "cached":
                    print(
                        f"[{idx + 1}/{len(segments)}] Cached ({duration:.1f}s) - {label}"
                    )
                    cached += 1
                elif success:
                    print(
                        f"[{idx + 1}/{len(segments)}] Generated ({duration:.1f}s) - {label}"
                    )
                    generated += 1
                else:
                    print(f"[{idx + 1}/{len(segments)}] Failed - {status} - {label}")
                    failed += 1

                results[idx] = (success, duration)

    # Calculate total duration
    total_duration = sum(
        get_duration(f"{audio_dir}/segment_{i:02d}.mp3")
        for i in range(len(segments))
        if os.path.exists(f"{audio_dir}/segment_{i:02d}.mp3")
    )

    print(f"\n{'=' * 60}")
    print(f"Segment Generation Complete")
    print(f"Generated: {generated} | Cached: {cached} | Failed: {failed}")
    print(
        f"Total segment duration: {total_duration:.1f}s ({total_duration / 60:.1f} min)"
    )

    if failed > 0:
        print(f"\nWarning: {failed} segments failed. Fix errors and re-run.")
        sys.exit(1)

    # Concatenate all segments into final podcast
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
