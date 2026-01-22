#!/usr/bin/env python3
"""
Visual Router - Routes segments to appropriate visual generators based on type.

Supports visual types:
- footage: YouTube footage (official F1 channels prioritized)
- graphic: AI-generated images with Ken Burns animation
- animation: AI-generated video (Runway/Pika)
- diagram: Manim programmatic animations
- library: Pre-built reusable assets
"""
import os
import sys
import json
import argparse
from typing import Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir

# Thread-safe print
print_lock = threading.Lock()


def safe_print(msg: str):
    """Thread-safe printing."""
    with print_lock:
        print(msg, flush=True)


# Check available generators
def check_generators():
    """Check which generators are available."""
    available = {}

    try:
        from src.footage_downloader import download_segment_enhanced
        available['footage'] = True
    except ImportError:
        available['footage'] = False

    try:
        from src.graphic_generator import generate_graphic_segment
        available['graphic'] = True
    except ImportError:
        available['graphic'] = False

    try:
        from src.ai_video_generator import generate_ai_video_segment
        available['animation'] = True
    except ImportError:
        available['animation'] = False

    try:
        from src.manim_generator import generate_manim_segment
        available['diagram'] = True
    except ImportError:
        available['diagram'] = False

    try:
        from src.asset_library import get_library_asset
        available['library'] = True
    except ImportError:
        available['library'] = False

    return available


def process_segment(segment: Dict, idx: int, output_dir: str,
                    validate: bool = False) -> Tuple[int, bool, str, Optional[str]]:
    """
    Route segment to appropriate generator.

    Returns: (idx, success, source_type, error)
    """
    output_file = f"{output_dir}/segment_{idx:02d}.mp4"

    # Check if already exists
    if os.path.exists(output_file):
        return idx, True, "cached", None

    visual_type = segment.get("visual_type", "footage")

    try:
        if visual_type == "footage":
            try:
                from src.footage_downloader import download_segment_enhanced
            except ImportError:
                # Fall back to basic downloader
                from src.footage_downloader import download_segment
                args = (idx, segment, output_dir, f"segment_{idx:02d}.mp4")
                _, success, title, error = download_segment(args)
                return idx, success, "footage", error

            success, error = download_segment_enhanced(segment, output_file, validate=validate)
            return idx, success, "footage", error

        elif visual_type == "graphic":
            try:
                from src.graphic_generator import generate_graphic_segment
            except ImportError:
                return idx, False, "graphic", "Graphic generator not available (pip install openai)"

            success, error = generate_graphic_segment(
                description=segment.get("graphic_description", segment.get("text", "")),
                style=segment.get("graphic_style", "technical_diagram"),
                output_path=output_file,
                duration=segment.get("duration", 5),
                effect=segment.get("graphic_effect", "zoom_in")
            )
            return idx, success, "graphic", error

        elif visual_type == "animation":
            try:
                from src.ai_video_generator import generate_ai_video_segment
            except ImportError:
                return idx, False, "animation", "AI video generator not available (pip install runwayml)"

            success, error = generate_ai_video_segment(
                prompt=segment.get("animation_prompt", segment.get("text", "")),
                style=segment.get("animation_style", "cinematic"),
                output_path=output_file,
                duration=segment.get("duration", 4)
            )
            return idx, success, "animation", error

        elif visual_type == "diagram":
            try:
                from src.manim_generator import generate_manim_segment
            except ImportError:
                return idx, False, "diagram", "Manim generator not available (pip install manim)"

            success, error = generate_manim_segment(
                diagram_type=segment.get("diagram_type"),
                params=segment.get("diagram_params", {}),
                output_path=output_file,
                duration=segment.get("duration", 5)
            )
            return idx, success, "diagram", error

        elif visual_type == "library":
            try:
                from src.asset_library import get_library_asset
            except ImportError:
                return idx, False, "library", "Asset library not available"

            success, error = get_library_asset(
                asset_name=segment.get("library_asset"),
                output_path=output_file
            )
            return idx, success, "library", error

        else:
            return idx, False, "unknown", f"Unknown visual_type: {visual_type}"

    except Exception as e:
        return idx, False, visual_type, str(e)


def main():
    parser = argparse.ArgumentParser(description='Generate all visual content for a project')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--segment', type=int, help='Process single segment')
    parser.add_argument('--sequential', action='store_true', help='Disable concurrency')
    parser.add_argument('--workers', type=int, default=3, help='Max concurrent workers')
    parser.add_argument('--list', action='store_true', help='List segments and their types')
    parser.add_argument('--validate', action='store_true', help='Enable validation for footage')
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    output_dir = f"{project_dir}/footage"
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    with open(script_file) as f:
        script = json.load(f)

    segments = script.get("segments", [])

    # List mode
    if args.list:
        print("=" * 70)
        print(f"Visual Content - Project: {args.project}")
        print("=" * 70)

        type_counts = {}
        for i, seg in enumerate(segments):
            visual_type = seg.get("visual_type", "footage")
            type_counts[visual_type] = type_counts.get(visual_type, 0) + 1

            output_file = f"{output_dir}/segment_{i:02d}.mp4"
            status = "[OK]" if os.path.exists(output_file) else "[  ]"

            context = seg.get('context', seg.get('text', 'segment')[:30])
            print(f"{status} [{i:02d}] {visual_type:10} | {context[:40]}")

            if visual_type == "graphic":
                desc = seg.get('graphic_description', '')[:50]
                print(f"           Style: {seg.get('graphic_style', 'default')}")
                if desc:
                    print(f"           Desc: {desc}...")
            elif visual_type == "diagram":
                print(f"           Type: {seg.get('diagram_type', 'unknown')}")
            elif visual_type == "library":
                print(f"           Asset: {seg.get('library_asset', 'unknown')}")
            elif visual_type == "animation":
                print(f"           Style: {seg.get('animation_style', 'cinematic')}")

        print("-" * 70)
        print("Summary by type:")
        for vtype, count in sorted(type_counts.items()):
            print(f"  {vtype}: {count} segments")

        # Check generator availability
        available = check_generators()
        print("\nGenerator availability:")
        for gen, avail in available.items():
            status = "available" if avail else "not installed"
            print(f"  {gen}: {status}")
        return

    # Single segment mode
    if args.segment is not None:
        if args.segment >= len(segments):
            print(f"Error: Segment {args.segment} not found (max: {len(segments)-1})")
            sys.exit(1)

        segment = segments[args.segment]
        visual_type = segment.get("visual_type", "footage")
        print(f"Processing segment {args.segment}: {visual_type}")

        idx, success, source, error = process_segment(
            segment, args.segment, output_dir, args.validate
        )

        if success:
            if source == "cached":
                print(f"Already exists (cached)")
            else:
                print(f"Success: {source}")
        else:
            print(f"Failed: {error}")
            sys.exit(1)
        return

    # Batch mode
    print("=" * 70)
    print(f"Generating Visual Content - Project: {args.project}")
    print("=" * 70)

    # Check availability
    available = check_generators()
    print("\nGenerator status:")
    for gen, avail in available.items():
        status = "OK" if avail else "NOT AVAILABLE"
        print(f"  {gen}: {status}")
    print()

    # Count types needed
    types_needed = {}
    for seg in segments:
        vtype = seg.get("visual_type", "footage")
        types_needed[vtype] = types_needed.get(vtype, 0) + 1

    # Warn about unavailable generators
    for vtype, count in types_needed.items():
        if not available.get(vtype, False) and vtype != "footage":
            print(f"WARNING: {count} segments need '{vtype}' but generator is not available")

    print(f"\nProcessing {len(segments)} segments...")
    if args.validate:
        print("Validation: ENABLED")
    print()

    results = {"success": 0, "cached": 0, "failed": 0}
    type_results = {}

    if args.sequential:
        for i, seg in enumerate(segments):
            visual_type = seg.get("visual_type", "footage")
            context = seg.get('context', seg.get('text', 'segment')[:25])
            print(f"[{i:02d}] {visual_type}: {context}...", end=" ", flush=True)

            idx, success, source, error = process_segment(
                seg, i, output_dir, args.validate
            )

            if source == "cached":
                print("Cached")
                results["cached"] += 1
            elif success:
                print(f"Done ({source})")
                results["success"] += 1
                type_results[source] = type_results.get(source, 0) + 1
            else:
                print(f"Failed: {error}")
                results["failed"] += 1
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(process_segment, seg, i, output_dir, args.validate): i
                for i, seg in enumerate(segments)
            }

            for future in as_completed(futures):
                idx = futures[future]
                idx, success, source, error = future.result()
                seg = segments[idx]
                context = seg.get('context', seg.get('text', 'segment')[:25])

                if source == "cached":
                    safe_print(f"[{idx:02d}] Cached: {context}")
                    results["cached"] += 1
                elif success:
                    safe_print(f"[{idx:02d}] Done ({source}): {context}")
                    results["success"] += 1
                    type_results[source] = type_results.get(source, 0) + 1
                else:
                    safe_print(f"[{idx:02d}] Failed: {error}")
                    results["failed"] += 1

    print(f"\n{'=' * 70}")
    print(f"Results: {results['success']} generated | {results['cached']} cached | {results['failed']} failed")
    if type_results:
        print(f"By type: {type_results}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
