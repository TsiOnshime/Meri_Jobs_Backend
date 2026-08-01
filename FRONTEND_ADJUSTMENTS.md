# Frontend Adjustments for Backend API Changes

## Backend Updates Completed

### User Model Changes
Added new fields to support onboarding:
- `full_name` (string, optional)
- `language` (enum: 'en' | 'am', default: 'en')
- `phone` (string, optional)
- `location` (string, optional)
- `bio` (text, optional)

### API Gateway Profile Endpoints
Updated profile endpoints to use `/auth/` prefix:
- `GET/PUT /api/v1/auth/profile` - Basic profile
- `GET/PUT /api/v1/auth/profile/detail` - Detailed profile

---

## Required Frontend Changes

### 1. Update API Endpoints

**❌ WRONG - You are currently using:**
```typescript
'/api/auth/signup'  // Wrong endpoint
'/api/auth/login'   // Wrong endpoint
```

**✅ CORRECT - Use these instead:**
```typescript
'/api/v1/auth/register'  // Correct endpoint
'/api/v1/auth/login'     // Correct endpoint
'/api/v1/auth/refresh'   // Add this for token refresh
'/api/v1/auth/logout'    // Add this for logout
'/api/v1/auth/me'        // Add this for current user
```

**Profile Endpoints:**
```typescript
// ❌ WRONG: No profile endpoints currently
// ✅ CORRECT: Use these for profile management
'/api/v1/auth/profile'         // Basic profile updates
'/api/v1/auth/profile/detail'  // Detailed profile (onboarding data)
```

### 2. Update Response Handling

**❌ WRONG - You are currently expecting:**
```typescript
{
  user: { id, email, fullName, language },
  token: "single_token"
}
```

**✅ CORRECT - Backend actually returns:**
```typescript
{
  user: { id, email, name, full_name, language, phone, location, bio, role, created_at, last_login },
  access: "jwt_access_token",
  refresh: "jwt_refresh_token"
}
```

**Required Changes:**
- Handle `access` and `refresh` tokens separately (not single `token`)
- Store both tokens (access for API calls, refresh for renewal)
- Update user field names: `fullName` → `full_name`
- Add new user fields to types

### 3. Update Types

**❌ WRONG - You are currently using:**
```typescript
export interface User {
  id: string;
  email: string;
  fullName: string;  // Wrong field name
  language: 'en' | 'am';
}

export interface AuthResponse {
  user: User;
  token: string;  // Wrong - should be access/refresh
}

export interface SignupPayload {
  fullName: string;  // Wrong field name
  email: string;
  password: string;
  language: 'en' | 'am';
}
```

**✅ CORRECT - Use these instead:**
```typescript
export interface User {
  id: string;
  email: string;
  name: string;
  full_name: string;        // Correct field name
  language: 'en' | 'am';
  phone?: string;            // Add this
  location?: string;         // Add this
  bio?: string;              // Add this
  role: 'user' | 'premium_user' | 'admin';
  created_at: string;
  last_login?: string;
}

export interface AuthResponse {
  user: User;
  access: string;            // Correct field name
  refresh: string;          // Add this
}

export interface SignupPayload {
  name: string;             // Correct field name
  email: string;
  password: string;
  language?: 'en' | 'am';
}
```

### 4. Update Auth API Functions

**❌ WRONG - You are currently using:**
```typescript
export async function signupUser(payload: SignupPayload): Promise<AuthResponse> {
  const res = await fetch('/api/auth/signup', {  // Wrong endpoint
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  // ... expects single token
}

export async function loginUser(payload: LoginPayload): Promise<AuthResponse> {
  const res = await fetch('/api/auth/login', {  // Wrong endpoint
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  // ... expects single token
}
```

**✅ CORRECT - Use these instead:**
```typescript
export async function signupUser(payload: SignupPayload): Promise<AuthResponse> {
  const res = await fetch('/api/v1/auth/register', {  // Correct endpoint
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error('Failed to create account');
  }

  return res.json();  // Returns { user, access, refresh }
}

export async function loginUser(payload: LoginPayload): Promise<AuthResponse> {
  const res = await fetch('/api/v1/auth/login', {  // Correct endpoint
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error('Failed to login');
  }

  return res.json();  // Returns { user, access, refresh }
}

// ❌ WRONG: Missing this function
// ✅ CORRECT: Add this for token refresh
export async function refreshToken(refreshToken: string): Promise<{ access: string, refresh: string }> {
  const res = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken }),
  });

  if (!res.ok) {
    throw new Error('Failed to refresh token');
  }

  return res.json();
}
```

### 5. Update Token Storage

**❌ WRONG - You are currently using:**
```typescript
// Storing single token
localStorage.setItem('token', response.token);

// Using single token for API calls
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json'
};
```

**✅ CORRECT - Use this instead:**
```typescript
// Store both tokens separately
localStorage.setItem('access_token', response.access);
localStorage.setItem('refresh_token', response.refresh);

// Use access token for API calls
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json'
};

// Use refresh token to get new access token when expired
const newTokens = await refreshToken(localStorage.getItem('refresh_token'));
localStorage.setItem('access_token', newTokens.access);
localStorage.setItem('refresh_token', newTokens.refresh);
```

### 6. Update Onboarding Flow

**❌ WRONG - You are currently using:**
```typescript
// No profile endpoints - onboarding data not being saved
// No way to update user profile after registration
```

**✅ CORRECT - Use this instead:**
```typescript
// Update profile during onboarding
export async function updateProfile(profileData: Partial<User>): Promise<{ user: User }> {
  const res = await fetch('/api/v1/auth/profile/detail', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(profileData),
  });

  if (!res.ok) {
    throw new Error('Failed to update profile');
  }

  return res.json();
}

// Example usage during onboarding
await updateProfile({
  full_name: "John Doe",
  phone: "+1234567890",
  location: "Addis Ababa",
  bio: "Software developer looking for opportunities"
});
```

---

## Migration Steps

1. **Update types** - Add new user fields and change response structure
2. **Update API calls** - Change endpoints to `/api/v1/` prefix
3. **Update token handling** - Store and use access/refresh tokens separately
4. **Update onboarding** - Use profile endpoints for additional user data
5. **Test auth flow** - Register → Login → Token refresh → Profile update

---

## Notes

- Backend now supports English ('en') and Amharic ('am') languages
- Profile fields are optional - can be updated during onboarding
- Access tokens expire in 60 minutes - use refresh token to renew
- All authenticated endpoints require `Authorization: Bearer <access_token>` header
