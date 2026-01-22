#!/usr/bin/env python3
"""
Graphic Generator - AI image generation with Ken Burns animation.

Generates static images using DALL-E 3 (or other backends) and applies
Ken Burns effect (pan/zoom) to create video segments.

Supported backends:
- OpenAI DALL-E 3 (default)
- Stability AI (future)
- Local Stable Diffusion (future)
"""
import os
import sys
import json
import argparse
import subprocess
import tempfile
import urllib.request
from typing import Tuple, Optional, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import FRAME_RATE

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Graphic styles with prompt modifiers
GRAPHIC_STYLES = {
    "technical_diagram": {
        "prefix": "Technical engineering diagram, clean lines, labeled components, ",
        "suffix": ", white background, professional technical illustration style, blueprint aesthetic, high detail",
        "size": "1792x1024"  # Landscape for technical
    },
    "cutaway": {
        "prefix": "Detailed cross-section cutaway view showing internal structure, ",
        "suffix": ", professional engineering illustration, labeled parts, clean white background, technical accuracy",
        "size": "1792x1024"
    },
    "infographic": {
        "prefix": "Clean modern infographic showing ",
        "suffix": ", data visualization, minimal design, professional quality, clear labels",
        "size": "1024x1792"  # Portrait for infographics
    },
    "realistic": {
        "prefix": "Photorealistic high-quality render of ",
        "suffix": ", high detail, professional 3D visualization, dramatic lighting, cinematic quality",
        "size": "1792x1024"
    },
    "schematic": {
        "prefix": "Technical schematic diagram of ",
        "suffix": ", engineering drawing style, precise lines, labeled, white background, technical blueprint",
        "size": "1792x1024"
    },
    "comparison": {
        "prefix": "Side-by-side comparison diagram showing ",
        "suffix": ", clear labels, professional infographic style, visual contrast between elements",
        "size": "1792x1024"
    },
    "exploded_view": {
        "prefix": "Exploded view technical diagram showing all components of ",
        "suffix": ", parts separated and labeled, professional engineering illustration, white background",
        "size": "1792x1024"
    },
    "heatmap": {
        "prefix": "Thermal visualization heatmap showing ",
        "suffix": ", color gradient from blue (cool) to red (hot), professional scientific visualization",
        "size": "1792x1024"
    },
    "airflow": {
        "prefix": "Aerodynamic airflow visualization diagram showing ",
        "suffix": ", streamlines, pressure zones in blue (low) and red (high), professional CFD-style rendering",
        "size": "1792x1024"
    }
}

# F1-specific prompt enhancements
F1_CONTEXT = """
Formula 1 technical context. F1 cars feature:
- Front and rear wings with complex multi-element designs for downforce
- Sidepods containing radiators with dramatic undercuts
- Halo titanium safety device above cockpit
- Open-wheel design with 18-inch tires
- Ground effect venturi tunnels in the floor
- DRS (drag reduction system) flap on rear wing
- Power unit: 1.6L V6 turbo hybrid with MGU-K and MGU-H
Use accurate F1 terminology and modern 2022+ car regulations.
"""


def generate_image_dalle(prompt: str, style: str = "technical_diagram",
                         size: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Generate image using DALL-E 3.

    Returns: (success, image_path, error)
    """
    if not OPENAI_AVAILABLE:
        return False, None, "OpenAI package not installed. Run: pip install openai"

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return False, None, "OPENAI_API_KEY environment variable not set"

    style_config = GRAPHIC_STYLES.get(style, GRAPHIC_STYLES["technical_diagram"])

    # Build enhanced prompt
    full_prompt = f"{style_config['prefix']}{prompt}{style_config['suffix']}"

    # Add F1 context for F1-related content
    f1_keywords = ["f1", "formula", "car", "wing", "aero", "downforce", "tire", "tyre",
                   "diffuser", "sidepod", "floor", "drs", "kers", "ers", "mgu"]
    if any(kw in prompt.lower() for kw in f1_keywords):
        full_prompt = f"{F1_CONTEXT}\n\n{full_prompt}"

    try:
        client = OpenAI(api_key=api_key)

        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size=size or style_config["size"],
            quality="hd",
            n=1
        )

        image_url = response.data[0].url

        # Download image to temp file
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        urllib.request.urlretrieve(image_url, temp_file.name)

        return True, temp_file.name, None

    except Exception as e:
        return False, None, str(e)


def apply_ken_burns(image_path: str, output_path: str, duration: float = 5,
                    effect: str = "zoom_in", resolution: str = "1080p") -> Tuple[bool, Optional[str]]:
    """
    Apply Ken Burns effect (pan/zoom) to static image.

    Effects:
    - zoom_in: Slow zoom in to center
    - zoom_out: Start zoomed, pull back
    - pan_left: Pan from right to left
    - pan_right: Pan from left to right
    - pan_up: Pan from bottom to top
    - pan_down: Pan from top to bottom

    Resolution options:
    - 1080p: 1920x1080 (default, good for most uses)
    - 4k: 3840x2160
    - vertical: 1080x1920 (for shorts)
    """
    # Calculate frames
    total_frames = int(duration * FRAME_RATE)

    # Resolution settings
    resolutions = {
        "1080p": (1920, 1080),
        "4k": (3840, 2160),
        "vertical": (1080, 1920)
    }
    out_w, out_h = resolutions.get(resolution, (1920, 1080))

    # Ken Burns effect parameters
    effects = {
        "zoom_in": {
            "start_scale": 1.0,
            "end_scale": 1.15,
            "start_x": 0,
            "start_y": 0,
            "end_x": 0,
            "end_y": 0
        },
        "zoom_out": {
            "start_scale": 1.15,
            "end_scale": 1.0,
            "start_x": 0,
            "start_y": 0,
            "end_x": 0,
            "end_y": 0
        },
        "pan_left": {
            "start_scale": 1.1,
            "end_scale": 1.1,
            "start_x": 50,
            "start_y": 0,
            "end_x": -50,
            "end_y": 0
        },
        "pan_right": {
            "start_scale": 1.1,
            "end_scale": 1.1,
            "start_x": -50,
            "start_y": 0,
            "end_x": 50,
            "end_y": 0
        },
        "pan_up": {
            "start_scale": 1.1,
            "end_scale": 1.1,
            "start_x": 0,
            "start_y": 30,
            "end_x": 0,
            "end_y": -30
        },
        "pan_down": {
            "start_scale": 1.1,
            "end_scale": 1.1,
            "start_x": 0,
            "start_y": -30,
            "end_x": 0,
            "end_y": 30
        },
        "zoom_pan_right": {
            "start_scale": 1.0,
            "end_scale": 1.12,
            "start_x": -30,
            "start_y": 0,
            "end_x": 30,
            "end_y": 0
        }
    }

    params = effects.get(effect, effects["zoom_in"])

    # Calculate zoom expression (linear interpolation)
    start_z = params["start_scale"]
    end_z = params["end_scale"]
    z_expr = f"if(lte(on,1),{start_z},{start_z}+(on/{total_frames})*({end_z}-{start_z}))"

    # Position expressions
    start_x = params["start_x"]
    end_x = params["end_x"]
    x_expr = f"iw/2-(iw/zoom/2)+({start_x}+(on/{total_frames})*({end_x}-{start_x}))"

    start_y = params["start_y"]
    end_y = params["end_y"]
    y_expr = f"ih/2-(ih/zoom/2)+({start_y}+(on/{total_frames})*({end_y}-{start_y}))"

    # FFmpeg filter
    filter_complex = (
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
        f"d={total_frames}:s={out_w}x{out_h}:fps={FRAME_RATE},"
        f"format=yuv420p"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", image_path,
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-t", str(duration),
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, None

    return False, result.stderr[:500] if result.stderr else "FFmpeg failed"


def generate_graphic_segment(description: str, style: str, output_path: str,
                             duration: float = 5, effect: str = "zoom_in",
                             resolution: str = "1080p") -> Tuple[bool, Optional[str]]:
    """
    Complete pipeline: Generate image → Apply Ken Burns → Output video.

    Args:
        description: Text description for image generation
        style: Graphic style (see GRAPHIC_STYLES)
        output_path: Where to save the output video
        duration: Video duration in seconds
        effect: Ken Burns effect type
        resolution: Output resolution (1080p, 4k, vertical)

    Returns:
        (success, error_message)
    """
    print(f"  Generating image: {description[:50]}...")

    # Step 1: Generate image
    success, image_path, error = generate_image_dalle(description, style)
    if not success:
        return False, f"Image generation failed: {error}"

    print(f"  Applying Ken Burns effect: {effect}")

    # Step 2: Apply Ken Burns
    success, error = apply_ken_burns(image_path, output_path, duration, effect, resolution)

    # Cleanup temp image
    try:
        os.unlink(image_path)
    except Exception:
        pass

    if not success:
        return False, f"Ken Burns failed: {error}"

    print(f"  Generated: {output_path}")
    return True, None


def main():
    parser = argparse.ArgumentParser(description='Generate graphics for video segments')
    parser.add_argument('--prompt', help='Direct prompt for image generation')
    parser.add_argument('--style', default='technical_diagram',
                        choices=list(GRAPHIC_STYLES.keys()),
                        help='Graphic style')
    parser.add_argument('--output', help='Output video path')
    parser.add_argument('--duration', type=float, default=5, help='Duration in seconds')
    parser.add_argument('--effect', default='zoom_in',
                        choices=['zoom_in', 'zoom_out', 'pan_left', 'pan_right',
                                 'pan_up', 'pan_down', 'zoom_pan_right'],
                        help='Ken Burns effect type')
    parser.add_argument('--resolution', default='1080p',
                        choices=['1080p', '4k', 'vertical'],
                        help='Output resolution')
    parser.add_argument('--list-styles', action='store_true', help='List available styles')
    parser.add_argument('--image-only', action='store_true',
                        help='Generate image only (no Ken Burns)')
    args = parser.parse_args()

    if args.list_styles:
        print("Available graphic styles:")
        print("=" * 60)
        for name, config in GRAPHIC_STYLES.items():
            print(f"\n  {name}:")
            print(f"    Size: {config['size']}")
            print(f"    Prefix: {config['prefix'][:40]}...")
        print()
        print("OpenAI available:", "Yes" if OPENAI_AVAILABLE else "No")
        print("OPENAI_API_KEY set:", "Yes" if os.environ.get("OPENAI_API_KEY") else "No")
        return

    if args.prompt:
        if args.image_only:
            # Just generate image
            output = args.output or "generated_image.png"
            success, path, error = generate_image_dalle(args.prompt, args.style)
            if success:
                import shutil
                shutil.move(path, output)
                print(f"Generated: {output}")
            else:
                print(f"Failed: {error}")
                sys.exit(1)
        else:
            # Generate full video
            if not args.output:
                print("Error: --output is required")
                sys.exit(1)

            success, error = generate_graphic_segment(
                args.prompt, args.style, args.output,
                args.duration, args.effect, args.resolution
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
