#!/usr/bin/env python3
"""
Advanced Visual Assembler for Long-Form F1 Content

Creates engaging videos by intelligently blending:
1. High-quality F1 images from multiple web sources
2. AI talking head for concept explanations
3. YouTube F1 clips for action sequences
4. Quote overlays with speaker images
5. Veo3 AI-generated video for scenes without good footage

Visual routing based on script content analysis.
"""
import os
import sys
import json
import argparse
import subprocess
import tempfile
import random
import re
import time
import urllib.request
import urllib.parse
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, Optional, List, Dict
from dataclasses import dataclass
from enum import Enum
import multiprocessing

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    get_project_dir, BACKGROUND_MUSIC,
    LONGFORM_FRAME_RATE, LONGFORM_AUDIO_BITRATE,
    LONGFORM_OUTPUT_WIDTH_4K, LONGFORM_OUTPUT_HEIGHT_4K,
    LONGFORM_OUTPUT_WIDTH_HD, LONGFORM_OUTPUT_HEIGHT_HD,
    MUSIC_VOLUME_LONGFORM,
    OUTRO_AUDIO_LONGFORM, CREDITS_DURATION_LONGFORM
)

# ============================================================================
# CONFIGURATION
# ============================================================================

MIN_CLIP_DURATION = 3.0  # Minimum seconds per visual
MAX_CLIP_DURATION = 5.0  # Maximum seconds per visual
CROSSFADE_DURATION = 0.5  # Crossfade between clips
API_RATE_LIMIT_DELAY = 0.5  # Seconds between API calls

# Ken Burns effects
KEN_BURNS_EFFECTS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]

# ============================================================================
# VISUAL TYPE DEFINITIONS
# ============================================================================

class VisualType(Enum):
    F1_IMAGE = "f1_image"
    TALKING_HEAD = "talking_head"
    YOUTUBE_CLIP = "youtube_clip"
    QUOTE_OVERLAY = "quote_overlay"
    VEO3_VIDEO = "veo3_video"  # AI-generated video


@dataclass
class VisualDecision:
    primary_type: VisualType
    fallback_type: VisualType
    search_queries: List[str]
    speaker_name: Optional[str] = None
    quote_text: Optional[str] = None
    veo3_prompt: Optional[str] = None  # For AI video generation
    confidence: float = 0.8


# ============================================================================
# F1 KNOWLEDGE BASE
# ============================================================================

F1_DRIVERS = {
    "verstappen": "Max Verstappen", "hamilton": "Lewis Hamilton",
    "leclerc": "Charles Leclerc", "norris": "Lando Norris",
    "sainz": "Carlos Sainz", "russell": "George Russell",
    "perez": "Sergio Perez", "alonso": "Fernando Alonso",
    "stroll": "Lance Stroll", "ocon": "Esteban Ocon",
    "gasly": "Pierre Gasly", "tsunoda": "Yuki Tsunoda",
    "ricciardo": "Daniel Ricciardo", "bottas": "Valtteri Bottas",
    "piastri": "Oscar Piastri", "lawson": "Liam Lawson",
    "antonelli": "Kimi Antonelli", "bearman": "Oliver Bearman",
    "schumacher": "Michael Schumacher", "senna": "Ayrton Senna",
    "vettel": "Sebastian Vettel", "raikkonen": "Kimi Raikkonen",
    "wolff": "Toto Wolff", "horner": "Christian Horner",
    "binotto": "Mattia Binotto", "brown": "Zak Brown",
    "newey": "Adrian Newey", "brawn": "Ross Brawn",
}

F1_TEAMS = {
    "red bull": "Red Bull Racing", "mercedes": "Mercedes F1",
    "ferrari": "Scuderia Ferrari", "mclaren": "McLaren F1",
    "aston martin": "Aston Martin F1", "alpine": "Alpine F1",
    "williams": "Williams Racing", "haas": "Haas F1",
    "sauber": "Sauber F1", "rb": "RB F1 Team",
}

FUEL_PARTNERS = {
    "aramco": "Saudi Aramco", "shell": "Shell",
    "petronas": "Petronas", "mobil": "ExxonMobil",
    "castrol": "Castrol", "bp": "BP", "gulf": "Gulf Oil",
}

CONCEPT_KEYWORDS = [
    "how", "why", "explain", "concept", "basically", "essentially",
    "fundamentally", "process", "mechanism", "chemistry", "physics",
    "engineering", "fischer-tropsch", "syngas", "catalyst", "molecule",
    "carbon capture", "efficiency", "thermal", "combustion",
    "compression ratio", "power unit", "mgu-h", "mgu-k", "hybrid",
]

ACTION_KEYWORDS = [
    "race", "racing", "overtake", "crash", "pit stop", "start",
    "finish", "podium", "celebration", "onboard", "battle",
    "wheel to wheel", "championship", "victory", "dramatic",
]

# Keywords that suggest Veo3 AI video would be ideal (abstract/cinematic concepts)
VEO3_KEYWORDS = [
    "future", "vision", "imagine", "revolution", "transformation",
    "evolution", "innovation", "breakthrough", "paradigm", "frontier",
    "molecular", "atomic", "chemical reaction", "synthesis",
    "production facility", "industrial", "manufacturing",
    "wind tunnel", "aerodynamic", "simulation",
]

# Veo3 prompt templates for common F1 scenarios
VEO3_PROMPTS = {
    "fuel_production": "Industrial fuel production facility with advanced chemistry equipment, glowing reactors, sustainable energy, futuristic laboratory",
    "carbon_capture": "Carbon capture technology visualization, CO2 molecules being absorbed, green industrial facility, environmental technology",
    "engine_tech": "Formula 1 power unit internal visualization, turbo spinning, energy flow through MGU-K, high-tech engineering",
    "wind_tunnel": "F1 car in wind tunnel, smoke particles flowing over aerodynamic bodywork, technical testing facility",
    "chemistry": "Chemical synthesis process visualization, molecular bonds forming, laboratory equipment, scientific innovation",
    "factory": "High-tech F1 factory floor, carbon fiber components being manufactured, robotic precision, clean room environment",
    "data_analysis": "F1 data analysis visualization, telemetry streams, holographic displays, race strategy simulation",
    "sustainable": "Sustainable energy technology, green fuel production, environmental innovation, clean energy future",
}

# ============================================================================
# GLOBAL CACHES
# ============================================================================

_IMAGE_CACHE: Dict[str, List[str]] = {}
_LAST_API_CALL = 0
_PRESENTER_IMAGE_PATH: Optional[str] = None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_duration(file_path: str) -> float:
    """Get duration of media file in seconds."""
    cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0


def get_api_key(name: str) -> Optional[str]:
    """Load API key from shared/creds folder."""
    creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shared", "creds", name)
    if os.path.exists(creds_path):
        with open(creds_path) as f:
            return f.read().strip()
    return os.environ.get(f"{name.upper()}_API_KEY")


def download_file(url: str, output_path: str, timeout: int = 30) -> bool:
    """Download a file from URL."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception:
        return False


# ============================================================================
# VISUAL ROUTING - Decides what visual type to use
# ============================================================================

def detect_quote(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect if text contains a quote and extract speaker name."""
    speaker = None
    quote = None

    # Quote patterns
    quote_match = re.search(r'"([^"]{20,})"', text)
    if quote_match:
        quote = quote_match.group(1)

    # Speaker patterns
    speaker_patterns = [
        r"([A-Z][a-z]+ [A-Z][a-z]+) (?:said|stated|explained|mentioned|noted)",
        r"(?:said|stated|explained) ([A-Z][a-z]+ [A-Z][a-z]+)",
        r"as ([A-Z][a-z]+ [A-Z][a-z]+) (?:put it|noted|explained)",
        r"according to ([A-Z][a-z]+ [A-Z][a-z]+)",
    ]

    for pattern in speaker_patterns:
        match = re.search(pattern, text)
        if match:
            speaker = match.group(1)
            break

    # Check for known F1 figures
    if not speaker:
        text_lower = text.lower()
        for key, name in F1_DRIVERS.items():
            if key in text_lower and any(w in text_lower for w in ["said", "stated", "explained", "according"]):
                speaker = name
                break

    return speaker, quote


def detect_f1_entities(text: str) -> Dict[str, List[str]]:
    """Detect F1-related entities in text."""
    text_lower = text.lower()
    entities = {"drivers": [], "teams": [], "fuel_partners": []}

    for key, name in F1_DRIVERS.items():
        if key in text_lower:
            entities["drivers"].append(name)

    for key, name in F1_TEAMS.items():
        if key in text_lower:
            entities["teams"].append(name)

    for key, name in FUEL_PARTNERS.items():
        if key in text_lower:
            entities["fuel_partners"].append(name)

    return entities


def get_veo3_prompt(text: str, context: str) -> Optional[str]:
    """Generate an appropriate Veo3 prompt based on content."""
    text_lower = f"{text} {context}".lower()

    # Check for matching templates
    if any(kw in text_lower for kw in ["fuel production", "sustainable fuel", "synthetic fuel"]):
        return VEO3_PROMPTS["fuel_production"]
    if any(kw in text_lower for kw in ["carbon capture", "co2", "carbon dioxide"]):
        return VEO3_PROMPTS["carbon_capture"]
    if any(kw in text_lower for kw in ["power unit", "engine", "mgu", "turbo"]):
        return VEO3_PROMPTS["engine_tech"]
    if any(kw in text_lower for kw in ["wind tunnel", "aerodynamic", "downforce"]):
        return VEO3_PROMPTS["wind_tunnel"]
    if any(kw in text_lower for kw in ["chemistry", "chemical", "molecule", "synthesis", "fischer-tropsch"]):
        return VEO3_PROMPTS["chemistry"]
    if any(kw in text_lower for kw in ["factory", "manufacturing", "production"]):
        return VEO3_PROMPTS["factory"]
    if any(kw in text_lower for kw in ["data", "telemetry", "analysis", "strategy"]):
        return VEO3_PROMPTS["data_analysis"]
    if any(kw in text_lower for kw in ["sustainable", "green", "environment", "future"]):
        return VEO3_PROMPTS["sustainable"]

    return None


def route_visual(segment: Dict, use_veo3: bool = True) -> VisualDecision:
    """Determine the best visual type for a segment."""
    text = segment.get("text", "")
    context = segment.get("context", "")
    footage_query = segment.get("footage_query", "")

    combined_text = f"{text} {context} {footage_query}"
    text_lower = combined_text.lower()

    # Check for quotes first
    speaker, quote = detect_quote(text)
    if speaker and quote:
        return VisualDecision(
            primary_type=VisualType.QUOTE_OVERLAY,
            fallback_type=VisualType.F1_IMAGE,
            search_queries=[f"{speaker} F1", f"{speaker} portrait"],
            speaker_name=speaker,
            quote_text=quote,
            confidence=0.95
        )

    # Detect F1 entities
    entities = detect_f1_entities(combined_text)

    # Build search queries
    search_queries = []
    for driver in entities["drivers"][:2]:
        search_queries.append(f"{driver} F1 2024")
    for team in entities["teams"][:2]:
        search_queries.append(f"{team} F1 car")
    for partner in entities["fuel_partners"][:1]:
        search_queries.append(f"{partner} F1")

    if footage_query and not footage_query.startswith("GRAPHIC:"):
        search_queries.append(footage_query)

    # Decision logic
    has_f1_content = any(entities[k] for k in entities)
    is_concept = any(kw in text_lower for kw in CONCEPT_KEYWORDS)
    is_action = any(kw in text_lower for kw in ACTION_KEYWORDS)
    is_veo3_suitable = any(kw in text_lower for kw in VEO3_KEYWORDS)

    # Check for Veo3-suitable content (abstract concepts, visualizations)
    if use_veo3 and is_veo3_suitable and not has_f1_content:
        veo3_prompt = get_veo3_prompt(text, context)
        if veo3_prompt:
            return VisualDecision(
                primary_type=VisualType.VEO3_VIDEO,
                fallback_type=VisualType.TALKING_HEAD,
                search_queries=search_queries or ["F1 technology"],
                veo3_prompt=veo3_prompt,
                confidence=0.85
            )

    if is_action and has_f1_content:
        return VisualDecision(
            primary_type=VisualType.YOUTUBE_CLIP,
            fallback_type=VisualType.F1_IMAGE,
            search_queries=search_queries or [f"F1 {context}"],
            confidence=0.85
        )

    if has_f1_content and not is_concept:
        return VisualDecision(
            primary_type=VisualType.F1_IMAGE,
            fallback_type=VisualType.TALKING_HEAD,
            search_queries=search_queries or [f"F1 {context}"],
            confidence=0.9
        )

    if is_concept:
        # For concept explanations, Veo3 could be a good fallback
        veo3_prompt = get_veo3_prompt(text, context) if use_veo3 else None
        return VisualDecision(
            primary_type=VisualType.TALKING_HEAD,
            fallback_type=VisualType.VEO3_VIDEO if veo3_prompt else VisualType.F1_IMAGE,
            search_queries=search_queries or ["F1 technology", "motorsport engineering"],
            veo3_prompt=veo3_prompt,
            confidence=0.8
        )

    # Default
    return VisualDecision(
        primary_type=VisualType.F1_IMAGE,
        fallback_type=VisualType.TALKING_HEAD,
        search_queries=search_queries or ["Formula 1 racing", "F1 car"],
        confidence=0.6
    )


# ============================================================================
# IMAGE FETCHING - Multiple sources for best F1 images
# ============================================================================

def search_images_pexels(query: str, num_images: int = 5) -> List[str]:
    """Search Pexels for images."""
    global _LAST_API_CALL

    cache_key = f"pexels_{query}_{num_images}"
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    api_key = get_api_key("pexels")
    if not api_key:
        return []

    # Rate limiting
    elapsed = time.time() - _LAST_API_CALL
    if elapsed < API_RATE_LIMIT_DELAY:
        time.sleep(API_RATE_LIMIT_DELAY - elapsed)

    urls = []
    try:
        search_url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page={num_images}&orientation=landscape"
        req = urllib.request.Request(search_url, headers={
            "Authorization": api_key,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

        _LAST_API_CALL = time.time()

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())

        for photo in data.get("photos", []):
            urls.append(photo["src"]["large2x"])

        _IMAGE_CACHE[cache_key] = urls
    except Exception:
        pass

    return urls


def search_images_unsplash(query: str, num_images: int = 5) -> List[str]:
    """Search Unsplash for images."""
    global _LAST_API_CALL

    cache_key = f"unsplash_{query}_{num_images}"
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    api_key = get_api_key("unsplash")
    if not api_key:
        return []

    elapsed = time.time() - _LAST_API_CALL
    if elapsed < API_RATE_LIMIT_DELAY:
        time.sleep(API_RATE_LIMIT_DELAY - elapsed)

    urls = []
    try:
        search_url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(query)}&per_page={num_images}&orientation=landscape"
        req = urllib.request.Request(search_url, headers={
            "Authorization": f"Client-ID {api_key}",
            "User-Agent": "Mozilla/5.0"
        })

        _LAST_API_CALL = time.time()

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())

        for photo in data.get("results", []):
            urls.append(photo["urls"]["regular"])

        _IMAGE_CACHE[cache_key] = urls
    except Exception:
        pass

    return urls


def search_f1_images(queries: List[str], num_per_query: int = 3) -> List[str]:
    """
    Search for F1 images from multiple sources.
    Prioritizes quality and relevance.
    """
    all_urls = []

    for query in queries[:4]:  # Limit queries
        # Add F1-specific terms for better results
        f1_query = f"{query} Formula 1" if "f1" not in query.lower() else query

        # Try Pexels first (better for racing/cars)
        urls = search_images_pexels(f1_query, num_per_query)
        all_urls.extend(urls)

        # Try Unsplash as backup
        if len(urls) < num_per_query:
            unsplash_urls = search_images_unsplash(f1_query, num_per_query - len(urls))
            all_urls.extend(unsplash_urls)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


# ============================================================================
# YOUTUBE CLIP FETCHING
# ============================================================================

def search_youtube_f1_clips(query: str, max_results: int = 3) -> List[Dict]:
    """Search YouTube for F1 clips, prioritizing official F1 channel."""
    try:
        # Add F1 to query for better results
        search_query = f"F1 {query}" if "f1" not in query.lower() else query

        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(id)s|%(title)s|%(duration)s|%(channel)s",
            f"ytsearch{max_results * 2}:{search_query}",
            "--no-warnings"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        clips = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 4:
                    video_id, title, duration_str, channel = parts[:4]
                    try:
                        duration = float(duration_str) if duration_str and duration_str != 'NA' else 60
                    except ValueError:
                        duration = 60

                    # Skip very long videos
                    if duration > 600:
                        continue

                    # Prioritize official F1 content
                    priority = 0
                    if 'formula 1' in channel.lower() or 'f1' in channel.lower():
                        priority = 2
                    elif 'motorsport' in channel.lower() or 'racing' in channel.lower():
                        priority = 1

                    clips.append({
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "title": title,
                        "duration": duration,
                        "channel": channel,
                        "priority": priority
                    })

        # Sort by priority (official F1 content first)
        clips.sort(key=lambda x: -x["priority"])
        return clips[:max_results]

    except Exception as e:
        print(f"    YouTube search error: {e}")
        return []


def download_youtube_clip(url: str, output_path: str, start_time: int = 10, duration: int = 10) -> bool:
    """Download a short clip from YouTube."""
    try:
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
            "--merge-output-format", "mp4",
            "-o", output_path,
            "--download-sections", f"*{start_time}-{start_time + duration}",
            "--no-playlist",
            "--no-warnings",
            "--quiet",
            url
        ]

        subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 10000
    except Exception:
        return False


# ============================================================================
# TALKING HEAD GENERATION
# ============================================================================

def get_presenter_image(work_dir: str) -> str:
    """Get or download a presenter image for talking head segments."""
    global _PRESENTER_IMAGE_PATH

    if _PRESENTER_IMAGE_PATH and os.path.exists(_PRESENTER_IMAGE_PATH):
        return _PRESENTER_IMAGE_PATH

    presenter_path = os.path.join(work_dir, "presenter.jpg")

    if os.path.exists(presenter_path):
        _PRESENTER_IMAGE_PATH = presenter_path
        return presenter_path

    # Professional presenter images - try Pexels
    presenter_urls = [
        "https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&w=1200",
        "https://images.pexels.com/photos/3778603/pexels-photo-3778603.jpeg?auto=compress&w=1200",
        "https://images.pexels.com/photos/1222271/pexels-photo-1222271.jpeg?auto=compress&w=1200",
    ]

    for url in presenter_urls:
        if download_file(url, presenter_path):
            _PRESENTER_IMAGE_PATH = presenter_path
            return presenter_path

    return ""


def create_talking_head_clip(
    audio_path: str,
    output_path: str,
    presenter_image: str,
    width: int,
    height: int
) -> bool:
    """
    Create a talking head video with subtle animation.
    Uses Ken Burns effect with gentle sway for lifelike feel.
    """
    duration = get_duration(audio_path)
    if duration <= 0:
        return False

    fps = LONGFORM_FRAME_RATE
    total_frames = int(duration * fps)

    # Subtle zoom with gentle horizontal sway for lifelike movement
    filter_complex = (
        f"scale=w={width*2}:h={height*2}:force_original_aspect_ratio=increase,"
        f"crop={width*2}:{height*2},"
        f"zoompan=z='1.05+0.03*sin(on/120)':"  # Breathing-like zoom
        f"x='iw/2-(iw/zoom/2)+sin(on/90)*15':"  # Gentle horizontal sway
        f"y='ih/2-(ih/zoom/2)+cos(on/100)*8':"  # Subtle vertical movement
        f"d={total_frames}:s={width}x{height}:fps={fps},"
        f"format=yuv420p"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", presenter_image,
        "-i", audio_path,
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", LONGFORM_AUDIO_BITRATE,
        "-t", str(duration),
        "-shortest",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 10000


# ============================================================================
# QUOTE OVERLAY GENERATION
# ============================================================================

def search_person_image(name: str) -> Optional[str]:
    """Search for an image of a specific person."""
    queries = [
        f"{name} portrait",
        f"{name} F1",
        f"{name} Formula 1"
    ]

    for query in queries:
        urls = search_images_pexels(query, 2)
        if urls:
            return urls[0]

        urls = search_images_unsplash(query, 2)
        if urls:
            return urls[0]

    return None


def create_quote_overlay_clip(
    audio_path: str,
    output_path: str,
    quote_text: str,
    speaker_name: str,
    speaker_image_url: Optional[str],
    work_dir: str,
    width: int,
    height: int
) -> bool:
    """Create a clip showing a quote with speaker's image."""
    duration = get_duration(audio_path)
    if duration <= 0:
        return False

    # Download speaker image or use placeholder
    speaker_img_path = os.path.join(work_dir, "speaker.jpg")
    if speaker_image_url:
        download_file(speaker_image_url, speaker_img_path)

    has_speaker_image = os.path.exists(speaker_img_path) and os.path.getsize(speaker_img_path) > 1000

    fps = LONGFORM_FRAME_RATE
    f1_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"
    regular_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Regular.ttf"

    # Font sizes based on resolution
    if width >= 3840:
        quote_size, name_size = 56, 40
    else:
        quote_size, name_size = 36, 28

    # Wrap quote text (max ~50 chars per line)
    words = quote_text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= 50:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    wrapped_quote = "\\n".join(lines)

    if has_speaker_image:
        # Create with speaker image on left, quote on right
        img_size = int(height * 0.5)
        img_x = int(width * 0.08)
        img_y = int((height - img_size) / 2)
        text_x = int(width * 0.4)
        text_y = int(height * 0.35)
        name_y = int(height * 0.65)

        filter_complex = (
            f"[0:v]scale={img_size}:{img_size}:force_original_aspect_ratio=decrease,"
            f"pad={img_size}:{img_size}:(ow-iw)/2:(oh-ih)/2:black[speaker];"
            f"color=c=#1a1a1a:s={width}x{height}:d={duration}:r={fps}[bg];"
            f"[bg][speaker]overlay={img_x}:{img_y},"
            f"drawtext=text='\"'{wrapped_quote}'\"':"
            f"fontfile={regular_font}:fontsize={quote_size}:"
            f"fontcolor=white:x={text_x}:y={text_y}:line_spacing=20,"
            f"drawtext=text='— {speaker_name}':"
            f"fontfile={f1_font}:fontsize={name_size}:"
            f"fontcolor=#E8002D:x={text_x}:y={name_y},"
            f"format=yuv420p[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", speaker_img_path,
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
            "-t", str(duration),
            output_path
        ]
    else:
        # Quote-only overlay (no speaker image)
        text_y = int(height * 0.4)
        name_y = int(height * 0.6)

        filter_complex = (
            f"color=c=#1a1a1a:s={width}x{height}:d={duration}:r={fps},"
            f"drawtext=text='\"'{wrapped_quote}'\"':"
            f"fontfile={regular_font}:fontsize={quote_size}:"
            f"fontcolor=white:x=(w-text_w)/2:y={text_y}:line_spacing=20,"
            f"drawtext=text='— {speaker_name}':"
            f"fontfile={f1_font}:fontsize={name_size}:"
            f"fontcolor=#E8002D:x=(w-text_w)/2:y={name_y},"
            f"format=yuv420p[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=#1a1a1a:s={width}x{height}:d={duration}:r={fps}",
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
            "-t", str(duration),
            output_path
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


# ============================================================================
# VIDEO CLIP CREATION (Ken Burns effect on images)
# ============================================================================

def create_image_clip(
    image_path: str,
    output_path: str,
    duration: float,
    width: int,
    height: int,
    effect: str = "zoom_in"
) -> bool:
    """Create a video clip from an image with Ken Burns effect."""
    fps = LONGFORM_FRAME_RATE
    total_frames = int(duration * fps)

    effects = {
        "zoom_in": {"start_z": 1.0, "end_z": 1.15, "x_shift": 0, "y_shift": 0},
        "zoom_out": {"start_z": 1.15, "end_z": 1.0, "x_shift": 0, "y_shift": 0},
        "pan_left": {"start_z": 1.1, "end_z": 1.1, "x_shift": 50, "y_shift": 0},
        "pan_right": {"start_z": 1.1, "end_z": 1.1, "x_shift": -50, "y_shift": 0},
    }

    params = effects.get(effect, effects["zoom_in"])
    z_expr = f"{params['start_z']}+(on/{total_frames})*({params['end_z']}-{params['start_z']})"
    x_shift = params['x_shift']
    x_expr = f"iw/2-(iw/zoom/2)+({x_shift}-(on/{total_frames})*{x_shift*2})" if x_shift else "iw/2-(iw/zoom/2)"
    y_expr = "ih/2-(ih/zoom/2)"

    filter_complex = f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s={width}x{height}:fps={fps},format=yuv420p"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-vf", filter_complex,
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-an",
        output_path
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


def process_video_clip(
    input_path: str,
    output_path: str,
    duration: float,
    width: int,
    height: int,
    start_time: float = 0
) -> bool:
    """Process a video clip to match target resolution and duration."""
    filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1,format=yuv420p"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", input_path,
        "-t", str(duration),
        "-vf", filter_complex,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        output_path
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


# ============================================================================
# SEGMENT ASSEMBLY - Combines multiple visual sources
# ============================================================================

def create_segment_video(
    segment_idx: int,
    segment: Dict,
    audio_path: str,
    work_dir: str,
    output_path: str,
    width: int,
    height: int,
    use_talking_head: bool = True,
    use_veo3: bool = False
) -> Tuple[bool, str, str]:
    """
    Create a segment video by intelligently blending visual sources.

    Returns: (success, error_message, visual_type_used)
    """
    audio_duration = get_duration(audio_path)
    if audio_duration <= 0:
        return False, "Invalid audio duration", ""

    segment_work_dir = os.path.join(work_dir, f"segment_{segment_idx:02d}")
    os.makedirs(segment_work_dir, exist_ok=True)

    # Get visual routing decision
    decision = route_visual(segment, use_veo3=use_veo3)
    visual_type_used = decision.primary_type.value

    # Handle quote overlays
    if decision.primary_type == VisualType.QUOTE_OVERLAY and decision.speaker_name and decision.quote_text:
        speaker_image_url = search_person_image(decision.speaker_name)
        success = create_quote_overlay_clip(
            audio_path, output_path, decision.quote_text, decision.speaker_name,
            speaker_image_url, segment_work_dir, width, height
        )
        if success:
            return True, "", "quote_overlay"

    # Handle Veo3 AI-generated video
    if decision.primary_type == VisualType.VEO3_VIDEO and decision.veo3_prompt and use_veo3:
        try:
            from src.veo3_generator import is_veo3_available, generate_f1_scene, process_veo3_video

            available, msg = is_veo3_available()
            if available:
                veo3_raw = os.path.join(segment_work_dir, "veo3_raw.mp4")
                veo3_processed = os.path.join(segment_work_dir, "veo3_clip.mp4")

                # Generate 8s clip (max Veo3 duration)
                success, error = generate_f1_scene(
                    decision.veo3_prompt, veo3_raw,
                    duration=8, width=width, height=height,
                    use_fast=True
                )

                if success:
                    # Process to match audio duration
                    if process_veo3_video(veo3_raw, veo3_processed, audio_duration, width, height):
                        # Add audio
                        cmd = [
                            "ffmpeg", "-y",
                            "-i", veo3_processed, "-i", audio_path,
                            "-c:v", "copy", "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
                            "-shortest", output_path
                        ]
                        subprocess.run(cmd, capture_output=True, text=True)
                        if os.path.exists(output_path):
                            return True, "", "veo3_video"
                else:
                    print(f"      Veo3 failed: {error}, trying fallback...")
        except ImportError:
            print("      Veo3 module not available, using fallback...")

    # Calculate how many clips we need (change visuals every 3-5 seconds)
    num_clips = max(2, int(audio_duration / MAX_CLIP_DURATION) + 1)
    clip_duration = audio_duration / num_clips

    # Gather visuals based on decision
    clip_files = []
    effect_idx = 0

    # Try primary visual type first
    if decision.primary_type == VisualType.YOUTUBE_CLIP:
        # Try to get YouTube clips
        for query in decision.search_queries[:2]:
            clips = search_youtube_f1_clips(query, 2)
            for clip_info in clips[:2]:
                if len(clip_files) >= num_clips:
                    break
                clip_idx = len(clip_files)
                raw_path = os.path.join(segment_work_dir, f"yt_raw_{clip_idx}.mp4")
                clip_path = os.path.join(segment_work_dir, f"clip_{clip_idx:02d}.mp4")
                this_duration = clip_duration if clip_idx < num_clips - 1 else audio_duration - clip_idx * clip_duration

                if download_youtube_clip(clip_info["url"], raw_path, start_time=15, duration=int(this_duration) + 3):
                    if process_video_clip(raw_path, clip_path, this_duration, width, height):
                        clip_files.append(clip_path)
                        visual_type_used = "youtube_clip"

    elif decision.primary_type == VisualType.TALKING_HEAD and use_talking_head:
        # Use talking head for entire segment
        presenter_img = get_presenter_image(work_dir)
        if presenter_img:
            if create_talking_head_clip(audio_path, output_path, presenter_img, width, height):
                return True, "", "talking_head"

    # Get F1 images if we need more clips or primary type was F1_IMAGE
    if len(clip_files) < num_clips:
        image_urls = search_f1_images(decision.search_queries, num_per_query=4)

        for i, url in enumerate(image_urls):
            if len(clip_files) >= num_clips:
                break

            clip_idx = len(clip_files)
            img_path = os.path.join(segment_work_dir, f"img_{clip_idx:02d}.jpg")
            clip_path = os.path.join(segment_work_dir, f"clip_{clip_idx:02d}.mp4")
            this_duration = clip_duration if clip_idx < num_clips - 1 else audio_duration - clip_idx * clip_duration

            if download_file(url, img_path):
                effect = KEN_BURNS_EFFECTS[effect_idx % len(KEN_BURNS_EFFECTS)]
                effect_idx += 1
                if create_image_clip(img_path, clip_path, this_duration, width, height, effect):
                    clip_files.append(clip_path)
                    visual_type_used = "f1_image"

    # Fallback to talking head if no clips created
    if not clip_files and use_talking_head:
        presenter_img = get_presenter_image(work_dir)
        if presenter_img:
            if create_talking_head_clip(audio_path, output_path, presenter_img, width, height):
                return True, "", "talking_head_fallback"

    if not clip_files:
        return False, "No visuals created", ""

    # If only one clip, add audio and done
    if len(clip_files) == 1:
        cmd = [
            "ffmpeg", "-y",
            "-i", clip_files[0], "-i", audio_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
            "-shortest", output_path
        ]
        subprocess.run(cmd, capture_output=True, text=True)
        return os.path.exists(output_path), "", visual_type_used

    # Create crossfade transitions
    xfade_duration = min(CROSSFADE_DURATION, clip_duration / 4)
    inputs = []
    for clip in clip_files:
        inputs.extend(["-i", clip])

    # Build xfade chain
    if len(clip_files) == 2:
        offset = clip_duration - xfade_duration
        filter_complex = f"[0:v][1:v]xfade=transition=fade:duration={xfade_duration}:offset={offset},format=yuv420p[outv]"
    else:
        current_offset = clip_duration - xfade_duration
        filter_complex = f"[0:v][1:v]xfade=transition=fade:duration={xfade_duration}:offset={current_offset}[v1]"
        for i in range(2, len(clip_files)):
            current_offset += clip_duration - xfade_duration
            if i == len(clip_files) - 1:
                filter_complex += f";[v{i-1}][{i}:v]xfade=transition=fade:duration={xfade_duration}:offset={current_offset},format=yuv420p[outv]"
            else:
                filter_complex += f";[v{i-1}][{i}:v]xfade=transition=fade:duration={xfade_duration}:offset={current_offset}[v{i}]"

    temp_video = os.path.join(segment_work_dir, "temp_video.mp4")
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        temp_video
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not os.path.exists(temp_video):
        # Fallback: simple concat
        concat_file = os.path.join(segment_work_dir, "concat.txt")
        with open(concat_file, 'w') as f:
            for clip in clip_files:
                f.write(f"file '{clip}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            temp_video
        ]
        subprocess.run(cmd, capture_output=True, text=True)

    if not os.path.exists(temp_video):
        return False, "Failed to create transition video", ""

    # Add audio
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_video, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
        "-t", str(audio_duration), "-shortest",
        output_path
    ]

    subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(output_path):
        return True, "", visual_type_used

    return False, "Failed to add audio", ""


# ============================================================================
# OUTRO AND MUSIC
# ============================================================================

def create_outro_video(output_path: str, width: int, height: int) -> bool:
    """Create outro video with credits."""
    if not os.path.exists(OUTRO_AUDIO_LONGFORM):
        return False

    outro_duration = get_duration(OUTRO_AUDIO_LONGFORM)
    f1_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"

    if width >= 3840:
        title_size, channel_size, cta_size = 72, 96, 48
    else:
        title_size, channel_size, cta_size = 48, 64, 32

    center_y = int(height * 0.45)
    cta_y = int(height * 0.58)

    filter_complex = (
        f"color=black:s={width}x{height}:d={outro_duration}:r={LONGFORM_FRAME_RATE},"
        f"format=yuv420p,"
        f"drawtext=text='Sources & References in Description':"
        f"fontfile={f1_font}:fontsize={title_size}:"
        f"fontcolor=white:x=(w-text_w)/2:y={center_y}:"
        f"enable='lt(t,{CREDITS_DURATION_LONGFORM})',"
        f"drawtext=text='F1 BURNOUTS':"
        f"fontfile={f1_font}:fontsize={channel_size}:"
        f"fontcolor=#E8002D:x=(w-text_w)/2:y={center_y}:"
        f"enable='gte(t,{CREDITS_DURATION_LONGFORM})',"
        f"drawtext=text='LIKE • SUBSCRIBE • BELL':"
        f"fontfile={f1_font}:fontsize={cta_size}:"
        f"fontcolor=white:x=(w-text_w)/2:y={cta_y}:"
        f"enable='gte(t,{CREDITS_DURATION_LONGFORM})'[outv]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=black:s={width}x{height}:d={outro_duration}:r={LONGFORM_FRAME_RATE}",
        "-i", OUTRO_AUDIO_LONGFORM,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
        "-t", str(outro_duration),
        output_path
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


def add_background_music(video_path: str, output_path: str, music_volume: float = MUSIC_VOLUME_LONGFORM) -> bool:
    """Mix background music under video audio."""
    if not os.path.exists(BACKGROUND_MUSIC):
        subprocess.run(["cp", video_path, output_path])
        return True

    video_duration = get_duration(video_path)

    filter_complex = (
        f"[0:a]aformat=channel_layouts=stereo[voice];"
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{video_duration},"
        f"afade=t=in:st=0:d=3,afade=t=out:st={video_duration-3}:d=3,"
        f"volume={music_volume}[music];"
        f"[voice][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path, "-i", BACKGROUND_MUSIC,
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
        output_path
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


def generate_srt_captions(script: Dict, audio_dir: str, output_path: str) -> bool:
    """Generate SRT caption file."""
    segments = script.get("segments", [])
    srt_content = []
    current_time = 0.0

    for i, segment in enumerate(segments):
        audio_file = f"{audio_dir}/segment_{i:02d}.mp3"
        duration = get_duration(audio_file) if os.path.exists(audio_file) else len(segment['text'].split()) / 2.5

        start_time = current_time
        end_time = current_time + duration

        def fmt(s):
            h, m = int(s // 3600), int((s % 3600) // 60)
            return f"{h:02d}:{m:02d}:{s % 60:06.3f}".replace('.', ',')

        srt_content.extend([str(i + 1), f"{fmt(start_time)} --> {fmt(end_time)}", segment['text'], ""])
        current_time = end_time

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Advanced Visual Assembler for F1 Videos')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--resolution', choices=['4k', 'hd'], default='hd', help='Output resolution')
    parser.add_argument('--no-music', action='store_true', help='Skip background music')
    parser.add_argument('--no-credits', action='store_true', help='Skip end credits')
    parser.add_argument('--no-talking-head', action='store_true', help='Disable talking head visuals')
    parser.add_argument('--veo3', action='store_true', help='Enable Veo3 AI video generation')
    parser.add_argument('--analyze', action='store_true', help='Analyze script and show visual routing')
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    audio_dir = f"{project_dir}/audio"
    work_dir = f"{project_dir}/temp/visuals"
    temp_dir = f"{project_dir}/temp"
    output_dir = f"{project_dir}/output"
    script_file = f"{project_dir}/script.json"

    for d in [work_dir, temp_dir, output_dir]:
        os.makedirs(d, exist_ok=True)

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    # Resolution
    if args.resolution == '4k':
        width, height = LONGFORM_OUTPUT_WIDTH_4K, LONGFORM_OUTPUT_HEIGHT_4K
    else:
        width, height = LONGFORM_OUTPUT_WIDTH_HD, LONGFORM_OUTPUT_HEIGHT_HD

    with open(script_file) as f:
        script = json.load(f)

    segments = script["segments"]

    # Check Veo3 availability if enabled
    veo3_available = False
    if args.veo3:
        try:
            from src.veo3_generator import is_veo3_available
            veo3_available, veo3_msg = is_veo3_available()
            if not veo3_available:
                print(f"WARNING: Veo3 requested but not available: {veo3_msg}")
                print("         Will fall back to other visual types.")
        except ImportError:
            print("WARNING: Veo3 module not found. Run: pip install google-genai")

    # Analyze mode
    if args.analyze:
        print("=" * 70)
        print(f"Visual Routing Analysis - Project: {args.project}")
        print(f"Veo3 enabled: {args.veo3} (available: {veo3_available})")
        print("=" * 70)

        type_counts = {}
        for i, seg in enumerate(segments):
            decision = route_visual(seg, use_veo3=args.veo3)
            vtype = decision.primary_type.value
            type_counts[vtype] = type_counts.get(vtype, 0) + 1

            context = seg.get('context', seg.get('text', '')[:30])
            print(f"[{i:02d}] {vtype:15} | {context[:45]}")
            if decision.speaker_name:
                print(f"      Speaker: {decision.speaker_name}")
            if decision.veo3_prompt:
                print(f"      Veo3: {decision.veo3_prompt[:50]}...")
            print(f"      Queries: {decision.search_queries[:2]}")

        print("-" * 70)
        print("Summary:")
        for vtype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            pct = count / len(segments) * 100
            print(f"  {vtype}: {count} segments ({pct:.0f}%)")
        return

    print("=" * 70)
    print(f"Advanced Visual Assembler - Project: {args.project}")
    print(f"Resolution: {width}x{height} ({args.resolution.upper()})")
    print(f"Visual Duration: {MIN_CLIP_DURATION}-{MAX_CLIP_DURATION}s per clip")
    print(f"Talking Head: {'Disabled' if args.no_talking_head else 'Enabled'}")
    print(f"Veo3 AI Video: {'Enabled' if args.veo3 else 'Disabled'}")
    print("=" * 70)

    # Check audio
    missing = [i for i in range(len(segments)) if not os.path.exists(f"{audio_dir}/segment_{i:02d}.mp3")]
    if missing:
        print(f"\nMissing audio: {missing}")
        sys.exit(1)

    print(f"\nProcessing {len(segments)} segments...\n")

    segment_videos = []
    visual_stats = {}

    for i, segment in enumerate(segments):
        context = segment.get('context', segment.get('section', 'segment'))[:40]
        print(f"[{i+1}/{len(segments)}] {context}...")

        output_path = f"{temp_dir}/segment_{i:02d}.mp4"
        audio_path = f"{audio_dir}/segment_{i:02d}.mp3"

        success, error, vtype = create_segment_video(
            i, segment, audio_path, work_dir, output_path, width, height,
            use_talking_head=not args.no_talking_head,
            use_veo3=args.veo3
        )

        if success:
            segment_videos.append(output_path)
            dur = get_duration(output_path)
            visual_stats[vtype] = visual_stats.get(vtype, 0) + 1
            print(f"    Done ({dur:.1f}s) [{vtype}]")
        else:
            print(f"    Failed: {error}")

    if not segment_videos:
        print("\nNo segments created!")
        sys.exit(1)

    # Outro
    if not args.no_credits:
        print("\nCreating outro...")
        outro_path = f"{temp_dir}/outro.mp4"
        if create_outro_video(outro_path, width, height):
            segment_videos.append(outro_path)

    # Concatenate
    print(f"\nConcatenating {len(segment_videos)} segments...")
    concat_file = f"{temp_dir}/concat.txt"
    with open(concat_file, 'w') as f:
        for v in segment_videos:
            f.write(f"file '{v}'\n")

    concat_output = f"{temp_dir}/concat.mp4"
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
        concat_output
    ]
    subprocess.run(cmd, capture_output=True, text=True)

    # Add music
    final_output = f"{output_dir}/final.mp4"
    if not args.no_music:
        print("Adding background music...")
        add_background_music(concat_output, final_output)
    else:
        subprocess.run(["cp", concat_output, final_output])

    # Captions
    generate_srt_captions(script, audio_dir, f"{output_dir}/captions.srt")

    if os.path.exists(final_output):
        size_mb = os.path.getsize(final_output) / (1024 * 1024)
        duration = get_duration(final_output)
        print(f"\n{'=' * 70}")
        print(f"SUCCESS: {final_output}")
        print(f"Duration: {duration/60:.1f} minutes ({duration:.0f}s)")
        print(f"Size: {size_mb:.1f}MB")
        print(f"\nVisual breakdown:")
        for vtype, count in sorted(visual_stats.items(), key=lambda x: -x[1]):
            print(f"  {vtype}: {count} segments")
        print(f"{'=' * 70}")
    else:
        print("\nFailed to create final video")
        sys.exit(1)


if __name__ == "__main__":
    main()
