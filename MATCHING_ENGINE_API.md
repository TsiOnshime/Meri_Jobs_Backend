# Matching Engine Service API Documentation

## Base URL
```
http://localhost:8080/api/v1
```

## Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer <access_token>
```

---

## GET /matches/{cv_id}
Get job matches for a specific CV.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `cv_id` - UUID of the CV to match against

**Query Parameters:**
- `limit` - Maximum number of results (default: 20, max: 100)
- `offset` - Pagination offset (default: 0)
- `sort` - Sort order: `score` (default), `relevance`, `date`

**Response 200:**
```json
{
  "cv_id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
  "total_matches": 150,
  "matches": [
    {
      "job_id": "abc123-def4-5678-90ab-cdef12345678",
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "Addis Ababa",
      "score": 0.95,
      "relevance": "high",
      "salary_range": "$80,000 - $120,000",
      "posted_date": "2026-07-15T00:00:00Z",
      "description": "We are looking for an experienced software engineer...",
      "matched_skills": ["Python", "JavaScript", "React"],
      "requirements": ["5+ years experience", "Bachelor's degree"]
    },
    {
      "job_id": "xyz789-ghi0-1234-56ab-cdef12345678",
      "title": "Full Stack Developer",
      "company": "Startup Inc",
      "location": "Remote",
      "score": 0.88,
      "relevance": "high",
      "salary_range": "$70,000 - $100,000",
      "posted_date": "2026-07-20T00:00:00Z",
      "description": "Join our team to build amazing products...",
      "matched_skills": ["JavaScript", "React", "Node.js"],
      "requirements": ["3+ years experience", "Portfolio required"]
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 150,
    "has_more": true
  }
}
```

**Error Response 404:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "CV not found"
  },
  "correlation_id": "uuid"
}
```

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid CV ID format"
  },
  "correlation_id": "uuid"
}
```

---

## GET /matches/{cv_id}/{job_id}
Get detailed information about a specific job match.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `cv_id` - UUID of the CV
- `job_id` - UUID of the job

**Response 200:**
```json
{
  "cv_id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
  "job_id": "abc123-def4-5678-90ab-cdef12345678",
  "title": "Senior Software Engineer",
  "company": "Tech Corp",
  "location": "Addis Ababa",
  "score": 0.95,
  "relevance": "high",
  "salary_range": "$80,000 - $120,000",
  "posted_date": "2026-07-15T00:00:00Z",
  "deadline": "2026-08-15T00:00:00Z",
  "description": "We are looking for an experienced software engineer to join our team. You will be responsible for developing and maintaining web applications using modern technologies.",
  "requirements": [
    "5+ years of software development experience",
    "Bachelor's degree in Computer Science or related field",
    "Strong proficiency in Python and JavaScript",
    "Experience with React and Node.js",
    "Knowledge of cloud services (AWS/GCP)"
  ],
  "benefits": [
    "Competitive salary",
    "Health insurance",
    "Remote work options",
    "Professional development budget"
  ],
  "matched_skills": ["Python", "JavaScript", "React"],
  "skill_gaps": ["AWS", "Docker"],
  "match_analysis": {
    "overall_score": 0.95,
    "skill_match": 0.90,
    "experience_match": 0.95,
    "location_match": 1.0,
    "salary_match": 0.85
  },
  "application_url": "https://example.com/apply/123",
  "contact_email": "jobs@techcorp.com"
}
```

**Error Response 404:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "CV or job not found"
  },
  "correlation_id": "uuid"
}
```

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid CV ID or job ID format"
  },
  "correlation_id": "uuid"
}
```

---

## Error Response Format

All errors follow this consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  },
  "correlation_id": "uuid-for-tracking"
}
```

### Common Error Codes

- `AUTH_MISSING_TOKEN` - Missing authorization header
- `AUTH_INVALID_TOKEN` - Invalid or expired token
- `VALIDATION_ERROR` - Request validation failed
- `NOT_FOUND` - Resource not found
- `SERVICE_UNAVAILABLE` - Downstream service error

---

## Rate Limits

- **Matches list endpoint:** 100 requests per minute
- **Match detail endpoint:** 200 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit-Minute`
- `X-RateLimit-Remaining-Minute`

---

## Match Scoring

### Overall Score
- Range: 0.0 to 1.0
- Higher scores indicate better matches
- Calculated from multiple factors

### Scoring Factors
- **Skill Match (0-1.0):** How well CV skills match job requirements
- **Experience Match (0-1.0):** Alignment of experience level
- **Location Match (0-1.0):** Geographic compatibility
- **Salary Match (0-1.0):** Salary expectations alignment

### Relevance Levels
- `high` - Score >= 0.8
- `medium` - Score >= 0.5
- `low` - Score < 0.5

---

## Sorting Options

### Sort by Score
- Sorts by overall match score (highest first)
- Default sorting method

### Sort by Relevance
- Sorts by relevance level (high → medium → low)
- Secondary sort by score within relevance level

### Sort by Date
- Sorts by job posting date (newest first)
- Useful for finding recent opportunities

---

## Pagination

### Basic Pagination
```json
{
  "limit": 20,
  "offset": 0,
  "total": 150,
  "has_more": true
}
```

### Pagination Flow
1. Start with `offset=0` and desired `limit`
2. Check `has_more` field in response
3. If `has_more=true`, increment `offset` by `limit`
4. Repeat until `has_more=false`

### Example
- Request 1: `offset=0, limit=20` → results 1-20
- Request 2: `offset=20, limit=20` → results 21-40
- Request 3: `offset=40, limit=20` → results 41-60

---

## Testing Guidance

### Get Matches Flow
1. Ensure CV has been uploaded and parsed
2. Call `/matches/{cv_id}` with CV UUID
3. Use query parameters to control results
4. Check `has_more` for pagination
5. Iterate through pages if needed

### Get Match Detail Flow
1. Get matches list to find job IDs
2. Call `/matches/{cv_id}/{job_id}` for detailed info
3. Review match analysis and skill gaps
4. Use information for application decision

### Match Analysis Interpretation
- **Overall Score:** Primary indicator of match quality
- **Skill Match:** Technical compatibility
- **Experience Match:** Career level alignment
- **Location Match:** Geographic feasibility
- **Salary Match:** Compensation alignment

### Skill Gap Analysis
- **Matched Skills:** Skills you have that match requirements
- **Skill Gaps:** Required skills you don't have
- Use this information to identify learning opportunities

---

## Notes

- Matching is performed asynchronously after CV parsing
- Match scores are recalculated periodically
- Job data is sourced from external job boards
- All datetime fields are ISO 8601 in UTC
- Use the `correlation_id` from error responses when reporting issues
- Matches are personalized to the user's CV profile
- Job availability may change between requests
- Rate limits are enforced per user account
- Match scores are relative to the specific CV used
