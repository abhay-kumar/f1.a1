# Find F1 Short Ideas from Reddit

Discover trending F1 content ideas from Reddit's r/formula1 subreddit for short-form videos.

## Parameters

- `$ARGUMENTS` - Time range: `day` (past 24 hours), `week` (past 7 days), or `month` (past 30 days). Defaults to `week` if not specified.

## Instructions

You are searching Reddit for popular F1 discussions from the specified time range to generate fresh short-form video ideas.

**Time Range**: Based on the `$ARGUMENTS` parameter:
- `day` → Search for posts from the past 24 hours / yesterday
- `week` (default) → Search for posts from the past 7 days
- `month` → Search for posts from the past 30 days

### Storage Location

Previously proposed ideas are stored in: `shared/reddit_ideas.json`

This file tracks all ideas you've proposed to avoid duplicates. The format is:
```json
{
  "ideas": [
    {
      "id": "unique-slug",
      "title": "Video Title Idea",
      "synopsis": "Brief description of the video concept",
      "reddit_source": "Thread title or topic that inspired this",
      "proposed_date": "2025-01-22",
      "status": "proposed"
    }
  ]
}
```

### Workflow

1. **Load Existing Ideas**: Read `shared/reddit_ideas.json` to know what's already been proposed. If the file doesn't exist, start with an empty list.

2. **Search Reddit**: Use web search to find popular threads from r/formula1 within the specified time range:
   - For `day`: `site:reddit.com/r/formula1 past 24 hours popular`, `reddit r/formula1 trending today`
   - For `week`: `site:reddit.com/r/formula1 past week popular`, `reddit r/formula1 trending this week`
   - For `month`: `site:reddit.com/r/formula1 past month popular`, `reddit r/formula1 trending this month`
   
3. **Analyze Threads**: For each popular thread found, evaluate:
   - Is it a compelling story/fact that works in 60 seconds?
   - Does it have emotional hook (drama, surprise, nostalgia)?
   - Is it visually representable with available F1 footage?
   - Is it timely/relevant to current F1 news?

4. **Filter Duplicates**: Compare potential ideas against existing ideas in `reddit_ideas.json`:
   - Check if similar topics/stories have been proposed before
   - Look for semantic similarity, not just exact matches
   - Skip ideas that are too similar to previously proposed ones

5. **Generate Top 10 Ideas**: Create 10 unique, compelling video concepts:
   - Each idea should be specific enough to create a script
   - Include a catchy title and brief synopsis
   - Note the Reddit source that inspired it

6. **Update Storage**: Append the new ideas to `shared/reddit_ideas.json` with today's date

7. **Present Results**: Display the ideas in a clear, actionable format

### Idea Quality Criteria

Good short-form F1 ideas typically include:
- **Dramatic moments**: Crashes, overtakes, last-lap battles
- **Unknown facts**: "Did you know..." style revelations
- **Driver stories**: Personal struggles, rivalries, friendships
- **Historical parallels**: Comparing past and present
- **Controversial takes**: Debatable opinions that spark engagement
- **Recent news angles**: Fresh takes on current events
- **Statistical surprises**: Counter-intuitive data points
- **Behind-the-scenes**: Team dynamics, pit lane stories

### Output Format

Present the ideas as a numbered list:

```
## Top 10 F1 Short Ideas ([TIME_RANGE] ending [DATE])

1. **[Title]**
   Synopsis: [2-3 sentence description]
   Reddit source: [Thread/topic that inspired this]
   Why it works: [Brief explanation]

2. ...
```

### After Finding Ideas

Suggest the user can create any video by running:
```
/f1-create-short [paste the synopsis here]
```

### Example Search Queries

Adjust queries based on the time range parameter:

**For `day`:**
- `site:reddit.com/r/formula1 popular today 2025`
- `reddit formula1 trending discussions today`
- `r/formula1 hot posts 24 hours`

**For `week` (default):**
- `site:reddit.com/r/formula1 popular this week 2025`
- `reddit formula1 trending discussions this week`
- `r/formula1 hot posts week`

**For `month`:**
- `site:reddit.com/r/formula1 popular this month 2025`
- `reddit formula1 trending discussions month`
- `r/formula1 top posts month`

### Notes

- Focus on stories that translate well to visual short-form content
- Avoid ideas requiring extensive footage that may be hard to find
- Prefer universally interesting topics over niche technical discussions
- Consider seasonal relevance (off-season vs race weekends)
