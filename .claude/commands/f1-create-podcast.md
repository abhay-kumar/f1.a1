# Create F1 Podcast

Create an F1 podcast episode with two hosts discussing the provided topics.

## Parameters

- `$ARGUMENTS` - Synopsis/topics for the podcast episode (required). Can be a single topic or comma-separated list.

## Podcast Hosts

The podcast features two F1 fans with distinct personalities:

### Alex (Male Host)
- **Passion**: Racing, drivers, rivalries, on-track battles, championship drama
- **Style**: Enthusiastic, emotional, loves driver comparisons and historic moments
- **Voice**: Josh (ElevenLabs) - deep, engaging male voice
- **Typical takes**: "That overtake was pure instinct!", "Verstappen's racecraft reminds me of Senna"

### Sophie (Female Host)
- **Passion**: Aerodynamics, engineering, fuel efficiency, regulations, technical innovation
- **Style**: Analytical, precise, enjoys explaining how things work
- **Voice**: Matilda (ElevenLabs) - warm, articulate female voice
- **Typical takes**: "The floor redesign gave them 15 points of downforce", "The new fuel regs will change pit strategy"

## Instructions

You are creating a ~20 minute podcast episode where Alex and Sophie discuss F1 topics in their unique styles.

### Project Structure
```
projects/{project-name}/
├── script.json         # Podcast script with dialogue
├── audio/              # Generated voiceovers per segment
└── output/             # Final podcast audio (final.mp3)
```

### Workflow

1. **Parse Topics**: Extract the topics/synopsis from `$ARGUMENTS`

2. **Research** (if needed): Search web for recent facts, quotes, technical details

3. **Generate Script**: Create `script.json` with this podcast format:
   ```json
   {
     "title": "Podcast Episode Title",
     "format": "podcast",
     "duration_target": 1200,
     "hosts": {
       "alex": {
         "voice_id": "TxGEqnHWrfWFTfGW9XjX",
         "description": "Racing and drivers enthusiast"
       },
       "sophie": {
         "voice_id": "XrExE9yKIg1WjnnlVkGX",
         "description": "Engineering and technical expert"
       }
     },
     "segments": [
       {
         "id": 1,
         "host": "alex",
         "text": "Welcome to Pit Lane Talk! I'm Alex...",
         "context": "Intro"
       },
       {
         "id": 2,
         "host": "sophie",
         "text": "And I'm Sophie. Today we're diving into...",
         "context": "Intro"
       }
     ]
   }
   ```

4. **Script Guidelines**:
   - **Natural conversation**: Include reactions, agreements, friendly disagreements
   - **Host authenticity**: Alex focuses on racing/drivers, Sophie on engineering/tech
   - **Back-and-forth**: Alternate hosts, with occasional interruptions/reactions
   - **Depth over breadth**: Deep-dive into topics rather than surface-level coverage
   - **Target duration**: ~20 minutes (approximately 3000-3500 words total)
   - **Structure**: Intro → Topic discussions → Predictions/opinions → Outro

5. **CHECKPOINT - Script Review**:
   - Present the complete script to the user
   - Show all segments with host, text, and context
   - Display estimated duration based on word count (~150 words/minute)
   - **STOP and wait for user approval**
   - Make any requested changes before proceeding

6. **Generate Audio**:
   ```bash
   python3 src/podcast_audio_generator.py --project {name}
   ```

7. **Verify Output**:
   - Check total duration matches expectations
   - Ensure smooth host transitions
   - Report final audio location

### Dialogue Writing Tips

**Alex's voice patterns**:
- Uses exclamations: "Incredible!", "What a move!"
- References driver skill: "His racecraft is unmatched"
- Emotional connections: "The fans were on their feet"
- Historical comparisons: "Reminds me of Schumacher at Spa"

**Sophie's voice patterns**:
- Technical precision: "The drag coefficient dropped by 0.02"
- Explains mechanisms: "Here's why that works..."
- Data-driven: "The telemetry showed..."
- Regulation awareness: "Under the new rules..."

**Natural conversation elements**:
- "That's a great point, but..." (friendly disagreement)
- "Exactly!" / "Right!" (agreement)
- "Oh, interesting..." (genuine curiosity)
- "Let me add to that..." (building on points)
- Laughter cues: "[laughs]" (will be interpreted by TTS)

### Example Segment Flow

```
Alex: "Max's defense in that race was just incredible. The way he positioned the car..."
Sophie: "It was smart, but from an engineering standpoint, his tire management was the real story. He kept those mediums alive for 10 laps longer than predicted."
Alex: "See, that's what I love about this sport - it's not just about raw speed, right?"
Sophie: "Exactly. It's physics, strategy, and human skill all combined. Speaking of strategy..."
```

### Output

Final audio: `projects/{name}/output/final.mp3`
- Format: MP3, high quality (256kbps)
- Duration: ~20 minutes
- Channels: Stereo (optional host panning)

### After Creation

Suggest potential next steps:
- Upload to podcast platform
- Create video version with waveform visualization
- Generate transcript for show notes
