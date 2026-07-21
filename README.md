# Meri Jobs — Backend

Event-driven microservices backend for Meri Jobs: an AI-powered career assistant
(CV optimization, job matching, and interview prep) for African/Ethiopian
professionals.

## Services

| Service | Owns | Port (local) |
|---|---|---|
| `api-gateway` | Auth, routing, request validation | 8000 |
| `cv-parser` | CV upload, extraction, optimization suggestions | 8001 |
| `matching-engine` | Skill resolution, scoring, matches | 8002 |
| `job-ingestion` | External job fetching, dedup | 8003 |
| `interview-prep` | Mock interview Q&A, feedback | 8004 |

All services communicate **only** through Kafka events defined in
`shared/events/` — never by importing each other's code or calling each
other directly (except `api-gateway`, which calls the others' REST APIs
on the frontend's behalf).

## Quick start

```bash
cp .env.example .env          # fill in real values
docker-compose up --build     # starts kafka, redis, postgres, and all 5 services
```

Each service can also be run standalone for local development — see
that service's own folder.

## Where to look first

- **`docs/architecture.md`** — system diagrams and design decisions
- **`shared/events/README.md`** — every event's payload, publisher, and consumers
- **`CONTRIBUTING.md`** — branching and PR rules before your first commit

## Repo layout

```
meri-jobs-backend/
├── docker-compose.yml
├── shared/events/        # event contracts — the thing every service agrees on
├── infra/                # kafka + postgres config for local dev
├── services/             # one folder per microservice, independently runnable
└── docs/                 # architecture diagrams and notes
```
