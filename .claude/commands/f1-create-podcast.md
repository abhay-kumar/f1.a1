# Create F1 Podcast

Create an F1 Burnouts podcast episode with the host discussing the provided topics directly with the audience.

## Parameters

- `$ARGUMENTS` - Synopsis/topics for the podcast episode (required). Can be a single topic or comma-separated list.

## The Host

The podcast features a single passionate host speaking directly to the audience:

### The Host of F1 Burnouts
- **Voice ID**: `nPczCjzI2devNBz1zQrb` (ElevenLabs)
- **Background**: Expert in both engineering and F1 motorsport regulations/history
- **Team Affinity**: Proud McLaren fan (and not shy about it!) but respects all teams
- **Core Values**: 
  - Objective and fair - gives credit where due, critical when warranted (even of McLaren)
  - Passionate about engineering excellence across all teams
  - Cares deeply about climate change initiatives in F1
  - Strong advocate for women in F1
  - Wishes well for underperforming teams and departing drivers/teams
- **Tone**: 
  - Immersive storytelling with intrigue
  - Humor and sarcasm woven throughout
  - Heartfelt when the moment calls for it
  - Brutal honesty when needed
  - Family-friendly (no swearing) - engages kids and adults alike
- **Speaking Style**: Conversational, as if talking directly to a friend about F1

## Instructions

You are creating a ~20 minute podcast episode where the host speaks directly to the audience about F1 topics.

### Project Structure
```
projects/{project-name}/
├── script.json         # Podcast script with monologue segments
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
     "host": {
       "name": "Host",
       "voice_id": "nPczCjzI2devNBz1zQrb",
       "description": "The host of F1 Burnouts - engineering expert and F1 historian"
     },
     "segments": [
       {
         "id": 1,
         "text": "Welcome to F1 Burnouts! I'm your host, and today we're diving into...",
         "context": "Intro",
         "emotion": "energetic"
       },
       {
         "id": 2,
         "text": "Now, let me tell you why this matters...",
         "context": "Main topic",
         "emotion": "intrigued"
       }
     ]
   }
   ```

4. **Script Guidelines**:
   - **Direct address**: Speak TO the audience, not at them ("you", "let me tell you", "think about this")
   - **Storytelling**: Build narratives with tension, reveals, and payoffs
   - **Emotional range**: Shift between excitement, contemplation, humor, sincerity
   - **Engineering depth**: Explain technical concepts accessibly but accurately
   - **Historical context**: Connect current events to F1 history
   - **Balanced criticism**: Praise AND critique where deserved (including McLaren)
   - **McLaren moments**: Occasional proud McLaren references, but never at expense of objectivity
   - **Sarcasm with heart**: Playful jabs that never feel mean-spirited
   - **Family-friendly**: No profanity - clever wordplay instead
   - **Target duration**: ~20 minutes (approximately 3000-3500 words total)
   - **Structure**: Hook → Intro → Deep dives → Reflections → Sign-off

5. **ElevenLabs TTS Compatibility** (CRITICAL):
   - **NO bracketed expressions**: Never use `[laughs]`, `[sighs]`, `[chuckles]`, `[gasps]`, etc. - ElevenLabs reads these literally as words
   - **NO stage directions**: Avoid `[pause]`, `[excited]`, `[whispers]` in the text
   - **Express emotions through words instead**:
     - Instead of `[laughs]`: "Ha!", "Oh, that's funny", "I have to laugh at that", "That cracks me up"
     - Instead of `[sighs]`: "Honestly...", "Look...", "I mean...", use trailing off with ellipsis
     - Instead of `[chuckles]`: "Heh", "That's amusing", weave humor into word choice
     - Instead of `[gasps]`: "Wait, what?!", "Hold on!", "Are you kidding me?!"
     - Instead of `[pause]`: Use "..." or start new sentence, or "Now..." / "So..."
   - **Use punctuation for pacing**: Ellipses (...) for trailing off, dashes (—) for interruption, exclamation marks for emphasis
   - **Emotion through vocabulary**: Choose words that inherently carry the emotion rather than describing the emotion

6. **Emotional Markers** (for TTS expression):
   - `emotion: "energetic"` - Exciting moments, celebrations
   - `emotion: "contemplative"` - Thoughtful analysis, historical reflection
   - `emotion: "humorous"` - Sarcastic takes, funny observations
   - `emotion: "heartfelt"` - Tributes, farewells, meaningful moments
   - `emotion: "serious"` - Critical analysis, important issues
   - `emotion: "passionate"` - Climate/women in F1 advocacy, engineering appreciation

7. **CHECKPOINT - Script Review**:
   - Present the complete script to the user
   - Show all segments with text, context, and emotion
   - Display estimated duration based on word count (~150 words/minute)
   - **STOP and wait for user approval**
   - Make any requested changes before proceeding

8. **Generate Audio**:
   ```bash
   python3 src/podcast_audio_generator.py --project {name}
   ```

9. **Verify Output**:
   - Check total duration matches expectations
   - Ensure smooth transitions between segments
   - Report final audio location

### Voice & Style Patterns

**Engaging the audience**:
- "Now, here's where it gets interesting..."
- "Stay with me on this one..."
- "I know what you're thinking, but hear me out..."
- "Let's break this down together..."
- "You're going to love this..."

**McLaren pride (balanced)**:
- "Look, I'm a McLaren fan, you all know that, but even I have to admit..."
- "As much as it pains my papaya-loving heart..."
- "Now, this is where my McLaren bias might show, but objectively speaking..."

**Engineering appreciation**:
- "The engineering behind this is absolutely brilliant..."
- "This is where the physics gets beautiful..."
- "The regulations say X, but the clever interpretation is..."

**Sarcasm and humor**:
- "Oh, what a surprise, another penalty that totally makes sense..."
- "Because obviously, that's exactly what everyone predicted..." 
- "And in news that shocked absolutely no one..."

**Heartfelt moments**:
- "This is what F1 is really about..."
- "You have to respect the journey..."
- "Regardless of the team, that's a human being who gave everything..."

**Critical but fair**:
- "I love this team, but let's be honest here..."
- "Credit where it's due, but also..."
- "This isn't criticism for its own sake - this matters because..."

**Climate and inclusion advocacy**:
- "F1 has a responsibility here, and here's what they're doing..."
- "The women making waves in this sport deserve recognition..."
- "Sustainability isn't just a buzzword - let me explain why this matters..."

**Wishing well**:
- "To the teams struggling right now - keep pushing, the sport needs you..."
- "As they exit the sport, let's remember what they contributed..."
- "Every team has a story, and theirs matters..."

### Example Segment Flow

```
[emotion: energetic]
"Welcome back to F1 Burnouts! I'm your host, and oh boy, do we have a lot to unpack today..."

[emotion: intrigued]
"Now, here's where it gets fascinating. You see, the regulations specifically state... but what Red Bull figured out was..."

[emotion: humorous]
"And in news that surprised absolutely everyone - and by everyone, I mean no one - we saw another strategic masterclass from Ferrari. And yes, that was sarcasm."

[emotion: heartfelt]
"But jokes aside, watching that driver cross the line for the last time... there's something about this sport that just grabs you, you know?"

[emotion: passionate]
"And this is why F1's sustainability initiatives matter. It's not just about racing - it's about proving that performance and environmental responsibility can coexist."

[emotion: energetic]
"That's all for today's episode of F1 Burnouts. Until next time, keep the rubber on the track!"
```

### Output

Final audio: `projects/{name}/output/final.mp3`
- Format: MP3, high quality (256kbps)
- Duration: ~20 minutes
- Channels: Stereo

### After Creation

Suggest potential next steps:
- Upload to podcast platform
- Create video version with waveform visualization
- Generate transcript for show notes
