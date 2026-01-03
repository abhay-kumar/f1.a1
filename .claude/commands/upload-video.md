# Upload F1 Long-Form Video to YouTube

Upload a completed F1 long-form video to YouTube with auto-generated metadata, references in description, and captions.

## Input
Project name: $ARGUMENTS

## Instructions

1. **Validate the project exists** and has required files:
   - Check `projects/{project}/output/final.mp4` exists
   - Check `projects/{project}/script.json` exists
   - Check `projects/{project}/output/captions.srt` exists (optional but recommended)

2. **Preview the upload metadata** by running:
   ```bash
   python3 src/youtube_uploader_longform.py --project {project} --dry-run
   ```

3. **Show the user** the auto-generated:
   - Title (from script.json title field)
   - Description preview (summary + references section)
   - Tags (drivers/teams/topics mentioned)
   - References count (sources cited in description)
   - Captions status (whether SRT file will be uploaded)
   - Video file size

4. **Ask the user** to confirm or modify:
   - Title override (optional)
   - Privacy setting (public/unlisted/private - default is public)

5. **Upload the video** (public by default):
   ```bash
   python3 src/youtube_uploader_longform.py --project {project}
   ```
   Or with custom title:
   ```bash
   python3 src/youtube_uploader_longform.py --project {project} --title "Custom Title"
   ```
   Or with different privacy:
   ```bash
   python3 src/youtube_uploader_longform.py --project {project} --privacy unlisted
   ```

6. **Report the result**:
   - Show the YouTube URL
   - Confirm captions were uploaded (if available)
   - Confirm upload_info.json was saved

## What Gets Uploaded

### Video
- Full 16:9 horizontal video (4K or HD)
- Includes outro with channel branding and CTA

### Description (Auto-Generated)
- Opening summary from first 2-3 script segments
- "ABOUT THIS VIDEO" section
- Chapters (if sections are defined in script)
- **References section** with all cited sources and URLs
- Hashtags: #F1 #Formula1 #Racing #Motorsport

### Tags (Auto-Detected)
- Base tags: F1, Formula1, Racing, Motorsport, Grand Prix
- Driver tags (detected from script): Verstappen, Hamilton, Leclerc, etc.
- Team tags (detected from script): Red Bull, Ferrari, Mercedes, etc.
- Topic tags: World Championship, F1 History, etc.

### Captions
- Uploads `captions.srt` file if present in output folder
- Allows viewers to toggle closed captions on YouTube

## First-time Setup

If YouTube credentials are not configured, guide the user:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable **YouTube Data API v3**
3. Go to Credentials > Create Credentials > OAuth 2.0 Client ID
4. Select "Desktop app" as application type
5. Download the JSON file
6. Save it as: `shared/creds/youtube_client_secrets.json`

First upload will open a browser for Google sign-in to grant YouTube access.

**Note**: The first time you upload after adding caption support, you may need to re-authenticate to grant the additional `youtube.force-ssl` permission required for caption uploads.

## Example Usage

```
/upload-video sustainable-fuels-2026
```

This will:
1. Read the script from `projects/sustainable-fuels-2026/script.json`
2. Generate title: "F1 2026: The Sustainable Fuel Revolution" (or similar)
3. Generate description with:
   - Video summary
   - Chapters (if defined)
   - All source references with URLs
4. Auto-tag: F1, Ferrari, Mercedes, Aramco, Shell, Sustainable Fuel, etc.
5. Detect captions file at `output/captions.srt`
6. Ask for confirmation
7. Upload video and captions
8. Return the YouTube URL

## Differences from /upload-short

| Feature | /upload-short | /upload-video |
|---------|---------------|---------------|
| Format | 9:16 Vertical | 16:9 Horizontal |
| Duration | ~60 seconds | ~10+ minutes |
| Title suffix | Adds #Shorts | No suffix |
| Description | Summary only | Summary + References + Chapters |
| Captions | Not supported | SRT upload supported |
| References | Not included | Full citations in description |
| Privacy default | public | public |

## Output Files

After successful upload:
- `projects/{project}/upload_info.json` - Contains:
  ```json
  {
    "video_id": "abc123xyz",
    "url": "https://youtube.com/watch?v=abc123xyz",
    "title": "Video Title",
    "privacy": "public",
    "format": "longform",
    "references_count": 12,
    "captions_uploaded": true
  }
  ```
