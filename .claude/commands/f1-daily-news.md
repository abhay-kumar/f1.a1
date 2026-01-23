# F1 Daily News Update

Create a daily F1 news update short video by finding trending stories from the past 24 hours and assembling them into a news-style video.

## Instructions

You are creating a daily F1 news update short video. This command orchestrates the full workflow:
1. Find trending F1 stories from Reddit (past 24 hours)
2. Get user confirmation on which stories to include
3. Create a news-style short video with all selected stories

### Phase 1: Find Trending Stories

**Time Range**: Always search for the past 24 hours (daily news format).

1. **Load Existing Ideas**: Read `shared/reddit_ideas.json` to check what's already been proposed

2. **Search Reddit**: Find popular F1 discussions from the specified time range:
   - Use web search: `site:reddit.com/r/formula1 popular today 2026`, `reddit formula1 trending`
   - Look for breaking news, controversies, team updates, driver news
   - Focus on stories from the past 24 hours for "daily" feel

3. **Filter and Rank**: Identify the top stories that:
   - Are newsworthy and current
   - Can be explained in 1-2 sentences each
   - Have available footage (team launches, races, driver content)
   - Haven't been covered in recent videos

4. **Present Stories**: Show the user a numbered list of potential stories:
   ```
   ## Today's F1 News Stories ([DATE])
   
   1. **[Headline]** - [1-2 sentence summary]
   2. **[Headline]** - [1-2 sentence summary]
   ...
   ```

5. **CHECKPOINT - User Selection**: 
   - Ask user which stories to include (by number or ID)
   - Recommend 6-8 stories for a ~60-90 second video
   - Wait for explicit confirmation before proceeding

### Phase 2: Create News Video

Once user confirms story selection, create the daily news video:

1. **Project Setup**: 
   - Create project folder: `projects/f1-daily-news-{date}` (e.g., `f1-daily-news-jan23`)
   - Use today's date in the folder name

2. **Script Structure**: Generate `script.json` with this news format:
   ```json
   {
     "title": "F1 Daily News - [Full Date]",
     "duration_target": 60,
     "segments": [
       {
         "id": 1,
         "text": "Welcome to F1 Daily News, your sixty-second briefing on everything Formula One. It's [date]. Here's what you need to know.",
         "context": "Intro - establish daily news format",
         "footage_query": "F1 2026 cars grid formation",
         "footage_start": 10
       },
       // ... news segments (one per story, 1-2 sentences each) ...
       {
         "id": N,
         "text": "That's your F1 Daily News. Subscribe, hit the bell, and drop a comment with your thoughts. See you tomorrow!",
         "context": "Outro - CTA for subscribe/like/comment (reusable)",
         "footage_query": "F1 racing action montage",
         "footage_start": 25
       }
     ]
   }
   ```

3. **Script Guidelines**:
   - Keep each news item to 1-2 crisp sentences
   - Use present tense for immediacy ("Ferrari reveals...", "Hamilton admits...")
   - Include specific details (names, numbers, quotes)
   - Transition naturally between stories
   - Total target: ~60-90 seconds

4. **CHECKPOINT - Script Review**:
   - Present the complete script to user
   - Show all segments with text and footage queries
   - **STOP and wait for user approval**
   - Make any requested changes before proceeding

5. **Video Production Pipeline**:
   ```bash
   # Generate voiceovers
   python3 src/audio_generator.py --project f1-daily-news-{date}
   
   # Download footage for all segments
   python3 src/footage_downloader.py --project f1-daily-news-{date}
   
   # If any segment fails, retry with alternative query:
   python3 src/footage_downloader.py --project f1-daily-news-{date} --segment {id} --query "alternative search"
   
   # Extract preview frames
   python3 src/preview_extractor.py --project f1-daily-news-{date}
   
   # Assemble final video
   python3 src/video_assembler.py --project f1-daily-news-{date}
   ```

6. **Footage Verification**: 
   - Check that downloaded footage matches each news story
   - Re-download with different queries if footage is incorrect
   - Update `footage_start` timestamps as needed

7. **Final Output**:
   - Verify video/audio sync
   - Report final video location and specs

### News Writing Style

- **Crisp and punchy**: No filler words, every word counts
- **Active voice**: "Ferrari reveals" not "It was revealed by Ferrari"
- **Specific details**: Include names, numbers, dates
- **Natural flow**: Stories should transition smoothly
- **Variety**: Mix team news, driver news, technical updates, controversies

### Example News Segment

**Good**: "Lewis Hamilton finally drove a Ferrari at Fiorano today. The SF-26 marks his first competitive laps in red, with Ferrari finishing the car just one day before launch."

**Bad**: "So there's been some exciting news from Ferrari today. Lewis Hamilton, who as you know moved from Mercedes, has finally had the chance to drive the new car."

### Reusable Elements

The **intro** and **outro** segments are designed to be consistent across all daily news videos:
- Intro: "Welcome to F1 Daily News, your sixty-second briefing..."
- Outro: "That's your F1 Daily News. Subscribe, hit the bell..."

This builds brand recognition and viewer expectations.

### Update Reddit Ideas

After creating the video, update `shared/reddit_ideas.json`:
- Add any new story ideas discovered during research
- Mark used stories with `"status": "used"` and `"used_date"`

### Output

Final video: `projects/f1-daily-news-{date}/output/final.mp4`
- Format: 1080x1920 (9:16 vertical)
- Duration: ~60-90 seconds
- Style: Fast-paced news update

### Next Step

After the video is created, suggest:
```
/f1-upload-short
```
to upload to YouTube with appropriate daily news metadata.
