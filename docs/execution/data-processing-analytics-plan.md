# Activity Data Fetching & Sync - Backend-AI Planning

## Introduction
Fetching and synchronizing user activity data from Strava is essential for powering analytics and AI insights in StravaAI. The backend must reliably fetch the latest activity and up to one month of historical data, handle incremental syncs, and store all relevant activity details in MongoDB. This enables downstream analytics and AI modules to operate on fresh, accurate data.

## Strategy

### Implementation Options
1. **On-Demand Fetching (API-Driven)**
   - Fetch activities when the user logs in or requests a sync.
   - Pros: Simple, reduces unnecessary API calls.
   - Cons: Data may be stale if user is inactive.

2. **Scheduled Background Sync (Recommended for Pre-MVP)**
   - Use a background job (e.g., Celery, FastAPI background tasks) to periodically sync activities for all users.
   - Pros: Ensures data freshness, offloads work from user requests.
   - Cons: Requires job scheduling and monitoring.

3. **Webhook-Based Sync (Strava Push API)**
   - Use Strava’s webhook to receive activity updates in real time.
   - Pros: Real-time updates, efficient.
   - Cons: More setup, Strava webhook limits, not critical for Pre-MVP.

### Recommended MVP Approach
- **Hybrid**: Implement on-demand fetching for user-triggered syncs and login, plus a simple scheduled background sync (e.g., every 6-12 hours) for all users.
- Store all fetched activities in the MongoDB `activities` collection, using the schema from the technical spec.
- Handle Strava API rate limits and errors gracefully (exponential backoff, caching, logging).
- Store raw Strava response for future-proofing AI/analytics.

## Executive Checklist
- [ ] Implement `/api/activities/latest` and `/api/activities/history` endpoints
- [ ] Implement `/api/activities/sync` endpoint for manual sync
- [ ] Store all activity data in MongoDB using defined schema
- [ ] Store raw Strava response in `raw_data` field
- [ ] Handle Strava API rate limits and errors (logging, retry, backoff)
- [ ] Update user’s `last_activity_sync` timestamp
- [ ] Document sync flow and error handling for future AI/analytics modules
