# Database Schemas & Data Models

## Overview

This document describes the MongoDB database schemas, indexes, and data models implemented for the StravaAI platform. The system uses MongoDB Atlas with optimized indexes for performance-critical queries.

## Database Collections

### 1. Users Collection

**Purpose**: Store user profiles, authentication tokens, and personal information.

**Schema**:
```javascript
{
  "_id": ObjectId,                    // MongoDB document ID
  "strava_id": Number,                // Strava athlete ID (unique)
  "username": String,                 // Strava username
  "firstname": String,                // User's first name
  "lastname": String,                 // User's last name
  "email": String,                    // User's email (optional)
  "age": Number,                      // User-provided age (optional)
  "weight": Number,                   // User-provided weight in kg (optional)
  "city": String,                     // User's city from Strava (optional)
  "country": String,                  // User's country from Strava (optional)
  "milestones": [                     // Array of user milestones
    {
      "id": ObjectId,                 // Milestone ID
      "name": String,                 // Milestone name
      "date": Date,                   // Target date
      "target": String,               // Target goal (e.g., "sub-2:30")
      "sport_type": String,           // Sport type
      "distance": Number,             // Target distance in meters
      "created_at": Date              // Creation timestamp
    }
  ],
  "access_token": String,             // Encrypted Strava access token
  "refresh_token": String,            // Encrypted Strava refresh token
  "token_expires_at": Date,           // Token expiration timestamp
  "created_at": Date,                 // User creation timestamp
  "updated_at": Date,                 // Last update timestamp
  "last_activity_sync": Date          // Last activity sync timestamp (optional)
}
```

**Indexes**:
- `strava_id` (unique) - Primary lookup for user authentication
- `username` - For username-based queries
- `email` - For email-based queries
- `access_token` - For token validation
- `token_expires_at` - For expired token cleanup

### 2. Activities Collection

**Purpose**: Store user activities synced from Strava with analytics-ready structure.

**Schema**:
```javascript
{
  "_id": ObjectId,                    // MongoDB document ID
  "user_id": ObjectId,                // Reference to User document
  "strava_activity_id": Number,       // Strava activity ID (unique)
  "name": String,                     // Activity name
  "type": String,                     // Activity type ("Swim", "Run", "Ride")
  "sport_type": String,               // More specific sport type from Strava
  "distance": Number,                 // Distance in meters
  "moving_time": Number,              // Moving time in seconds
  "elapsed_time": Number,             // Total elapsed time in seconds
  "total_elevation_gain": Number,     // Total elevation gain in meters (optional)
  "average_speed": Number,            // Average speed in m/s (optional)
  "max_speed": Number,                // Maximum speed in m/s (optional)
  "average_heartrate": Number,        // Average heart rate in bpm (optional)
  "max_heartrate": Number,            // Maximum heart rate in bpm (optional)
  "start_date": Date,                 // Activity start date
  "start_date_local": Date,           // Local start date
  "timezone": String,                 // Activity timezone (optional)
  "location_city": String,            // Activity location city (optional)
  "location_state": String,           // Activity location state (optional)
  "location_country": String,         // Activity location country (optional)
  "map": {                            // Activity map data (optional)
    "summary_polyline": String,       // Google polyline encoded route
    "resource_state": Number          // Resource state from Strava
  },
  "raw_data": Object,                 // Full Strava API response
  "created_at": Date,                 // Document creation timestamp
  "updated_at": Date                  // Last update timestamp
}
```

**Indexes**:
- `user_id` - For user-specific activity queries
- `strava_activity_id` (unique) - For duplicate prevention
- `type` - For activity type filtering
- `sport_type` - For sport-specific queries
- `start_date` (descending) - For chronological ordering
- `user_id + start_date` (compound) - For user's chronological activities
- `user_id + type` (compound) - For user's activities by type
- `distance` (descending) - For distance-based queries

### 3. Insights Collection

**Purpose**: Store AI-generated insights and recommendations.

**Schema**:
```javascript
{
  "_id": ObjectId,                    // MongoDB document ID
  "user_id": ObjectId,                // Reference to User document
  "activity_id": ObjectId,            // Reference to Activity document (optional)
  "insight_type": String,             // Type: "performance", "training", "milestone"
  "insight_text": String,             // Main insight text
  "recommendation": String,           // Actionable recommendation
  "confidence_score": Number,         // AI confidence score (0-1)
  "ai_model": String,                 // AI model used ("gpt-4o", "gemini-2.5")
  "context_data": {                   // Context data for insight (optional)
    "activity_count": Number,         // Number of activities in context
    "time_period": String,            // Time period ("1_week", "1_month")
    "sport_type": String,             // Sport type for context
    "milestone_progress": Number      // Milestone progress 0-100
  },
  "created_at": Date                  // Insight creation timestamp
}
```

**Indexes**:
- `user_id` - For user-specific insights
- `activity_id` - For activity-specific insights
- `insight_type` - For insight type filtering
- `created_at` (descending) - For chronological ordering
- `user_id + created_at` (compound) - For user's chronological insights
- `confidence_score` (descending) - For quality-based filtering

## Data Validation

### Pydantic Models

The system uses Pydantic models for data validation and serialization:

1. **User Model**: Validates user data with age and weight constraints
2. **Activity Model**: Validates activity data with distance and time constraints
3. **Insight Model**: Validates insight data with confidence score constraints
4. **Milestone Model**: Validates milestone data with date and distance constraints

### Validation Rules

- **Age**: Must be between 0 and 150
- **Weight**: Must be positive
- **Distance**: Must be non-negative
- **Time**: Must be non-negative
- **Confidence Score**: Must be between 0 and 1

## Security Features

### Token Encryption

- **Access Tokens**: Encrypted using Fernet (AES-128) with PBKDF2 key derivation
- **Refresh Tokens**: Encrypted using the same method
- **Key Derivation**: Uses SECRET_KEY environment variable with 100,000 iterations
- **Salt**: Fixed salt for consistency across application restarts

### Data Protection

- **HTTPS**: All communications use HTTPS
- **Input Validation**: All inputs validated with Pydantic models
- **SQL Injection Prevention**: MongoDB prevents SQL injection
- **XSS Protection**: Frontend implements XSS protection

## Performance Optimization

### Index Strategy

1. **Primary Lookups**: Unique indexes on `strava_id` and `strava_activity_id`
2. **User Queries**: Compound indexes for user-specific data
3. **Time-based Queries**: Descending indexes on date fields
4. **Filtering**: Indexes on frequently filtered fields

### Query Optimization

1. **Pagination**: Skip/limit for large result sets
2. **Aggregation**: MongoDB aggregation pipeline for complex analytics
3. **Projection**: Only fetch required fields
4. **Connection Pooling**: Motor async driver with connection pooling

## Data Flow

### Authentication Flow

1. User authorizes with Strava OAuth
2. Tokens encrypted and stored in database
3. User session created with Strava ID
4. Automatic token refresh on expiration

### Activity Sync Flow

1. User triggers activity sync
2. Fetch activities from Strava API
3. Validate and sanitize activity data
4. Store in database with full raw data
5. Update user's last sync timestamp

### Insight Generation Flow

1. AI module analyzes user data
2. Generate insights with confidence scores
3. Store insights with context data
4. Associate with specific activities if applicable

## Environment Configuration

### Required Environment Variables

```bash
# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/stravaai
DATABASE_NAME=stravaai

# Security
SECRET_KEY=your-secret-key-for-encryption
JWT_SECRET=your-jwt-secret

# Strava API
STRAVA_CLIENT_ID=your_strava_client_id
STRAVA_CLIENT_SECRET=your_strava_client_secret
STRAVA_REDIRECT_URI=http://localhost:3000/api/auth/strava/callback
```

## Migration Strategy

### Schema Evolution

1. **Backward Compatibility**: New fields are optional
2. **Data Migration**: Scripts for schema updates
3. **Version Control**: Schema versions tracked
4. **Rollback Plan**: Database backups before migrations

### Index Management

1. **Background Index Creation**: Non-blocking index creation
2. **Index Monitoring**: Performance monitoring for index usage
3. **Index Cleanup**: Remove unused indexes
4. **Compound Index Optimization**: Optimize for common query patterns

## Monitoring & Maintenance

### Database Monitoring

1. **Connection Pool**: Monitor connection pool usage
2. **Query Performance**: Monitor slow queries
3. **Index Usage**: Monitor index hit rates
4. **Storage Usage**: Monitor database size growth

### Backup Strategy

1. **Automated Backups**: Daily automated backups
2. **Point-in-Time Recovery**: MongoDB Atlas point-in-time recovery
3. **Backup Testing**: Regular backup restoration testing
4. **Disaster Recovery**: Multi-region backup strategy

## API Integration

### Frontend Integration

The database schemas are designed to support all API endpoints defined in the technical specification:

- **Authentication**: Secure token storage and refresh
- **User Management**: Profile and milestone management
- **Activity Management**: Sync, query, and analytics
- **Insights**: AI-generated insights and recommendations

### AI Module Integration

The database structure supports AI module integration:

- **Context Data**: Rich context for AI analysis
- **Confidence Scores**: Quality metrics for insights
- **Historical Data**: Complete activity history for analysis
- **User Preferences**: Milestones and goals for personalized insights
