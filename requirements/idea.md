# StravaAI

**Pre-MVP: AI-Powered Activity Insight Dashboard (Strava OAuth)**

---

### Objective

Build a minimal product that delivers personalized insights from Strava activities using AI, with the ability to connect accounts via OAuth. Focus is on key insights from the **latest activity**, contextualized with **1-month history**, and showing progress toward **upcoming milestones** (e.g., Oceanman, Half Marathon).

---

### Authentication

Client send an autharisation token for the first time that will be used to get access_token and refresh_token, access_token will be used in all Strava APIs if access_token expire use refresh_token to fetch access_token again. If refresh_token expire then prompt client to get Strava authorisation again

### Pre MVP Features

### 1. User Onboarding

- Ask name, age and current weight
- Set milestone (e.g., "Oceanman 5K on Oct 25").

### 2. Activity Fetch

- Fetch latest activity (Swim, Run, Ride) and last 1 month of history.

### 3. Analytics Dashboard

- Metrics:
    - Distance, Time, Avg Pace, HR Zones.
    - Week-over-week trend graphs.
    - Monthly volume & intensity chart.

### 4. AI Insights Engine (via OpenAI/Gemini)

- System Prompt Strategy:
    - Inputs: user profile, activity history (1 month), latest activity, goal milestone.
    - Sample prompt:
        
        > You are an elite endurance sports coach. Given the user's past month of swim data and today's activity, analyze whether they are progressing toward their 5K Oceanman race goal on Oct 25. Highlight pacing, heart-rate, or stamina issues. Suggest one focused tip for improvement.
        > 
- Output:
    - Insight 1-liner: "Your pace improved by 4% but HR still spikes in final 500m."
    - Expandable recommendation block.

### 5. Performance Milestone Tracking

- Track goal proximity with progress bar.
- Highlight gaps (e.g., "To hit sub-2:30 in Oceanman, improve endurance at zone 3").

---

### Architecture Sketch

- Backend: FastAPI
- Strava API integration
- LLM API: OpenAI GPT-4o or Gemini 2.5 lite
- Database: Mongo DB
- Deployment: Docker

---