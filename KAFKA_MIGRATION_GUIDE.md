# Kafka & Migration Guide

This guide covers Kafka setup, database migrations, and API documentation for CV Parser and Matching Engine services.

## Table of Contents
- [Kafka Setup](#kafka-setup)
- [Database Migrations](#database-migrations)
- [CV Parser API](#cv-parser-api)
- [Matching Engine API](#matching-engine-api)
- [Troubleshooting](#troubleshooting)

---

## Kafka Setup

### Required Topics

The system uses Kafka for event-driven communication between services. The following topics must be created:

| Topic | Purpose | Producer | Consumer |
|-------|---------|----------|----------|
| `cv.parsed` | CV parsing completed event | CV Parser | Matching Engine |
| `job.ingested` | Job ingestion completed event | Job Ingestion | Matching Engine |

### Creating Topics

```bash
# Create cv.parsed topic
docker compose exec kafka kafka-topics --create --topic cv.parsed --bootstrap-server localhost:9092 --partitions 1 --if-not-exists

# Create job.ingested topic
docker compose exec kafka kafka-topics --create --topic job.ingested --bootstrap-server localhost:9092 --partitions 1 --if-not-exists
```

### Listing Topics

```bash
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

Expected output:
```
__consumer_offsets
cv.parsed
job.ingested
```

### Kafka Configuration

Environment variable in `.env`:
```
KAFKA_BROKER_URL=kafka:9092
```

### Event Schemas

#### cv.parsed Event
```json
{
  "event": "cv.parsed",
  "cv_id": "uuid",
  "raw_skills": ["python", "django", "postgresql"],
  "experience_years": 3,
  "seniority": "mid",
  "role_category": "backend",
  "timestamp": "2026-08-01T12:00:00Z"
}
```

#### job.ingested Event
```json
{
  "event": "job.ingested",
  "job_id": "uuid",
  "title": "Backend Developer",
  "skills": ["python", "django"],
  "min_experience": 2,
  "seniority_level": "mid",
  "role_category": "backend",
  "location": "remote",
  "source_url": "https://example.com/job/123"
}
```

---

## Database Migrations

### Running Migrations

#### CV Parser Service
```bash
docker compose exec cv-parser python manage.py migrate
```

#### Matching Engine Service
```bash
docker compose exec matching-engine python manage.py migrate
```

#### Users Service
```bash
docker compose exec users python manage.py migrate
```

#### Interview Prep Service
```bash
docker compose exec interview-prep python manage.py migrate
```

### Checking Migration Status

```bash
# CV Parser
docker compose exec cv-parser python manage.py showmigrations

# Matching Engine
docker compose exec matching-engine python manage.py showmigrations
```

### Common Migration Issues

#### Issue: "no such table" Error
**Cause:** Database was reset or service was rebuilt without running migrations.

**Solution:**
```bash
docker compose exec <service-name> python manage.py migrate
```

#### Issue: Migration Already Applied
**Cause:** Migration was already run.

**Solution:** This is normal. Use `showmigrations` to verify status.

### Rebuilding Services

When a service is rebuilt, the database may be reset. Always run migrations after rebuilding:

```bash
# Rebuild service
docker compose up -d --build <service-name>

# Run migrations
docker compose exec <service-name> python manage.py migrate
```

---

## CV Parser API

### Base URL
```
http://localhost:8080/api/v1
```

### Endpoints

#### 1. Upload CV
**Endpoint:** `POST /cv/upload`

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

**Request Body (multipart/form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | PDF or DOCX file |
| user_id | UUID | Yes | User ID from JWT token |

**Example using curl:**
```bash
curl -X POST http://localhost:8080/api/v1/cv/upload \
  -H "Authorization: Bearer <jwt_token>" \
  -F "file=@cv.pdf" \
  -F "user_id=ea2e18dd-6fac-463e-8827-b5c663f8bb56"
```

**Success Response (200 OK):**
```json
{
  "cv_id": "d6e6df21-f911-4796-80f2-af3f15a2ecb4",
  "status": "pending"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid file format"
  }
}
```

---

#### 2. Get CV Status
**Endpoint:** `GET /cv/{cv_id}/status`

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Success Response (200 OK):**
```json
{
  "cv_id": "d6e6df21-f911-4796-80f2-af3f15a2ecb4",
  "status": "needs_review",
  "uploaded_at": "2026-08-01T17:43:38.160806Z",
  "updated_at": "2026-08-01T17:43:38.596718Z",
  "score": {
    "overall": 15,
    "completeness": 0,
    "keyword_relevance": 0,
    "clarity": 50
  },
  "parsed": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "professional_summary": "Experienced developer...",
    "education": [
      {
        "degree": "BSc Computer Science",
        "institution": "University",
        "year": "2020"
      }
    ],
    "experience": [
      {
        "title": "Senior Developer",
        "company": "Tech Corp",
        "years": "3"
      }
    ],
    "skills": ["python", "django", "postgresql"],
    "certifications": ["AWS Certified"],
    "confidence_score": 0.85
  },
  "suggestions": [
    {
      "suggestion_id": "uuid",
      "type": "add_skill",
      "field_reference": "skills",
      "suggestion": "Consider adding 'docker' to your skills"
    }
  ],
  "flagged_sections": ["name", "email", "experience", "skills"]
}
```

**Error Response (404 Not Found):**
```json
{
  "error": {
    "code": "CV_NOT_FOUND",
    "message": "CV not found"
  }
}
```

---

#### 3. Update CV
**Endpoint:** `PATCH /cv/{cv_id}`

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "professional_summary": "Updated summary",
  "education": [...],
  "experience": [...],
  "skills": ["python", "django", "postgresql"],
  "certifications": [...]
}
```

**Success Response (200 OK):**
```json
{
  "cv_id": "d6e6df21-f911-4796-80f2-af3f15a2ecb4",
  "status": "processed"
}
```

---

#### 4. Export CV
**Endpoint:** `GET /cv/{cv_id}/export?format={format}`

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| format | string | `json`, `pdf` | Export format |

**JSON Format Response (200 OK):**
```json
{
  "cv_id": "d6e6df21-f911-4796-80f2-af3f15a2ecb4",
  "status": "needs_review",
  "parsed": {
    "name": "John Doe",
    "email": "john@example.com",
    "skills": ["python", "django"]
  },
  "score": {
    "overall": 15
  }
}
```

**PDF Format Response (200 OK):**
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="{cv_id}-optimized.pdf"`
- Binary PDF data

**Error Response (409 Conflict):**
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "CV is still being processed -- nothing to export yet"
  }
}
```

---

#### 5. Accept Suggestions
**Endpoint:** `POST /cv/{cv_id}/suggestions/accept`

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "suggestion_ids": ["uuid1", "uuid2"]
}
```

**Success Response (200 OK):**
```json
{
  "cv_id": "d6e6df21-f911-4796-80f2-af3f15a2ecb4",
  "accepted_count": 2
}
```

---

## Matching Engine API

### Base URL
```
http://localhost:8080/api/v1
```

### Endpoints

#### 1. Get Matches for CV
**Endpoint:** `GET /matches/{cv_id}`

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| min_score | float | 0 | Minimum overall score |
| limit | int | 20 | Number of results |
| offset | int | 0 | Pagination offset |
| sort | string | `score` | Sort by `score` or `recent` |

**Success Response (200 OK):**
```json
{
  "cv_id": "7a8c3b1d-12cf-4d6e-a46a-359cff39384f",
  "count": 1,
  "results": [
    {
      "job_id": "7a20d4aa-76f6-4256-8c3f-9da3b3645300",
      "overall_score": 85,
      "source_url": "http://example.com/job1",
      "computed_at": "2026-08-01"
    }
  ]
}
```

**Error Response (404 Not Found):**
```json
{
  "error": {
    "code": "cv_not_found",
    "message": "No CV record found for {cv_id}"
  }
}
```

---

#### 2. Get Match Detail
**Endpoint:** `GET /matches/{cv_id}/{job_id}`

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Success Response (200 OK):**
```json
{
  "cv_id": "7a8c3b1d-12cf-4d6e-a46a-359cff39384f",
  "job_id": "7a20d4aa-76f6-4256-8c3f-9da3b3645300",
  "overall_score": 85,
  "source_url": "http://example.com/job1",
  "breakdown": {
    "skills": 90,
    "experience": 80,
    "location": 85
  },
  "computed_at": "2026-08-01"
}
```

**Error Response (404 Not Found):**
```json
{
  "error": {
    "code": "match_not_found",
    "message": "No match found for {cv_id}"
  }
}
```

---

## Troubleshooting

### Kafka Issues

#### Worker Cannot Connect to Topics
**Error:** `KafkaError{code=UNKNOWN_TOPIC_OR_PARTITION}`

**Solution:**
1. Check if topics exist:
   ```bash
   docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
   ```
2. Create missing topics:
   ```bash
   docker compose exec kafka kafka-topics --create --topic cv.parsed --bootstrap-server localhost:9092 --partitions 1 --if-not-exists
   docker compose exec kafka kafka-topics --create --topic job.ingested --bootstrap-server localhost:9092 --partitions 1 --if-not-exists
   ```
3. Restart the worker:
   ```bash
   docker compose restart matching-engine-worker
   ```

#### Worker Not Processing Events
**Check worker logs:**
```bash
docker compose logs matching-engine-worker --tail 50
```

**Restart worker:**
```bash
docker compose restart matching-engine-worker
```

---

### Database Migration Issues

#### "no such table" Error
**Cause:** Database was reset or service was rebuilt.

**Solution:**
```bash
docker compose exec <service-name> python manage.py migrate
```

#### Migration Already Applied
**Cause:** Migration was already run.

**Solution:** This is normal. Verify with:
```bash
docker compose exec <service-name> python manage.py showmigrations
```

---

### CV Parser Issues

#### Empty Parsed Data
**Cause:** PDF extraction failed or file format not supported.

**Solution:**
1. Check CV status:
   ```bash
   GET /api/v1/cv/{cv_id}/status
   ```
2. If `status` is `needs_review` and `parsed` is empty, the PDF could not be parsed.
3. Try uploading a different PDF format or DOCX file.

#### CV Export Fails
**Cause:** CV not fully processed or no parsed data.

**Solution:**
1. Check CV status first
2. Ensure `status` is `processed` or `needs_review`
3. Ensure `parsed` data is not empty

---

### Matching Engine Issues

#### No CV in Matching Engine
**Cause:** Kafka event flow not working or CV not published.

**Solution:**
1. Check Kafka topics exist
2. Check matching engine worker is running:
   ```bash
   docker compose ps matching-engine-worker
   ```
3. Check worker logs for errors
4. Verify CV parser is publishing events

#### Worker Missing Dependencies
**Error:** `ModuleNotFoundError: No module named 'django'`

**Solution:**
```bash
docker compose up -d --build matching-engine-worker
```

---

### Service Not Responding

#### Check Service Status
```bash
docker compose ps
```

#### Check Service Logs
```bash
docker compose logs <service-name> --tail 50
```

#### Restart Service
```bash
docker compose restart <service-name>
```

#### Rebuild Service
```bash
docker compose up -d --build <service-name>
```

---

## Development Workflow

### Initial Setup

1. **Start all services:**
   ```bash
   docker compose up -d
   ```

2. **Wait for services to be healthy:**
   ```bash
   docker compose ps
   ```

3. **Create Kafka topics:**
   ```bash
   docker compose exec kafka kafka-topics --create --topic cv.parsed --bootstrap-server localhost:9092 --partitions 1 --if-not-exists
   docker compose exec kafka kafka-topics --create --topic job.ingested --bootstrap-server localhost:9092 --partitions 1 --if-not-exists
   ```

4. **Run migrations:**
   ```bash
   docker compose exec cv-parser python manage.py migrate
   docker compose exec matching-engine python manage.py migrate
   docker compose exec users python manage.py migrate
   docker compose exec interview-prep python manage.py migrate
   ```

5. **Restart workers:**
   ```bash
   docker compose restart matching-engine-worker
   ```

### After Rebuilding Services

1. **Rebuild specific service:**
   ```bash
   docker compose up -d --build <service-name>
   ```

2. **Run migrations for that service:**
   ```bash
   docker compose exec <service-name> python manage.py migrate
   ```

3. **Restart workers if needed:**
   ```bash
   docker compose restart matching-engine-worker
   ```

---

## Testing

### Test CV Upload Flow

1. **Register user:**
   ```bash
   POST /api/v1/auth/register
   {
     "email": "test@example.com",
     "password": "Test1234",
     "name": "Test User"
   }
   ```

2. **Login to get JWT:**
   ```bash
   POST /api/v1/auth/login
   {
     "email": "test@example.com",
     "password": "Test1234"
   }
   ```

3. **Upload CV:**
   ```bash
   POST /api/v1/cv/upload
   Headers: Authorization: Bearer <jwt_token>
   Body: multipart/form-data with file and user_id
   ```

4. **Check CV status:**
   ```bash
   GET /api/v1/cv/{cv_id}/status
   ```

5. **Export CV:**
   ```bash
   GET /api/v1/cv/{cv_id}/export?format=json
   ```

### Test Matching Engine Flow

1. **Create test data in matching engine:**
   ```bash
   docker compose exec matching-engine python manage.py shell -c "from matching.models import CV, Skill, Job, Match; from uuid import uuid4; from datetime import datetime; s1 = Skill.objects.create(name='python'); s2 = Skill.objects.create(name='django'); cv = CV.objects.create(cv_id=uuid4(), skill_ids=[s1.id, s2.id], experience_years=3, seniority='mid', role_category='backend'); job = Job.objects.create(job_id=uuid4(), skill_ids=[s1.id, s2.id], min_experience=2, seniority_level='mid', role_category='backend', location='remote', source_url='http://example.com/job1', ingested_at=datetime.now()); match = Match.objects.create(cv=cv, job=job, overall_score=85, breakdown={'skills': 90, 'experience': 80}); print('Test data created')"
   ```

2. **Get CV ID:**
   ```bash
   docker compose exec matching-engine python manage.py shell -c "from matching.models import CV; cv = CV.objects.first(); print(f'CV ID: {cv.cv_id}')"
   ```

3. **Get matches:**
   ```bash
   GET /api/v1/matches/{cv_id}
   ```

---

## Environment Variables

### Required in `.env`

```bash
# Postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=merijobs
POSTGRES_USER=merijobs
POSTGRES_PASSWORD=changeme

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Kafka
KAFKA_BROKER_URL=kafka:9092

# Auth
JWT_SECRET_KEY=changeme-generate-a-real-secret
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60

# Internal Service URLs
CV_PARSER_URL=http://cv-parser:8001
MATCHING_ENGINE_URL=http://matching-engine:8002
JOB_INGESTION_URL=http://job-ingestion:8003
INTERVIEW_PREP_URL=http://interview-prep:8004
USERS_URL=http://users:8005

# Internal Token
INTERNAL_TOKEN=changeme-generate-a-real-internal-token

# Django
DJANGO_SECRET_KEY=changeme-generate-a-real-secret
DJANGO_DEBUG=True
```

---

## Service Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| API Gateway | 8080 | 8080 |
| CV Parser | 8001 | - |
| Matching Engine | 8002 | - |
| Job Ingestion | 8003 | 8003 |
| Interview Prep | 8004 | 8004 |
| Users | 8005 | - |
| Kafka | 9092 | - |
| Zookeeper | 2181 | - |
| Postgres | 5432 | - |
| Redis | 6379 | - |

