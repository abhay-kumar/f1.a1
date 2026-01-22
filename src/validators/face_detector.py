#!/usr/bin/env python3
"""
Face Detector - Detect talking heads in footage.

Uses OpenCV's Haar cascades for fast face detection.
Scores footage based on face prominence and position.

A "talking head" is defined as:
- Face occupying significant portion of frame
- Face centered or prominently positioned
- Face appearing in multiple frames
"""
import os
import subprocess
import tempfile
from typing import Tuple, List
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def extract_frames(video_path: str, num_frames: int = 5) -> List[np.ndarray]:
    """
    Extract evenly-spaced frames from video.

    Focuses on middle 80% of video to avoid intro/outro cards.
    """
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


def detect_faces_in_frame(frame: np.ndarray, cascade_path: str = None) -> List[Tuple]:
    """
    Detect faces in a single frame.

    Returns list of (x, y, w, h) tuples for each detected face.
    """
    if not CV2_AVAILABLE:
        return []

    # Use default frontal face cascade
    if cascade_path is None:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

    cascade = cv2.CascadeClassifier(cascade_path)

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(50, 50)  # Minimum face size
    )

    return list(faces)


def score_face_prominence(faces: List[Tuple], frame_shape: Tuple) -> float:
    """
    Score face prominence based on size and position.

    Higher score = more prominent face = more likely talking head.

    Factors:
    - Face size relative to frame
    - Face position (centered = higher score)
    - Number of faces (single face = higher score)
    """
    if not faces:
        return 0.0

    frame_h, frame_w = frame_shape[:2]
    frame_area = frame_h * frame_w

    max_score = 0.0

    for (x, y, w, h) in faces:
        face_area = w * h

        # Size score: face area / frame area
        # Normalize to 0-1 range (25% of frame = 1.0)
        size_score = min(1.0, (face_area / frame_area) * 4)

        # Position score: centered = higher
        face_center_x = x + w / 2
        face_center_y = y + h / 2

        x_offset = abs(face_center_x - frame_w / 2) / (frame_w / 2)
        y_offset = abs(face_center_y - frame_h / 2) / (frame_h / 2)

        # More centered = higher score
        center_score = 1.0 - (x_offset * 0.5 + y_offset * 0.5)

        # Combined score
        combined = (size_score * 0.6) + (center_score * 0.4)
        max_score = max(max_score, combined)

    # Penalty for multiple faces (less likely to be single talking head)
    if len(faces) > 1:
        max_score *= 0.7

    return min(1.0, max_score)


def detect_talking_head(video_path: str,
                        threshold: float = 0.4) -> Tuple[bool, float, str]:
    """
    Detect if video contains a talking head.

    Args:
        video_path: Path to video file
        threshold: Score threshold (above = talking head)

    Returns:
        (is_talking_head, score, reason)
    """
    if not CV2_AVAILABLE:
        return False, 0.0, "OpenCV not available"

    if not os.path.exists(video_path):
        return False, 0.0, "File not found"

    # Extract sample frames
    frames = extract_frames(video_path, num_frames=5)
    if not frames:
        return False, 0.0, "Could not extract frames"

    # Detect faces in each frame
    frame_scores = []
    frames_with_faces = 0

    for frame in frames:
        faces = detect_faces_in_frame(frame)
        if faces:
            frames_with_faces += 1
            score = score_face_prominence(faces, frame.shape)
            frame_scores.append(score)
        else:
            frame_scores.append(0.0)

    # Overall score: average of frame scores
    if frame_scores:
        avg_score = sum(frame_scores) / len(frame_scores)
    else:
        avg_score = 0.0

    # Boost score if faces appear in multiple frames
    consistency_boost = (frames_with_faces / len(frames)) * 0.2
    final_score = min(1.0, avg_score + consistency_boost)

    # Determine result
    is_talking = final_score >= threshold

    if is_talking:
        reason = f"Prominent face in {frames_with_faces}/{len(frames)} frames"
    else:
        reason = "No prominent faces detected"

    return is_talking, final_score, reason


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Detect talking heads in video')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--threshold', type=float, default=0.4,
                        help='Detection threshold (default: 0.4)')
    parser.add_argument('--debug', action='store_true',
                        help='Save debug images with face boxes')
    args = parser.parse_args()

    if not CV2_AVAILABLE:
        print("Error: OpenCV not installed. Run: pip install opencv-python")
        return

    is_talking, score, reason = detect_talking_head(args.video, args.threshold)

    print(f"Video: {args.video}")
    print(f"Score: {score:.2f}")
    print(f"Threshold: {args.threshold}")
    print(f"Result: {'TALKING HEAD DETECTED' if is_talking else 'No talking head'}")
    print(f"Reason: {reason}")

    if args.debug:
        # Save debug frames with face boxes
        frames = extract_frames(args.video, num_frames=5)
        for i, frame in enumerate(frames):
            faces = detect_faces_in_frame(frame)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            debug_path = f"debug_face_{i}.jpg"
            cv2.imwrite(debug_path, frame)
            print(f"Saved: {debug_path}")


if __name__ == "__main__":
    main()
