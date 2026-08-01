# User Service API Documentation

## Base URL
```
http://localhost:8080/api/v1
```

## Authentication
All endpoints (except register and login) require JWT authentication:
```
Authorization: Bearer <access_token>
```

---

## POST /auth/register
Create a new user account.

**Request Body (JSON):**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "language": "en"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Response 201:**
```json
{
  "user": {
    "id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
    "email": "john@example.com",
    "name": "John Doe",
    "full_name": "",
    "language": "en",
    "phone": "",
    "location": "",
    "bio": "",
    "role": "user",
    "created_at": "2026-08-01T16:01:02.965768Z",
    "last_login": null
  },
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
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

**Error Response 400 (Password Validation):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Password must contain at least one uppercase letter."
  },
  "correlation_id": "uuid"
}
```

---

## POST /auth/login
Authenticate with email and password.

**Request Body (JSON):**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response 200:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
    "email": "john@example.com",
    "name": "John Doe",
    "full_name": "John Doe",
    "language": "en",
    "phone": "+1234567890",
    "location": "Addis Ababa",
    "bio": "Software developer",
    "role": "user",
    "created_at": "2026-08-01T16:01:02.965768Z",
    "last_login": "2026-08-01T16:30:00.000000Z"
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

**Error Response 403:**
```json
{
  "error": {
    "code": "ACCOUNT_DEACTIVATED",
    "message": "Account is deactivated"
  },
  "correlation_id": "uuid"
}
```

---

## POST /auth/refresh
Exchange a refresh token for a new token pair.

**Request Body (JSON):**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response 200:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
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

## POST /auth/logout
Invalidate the given refresh token.

**Request Body (JSON):**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response 200:**
```json
{
  "message": "Successfully logged out"
}
```

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Refresh token is required"
  },
  "correlation_id": "uuid"
}
```

---

## GET /auth/me
Return the currently authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "user": {
    "id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
    "email": "john@example.com",
    "name": "John Doe",
    "full_name": "John Doe",
    "language": "en",
    "phone": "+1234567890",
    "location": "Addis Ababa",
    "bio": "Software developer",
    "role": "user",
    "created_at": "2026-08-01T16:01:02.965768Z",
    "last_login": "2026-08-01T16:30:00.000000Z"
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

## GET /auth/profile
Get user profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "user": {
    "id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
    "email": "john@example.com",
    "name": "John Doe",
    "full_name": "John Doe",
    "language": "en",
    "phone": "+1234567890",
    "location": "Addis Ababa",
    "bio": "Software developer",
    "role": "user",
    "created_at": "2026-08-01T16:01:02.965768Z",
    "last_login": "2026-08-01T16:30:00.000000Z"
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

## PUT /auth/profile
Update user profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (JSON):**
```json
{
  "full_name": "John Doe",
  "phone": "+1234567890",
  "location": "Addis Ababa",
  "bio": "Software developer"
}
```

**All fields are optional. Only include fields you want to update.**

**Response 200:**
```json
{
  "user": {
    "id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
    "email": "john@example.com",
    "name": "John Doe",
    "full_name": "John Doe",
    "language": "en",
    "phone": "+1234567890",
    "location": "Addis Ababa",
    "bio": "Software developer",
    "role": "user",
    "created_at": "2026-08-01T16:01:02.965768Z",
    "last_login": "2026-08-01T16:30:00.000000Z"
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

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid field value"
  },
  "correlation_id": "uuid"
}
```

---

## GET /auth/profile/detail
Get detailed user profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "user": {
    "id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
    "email": "john@example.com",
    "name": "John Doe",
    "full_name": "John Doe",
    "language": "en",
    "phone": "+1234567890",
    "location": "Addis Ababa",
    "bio": "Software developer",
    "role": "user",
    "created_at": "2026-08-01T16:01:02.965768Z",
    "last_login": "2026-08-01T16:30:00.000000Z"
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

## PUT /auth/profile/detail
Update detailed user profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (JSON):**
```json
{
  "full_name": "John Doe",
  "phone": "+1234567890",
  "location": "Addis Ababa",
  "bio": "Software developer"
}
```

**All fields are optional. Only include fields you want to update.**

**Response 200:**
```json
{
  "user": {
    "id": "9ca9882b-d068-4f54-90e1-204d121ca0e5",
    "email": "john@example.com",
    "name": "John Doe",
    "full_name": "John Doe",
    "language": "en",
    "phone": "+1234567890",
    "location": "Addis Ababa",
    "bio": "Software developer",
    "role": "user",
    "created_at": "2026-08-01T16:01:02.965768Z",
    "last_login": "2026-08-01T16:30:00.000000Z"
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

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid field value"
  },
  "correlation_id": "uuid"
}
```

---

## POST /auth/change-password
Change user password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (JSON):**
```json
{
  "old_password": "OldPass123",
  "new_password": "NewPass123"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Response 200:**
```json
{
  "message": "Password changed successfully"
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

**Error Response 400:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Old password and new password are required"
  },
  "correlation_id": "uuid"
}
```

**Error Response 400 (Invalid Old Password):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid old password"
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
- `ACCOUNT_DEACTIVATED` - User account is deactivated
- `VALIDATION_ERROR` - Request validation failed
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `SERVICE_UNAVAILABLE` - Downstream service error

---

## Rate Limits

- **Auth endpoints:** 5 requests per minute
- **Profile endpoints:** 100 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit-Minute`
- `X-RateLimit-Remaining-Minute`

---

## Token Management

### Access Token
- **Lifetime:** 60 minutes
- **Usage:** Use for all authenticated API calls
- **Storage:** Store in localStorage or secure cookie

### Refresh Token
- **Lifetime:** 7 days
- **Usage:** Exchange for new access token when expired
- **Storage:** Store in localStorage or secure cookie

### Token Refresh Flow
1. When access token expires (401 error)
2. Call `/auth/refresh` with refresh token
3. Store new access and refresh tokens
4. Retry original request with new access token

---

## User Fields

### Basic Fields
- `id` - UUID (read-only)
- `email` - Email address (unique, required)
- `name` - Display name (required)
- `role` - User role: 'user', 'premium_user', 'admin' (read-only)

### Profile Fields
- `full_name` - Full name (optional)
- `language` - Language preference: 'en' (English) or 'am' (Amharic)
- `phone` - Phone number (optional)
- `location` - Location (optional)
- `bio` - Bio/description (optional)

### Metadata Fields
- `created_at` - Account creation timestamp (read-only)
- `last_login` - Last login timestamp (read-only)
- `is_active` - Account status (read-only)

---

## Testing Guidance

### Registration Flow
1. Call `/auth/register` with user data
2. Store returned `access` and `refresh` tokens
3. Use access token for subsequent API calls

### Login Flow
1. Call `/auth/login` with credentials
2. Store returned `access` and `refresh` tokens
3. Use access token for subsequent API calls

### Profile Update Flow
1. Call `/auth/profile` or `/auth/profile/detail` to get current profile
2. Call `/auth/profile` or `/auth/profile/detail` with PUT to update
3. Only include fields you want to update (partial updates supported)

### Password Change Flow
1. Call `/auth/change-password` with old and new passwords
2. After successful change, user must login again with new password
3. Old tokens are invalidated

### Token Refresh Flow
1. When receiving 401 errors, call `/auth/refresh`
2. Use the stored refresh token
3. Update stored tokens with new ones
4. Retry the failed request

### Logout Flow
1. Call `/auth/logout` with refresh token
2. Clear stored tokens from client
3. Redirect to login page

---

## Notes

- All datetime fields are ISO 8601 in UTC
- Use the `correlation_id` from error responses when reporting issues
- Profile fields are optional and can be updated at any time
- Language preference affects UI language (English/Amharic)
- Password changes invalidate all existing tokens
- Rate limits are enforced per IP address
- Access tokens should be refreshed before expiration to avoid service interruption
