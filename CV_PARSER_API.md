# CV Parser Service API Documentation

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

## POST /cv/upload
Upload a CV file for parsing.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (multipart/form-data):**
```
file: <cv_file>
```

**Supported File Types:**
- PDF (.pdf)
- Word Document (.docx)

**File Size Limit:** 10MB

**Response 201:**
```json
{
  "cv_id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
  "status": "processing"
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

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File too large"
  },
  "correlation_id": "uuid"
}
```

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing file"
  },
  "correlation_id": "uuid"
}
```

---

## GET /cv/{cv_id}/status
Get the parsing status of a CV.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "cv_id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
  "status": "completed",
  "progress": 100,
  "parsed_data": {
    "email": "john@example.com",
    "phone": "+1234567890",
    "skills": ["Python", "JavaScript", "React"],
    "experience": [
      {
        "company": "Tech Corp",
        "position": "Software Engineer",
        "duration": "2 years"
      }
    ],
    "education": [
      {
        "institution": "University",
        "degree": "Bachelor of Science",
        "year": "2020"
      }
    ]
  }
}
```

**Status Values:**
- `processing` - CV is being parsed
- `completed` - Parsing completed successfully
- `failed` - Parsing failed

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

## PATCH /cv/{cv_id}
Update parsed CV data.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "field": "email",
  "value": "newemail@example.com"
}
```

**Supported Fields:**
- `email`
- `phone`
- `skills` (array)
- `experience` (array)
- `education` (array)

**Response 200:**
```json
{
  "cv_id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
  "status": "completed",
  "field": "email",
  "value": "newemail@example.com"
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
    "message": "Invalid field"
  },
  "correlation_id": "uuid"
}
```

---

## GET /cv/{cv_id}/export
Export parsed CV data in various formats.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `format` - Export format: `json` (default), `pdf`, `docx`

**Response 200 (JSON format):**
```json
{
  "cv_id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
  "data": {
    "email": "john@example.com",
    "phone": "+1234567890",
    "skills": ["Python", "JavaScript", "React"],
    "experience": [...],
    "education": [...]
  }
}
```

**Response 200 (PDF/DOCX format):**
Binary file download

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

## POST /cv/{cv_id}/suggestions/accept
Accept a parsing suggestion.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
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
  "cv_id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
  "suggestion_id": "uuid",
  "status": "accepted"
}
```

**Error Response 404:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "CV or suggestion not found"
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
- `FILE_TOO_LARGE` - File exceeds size limit
- `UNSUPPORTED_FILE_TYPE` - Invalid file format
- `SERVICE_UNAVAILABLE` - Downstream service error

---

## Rate Limits

- **Upload endpoint:** 10 requests per hour
- **Status endpoint:** 100 requests per minute
- **Update endpoint:** 50 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit-Minute`
- `X-RateLimit-Remaining-Minute`

---

## Parsed Data Structure

### Contact Information
- `email` - Email address
- `phone` - Phone number

### Skills
- `skills` - Array of skill names
  ```json
  ["Python", "JavaScript", "React", "Docker"]
  ```

### Experience
- `experience` - Array of work experience objects
  ```json
  [
    {
      "company": "Tech Corp",
      "position": "Software Engineer",
      "duration": "2 years",
      "description": "Developed web applications"
    }
  ]
  ```

### Education
- `education` - Array of education objects
  ```json
  [
    {
      "institution": "University",
      "degree": "Bachelor of Science",
      "field": "Computer Science",
      "year": "2020"
    }
  ]
  ```

---

## Testing Guidance

### CV Upload Flow
1. Ensure file is .pdf or .docx format
2. File size must be under 10MB
3. Call `/cv/upload` with file in multipart/form-data
4. Store returned `cv_id` for subsequent operations
5. Wait for parsing to complete (check status)

### Status Check Flow
1. Call `/cv/{cv_id}/status` to check parsing progress
2. Monitor `status` field: `processing` → `completed` or `failed`
3. When `completed`, access `parsed_data` field
4. When `failed`, check error details

### Data Update Flow
1. Call `/cv/{cv_id}/status` to ensure parsing is complete
2. Call `/cv/{cv_id}` with PATCH to update specific fields
3. Only update one field at a time
4. Verify update by calling status endpoint again

### Export Flow
1. Ensure CV parsing is complete
2. Call `/cv/{cv_id}/export` with desired format
3. For JSON: receive JSON response
4. For PDF/DOCX: receive binary file download

### Suggestion Acceptance Flow
1. Get CV status to see available suggestions
2. Call `/cv/{cv_id}/suggestions/accept` with suggestion_id
3. Verify suggestion was applied
4. Check status endpoint to see updated data

---

## Notes

- CV parsing is asynchronous - upload returns immediately with `cv_id`
- Parsing typically takes 5-30 seconds depending on file size
- All datetime fields are ISO 8601 in UTC
- Use the `correlation_id` from error responses when reporting issues
- File uploads are validated for type and size before processing
- Parsed data may contain suggestions for manual review
- Export formats require additional processing time
- Rate limits are enforced per user account
- CV data is associated with the authenticated user's account
