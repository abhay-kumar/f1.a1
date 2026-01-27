#!/usr/bin/env python3
"""
SSML Generator - Creates expressive SSML markup for immersive podcast TTS

Converts plain podcast scripts into SSML-enhanced text with:
- Emotion markers [excited], [contemplative], etc.
- Prosody control for rate, pitch, volume
- Strategic pauses for emphasis
- Natural speech patterns
"""

import json
import os
import re
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir

# Emotion to Gemini TTS marker mapping
# Gemini supports: [angry], [excited], [sarcastic], [scornful], [empathetic],
#                  [shouting], [whispering], [laughing], [sighing], [speaking slowly]
EMOTION_MARKERS = {
    "energetic": "[excited]",
    "intrigued": "[intrigued]",
    "contemplative": "[speaking slowly]",
    "humorous": "[playful]",
    "heartfelt": "[empathetic]",
    "serious": "[serious]",
    "passionate": "[passionate]",
}

# Prosody settings for different emotions
PROSODY_SETTINGS = {
    "energetic": {"rate": "105%", "pitch": "+5%"},
    "intrigued": {"rate": "95%", "pitch": "+2%"},
    "contemplative": {"rate": "85%", "pitch": "-3%"},
    "humorous": {"rate": "100%", "pitch": "+3%"},
    "heartfelt": {"rate": "90%", "pitch": "-2%"},
    "serious": {"rate": "92%", "pitch": "-5%"},
    "passionate": {"rate": "102%", "pitch": "+3%"},
}

# Patterns that should have pauses
PAUSE_PATTERNS = [
    # After introductory phrases
    (r"(Welcome back[^.!?]*[.!?])", r"\1 <break time='0.8s'/>"),
    (r"(I'm your host[^.!?]*[.!?])", r"\1 <break time='0.5s'/>"),
    # Before dramatic reveals
    (
        r"(And here's (?:the thing|where it gets|what I think)[^:]*:)",
        r"<break time='0.4s'/> \1",
    ),
    (r"(But here's the (?:thing|deal|catch)[^:]*:)", r"<break time='0.4s'/> \1"),
    # After questions (rhetorical pause)
    (r"(\?)\s+([A-Z])", r"? <break time='0.6s'/> \2"),
    # Before "Now" transitions
    (r"\.\s+(Now,)", r". <break time='0.5s'/> \1"),
    (r"\.\s+(Now\.\.\.)", r". <break time='0.5s'/> \1"),
    # Ellipsis pauses (natural trailing off)
    (r"\.\.\.(\s+)", r"<break time='0.4s'/>\1"),
    # After segment transitions
    (r"(Alright,)", r"<break time='0.3s'/> \1"),
    (r"(Okay,)", r"<break time='0.3s'/> \1"),
    (r"(So,)", r"<break time='0.2s'/> \1"),
    # Emphasis before key facts
    (r"(one hundred percent)", r"<emphasis level='strong'>\1</emphasis>"),
    (r"(literally)", r"<emphasis level='moderate'>\1</emphasis>"),
    (r"(genuinely)", r"<emphasis level='moderate'>\1</emphasis>"),
    (r"(absolutely)", r"<emphasis level='moderate'>\1</emphasis>"),
]

# Words/phrases to emphasize
EMPHASIS_WORDS = [
    "incredible",
    "amazing",
    "brilliant",
    "fascinating",
    "revolutionary",
    "crucial",
    "critical",
    "massive",
    "huge",
    "wild",
    "insane",
    "never",
    "always",
    "every",
    "billion",
    "million",
    "first",
    "only",
    "fastest",
    "biggest",
    "smallest",
    "zero",
    "hundred percent",
]

# Numbers that should be spoken with emphasis
NUMBER_PATTERNS = [
    (r"\b(\d{4})\b", r'<say-as interpret-as="year">\1</say-as>'),  # Years
    (
        r"\b(\d+(?:\.\d+)?)\s*percent\b",
        r'<say-as interpret-as="cardinal">\1</say-as> percent',
    ),
    (r"\b(\d+)\s*kilometers?\s*per\s*hour\b", r"\1 kilometers per hour"),
    (r"\b(\d+)\s*mph\b", r"\1 miles per hour"),
]


def add_emotion_marker(text: str, emotion: str) -> str:
    """Add emotion marker at the start of the text"""
    marker = EMOTION_MARKERS.get(emotion, "")
    if marker:
        return f"{marker} {text}"
    return text


def add_prosody_wrapper(text: str, emotion: str) -> str:
    """Wrap text in prosody tags based on emotion"""
    settings = PROSODY_SETTINGS.get(emotion)
    if settings:
        rate = settings.get("rate", "100%")
        pitch = settings.get("pitch", "+0%")
        return f'<prosody rate="{rate}" pitch="{pitch}">{text}</prosody>'
    return text


def add_pauses(text: str) -> str:
    """Add strategic pauses for natural speech rhythm"""
    result = text
    for pattern, replacement in PAUSE_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result


def add_emphasis(text: str) -> str:
    """Add emphasis to key words and phrases"""
    result = text
    for word in EMPHASIS_WORDS:
        # Case-insensitive replacement, preserve original case
        pattern = rf"\b({word})\b"
        result = re.sub(
            pattern,
            r'<emphasis level="moderate">\1</emphasis>',
            result,
            flags=re.IGNORECASE,
        )
    return result


def process_numbers(text: str) -> str:
    """Process numbers for better TTS pronunciation"""
    result = text
    for pattern, replacement in NUMBER_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def enhance_punctuation(text: str) -> str:
    """Enhance punctuation for more expressive speech"""
    result = text

    # Add micro-pauses after commas in lists
    result = re.sub(r",\s+", ", ", result)

    # Exclamation marks get slight pause before
    result = re.sub(r"(\w)(!)", r"\1 !", result)

    # Em-dashes indicate interruption/aside - add pauses
    result = re.sub(r"\s*—\s*", " <break time='0.2s'/> ", result)
    result = re.sub(r"\s*--\s*", " <break time='0.2s'/> ", result)

    return result


def add_breath_marks(text: str) -> str:
    """Add natural breathing points for long sentences"""
    # Split into sentences
    sentences = re.split(r"([.!?]+)", text)
    result_parts = []

    for i, part in enumerate(sentences):
        if re.match(r"[.!?]+", part):
            result_parts.append(part)
        elif len(part) > 150:  # Long sentence
            # Add breath mark at natural break points (after clauses)
            part = re.sub(
                r"(,\s+(?:and|but|or|so|because|when|while|if|although)\s+)",
                r"\1<break time='0.2s'/>",
                part,
            )
            result_parts.append(part)
        else:
            result_parts.append(part)

    return "".join(result_parts)


def generate_ssml(text: str, emotion: str = "energetic") -> str:
    """
    Generate SSML-enhanced text for Gemini TTS

    Combines:
    - Emotion markers at the start
    - Prosody control for rate/pitch
    - Strategic pauses
    - Word emphasis
    - Natural breathing marks
    """
    # Start with the raw text
    result = text

    # 1. Process numbers for better pronunciation
    result = process_numbers(result)

    # 2. Add emphasis to key words
    result = add_emphasis(result)

    # 3. Enhance punctuation
    result = enhance_punctuation(result)

    # 4. Add strategic pauses
    result = add_pauses(result)

    # 5. Add breath marks for long sentences
    result = add_breath_marks(result)

    # 6. Add emotion marker at the start
    result = add_emotion_marker(result, emotion)

    # 7. Wrap in prosody for overall emotion-based delivery
    # Note: Gemini may not fully support prosody, but it doesn't hurt
    # result = add_prosody_wrapper(result, emotion)

    return result


def process_script(script: Dict) -> Dict:
    """
    Process entire script.json and add SSML markup to all segments

    Returns a new script dict with 'ssml_text' field added to each segment
    """
    enhanced_script = script.copy()
    enhanced_script["segments"] = []

    for segment in script["segments"]:
        enhanced_segment = segment.copy()
        emotion = segment.get("emotion", "energetic")
        original_text = segment["text"]

        # Generate SSML-enhanced version
        ssml_text = generate_ssml(original_text, emotion)
        enhanced_segment["ssml_text"] = ssml_text

        enhanced_script["segments"].append(enhanced_segment)

    return enhanced_script


def main():
    """CLI for testing SSML generation"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate SSML for podcast scripts")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument(
        "--preview", action="store_true", help="Preview SSML without saving"
    )
    parser.add_argument(
        "--segment", type=int, help="Only process specific segment (0-indexed)"
    )
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    with open(script_file) as f:
        script = json.load(f)

    if args.segment is not None:
        # Preview single segment
        if args.segment >= len(script["segments"]):
            print(
                f"Error: Segment {args.segment} not found (max: {len(script['segments']) - 1})"
            )
            sys.exit(1)

        segment = script["segments"][args.segment]
        emotion = segment.get("emotion", "energetic")

        print(f"{'=' * 60}")
        print(f"Segment {args.segment}: {segment.get('context', 'No context')}")
        print(f"Emotion: {emotion}")
        print(f"{'=' * 60}")
        print("\nOriginal:")
        print(segment["text"])
        print(f"\n{'-' * 60}")
        print("\nSSML Enhanced:")
        print(generate_ssml(segment["text"], emotion))
        print(f"{'=' * 60}")
    else:
        # Process entire script
        enhanced = process_script(script)

        if args.preview:
            # Just show preview
            print(f"{'=' * 60}")
            print(f"SSML Preview - {len(enhanced['segments'])} segments")
            print(f"{'=' * 60}\n")

            for i, segment in enumerate(enhanced["segments"][:3]):  # First 3 only
                print(
                    f"[Segment {i}] {segment.get('context', '')} ({segment.get('emotion', 'energetic')})"
                )
                print(f"SSML: {segment['ssml_text'][:200]}...")
                print()

            if len(enhanced["segments"]) > 3:
                print(f"... and {len(enhanced['segments']) - 3} more segments")
        else:
            # Save enhanced script
            output_file = f"{project_dir}/script_ssml.json"
            with open(output_file, "w") as f:
                json.dump(enhanced, f, indent=2)

            print(f"Enhanced script saved to: {output_file}")
            print(f"Processed {len(enhanced['segments'])} segments")


if __name__ == "__main__":
    main()
