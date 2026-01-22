#!/usr/bin/env python3
"""
AI Video Generator - Generate video content using AI models.

Generates dynamic video content for abstract concepts or scenes
that can't be easily captured from YouTube footage.

Supported backends:
- Runway Gen-3 Alpha (default)
- Luma Dream Machine (future)
- Pika Labs (future - requires Discord integration)
"""
import os
import sys
import time
import json
import shutil
import argparse
import tempfile
import urllib.request
from typing import Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import FRAME_RATE

# Try to import Runway SDK
try:
    from runwayml import RunwayML
    RUNWAY_AVAILABLE = True
except ImportError:
    RUNWAY_AVAILABLE = False

# Style presets for different content types
VIDEO_STYLES = {
    "cinematic": {
        "motion": "smooth cinematic camera movement, professional film quality",
        "quality": "4K, photorealistic, high detail, cinematic lighting"
    },
    "technical": {
        "motion": "slow steady camera, educational visualization",
        "quality": "clean, precise, professional technical visualization"
    },
    "dramatic": {
        "motion": "dynamic camera angles, dramatic lighting, high contrast",
        "quality": "cinematic color grading, professional production quality"
    },
    "abstract": {
        "motion": "flowing, morphing, surreal transitions",
        "quality": "artistic, stylized, creative visual effects"
    },
    "slow_motion": {
        "motion": "extremely slow motion, time appears frozen",
        "quality": "high frame rate feel, crystal clear detail"
    },
    "aerial": {
        "motion": "sweeping aerial view, drone-like movement",
        "quality": "epic scale, cinematic landscape, high altitude perspective"
    },
    "closeup": {
        "motion": "tight focus, subtle movement, intimate perspective",
        "quality": "macro detail, shallow depth of field, sharp focus"
    }
}

# F1-specific context for prompts
F1_VIDEO_CONTEXT = """
Formula 1 racing context:
- Modern F1 cars: sleek, low, complex aerodynamics, open wheels
- Race circuits: Iconic tracks with grandstands, barriers, kerbs
- High-speed action: 200+ mph, tire smoke, sparks flying
- Professional motorsport atmosphere: team garages, pit crews
"""


def generate_runway_video(prompt: str, style: str = "cinematic",
                          duration: int = 4) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Generate video using Runway Gen-3.

    Args:
        prompt: Text description of the video to generate
        style: Video style preset
        duration: Duration in seconds (4 or 10)

    Returns:
        (success, video_path, error)
    """
    if not RUNWAY_AVAILABLE:
        return False, None, "Runway SDK not installed. Run: pip install runwayml"

    api_key = os.environ.get("RUNWAY_API_KEY")
    if not api_key:
        return False, None, "RUNWAY_API_KEY environment variable not set"

    style_config = VIDEO_STYLES.get(style, VIDEO_STYLES["cinematic"])

    # Build enhanced prompt
    full_prompt = f"{prompt}. {style_config['motion']}. {style_config['quality']}"

    # Add F1 context if relevant
    f1_keywords = ["f1", "formula", "race", "car", "circuit", "track", "pit", "driver"]
    if any(kw in prompt.lower() for kw in f1_keywords):
        full_prompt = f"{F1_VIDEO_CONTEXT}\n\n{full_prompt}"

    try:
        client = RunwayML(api_key=api_key)

        print(f"  Submitting to Runway Gen-3...")

        # Create generation task
        task = client.image_to_video.create(
            model="gen3a_turbo",
            prompt_text=full_prompt,
            duration=duration,
            ratio="16:9"
        )

        # Poll for completion
        task_id = task.id
        print(f"  Task ID: {task_id}")
        print(f"  Waiting for generation", end="", flush=True)

        max_polls = 120  # 10 minutes max
        poll_count = 0

        while poll_count < max_polls:
            status = client.tasks.retrieve(task_id)

            if status.status == "SUCCEEDED":
                print(" Done!")
                video_url = status.output[0]
                break
            elif status.status == "FAILED":
                print(" Failed!")
                return False, None, f"Generation failed: {status.failure}"
            elif status.status == "CANCELLED":
                print(" Cancelled!")
                return False, None, "Generation was cancelled"

            print(".", end="", flush=True)
            time.sleep(5)
            poll_count += 1

        if poll_count >= max_polls:
            return False, None, "Generation timed out after 10 minutes"

        # Download video
        print(f"  Downloading video...")
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        urllib.request.urlretrieve(video_url, temp_file.name)

        return True, temp_file.name, None

    except Exception as e:
        return False, None, str(e)


def generate_placeholder_video(prompt: str, output_path: str,
                               duration: float = 4) -> Tuple[bool, Optional[str]]:
    """
    Generate a placeholder video when AI generation is not available.

    Creates a simple video with the prompt text displayed.
    """
    import subprocess

    # Create a simple placeholder with FFmpeg
    filter_complex = (
        f"color=c=black:s=1920x1080:d={duration},"
        f"drawtext=text='{prompt[:100]}':fontcolor=white:fontsize=24:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:font=monospace"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s=1920x1080:d={duration}:r={FRAME_RATE}",
        "-vf", f"drawtext=text='[AI Video Placeholder]':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=100",
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(output_path):
        return True, None

    return False, result.stderr[:300] if result.stderr else "Placeholder generation failed"


def generate_ai_video_segment(prompt: str, style: str, output_path: str,
                              duration: int = 4, backend: str = "runway",
                              use_placeholder: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Generate AI video for a segment.

    Args:
        prompt: Text description of the video
        style: Video style preset
        output_path: Where to save the output
        duration: Duration in seconds
        backend: Which backend to use (runway, luma, pika)
        use_placeholder: If True, generate placeholder when backend unavailable

    Returns:
        (success, error_message)
    """
    print(f"  Generating AI video: {prompt[:50]}...")
    print(f"  Backend: {backend}, Style: {style}, Duration: {duration}s")

    if backend == "runway":
        if not RUNWAY_AVAILABLE and use_placeholder:
            print(f"  Runway not available, generating placeholder...")
            return generate_placeholder_video(prompt, output_path, duration)

        success, video_path, error = generate_runway_video(prompt, style, duration)
    else:
        return False, f"Unknown backend: {backend}. Available: runway"

    if not success:
        if use_placeholder:
            print(f"  Generation failed, creating placeholder...")
            return generate_placeholder_video(prompt, output_path, duration)
        return False, error

    # Move to output path
    shutil.move(video_path, output_path)
    print(f"  Generated: {output_path}")

    return True, None


def main():
    parser = argparse.ArgumentParser(description='Generate AI video content')
    parser.add_argument('--prompt', help='Video generation prompt')
    parser.add_argument('--style', default='cinematic', choices=list(VIDEO_STYLES.keys()),
                        help='Video style preset')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--duration', type=int, default=4, choices=[4, 10],
                        help='Duration in seconds (Runway supports 4 or 10)')
    parser.add_argument('--backend', default='runway', choices=['runway'],
                        help='AI backend to use')
    parser.add_argument('--placeholder', action='store_true',
                        help='Generate placeholder if backend unavailable')
    parser.add_argument('--list-styles', action='store_true',
                        help='List available video styles')
    parser.add_argument('--status', action='store_true',
                        help='Check backend availability')
    args = parser.parse_args()

    if args.list_styles:
        print("Available video styles:")
        print("=" * 60)
        for name, config in VIDEO_STYLES.items():
            print(f"\n  {name}:")
            print(f"    Motion: {config['motion'][:50]}...")
            print(f"    Quality: {config['quality'][:50]}...")
        return

    if args.status:
        print("AI Video Generator Status")
        print("=" * 40)
        print(f"Runway SDK installed: {'Yes' if RUNWAY_AVAILABLE else 'No'}")
        print(f"RUNWAY_API_KEY set: {'Yes' if os.environ.get('RUNWAY_API_KEY') else 'No'}")

        if RUNWAY_AVAILABLE and os.environ.get('RUNWAY_API_KEY'):
            print("\nRunway backend: READY")
        else:
            print("\nRunway backend: NOT CONFIGURED")
            if not RUNWAY_AVAILABLE:
                print("  Install with: pip install runwayml")
            if not os.environ.get('RUNWAY_API_KEY'):
                print("  Set RUNWAY_API_KEY environment variable")
        return

    if args.prompt:
        if not args.output:
            print("Error: --output is required")
            sys.exit(1)

        success, error = generate_ai_video_segment(
            args.prompt, args.style, args.output,
            args.duration, args.backend, args.placeholder
        )

        if success:
            print(f"Generated: {args.output}")
        else:
            print(f"Failed: {error}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
