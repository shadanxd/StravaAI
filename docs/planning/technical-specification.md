# StravaAI Technical Specification

## System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (React/Next)  │◄──►│   (FastAPI)     │◄──►│   APIs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   MongoDB       │
                       │   (Atlas)       │
                       └─────────────────┘
```

### Technology Stack
- **Backend**: FastAPI (Python 3.11+)
- **Database**: MongoDB Atlas
- **Frontend**: React 18+ with Next.js 14+
- **Styling**: Tailwind CSS
- **Authentication**: Strava OAuth 2.0
- **AI**: OpenAI GPT-4o or Gemini 2.5 Lite
- **Deployment**: Docker + Docker Compose
- **Monitoring**: Sentry (error tracking)

## Database Schema

### Users Collection
```javascript
{
  "_id": ObjectId,
  "strava_id": Number,           // Strava athlete ID
  "username": String,            // Strava username
  "firstname": String,
  "lastname": String,
  "email": String,               // Optional, from Strava
  "age": Number,                 // User-provided
  "weight": Number,              // User-provided (kg)
  "city": String,                // From Strava
  "country": String,             // From Strava
  "milestones": [{
    "id": ObjectId,
    "name": String,              // e.g., "Oceanman 5K"
    "date": Date,                // Target date
    "target": String,            // e.g., "sub-2:30"
    "sport_type": String,        // "Swim", "Run", "Ride"
    "distance": Number,          // Target distance in meters
    "created_at": Date
  }],
  "access_token": String,        // Encrypted
  "refresh_token": String,       // Encrypted
  "token_expires_at": Date,
  "created_at": Date,
  "updated_at": Date,
  "last_activity_sync": Date
}
```

### Activities Collection
```javascript
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "strava_activity_id": Number,
  "name": String,
  "type": String,                // "Swim", "Run", "Ride"
  "sport_type": String,          // More specific than type
  "distance": Number,            // meters
  "moving_time": Number,         // seconds
  "elapsed_time": Number,        // seconds
  "total_elevation_gain": Number, // meters
  "average_speed": Number,       // m/s
  "max_speed": Number,           // m/s
  "average_heartrate": Number,   // bpm
  "max_heartrate": Number,       // bpm
  "start_date": Date,
  "start_date_local": Date,
  "timezone": String,
  "location_city": String,
  "location_state": String,
  "location_country": String,
  "map": {
    "summary_polyline": String,
    "resource_state": Number
  },
  "raw_data": Object,            // Full Strava response
  "created_at": Date,
  "updated_at": Date
}
```

### Insights Collection
```javascript
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "activity_id": ObjectId,       // Optional, for activity-specific insights
  "insight_type": String,        // "performance", "training", "milestone"
  "insight_text": String,        // Main insight
  "recommendation": String,      // Actionable recommendation
  "confidence_score": Number,    // 0-1, AI confidence
  "ai_model": String,           // "gpt-4o", "gemini-2.5"
  "context_data": {
    "activity_count": Number,
    "time_period": String,       // "1_week", "1_month"
    "sport_type": String,
    "milestone_progress": Number // 0-100
  },
  "created_at": Date
}
```

## API Endpoints

### Authentication Endpoints
```python
# Strava OAuth Flow
POST /api/auth/strava/authorize
    # Redirects to Strava authorization URL

GET /api/auth/strava/callback
    # Handles Strava OAuth callback
    # Parameters: code, state
    # Returns: {user_id, access_token}

POST /api/auth/refresh
    # Refreshes expired access token
    # Headers: Authorization: Bearer <refresh_token>
    # Returns: {access_token, expires_at}

GET /api/auth/user
    # Get current user profile
    # Headers: Authorization: Bearer <access_token>
    # Returns: User profile data
```

### User Management Endpoints
```python
POST /api/users/onboarding
    # Complete user onboarding
    # Body: {name, age, weight, milestones}
    # Returns: {user_id, profile_complete}

PUT /api/users/profile
    # Update user profile
    # Body: {name, age, weight}
    # Returns: Updated profile

GET /api/users/profile
    # Get user profile
    # Returns: Complete user profile

POST /api/users/milestones
    # Add new milestone
    # Body: {name, date, target, sport_type, distance}
    # Returns: {milestone_id}

PUT /api/users/milestones/{milestone_id}
    # Update milestone
    # Body: {name, date, target, sport_type, distance}
    # Returns: Updated milestone

DELETE /api/users/milestones/{milestone_id}
    # Delete milestone
    # Returns: {success: true}
```

### Activities Endpoints
```python
GET /api/activities/latest
    # Get user's latest activity
    # Query params: sport_type (optional)
    # Returns: Latest activity data

GET /api/activities/history
    # Get user's activity history
    # Query params: 
    #   - sport_type (optional)
    #   - start_date (optional)
    #   - end_date (optional)
    #   - limit (default: 50)
    # Returns: Array of activities

POST /api/activities/sync
    # Manually trigger activity sync
    # Returns: {synced_count, total_count}

GET /api/activities/{activity_id}
    # Get specific activity details
    # Returns: Activity data with metrics
```

### Analytics Endpoints
```python
GET /api/analytics/dashboard
    # Get dashboard analytics
    # Query params: time_period (default: "1_month")
    # Returns: {
    #   summary: {total_distance, total_time, avg_pace},
    #   trends: {weekly_data, monthly_data},
    #   milestones: {progress, gaps}
    # }

GET /api/analytics/trends
    # Get trend analysis
    # Query params: 
    #   - sport_type (optional)
    #   - metric (distance, pace, heartrate)
    #   - period (1_week, 1_month, 3_months)
    # Returns: Trend data for charts

GET /api/analytics/milestones
    # Get milestone progress
    # Returns: Array of milestone progress data
```

### AI Insights Endpoints
```python
POST /api/insights/generate
    # Generate new AI insight
    # Body: {
    #   activity_id (optional),
    #   insight_type (performance, training, milestone),
    #   context (optional)
    # }
    # Returns: Generated insight

GET /api/insights/history
    # Get user's insight history
    # Query params: 
    #   - limit (default: 10)
    #   - insight_type (optional)
    # Returns: Array of insights

GET /api/insights/{insight_id}
    # Get specific insight
    # Returns: Insight details
```

## Frontend Component Architecture

### Page Structure
```
pages/
├── index.tsx              # Landing page
├── auth/
│   ├── login.tsx         # Strava login
│   └── callback.tsx      # OAuth callback
├── onboarding/
│   ├── profile.tsx       # User profile setup
│   └── milestones.tsx    # Milestone setup
├── dashboard/
│   ├── index.tsx         # Main dashboard
│   ├── analytics.tsx     # Detailed analytics
│   └── insights.tsx      # AI insights
└── settings/
    └── profile.tsx       # Profile settings
```

### Component Structure
```
components/
├── auth/
│   ├── StravaLogin.tsx
│   └── AuthGuard.tsx
├── dashboard/
│   ├── ActivityCard.tsx
│   ├── MetricsGrid.tsx
│   ├── TrendChart.tsx
│   └── MilestoneProgress.tsx
├── insights/
│   ├── InsightCard.tsx
│   ├── RecommendationBlock.tsx
│   └── InsightHistory.tsx
├── onboarding/
│   ├── ProfileForm.tsx
│   └── MilestoneForm.tsx
└── common/
    ├── Header.tsx
    ├── Sidebar.tsx
    ├── LoadingSpinner.tsx
    └── ErrorBoundary.tsx
```

## Environment Configuration

### Backend Environment Variables
```bash
# Strava API
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REDIRECT_URI=http://localhost:3000/api/auth/strava/callback

# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/stravaai

# AI API
OPENAI_API_KEY=your_openai_key
# or
GEMINI_API_KEY=your_gemini_key

# Security
SECRET_KEY=your_secret_key
JWT_SECRET=your_jwt_secret

# Application
DEBUG=True
ENVIRONMENT=development
```

### Frontend Environment Variables
```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRAVA_CLIENT_ID=your_client_id

# Analytics
NEXT_PUBLIC_GA_ID=your_ga_id
```

## Docker Configuration

### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017/stravaai
    depends_on:
      - mongo
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
    command: npm run dev

  mongo:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

## Security Considerations

### Authentication & Authorization
- JWT tokens for session management
- Encrypted storage of Strava tokens
- Automatic token refresh mechanism
- Rate limiting on API endpoints

### Data Protection
- HTTPS for all communications
- Input validation and sanitization
- SQL injection prevention (MongoDB)
- XSS protection in frontend

### API Security
- CORS configuration
- Request size limits
- API key rotation
- Error message sanitization

## Performance Optimization

### Backend
- Redis caching for API responses
- Database query optimization
- Background job processing
- Connection pooling

### Frontend
- Code splitting and lazy loading
- Image optimization
- Service worker for caching
- Bundle size optimization

### Database
- Index optimization
- Aggregation pipeline optimization
- Connection pooling
- Read replicas for scaling

## Monitoring & Logging

### Application Monitoring
- Error tracking with Sentry
- Performance monitoring
- User analytics
- API usage tracking

### Infrastructure Monitoring
- Server resource monitoring
- Database performance metrics
- Network latency tracking
- Uptime monitoring

## Testing Strategy

### Backend Testing
- Unit tests for business logic
- Integration tests for API endpoints
- Database migration tests
- Performance tests

### Frontend Testing
- Component unit tests
- Integration tests
- E2E tests with Playwright
- Visual regression tests

### API Testing
- Postman collections
- Automated API tests
- Load testing
- Security testing 