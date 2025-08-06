# StravaAI Pre-MVP Planning Document

## Introduction

The StravaAI project aims to build an AI-powered activity insight dashboard that integrates with Strava's OAuth system to provide personalized performance analytics for endurance sports enthusiasts. The core objective is to deliver actionable insights from Strava activities using AI, focusing on key metrics from the latest activity, contextualized with 1-month history, and progress tracking toward upcoming milestones (e.g., Oceanman, Half Marathon).

### Key Requirements:
- **Authentication**: OAuth integration with Strava API
- **Data Processing**: Fetch latest activity and 1-month history
- **AI Analytics**: OpenAI/Gemini integration for personalized insights
- **Dashboard**: Real-time metrics and progress tracking
- **Milestone Tracking**: Goal-oriented performance monitoring

### Target Users:
- Endurance sports enthusiasts (swimmers, runners, cyclists)
- Athletes training for specific events
- Users seeking AI-powered performance coaching

---

## Strategy

### Strategy 1: Monolithic FastAPI Application (RECOMMENDED)

**Approach**: Single FastAPI application with integrated frontend and backend
- **Pros**: 
  - Faster development for Pre-MVP
  - Simplified deployment and testing
  - Easier debugging and maintenance
  - Reduced complexity for initial launch
- **Cons**: 
  - Less scalable for future growth
  - Frontend/backend coupling

**Technology Stack**:
- Backend: FastAPI with Python 3.11+
- Database: MongoDB (flexible schema for activity data)
- AI: OpenAI GPT-4o or Gemini 2.5 Lite
- Frontend: React/Next.js with Tailwind CSS
- Authentication: Strava OAuth 2.0
- Deployment: Docker with Docker Compose

### Strategy 2: Microservices Architecture

**Approach**: Separate services for auth, data processing, AI, and frontend
- **Pros**: 
  - Better scalability
  - Independent service deployment
  - Technology flexibility per service
- **Cons**: 
  - Over-engineering for Pre-MVP
  - Complex deployment and testing
  - Higher development time

### Strategy 3: Serverless Architecture

**Approach**: AWS Lambda/Vercel functions with managed services
- **Pros**: 
  - Auto-scaling
  - Pay-per-use pricing
  - Managed infrastructure
- **Cons**: 
  - Cold start latency
  - Complex debugging
  - Vendor lock-in

**Recommendation**: Strategy 1 (Monolithic FastAPI) is optimal for Pre-MVP due to faster development, easier testing, and sufficient scalability for initial user base.

---

## Executive Checklist

### Phase 1: Environment Setup & Project Structure (Week 1)

#### 1.1 Development Environment Setup
- [ ] Install Python 3.11+ and Node.js 18+
- [ ] Set up virtual environment and package management
- [ ] Configure Docker and Docker Compose
- [ ] Set up MongoDB locally and in cloud
- [ ] Configure development IDE with linting and formatting

#### 1.2 Project Structure Creation
```
stravaAi/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

#### 1.3 Configuration Files
- [ ] Create `requirements.txt` with FastAPI, pymongo, httpx, python-dotenv
- [ ] Create `package.json` with React, Next.js, Tailwind CSS
- [ ] Set up environment variables template
- [ ] Configure Docker Compose for local development

### Phase 2: Authentication & Strava Integration (Week 1-2)

#### 2.1 Strava OAuth Implementation
- [ ] Register application with Strava API
- [ ] Implement OAuth 2.0 flow in FastAPI
- [ ] Create token refresh mechanism
- [ ] Set up secure token storage in MongoDB
- [ ] Implement user session management

#### 2.2 User Onboarding Flow
- [ ] Create user profile model (name, age, weight)
- [ ] Implement milestone setting functionality
- [ ] Design onboarding UI components
- [ ] Add form validation and error handling

#### 2.3 Strava API Integration
- [ ] Implement activity fetching endpoints
- [ ] Create data models for Strava activities
- [ ] Set up background job for data synchronization
- [ ] Add error handling for API rate limits

### Phase 3: Data Processing & Analytics (Week 2-3)

#### 3.1 Activity Data Processing
- [ ] Parse Strava activity data (swim, run, ride)
- [ ] Calculate key metrics (distance, pace, HR zones)
- [ ] Implement data aggregation for trends
- [ ] Create data validation and cleaning

#### 3.2 Analytics Dashboard
- [ ] Design dashboard layout and components
- [ ] Implement real-time metrics display
- [ ] Create week-over-week trend graphs
- [ ] Add monthly volume & intensity charts
- [ ] Implement responsive design

#### 3.3 Performance Tracking
- [ ] Create milestone progress tracking
- [ ] Implement goal proximity calculations
- [ ] Design progress visualization components
- [ ] Add performance gap analysis

### Phase 4: AI Insights Engine (Week 3-4)

#### 4.1 AI Integration Setup
- [ ] Set up OpenAI/Gemini API integration
- [ ] Create AI service layer
- [ ] Implement prompt engineering system
- [ ] Add rate limiting and error handling

#### 4.2 Insight Generation
- [ ] Design system prompts for different sports
- [ ] Implement context-aware analysis
- [ ] Create insight formatting and display
- [ ] Add recommendation generation

#### 4.3 AI Dashboard Components
- [ ] Design insight display components
- [ ] Implement expandable recommendation blocks
- [ ] Add insight history tracking
- [ ] Create personalized coaching tips

### Phase 5: Testing & Deployment (Week 4-5)

#### 5.1 Testing Implementation
- [ ] Write unit tests for core functionality
- [ ] Implement integration tests for API endpoints
- [ ] Add end-to-end testing
- [ ] Set up CI/CD pipeline

#### 5.2 Performance Optimization
- [ ] Implement caching for API responses
- [ ] Optimize database queries
- [ ] Add request rate limiting
- [ ] Implement error monitoring

#### 5.3 Deployment Preparation
- [ ] Create production Docker configuration
- [ ] Set up environment variables for production
- [ ] Configure monitoring and logging
- [ ] Prepare deployment documentation

### Phase 6: Documentation & Launch (Week 5)

#### 6.1 Documentation
- [ ] Write API documentation
- [ ] Create user guide
- [ ] Document deployment procedures
- [ ] Prepare troubleshooting guide

#### 6.2 Launch Preparation
- [ ] Set up production environment
- [ ] Configure SSL certificates
- [ ] Implement backup strategies
- [ ] Prepare launch checklist

---

## Technical Implementation Details

### Database Schema Design

```javascript
// Users Collection
{
  "_id": ObjectId,
  "strava_id": Number,
  "name": String,
  "age": Number,
  "weight": Number,
  "milestones": [{
    "name": String,
    "date": Date,
    "target": String
  }],
  "created_at": Date,
  "updated_at": Date
}

// Activities Collection
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "strava_activity_id": Number,
  "type": String, // "Swim", "Run", "Ride"
  "name": String,
  "distance": Number,
  "moving_time": Number,
  "average_speed": Number,
  "average_heartrate": Number,
  "max_heartrate": Number,
  "start_date": Date,
  "raw_data": Object, // Full Strava response
  "created_at": Date
}

// Insights Collection
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "activity_id": ObjectId,
  "insight_text": String,
  "recommendation": String,
  "ai_model": String,
  "created_at": Date
}
```

### API Endpoints Structure

```python
# Authentication
POST /api/auth/strava/callback
POST /api/auth/refresh
GET /api/auth/user

# User Management
POST /api/users/onboarding
PUT /api/users/milestones
GET /api/users/profile

# Activities
GET /api/activities/latest
GET /api/activities/history
POST /api/activities/sync

# Analytics
GET /api/analytics/dashboard
GET /api/analytics/trends
GET /api/analytics/milestones

# AI Insights
POST /api/insights/generate
GET /api/insights/history
```

### Frontend Component Structure

```
src/
├── components/
│   ├── auth/
│   │   ├── StravaLogin.tsx
│   │   └── UserOnboarding.tsx
│   ├── dashboard/
│   │   ├── ActivityMetrics.tsx
│   │   ├── TrendCharts.tsx
│   │   └── MilestoneProgress.tsx
│   ├── insights/
│   │   ├── InsightCard.tsx
│   │   └── RecommendationBlock.tsx
│   └── common/
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── LoadingSpinner.tsx
├── pages/
│   ├── dashboard.tsx
│   ├── onboarding.tsx
│   └── auth.tsx
└── services/
    ├── api.ts
    ├── strava.ts
    └── ai.ts
```

---

## Risk Assessment & Mitigation

### Technical Risks
1. **Strava API Rate Limits**: Implement exponential backoff and caching
2. **AI API Costs**: Set up usage monitoring and fallback responses
3. **Data Synchronization**: Implement robust error handling and retry logic
4. **Performance**: Use caching and optimize database queries

### Business Risks
1. **User Adoption**: Focus on core value proposition and ease of use
2. **Competition**: Emphasize AI-powered insights as differentiator
3. **Scalability**: Design with future microservices migration in mind

---

## Success Metrics

### Technical Metrics
- API response time < 200ms
- 99.9% uptime
- < 1% error rate
- User session duration > 5 minutes

### Business Metrics
- User onboarding completion rate > 80%
- Daily active users
- Insight engagement rate
- User retention after 7 days

---

## Timeline Summary

| Week | Focus | Deliverables |
|------|-------|-------------|
| 1 | Environment & Auth | Project setup, OAuth integration |
| 2 | Data Processing | Activity fetching, data models |
| 3 | Analytics Dashboard | Metrics display, charts |
| 4 | AI Integration | Insight generation, recommendations |
| 5 | Testing & Deployment | Production deployment, documentation |

**Total Estimated Time**: 5 weeks for Pre-MVP completion
**Team Size**: 2-3 developers (1 backend, 1 frontend, 1 full-stack)
**Budget**: ~$500/month for infrastructure and AI API costs 