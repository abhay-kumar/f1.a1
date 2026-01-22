#!/usr/bin/env python3
"""
Text Detector - Detect burned-in subtitles in footage.

Uses OpenCV edge detection for fast basic detection,
with optional PaddleOCR for higher accuracy.

Focuses on bottom 30% of frame where subtitles typically appear.
"""
import os
from typing import Tuple, List
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Try to import PaddleOCR for more accurate text detection
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False


def extract_frames(video_path: str, num_frames: int = 5) -> List[np.ndarray]:
    """Extract evenly-spaced frames from video."""
    if not CV2_AVAILABLE:
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames < num_frames:
        cap.release()
        return []

    # Focus on middle 80%
    start_frame = int(total_frames * 0.1)
    end_frame = int(total_frames * 0.9)
    frame_range = end_frame - start_frame

    frames = []
    step = frame_range // (num_frames + 1)

    for i in range(1, num_frames + 1):
        frame_idx = start_frame + (i * step)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            frames.append(frame)

    cap.release()
    return frames


def detect_text_edges(frame: np.ndarray, subtitle_region_ratio: float = 0.3) -> float:
    """
    Basic text detection using edge density in subtitle region.

    Returns a score from 0-1 indicating likelihood of text.
    """
    height, width = frame.shape[:2]

    # Focus on bottom portion where subtitles appear
    subtitle_region = frame[int(height * (1 - subtitle_region_ratio)):, :]

    # Convert to grayscale
    gray = cv2.cvtColor(subtitle_region, cv2.COLOR_BGR2GRAY)

    # Apply Canny edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Calculate edge density
    edge_density = np.sum(edges > 0) / edges.size

    # Text typically has moderate edge density (0.05-0.15)
    # Very low = no text, very high = busy scene
    if edge_density < 0.02:
        return 0.0
    elif edge_density > 0.2:
        # Likely busy scene, not just text
        return 0.3
    else:
        # In the text-likely range
        return min(1.0, edge_density * 5)


def detect_text_ocr(frame: np.ndarray, subtitle_region_ratio: float = 0.3) -> Tuple[float, List[str]]:
    """
    Accurate text detection using PaddleOCR.

    Returns (score, list of detected text strings).
    """
    if not PADDLE_AVAILABLE:
        return 0.0, []

    height, width = frame.shape[:2]

    # Focus on bottom portion
    subtitle_region = frame[int(height * (1 - subtitle_region_ratio)):, :]

    # Initialize OCR (use_angle_cls for rotated text, lang='en' for English)
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

    # Run OCR
    result = ocr.ocr(subtitle_region, cls=True)

    if not result or not result[0]:
        return 0.0, []

    # Extract text and calculate score
    texts = []
    total_confidence = 0

    for line in result[0]:
        if line and len(line) >= 2:
            text = line[1][0]
            confidence = line[1][1]
            if text.strip():
                texts.append(text)
                total_confidence += confidence

    if not texts:
        return 0.0, []

    # Score based on number of text regions and confidence
    avg_confidence = total_confidence / len(texts)
    text_count_score = min(1.0, len(texts) / 5)  # More text = higher score

    final_score = (avg_confidence * 0.6) + (text_count_score * 0.4)

    return final_score, texts


def detect_burned_in_text(video_path: str,
                          threshold: float = 0.3,
                          use_ocr: bool = None) -> Tuple[bool, float, str]:
    """
    Detect if video has burned-in text/subtitles.

    Args:
        video_path: Path to video file
        threshold: Score threshold (above = has text)
        use_ocr: Use PaddleOCR (auto-detect if None)

    Returns:
        (has_text, score, reason)
    """
    if not CV2_AVAILABLE:
        return False, 0.0, "OpenCV not available"

    if not os.path.exists(video_path):
        return False, 0.0, "File not found"

    # Extract sample frames
    frames = extract_frames(video_path, num_frames=5)
    if not frames:
        return False, 0.0, "Could not extract frames"

    # Auto-detect OCR availability
    if use_ocr is None:
        use_ocr = PADDLE_AVAILABLE

    frame_scores = []
    detected_texts = []

    for frame in frames:
        if use_ocr and PADDLE_AVAILABLE:
            score, texts = detect_text_ocr(frame)
            detected_texts.extend(texts)
        else:
            score = detect_text_edges(frame)

        frame_scores.append(score)

    # Average score across frames
    avg_score = sum(frame_scores) / len(frame_scores)

    # Boost if text appears consistently
    frames_with_text = sum(1 for s in frame_scores if s > 0.1)
    consistency_boost = (frames_with_text / len(frames)) * 0.15
    final_score = min(1.0, avg_score + consistency_boost)

    # Determine result
    has_text = final_score >= threshold

    if has_text:
        if detected_texts:
            sample = detected_texts[:2]
            reason = f"Text detected: {', '.join(sample)[:50]}..."
        else:
            reason = f"Text-like patterns in {frames_with_text}/{len(frames)} frames"
    else:
        reason = "No significant text detected"

    return has_text, final_score, reason


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Detect burned-in text in video')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--threshold', type=float, default=0.3,
                        help='Detection threshold (default: 0.3)')
    parser.add_argument('--ocr', action='store_true',
                        help='Force use of OCR (requires PaddleOCR)')
    parser.add_argument('--no-ocr', action='store_true',
                        help='Disable OCR, use edge detection only')
    parser.add_argument('--debug', action='store_true',
                        help='Save debug images showing subtitle region')
    args = parser.parse_args()

    if not CV2_AVAILABLE:
        print("Error: OpenCV not installed. Run: pip install opencv-python")
        return

    use_ocr = None
    if args.ocr:
        use_ocr = True
    elif args.no_ocr:
        use_ocr = False

    has_text, score, reason = detect_burned_in_text(args.video, args.threshold, use_ocr)

    print(f"Video: {args.video}")
    print(f"Score: {score:.2f}")
    print(f"Threshold: {args.threshold}")
    print(f"OCR available: {PADDLE_AVAILABLE}")
    print(f"Result: {'TEXT DETECTED' if has_text else 'No significant text'}")
    print(f"Reason: {reason}")

    if args.debug:
        # Save debug frames with subtitle region highlighted
        frames = extract_frames(args.video, num_frames=3)
        for i, frame in enumerate(frames):
            h, w = frame.shape[:2]
            # Draw rectangle around subtitle region
            y_start = int(h * 0.7)
            cv2.rectangle(frame, (0, y_start), (w, h), (0, 255, 0), 2)
            debug_path = f"debug_text_{i}.jpg"
            cv2.imwrite(debug_path, frame)
            print(f"Saved: {debug_path}")


if __name__ == "__main__":
    main()
