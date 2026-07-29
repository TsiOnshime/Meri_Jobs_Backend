# Meri Jobs Backend API Documentation

## Base URL
```
http://localhost:8080/api/v1
```

## Authentication
All endpoints (except public ones) require JWT authentication:
```
Authorization: Bearer <access_token>
```

---

## User Service Endpoints

### POST /auth/register
Create a new user account.

**Request Body (JSON):**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

**Response 201:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": null
  },
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
```

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email already exists"
  },
  "correlation_id": "uuid"
}
```

---

### POST /auth/login
Authenticate with email and password.

**Request Body (JSON):**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response 200:**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

**Error Response 401:**
```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Invalid credentials"
  },
  "correlation_id": "uuid"
}
```

---

### POST /auth/refresh
Exchange a refresh token for a new token pair.

**Request Body (JSON):**
```json
{
  "refresh": "jwt_refresh_token"
}
```

**Response 200:**
```json
{
  "access": "new_jwt_access_token",
  "refresh": "new_jwt_refresh_token"
}
```

**Error Response 401:**
```json
{
  "error": {
    "code": "AUTH_INVALID_TOKEN",
    "message": "Invalid or expired refresh token"
  },
  "correlation_id": "uuid"
}
```

---

### POST /auth/logout
Invalidate the given refresh token.

**Request Body (JSON):**
```json
{
  "refresh": "jwt_refresh_token"
}
```

**Response 200:**
```json
{
  "message": "Successfully logged out"
}
```

---

### GET /auth/me
Return the currently authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

**Error Response 401:**
```json
{
  "error": {
    "code": "AUTH_INVALID_TOKEN",
    "message": "Authentication required"
  },
  "correlation_id": "uuid"
}
```

---

## CV Parser Endpoints

### POST /cv/upload
Upload a CV file for asynchronous parsing.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (Multipart Form Data):**
- **file**: PDF or DOCX file (multipart/form-data)

**Important:** Do NOT manually set `Content-Type` header. Let your API client auto-generate `multipart/form-data; boundary=...`

**Example using curl:**
```bash
curl.exe -X POST "http://localhost:8080/api/v1/cv/upload" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@path/to/your/cv.pdf"
```

**Response 202:**
```json
{
  "cv_id": "uuid",
  "status": "processing",
  "message": "CV uploaded and is being processed"
}
```

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Unsupported file type",
    "detail": "Only .pdf and .docx are accepted"
  },
  "correlation_id": "uuid"
}
```

**Error Response 401:**
```json
{
  "error": {
    "code": "AUTH_INVALID_TOKEN",
    "message": "Authentication required"
  },
  "correlation_id": "uuid"
}
```

---

### GET /cv/{cv_id}/status
Poll the parsing status and retrieve parsed data once complete.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200 (Processing):**
```json
{
  "cv_id": "uuid",
  "status": "processing",
  "message": "CV is being parsed"
}
```

**Response 200 (Completed):**
```json
{
  "cv_id": "uuid",
  "status": "completed",
  "parsed_data": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "skills": ["Python", "Django", "React"],
    "experience": [...],
    "education": [...]
  },
  "optimization_suggestions": [
    {
      "section": "skills",
      "suggestion": "Add more technical skills",
      "priority": "high"
    }
  ]
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

---

### PATCH /cv/{cv_id}
Edit a single field of the parsed CV data.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (JSON):**
```json
{
  "field": "email",
  "value": "newemail@example.com"
}
```

**Response 200:**
```json
{
  "cv_id": "uuid",
  "field": "email",
  "updated_value": "newemail@example.com"
}
```

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid field or value"
  },
  "correlation_id": "uuid"
}
```

---

### GET /cv/{cv_id}/export
Export the CV as a binary PDF file.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
- **Content-Type:** `application/pdf`
- **Body:** Binary PDF file

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

---

### POST /cv/{cv_id}/suggestions/accept
Accept and apply an optimization suggestion.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (JSON):**
```json
{
  "suggestion_id": "uuid"
}
```

**Response 200:**
```json
{
  "message": "Suggestion accepted and applied"
}
```

**Error Response 404:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Suggestion not found"
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
- `AUTH_INVALID_CREDENTIALS` - Invalid login credentials
- `VALIDATION_ERROR` - Request validation failed
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `SERVICE_UNAVAILABLE` - Downstream service error
- `NOT_FOUND` - Resource not found
- `UNSUPPORTED_MEDIA_TYPE` - Invalid content type

---

## Rate Limits

- **Auth endpoints:** 5 requests per minute
- **CV upload:** 2 requests per minute
- **Other endpoints:** 100 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit-Minute`
- `X-RateLimit-Remaining-Minute`

---

## Notes

1. **Authentication:** All authenticated endpoints require `Authorization: Bearer <token>` header
2. **Token Refresh:** Use `/auth/refresh` before tokens expire
3. **File Uploads:** Must use `multipart/form-data` - do NOT manually set `Content-Type` header
4. **Datetime Format:** All datetime fields are ISO 8601 in UTC
5. **Correlation ID:** Use the `correlation_id` from error responses when reporting issues
6. **Bruno Client:** If using Bruno for file uploads, ensure NO `Content-Type` header is set in the Headers tab

---

## Testing Guidance

### User Service Testing
1. Register a new user with `/auth/register`
2. Login with `/auth/login` to get tokens
3. Test token refresh with `/auth/refresh`
4. Test logout with `/auth/logout`
5. Test current user info with `/auth/me`

### CV Parser Testing
1. Login to get access token
2. Upload CV using `/cv/upload` with curl (Bruno has multipart issues)
3. Poll status with `/cv/{cv_id}/status` until `status: "completed"`
4. Test CV editing with `/cv/{cv_id}/status`
5. Test export with `/cv/{cv_id}/export`
6. Test suggestions with `/cv/{cv_id}/suggestions/accept`

### File Upload Troubleshooting
If you encounter "Unsupported media type" errors:
- **Remove** any `Content-Type` header from your request
- Use `multipart/form-data` body type
- Let your API client auto-generate the boundary
- Use curl as a fallback: `curl -F "file=@cv.pdf" -H "Authorization: Bearer <token>"`
