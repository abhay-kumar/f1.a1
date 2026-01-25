# F1 Weekly Podcast

Create a weekly F1 podcast episode by finding trending stories from the past week and having Alex and Sophie discuss them.

## Instructions

You are creating a weekly F1 podcast that covers the most interesting stories from the past 7 days.

### Podcast Hosts

The podcast features two F1 fans with distinct personalities:

#### Alex (Male Host)
- **Passion**: Racing, drivers, rivalries, on-track battles, championship drama
- **Style**: Enthusiastic, emotional, loves driver comparisons and historic moments
- **Voice**: Josh (ElevenLabs) - deep, engaging male voice

#### Sophie (Female Host)
- **Passion**: Aerodynamics, engineering, fuel efficiency, regulations, technical innovation
- **Style**: Analytical, precise, enjoys explaining how things work
- **Voice**: Matilda (ElevenLabs) - warm, articulate female voice

### Workflow

#### Phase 1: Find Weekly Stories

Use `/f1-find-content week` to discover trending F1 stories from the past 7 days.

This will:
- Search Reddit's r/formula1 for popular discussions from the past week
- Filter out duplicate ideas already in `shared/reddit_ideas.json`
- Present a ranked list of newsworthy stories

After reviewing the ideas from `/f1-find-content week`:

1. **CHECKPOINT - Story Selection**:
   - Ask user which stories to include in the podcast (by number)
   - Recommend 4-6 stories for a ~20 minute episode
   - Wait for explicit confirmation before proceeding

#### Phase 2: Create Podcast Script

1. **Project Setup**:
   - Create project folder: `projects/f1-weekly-podcast-{date}` (e.g., `f1-weekly-podcast-jan23`)
   - Use the end date of the week in the folder name

2. **Generate Script**: Create `script.json` with this podcast format:
   ```json
   {
     "title": "F1 Weekly Roundup - Week of [Date Range]",
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
         "text": "Welcome back to Pit Lane Talk, your weekly F1 roundup! I'm Alex...",
         "context": "Intro"
       },
       {
         "id": 2,
         "host": "sophie",
         "text": "And I'm Sophie. Big week in Formula One...",
         "context": "Intro"
       }
     ]
   }
   ```

3. **Script Structure**:
   ```
   1. INTRO (~1 min)
      - Welcome, host introductions
      - Quick overview of what's coming
   
   2. HEADLINES (~2 min)
      - Quick-fire recap of the week's main news
      - Both hosts alternate headlines
   
   3. DEEP DIVES (~15 min)
      - 3-4 main stories discussed in depth
      - Alex leads on racing/driver stories
      - Sophie leads on technical/engineering stories
      - Natural back-and-forth conversation
   
   4. HOT TAKES (~2 min)
      - Each host gives a bold prediction or opinion
      - Friendly debate
   
   5. OUTRO (~1 min)
      - Recap key points
      - Tease next week
      - Subscribe/follow CTA
   ```

4. **Script Guidelines**:
   - **Natural conversation**: Include reactions, agreements, friendly disagreements
   - **Host authenticity**: Alex on racing/drivers, Sophie on engineering/tech
   - **Weekly context**: Reference specific events, dates, race weekends
   - **Target duration**: ~20 minutes (approximately 3000-3500 words total)
   - **Story balance**: Mix driver news, technical updates, team drama, regulations

5. **CHECKPOINT - Script Review**:
   - Present the complete script to the user
   - Show all segments with host, text, and context
   - Display estimated duration (~150 words/minute)
   - **STOP and wait for user approval**
   - Make any requested changes before proceeding

#### Phase 3: Generate Audio

```bash
python3 src/podcast_audio_generator.py --project f1-weekly-podcast-{date}
```

#### Phase 4: Verify & Deliver

1. **Check Output**:
   - Verify total duration (~20 minutes)
   - Ensure smooth host transitions
   - Report final audio location

2. **Update Tracking**:
   - Mark used stories in `shared/reddit_ideas.json` with `"status": "used_podcast"`

### Example Weekly Episode Flow

```
[INTRO]
Alex: "Welcome back to Pit Lane Talk! I'm Alex, and what a week it's been in Formula One!"
Sophie: "And I'm Sophie. We've got driver drama, technical updates, and some spicy regulation news to get through."
Alex: "Let's dive right in!"

[HEADLINES]
Sophie: "First up - Ferrari unveiled their new floor design at the test session..."
Alex: "And Hamilton had some choice words about the stewards after Sunday's incident..."

[DEEP DIVE - Story 1]
Alex: "Okay, let's talk about that Hamilton incident. I mean, the passion he showed..."
Sophie: "From a technical standpoint though, his car positioning was questionable..."

[HOT TAKES]
Alex: "My hot take this week - Norris will win the next three races."
Sophie: "Bold! Mine is that the new fuel regulations will completely shake up the midfield."

[OUTRO]
Sophie: "That's our weekly roundup! Thanks for listening."
Alex: "Subscribe, leave a review, and we'll catch you next week on Pit Lane Talk!"
```

### Output

Final audio: `projects/f1-weekly-podcast-{date}/output/final.mp3`
- Format: MP3, high quality (256kbps)
- Duration: ~20 minutes
- Style: Conversational weekly news podcast

### After Creation

Suggest potential next steps:
- Upload to podcast hosting platform
- Create audiogram clips for social media
- Generate transcript for show notes
