# Create F1 Podcast

Create an F1 Burnouts podcast episode with the host discussing the provided topics directly with the audience.

## Parameters

- `$ARGUMENTS` - Synopsis/topics for the podcast episode (required). Can be a single topic or comma-separated list.

## The Host

The podcast features a single passionate host speaking directly to the audience:

### The Host of F1 Burnouts
- **Voice**: Charon (Gemini TTS) - Informative, engaging, authoritative
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

## TTS Engine: Google Gemini 2.5

This podcast uses **Google Gemini 2.5 TTS** with **SSML enhancement** for immersive, expressive audio:

### Why Gemini TTS?
- **Free tier available** (gemini-2.5-flash-preview-tts)
- **Emotion markers** directly in text: `[excited]`, `[empathetic]`, `[speaking slowly]`
- **SSML support** for pauses, emphasis, and prosody control
- **Natural speech** with context-aware pacing

### SSML Features (Auto-Applied)
The `ssml_generator.py` module automatically enhances scripts with:
- **Strategic pauses** after key phrases and questions
- **Emphasis** on important words (incredible, billion, first, etc.)
- **Emotion markers** based on segment emotion field
- **Natural breathing points** for long sentences
- **Punctuation enhancement** for expressive delivery

### Available Voices
- **Charon** (default) - Informative, authoritative (ideal for podcasts)
- **Kore** - Firm, confident
- **Puck** - Upbeat, energetic
- **Zephyr** - Bright, lively
- **Enceladus** - Breathy, intimate
- **Aoede** - Breezy, conversational

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
     "tts_engine": "gemini",
     "voice": "Charon",
     "host": {
       "name": "Host",
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

5. **Gemini TTS Script Optimization** (IMPORTANT):
   
   Unlike ElevenLabs, Gemini TTS **supports** emotion markers and SSML tags. Use them strategically:
   
   **Emotion markers in text** (Gemini reads these as instructions, not words):
   - `[excited]` - For high-energy moments
   - `[empathetic]` - For heartfelt content
   - `[speaking slowly]` - For emphasis or dramatic effect
   - `[whispering]` - For intimate asides
   - `[laughing]` - For genuine humor moments
   - `[sighing]` - For exasperation or reflection
   
   **When to use emotion markers**:
   - At the START of emotionally distinct passages
   - Sparingly - one per paragraph maximum
   - For dramatic effect, not every sentence
   
   **Example with markers**:
   ```
   "[excited] And here's where it gets absolutely wild!"
   "[speaking slowly] Think about that for a moment... a billion cars."
   "[laughing] Oh, that's so typically Ferrari, isn't it?"
   ```
   
   **Punctuation for natural pacing**:
   - Ellipses (...) for trailing off or building suspense
   - Dashes (—) for interruptions or asides
   - Exclamation marks for emphasis (use sparingly)
   - Question marks with pauses for rhetorical effect
   
   **The SSML generator will automatically add**:
   - Pauses after questions
   - Emphasis on key words
   - Breath marks for long sentences
   - Micro-pauses at natural break points

6. **Emotional Markers** (segment metadata for SSML enhancement):
   - `emotion: "energetic"` - Exciting moments, celebrations → `[excited]` marker
   - `emotion: "contemplative"` - Thoughtful analysis → `[speaking slowly]` marker
   - `emotion: "humorous"` - Sarcastic takes → `[playful]` marker
   - `emotion: "heartfelt"` - Tributes, farewells → `[empathetic]` marker
   - `emotion: "serious"` - Critical analysis → `[serious]` marker
   - `emotion: "passionate"` - Advocacy, engineering appreciation → `[passionate]` marker

7. **CHECKPOINT - Script Review**:
   - Present the complete script to the user
   - Show all segments with text, context, and emotion
   - Display estimated duration based on word count (~150 words/minute)
   - **STOP and wait for user approval**
   - Make any requested changes before proceeding

8. **Generate Audio** (using Gemini TTS):
   ```bash
   # Default: Flash model (free), with SSML enhancement
   python3 src/gemini_podcast_audio_generator.py --project {name}
   
   # Options:
   # --model pro      # Use Pro model (paid, highest quality)
   # --model flash    # Use Flash model (free, default)
   # --voice Kore     # Change voice (default: Charon)
   # --no-ssml        # Disable SSML enhancement
   # --sequential     # Process segments one at a time
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

### Example Segment Flow (with Gemini emotion markers)

```
[emotion: energetic]
"[excited] Welcome back to F1 Burnouts! I'm your host, and oh boy, do we have a lot to unpack today..."

[emotion: intrigued]
"Now, here's where it gets fascinating. You see, the regulations specifically state... but what Red Bull figured out was..."

[emotion: humorous]
"[laughing] And in news that surprised absolutely everyone - and by everyone, I mean no one - we saw another strategic masterclass from Ferrari."

[emotion: heartfelt]
"[empathetic] But jokes aside, watching that driver cross the line for the last time... there's something about this sport that just grabs you, you know?"

[emotion: passionate]
"And this is why F1's sustainability initiatives matter. It's not just about racing - it's about proving that performance and environmental responsibility can coexist."

[emotion: energetic]
"[excited] That's all for today's episode of F1 Burnouts. Until next time, keep the rubber on the track!"
```

### Output

Final audio: `projects/{name}/output/final.mp3`
- Format: MP3, high quality (256kbps)
- Sample rate: 24kHz
- Duration: ~20 minutes
- Channels: Mono (Gemini TTS output)

### API Key Setup

Get your free Google AI API key:
1. Visit: https://aistudio.google.com/apikey
2. Create/copy your API key
3. Save it: `echo 'YOUR_KEY' > shared/creds/google_ai`

### After Creation

Suggest potential next steps:
- Upload to podcast platform
- Create video version with waveform visualization
- Generate transcript for show notes
