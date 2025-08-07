# Strava OAuth Authentication - Backend-AI Planning (Updated)

## Introduction
Strava OAuth Authentication is the entry point for all users of StravaAI. It enables secure login using Strava accounts, allowing the application to fetch user activity data and provide personalized analytics and AI-powered insights. This system must handle user authorization, token management (including refresh), and securely store credentials for subsequent API calls.

## Strategy

### Implementation Options
1. **Direct OAuth Flow with FastAPI**
   - Implement the OAuth 2.0 Authorization Code flow directly in FastAPI.
   - Handle redirect, callback, and token exchange endpoints.
   - Store access and refresh tokens securely in MongoDB (encrypted).
   - Use background jobs for token refresh.
   - Pros: Full control, easy to extend, minimal dependencies.
   - Cons: Slightly more code to maintain.

2. **Use OAuth Library (e.g., Authlib)**
   - Leverage Authlib or similar for OAuth flow abstraction.
   - Reduces boilerplate and potential security pitfalls.
   - Pros: Faster to implement, less error-prone.
   - Cons: Adds dependency, less control over edge cases.

3. **Third-Party Auth Service (Not Recommended for Pre-MVP)**
   - Use Auth0 or similar to manage OAuth.
   - Pros: Offloads security, easy scaling.
   - Cons: Overkill for Pre-MVP, adds cost and complexity.

### Recommended MVP Approach
- **Option 2**: Use Authlib for OAuth abstraction with manual token exchange for control.
- Store tokens encrypted in session (for MVP) and MongoDB (for production).
- Implement endpoints for login, callback, token refresh, and user profile fetch.
- Ensure all sensitive data is handled securely.
- Add background job for token refresh if needed.

## Frontend Integration Strategy

### Architecture Design
```
Frontend (React/Next.js) ←→ Backend (FastAPI) ←→ Strava API
     ↑                           ↑
   JWT Token              Session + JWT
   (Client State)         (Server State)
```

### Authentication Flow Design
1. **Frontend initiates OAuth** → Backend redirects to Strava
2. **User authorizes on Strava** → Strava redirects to backend callback
3. **Backend exchanges code** → Stores tokens in session + generates JWT
4. **Backend redirects to frontend** → Frontend stores JWT
5. **Frontend uses JWT for API calls** → Backend validates session

### Frontend Integration Requirements
- CORS configuration for cross-origin requests
- JWT token generation for frontend state management
- Session-based authentication for backend security
- Frontend authentication status endpoints
- Secure token storage and client-side state management

## Dependencies & Environment Setup

### Required Dependencies
```txt
fastapi
uvicorn
python-dotenv
pymongo
motor
Authlib
httpx
PyJWT
python-multipart
```

### Environment Variables
```bash
# Strava OAuth
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REDIRECT_URI=http://localhost:8000/exchange_token

# Security
JWT_SECRET=your_jwt_secret_key

# Frontend Integration
FRONTEND_URL=http://localhost:3000

# Database (for production)
MONGODB_URI=your_mongodb_connection_string
```

## Implementation Phases

### Phase 1: Basic OAuth Flow
- [x] Set up project structure and dependencies
- [x] Implement basic OAuth redirect and callback
- [x] Test with manual URL construction
- [x] Handle OAuth code exchange

### Phase 2: Session Management
- [x] Add SessionMiddleware for OAuth state
- [x] Implement secure token storage in session
- [x] Test session-based authentication
- [x] Handle CSRF protection and state validation

### Phase 3: Frontend Integration
- [x] Add CORS configuration for frontend communication
- [x] Implement JWT token generation for frontend state
- [x] Create frontend authentication endpoints
- [x] Test complete frontend-backend flow
- [x] Implement authentication status checking

### Phase 4: Security & Error Handling
- [x] Implement secure token storage (no client exposure)
- [x] Add authentication status and logout endpoints
- [x] Secure cookie configuration
- [ ] Implement comprehensive error handling
- [ ] Add token refresh logic
- [ ] Add production-ready security measures

## Executive Checklist
- [x] Register Strava application and obtain client credentials
- [x] Implement `/api/auth/strava/authorize` endpoint (redirect to Strava)
- [x] Implement `/exchange_token` endpoint (handle code exchange)
- [x] Securely store access and refresh tokens in session (encrypted)
- [x] Implement `/api/auth/status` endpoint for authentication status
- [x] Implement `/api/auth/user` endpoint to fetch user profile
- [x] Add JWT-based session management for API access
- [x] Enforce HTTPS and secure cookie/session handling
- [x] Add CORS configuration for frontend integration
- [x] Implement frontend authentication flow with JWT tokens
- [ ] Implement `/api/auth/refresh` endpoint for token refresh
- [ ] Securely store tokens in MongoDB (encrypted) for production
- [ ] Add comprehensive error handling and logging
- [ ] Document the authentication flow for frontend integration

## Security Considerations

### Token Storage Strategy
- **Development:** Session-based storage (encrypted by SessionMiddleware)
- **Production:** MongoDB storage (encrypted) with session fallback
- **Frontend:** JWT tokens for state management (no sensitive data)

### Security Measures Implemented
- Session-based authentication for backend security
- JWT tokens for frontend state management
- CORS configuration for cross-origin security
- Secure cookie configuration
- Token exposure prevention (no tokens returned to client)

### Security Measures Pending
- Token refresh logic implementation
- MongoDB integration for persistent storage
- Production-ready security hardening
- Rate limiting and abuse prevention

## Error Handling Strategy

### OAuth Flow Errors
- Invalid client_id errors from Strava API
- Session state mismatches during callback
- Token exchange failures
- Redirect URI mismatches

### Frontend Integration Errors
- CORS configuration issues
- Authentication status errors
- JWT token validation failures
- Session expiration handling

### Error Response Format
```json
{
  "error": "Error description",
  "details": "Additional error details",
  "code": "ERROR_CODE"
}
```

## Testing Strategy

### OAuth Flow Testing
- [x] Test OAuth redirect to Strava
- [x] Test OAuth callback and code exchange
- [x] Test session-based authentication
- [x] Test JWT token generation

### Frontend Integration Testing
- [x] Test CORS configuration
- [x] Test authentication status endpoint
- [x] Test frontend authentication flow
- [x] Test logout functionality

### Security Testing
- [x] Test token exposure prevention
- [x] Test session security
- [ ] Test token refresh logic
- [ ] Test error handling scenarios

## API Endpoints

### Authentication Endpoints
```python
# OAuth Flow
GET /api/auth/strava/authorize
    # Redirects to Strava authorization URL

GET /exchange_token
    # Handles Strava OAuth callback
    # Parameters: code, state
    # Returns: Redirect to frontend with JWT token

# Authentication Status
GET /api/auth/status
    # Check if user is authenticated
    # Returns: {authenticated: bool, user: object}

GET /api/auth/user
    # Get current user profile
    # Returns: User profile data

POST /api/auth/logout
    # Logout user (clear session)
    # Returns: {message: string}
```

### Frontend Integration Endpoints
```python
# Frontend Success Page
GET /auth/success
    # Success page after OAuth (tokens stored in session)
    # Returns: User info (no sensitive tokens)

# JWT Token Generation
# Automatically generated during OAuth callback
# Redirected to frontend with token parameter
```

## Lessons Learned

### Critical Success Factors
1. **Frontend Integration is Essential** - OAuth flow is only half the story
2. **Dependencies Matter** - Missing dependencies cause multiple iterations
3. **Error Handling is Critical** - OAuth flows have many failure points
4. **Security is Multi-Layered** - Session + JWT + CORS + Token storage

### Common Pitfalls to Avoid
1. **Incomplete Planning** - Always consider frontend integration from the start
2. **Missing Dependencies** - Document all required packages upfront
3. **Security Oversights** - Design security into the system from the beginning
4. **Poor Error Handling** - Plan for error scenarios and edge cases

### Best Practices
1. **Phased Implementation** - Break down complex features into manageable phases
2. **Comprehensive Testing** - Test complete user journeys, not just individual components
3. **Documentation** - Document decisions, trade-offs, and implementation details
4. **Security First** - Consider security implications in every design decision

## Future Enhancements

### Short Term (Next Sprint)
- [ ] Implement token refresh logic
- [ ] Add MongoDB integration for persistent storage
- [ ] Implement comprehensive error handling
- [ ] Add production-ready security measures

### Medium Term (Next Month)
- [ ] Add user onboarding flow
- [ ] Implement activity data fetching
- [ ] Add analytics dashboard
- [ ] Implement AI insights generation

### Long Term (Next Quarter)
- [ ] Add social features
- [ ] Implement advanced analytics
- [ ] Add mobile app support
- [ ] Scale to production environment
