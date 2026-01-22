#!/usr/bin/env python3
"""
Asset Library - Manage and retrieve pre-built reusable visual assets.

Provides a searchable library of pre-generated graphics, diagrams,
and animations that can be reused across projects.

Structure:
    shared/assets/
    ├── graphics/       # AI-generated images with Ken Burns
    ├── diagrams/       # Manim-generated animations
    ├── overlays/       # Transparent overlays (telemetry, etc.)
    └── manifest.json   # Asset metadata index
"""
import os
import sys
import json
import shutil
import argparse
from typing import Tuple, Optional, List, Dict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import SHARED_DIR

ASSET_DIR = f"{SHARED_DIR}/assets"
MANIFEST_FILE = f"{ASSET_DIR}/manifest.json"

# Asset categories
CATEGORIES = [
    "graphics",     # AI-generated static images with Ken Burns
    "diagrams",     # Manim programmatic animations
    "overlays",     # Transparent overlays
    "footage",      # Curated footage clips
    "animations",   # AI-generated video clips
]


def ensure_asset_dir():
    """Create asset directory structure if it doesn't exist."""
    os.makedirs(ASSET_DIR, exist_ok=True)
    for category in CATEGORIES:
        os.makedirs(f"{ASSET_DIR}/{category}", exist_ok=True)


def load_manifest() -> Dict:
    """Load or create asset manifest."""
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE) as f:
            return json.load(f)
    return {
        "version": 1,
        "assets": {},
        "categories": CATEGORIES,
        "last_updated": None
    }


def save_manifest(manifest: Dict):
    """Save asset manifest."""
    ensure_asset_dir()
    manifest["last_updated"] = datetime.now().isoformat()
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)


def get_library_asset(asset_name: str, output_path: str) -> Tuple[bool, Optional[str]]:
    """
    Retrieve an asset from the library and copy to output path.

    Args:
        asset_name: Name of the asset (as registered in manifest)
        output_path: Where to copy the asset

    Returns:
        (success, error_message)
    """
    manifest = load_manifest()

    if asset_name not in manifest.get("assets", {}):
        # Try partial match
        matches = [name for name in manifest.get("assets", {}).keys()
                   if asset_name.lower() in name.lower()]
        if matches:
            return False, f"Asset '{asset_name}' not found. Did you mean: {', '.join(matches[:3])}?"
        return False, f"Asset '{asset_name}' not found in library"

    asset_info = manifest["assets"][asset_name]
    source_path = f"{ASSET_DIR}/{asset_info['path']}"

    if not os.path.exists(source_path):
        return False, f"Asset file missing: {source_path}"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Copy to output location
    shutil.copy2(source_path, output_path)

    return True, None


def list_assets(category: str = None, search: str = None) -> List[Dict]:
    """
    List available assets, optionally filtered.

    Args:
        category: Filter by category
        search: Search in name, description, tags

    Returns:
        List of asset info dicts
    """
    manifest = load_manifest()
    assets = []

    for name, info in manifest.get("assets", {}).items():
        # Category filter
        if category and info.get("category") != category:
            continue

        # Search filter
        if search:
            search_lower = search.lower()
            searchable = f"{name} {info.get('description', '')} {' '.join(info.get('tags', []))}"
            if search_lower not in searchable.lower():
                continue

        assets.append({
            "name": name,
            "category": info.get("category", "uncategorized"),
            "description": info.get("description", ""),
            "duration": info.get("duration", 0),
            "tags": info.get("tags", []),
            "path": info.get("path", ""),
            "created": info.get("created", ""),
            "source": info.get("source", "unknown"),
        })

    return sorted(assets, key=lambda x: x["name"])


def add_asset(name: str, file_path: str, category: str,
              description: str = "", tags: List[str] = None,
              duration: float = 0, source: str = "manual") -> Tuple[bool, Optional[str]]:
    """
    Add a new asset to the library.

    Args:
        name: Unique identifier for the asset
        file_path: Path to the source file
        category: Asset category (graphics, diagrams, etc.)
        description: Human-readable description
        tags: List of searchable tags
        duration: Duration in seconds (for video assets)
        source: How asset was created (dalle, manim, manual, etc.)

    Returns:
        (success, error_message)
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    if category not in CATEGORIES:
        return False, f"Invalid category: {category}. Must be one of: {CATEGORIES}"

    manifest = load_manifest()

    if name in manifest.get("assets", {}):
        return False, f"Asset '{name}' already exists. Use update_asset to modify."

    # Create category directory
    category_dir = f"{ASSET_DIR}/{category}"
    os.makedirs(category_dir, exist_ok=True)

    # Copy file with standardized name
    ext = os.path.splitext(file_path)[1]
    filename = f"{name}{ext}"
    dest_path = f"{category}/{filename}"
    full_dest = f"{ASSET_DIR}/{dest_path}"

    shutil.copy2(file_path, full_dest)

    # Update manifest
    manifest.setdefault("assets", {})[name] = {
        "path": dest_path,
        "category": category,
        "description": description,
        "tags": tags or [],
        "duration": duration,
        "source": source,
        "created": datetime.now().isoformat(),
        "file_size": os.path.getsize(full_dest)
    }

    save_manifest(manifest)

    return True, None


def remove_asset(name: str) -> Tuple[bool, Optional[str]]:
    """Remove an asset from the library."""
    manifest = load_manifest()

    if name not in manifest.get("assets", {}):
        return False, f"Asset '{name}' not found"

    asset_info = manifest["assets"][name]
    file_path = f"{ASSET_DIR}/{asset_info['path']}"

    # Remove file
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove from manifest
    del manifest["assets"][name]
    save_manifest(manifest)

    return True, None


def update_asset(name: str, description: str = None,
                 tags: List[str] = None) -> Tuple[bool, Optional[str]]:
    """Update asset metadata."""
    manifest = load_manifest()

    if name not in manifest.get("assets", {}):
        return False, f"Asset '{name}' not found"

    if description is not None:
        manifest["assets"][name]["description"] = description

    if tags is not None:
        manifest["assets"][name]["tags"] = tags

    manifest["assets"][name]["updated"] = datetime.now().isoformat()
    save_manifest(manifest)

    return True, None


def get_asset_info(name: str) -> Optional[Dict]:
    """Get detailed info about an asset."""
    manifest = load_manifest()
    if name not in manifest.get("assets", {}):
        return None

    info = manifest["assets"][name].copy()
    info["name"] = name
    info["full_path"] = f"{ASSET_DIR}/{info['path']}"
    info["exists"] = os.path.exists(info["full_path"])

    return info


def import_from_project(project_name: str, segment_idx: int,
                        asset_name: str, category: str,
                        description: str = "", tags: List[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Import a generated segment from a project into the asset library.

    Args:
        project_name: Project to import from
        segment_idx: Segment index
        asset_name: Name for the new asset
        category: Asset category
        description: Description
        tags: Tags

    Returns:
        (success, error_message)
    """
    from src.config import get_project_dir

    project_dir = get_project_dir(project_name)
    segment_path = f"{project_dir}/footage/segment_{segment_idx:02d}.mp4"

    if not os.path.exists(segment_path):
        return False, f"Segment not found: {segment_path}"

    # Get duration using ffprobe
    import subprocess
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", segment_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        duration = float(result.stdout.strip())
    except ValueError:
        duration = 0

    return add_asset(
        name=asset_name,
        file_path=segment_path,
        category=category,
        description=description,
        tags=tags,
        duration=duration,
        source=f"project:{project_name}:segment_{segment_idx}"
    )


def main():
    parser = argparse.ArgumentParser(description='Manage visual asset library')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List assets')
    list_parser.add_argument('--category', '-c', choices=CATEGORIES, help='Filter by category')
    list_parser.add_argument('--search', '-s', help='Search in name/description/tags')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add new asset')
    add_parser.add_argument('name', help='Asset name (unique identifier)')
    add_parser.add_argument('file', help='Path to asset file')
    add_parser.add_argument('--category', '-c', required=True, choices=CATEGORIES)
    add_parser.add_argument('--description', '-d', default='', help='Asset description')
    add_parser.add_argument('--tags', '-t', nargs='+', help='Asset tags')
    add_parser.add_argument('--duration', type=float, default=0, help='Duration in seconds')
    add_parser.add_argument('--source', default='manual', help='Creation source')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove asset')
    remove_parser.add_argument('name', help='Asset name')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show asset details')
    info_parser.add_argument('name', help='Asset name')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search assets')
    search_parser.add_argument('query', help='Search query')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import from project')
    import_parser.add_argument('--project', '-p', required=True, help='Project name')
    import_parser.add_argument('--segment', '-s', type=int, required=True, help='Segment index')
    import_parser.add_argument('--name', '-n', required=True, help='New asset name')
    import_parser.add_argument('--category', '-c', required=True, choices=CATEGORIES)
    import_parser.add_argument('--description', '-d', default='')
    import_parser.add_argument('--tags', '-t', nargs='+')

    # Stats command
    subparsers.add_parser('stats', help='Show library statistics')

    args = parser.parse_args()

    if args.command == 'list':
        assets = list_assets(args.category, args.search)
        if not assets:
            print("No assets found")
            return

        print(f"{'Name':<35} {'Category':<12} {'Duration':<8} {'Description'}")
        print("-" * 90)
        for asset in assets:
            dur = f"{asset['duration']:.1f}s" if asset['duration'] else "-"
            print(f"{asset['name']:<35} {asset['category']:<12} {dur:<8} {asset['description'][:35]}")

    elif args.command == 'add':
        success, error = add_asset(
            args.name, args.file, args.category,
            args.description, args.tags, args.duration, args.source
        )
        if success:
            print(f"Added: {args.name}")
        else:
            print(f"Failed: {error}")
            sys.exit(1)

    elif args.command == 'remove':
        success, error = remove_asset(args.name)
        if success:
            print(f"Removed: {args.name}")
        else:
            print(f"Failed: {error}")
            sys.exit(1)

    elif args.command == 'info':
        info = get_asset_info(args.name)
        if info:
            print(f"Name:        {info['name']}")
            print(f"Category:    {info['category']}")
            print(f"Description: {info['description']}")
            print(f"Tags:        {', '.join(info.get('tags', []))}")
            print(f"Duration:    {info.get('duration', 0):.1f}s")
            print(f"Source:      {info.get('source', 'unknown')}")
            print(f"Created:     {info.get('created', 'unknown')}")
            print(f"Path:        {info['full_path']}")
            print(f"Exists:      {'Yes' if info['exists'] else 'NO - FILE MISSING'}")
        else:
            print(f"Asset not found: {args.name}")
            sys.exit(1)

    elif args.command == 'search':
        assets = list_assets(search=args.query)
        if not assets:
            print(f"No assets matching: {args.query}")
            return

        print(f"Found {len(assets)} assets matching '{args.query}':")
        for asset in assets:
            print(f"  {asset['name']}: {asset['description'][:50]}")

    elif args.command == 'import':
        success, error = import_from_project(
            args.project, args.segment, args.name,
            args.category, args.description, args.tags
        )
        if success:
            print(f"Imported: {args.name}")
        else:
            print(f"Failed: {error}")
            sys.exit(1)

    elif args.command == 'stats':
        manifest = load_manifest()
        assets = manifest.get("assets", {})

        print("Asset Library Statistics")
        print("=" * 40)
        print(f"Total assets: {len(assets)}")

        by_category = {}
        total_duration = 0
        total_size = 0

        for info in assets.values():
            cat = info.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
            total_duration += info.get("duration", 0)
            total_size += info.get("file_size", 0)

        print(f"\nBy category:")
        for cat in CATEGORIES:
            count = by_category.get(cat, 0)
            print(f"  {cat}: {count}")

        print(f"\nTotal duration: {total_duration:.1f}s ({total_duration/60:.1f}m)")
        print(f"Total size: {total_size / (1024*1024):.1f}MB")
        print(f"Last updated: {manifest.get('last_updated', 'never')}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
