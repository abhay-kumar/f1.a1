#!/usr/bin/env python3
"""
Footage Validator - Validates downloaded footage for quality.

Combines face detection (talking heads), text detection (burned-in subtitles),
and optional CLIP-based content matching to ensure footage meets quality standards.

Quality checks:
1. Face detection - Reject footage with talking heads
2. Text detection - Reject footage with burned-in subtitles
3. Content matching - Ensure footage matches script (optional, requires CLIP)
"""
import os
import sys
import json
import argparse
from typing import Tuple, Dict, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir

# Try to import validators
try:
    from src.validators.face_detector import detect_talking_head
    FACE_AVAILABLE = True
except ImportError:
    FACE_AVAILABLE = False

try:
    from src.validators.text_detector import detect_burned_in_text
    TEXT_AVAILABLE = True
except ImportError:
    TEXT_AVAILABLE = False

try:
    from src.validators.content_matcher import match_content_to_script
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False

# Default thresholds
DEFAULT_FACE_THRESHOLD = 0.4  # Max face score (0-1), above = reject
DEFAULT_TEXT_THRESHOLD = 0.3  # Max text score (0-1), above = reject
DEFAULT_CLIP_THRESHOLD = 0.4  # Min CLIP score (0-1), below = reject


def quick_validate(video_path: str, script_text: str = "",
                   face_threshold: float = DEFAULT_FACE_THRESHOLD,
                   text_threshold: float = DEFAULT_TEXT_THRESHOLD) -> Tuple[bool, str]:
    """
    Quick validation for use during download.

    Only runs face and text detection (fast).
    Returns (is_valid, reason).
    """
    reasons = []

    # Face check
    if FACE_AVAILABLE:
        is_talking, score, detail = detect_talking_head(video_path, face_threshold)
        if is_talking:
            reasons.append(f"talking_head:{score:.2f}")

    # Text check
    if TEXT_AVAILABLE:
        has_text, score, detail = detect_burned_in_text(video_path, text_threshold)
        if has_text:
            reasons.append(f"burned_text:{score:.2f}")

    if reasons:
        return False, ", ".join(reasons)

    return True, "passed"


def full_validate(video_path: str, script_text: str = "",
                  face_threshold: float = DEFAULT_FACE_THRESHOLD,
                  text_threshold: float = DEFAULT_TEXT_THRESHOLD,
                  clip_threshold: float = DEFAULT_CLIP_THRESHOLD) -> Dict:
    """
    Full validation with all checks and detailed results.

    Returns dict with:
    - passed: bool
    - face_score: float
    - text_score: float
    - clip_score: float (if enabled)
    - issues: list of issue descriptions
    """
    result = {
        "passed": True,
        "face_score": 0.0,
        "text_score": 0.0,
        "clip_score": 0.5,  # Neutral default
        "issues": [],
        "validators_used": []
    }

    # Face detection
    if FACE_AVAILABLE:
        result["validators_used"].append("face")
        is_talking, score, reason = detect_talking_head(video_path, face_threshold)
        result["face_score"] = score
        if is_talking:
            result["passed"] = False
            result["issues"].append(f"Talking head detected: {reason}")

    # Text detection
    if TEXT_AVAILABLE:
        result["validators_used"].append("text")
        has_text, score, reason = detect_burned_in_text(video_path, text_threshold)
        result["text_score"] = score
        if has_text:
            result["passed"] = False
            result["issues"].append(f"Burned-in text detected: {reason}")

    # Content matching (optional, requires script text)
    if CLIP_AVAILABLE and script_text:
        result["validators_used"].append("clip")
        is_relevant, score, reason = match_content_to_script(
            video_path, script_text, clip_threshold
        )
        result["clip_score"] = score
        if not is_relevant:
            result["passed"] = False
            result["issues"].append(f"Content mismatch: {reason}")

    return result


def validate_project(project_name: str, face_threshold: float = DEFAULT_FACE_THRESHOLD,
                     text_threshold: float = DEFAULT_TEXT_THRESHOLD,
                     clip_threshold: float = DEFAULT_CLIP_THRESHOLD,
                     use_clip: bool = False) -> Dict:
    """
    Validate all footage in a project.

    Returns dict with segment-by-segment results.
    """
    project_dir = get_project_dir(project_name)
    footage_dir = f"{project_dir}/footage"
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        return {"error": f"Script not found: {script_file}"}

    with open(script_file) as f:
        script = json.load(f)

    segments = script.get("segments", [])
    results = {
        "project": project_name,
        "total_segments": len(segments),
        "passed": 0,
        "failed": 0,
        "missing": 0,
        "segments": []
    }

    for i, seg in enumerate(segments):
        footage_file = f"{footage_dir}/segment_{i:02d}.mp4"

        seg_result = {
            "index": i,
            "context": seg.get("context", seg.get("text", "")[:30]),
            "file": footage_file
        }

        if not os.path.exists(footage_file):
            seg_result["status"] = "missing"
            results["missing"] += 1
        else:
            script_text = seg.get("text", "") if use_clip else ""
            validation = full_validate(
                footage_file, script_text,
                face_threshold, text_threshold, clip_threshold
            )
            seg_result.update(validation)

            if validation["passed"]:
                seg_result["status"] = "passed"
                results["passed"] += 1
            else:
                seg_result["status"] = "failed"
                results["failed"] += 1

        results["segments"].append(seg_result)

    return results


def main():
    parser = argparse.ArgumentParser(description='Validate footage quality')
    parser.add_argument('--project', help='Project name to validate')
    parser.add_argument('--file', help='Single file to validate')
    parser.add_argument('--script-text', help='Script text for CLIP matching')
    parser.add_argument('--face-threshold', type=float, default=DEFAULT_FACE_THRESHOLD,
                        help=f'Face detection threshold (default: {DEFAULT_FACE_THRESHOLD})')
    parser.add_argument('--text-threshold', type=float, default=DEFAULT_TEXT_THRESHOLD,
                        help=f'Text detection threshold (default: {DEFAULT_TEXT_THRESHOLD})')
    parser.add_argument('--clip-threshold', type=float, default=DEFAULT_CLIP_THRESHOLD,
                        help=f'CLIP matching threshold (default: {DEFAULT_CLIP_THRESHOLD})')
    parser.add_argument('--use-clip', action='store_true',
                        help='Enable CLIP content matching')
    parser.add_argument('--status', action='store_true',
                        help='Check validator availability')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON')
    args = parser.parse_args()

    if args.status:
        print("Footage Validator Status")
        print("=" * 40)
        print(f"Face detector: {'Available' if FACE_AVAILABLE else 'Not installed'}")
        print(f"Text detector: {'Available' if TEXT_AVAILABLE else 'Not installed'}")
        print(f"CLIP matcher:  {'Available' if CLIP_AVAILABLE else 'Not installed'}")

        if not FACE_AVAILABLE:
            print("\nInstall face detector: pip install opencv-python")
        if not TEXT_AVAILABLE:
            print("\nInstall text detector: pip install opencv-python paddleocr")
        if not CLIP_AVAILABLE:
            print("\nInstall CLIP: pip install torch clip-by-openai")
        return

    if args.file:
        # Single file validation
        print(f"Validating: {args.file}")
        result = full_validate(
            args.file,
            args.script_text or "",
            args.face_threshold,
            args.text_threshold,
            args.clip_threshold
        )

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nResult: {'PASSED' if result['passed'] else 'FAILED'}")
            print(f"Face score: {result['face_score']:.2f} (threshold: {args.face_threshold})")
            print(f"Text score: {result['text_score']:.2f} (threshold: {args.text_threshold})")
            if 'clip' in result.get('validators_used', []):
                print(f"CLIP score: {result['clip_score']:.2f} (threshold: {args.clip_threshold})")

            if result['issues']:
                print("\nIssues:")
                for issue in result['issues']:
                    print(f"  - {issue}")

    elif args.project:
        # Project validation
        print(f"Validating project: {args.project}")
        print("-" * 50)

        results = validate_project(
            args.project,
            args.face_threshold,
            args.text_threshold,
            args.clip_threshold,
            args.use_clip
        )

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for seg in results["segments"]:
                status_icon = {
                    "passed": "[OK]",
                    "failed": "[!!]",
                    "missing": "[--]"
                }.get(seg["status"], "[??]")

                print(f"{status_icon} [{seg['index']:02d}] {seg['context'][:40]}")

                if seg["status"] == "failed":
                    for issue in seg.get("issues", []):
                        print(f"         {issue}")

            print("-" * 50)
            print(f"Passed: {results['passed']} | Failed: {results['failed']} | Missing: {results['missing']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
