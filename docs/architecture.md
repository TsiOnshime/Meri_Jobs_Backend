# Meri Jobs — Backend Architecture

This is the living reference for how the system fits together. Fill in /
update this as the design evolves — treat it as the source of truth new
teammates read first.

## Style

Event-driven microservices. Services never call each other directly except
`api-gateway`, which calls the others' read-only REST APIs on the frontend's
behalf. All cross-service communication otherwise happens through Kafka
events defined in `shared/events/`.

## Services

- **api-gateway** — auth, routing, request validation
- **cv-parser** — CV upload, extraction, optimization suggestions
- **matching-engine** — skill resolution, gate evaluation, weighted scoring
- **job-ingestion** — external job fetching (Indeed/RemoteOK/Upwork), dedup
- **interview-prep** — mock interview Q&A and feedback

## Key design decisions (fill in / link diagrams here)

- [ ] High-level system diagram
- [ ] Event flow: job ingestion → matching → timeline read (sequence diagram)
- [ ] Matching-engine ER diagram
- [ ] Skill resolution pipeline (normalize → alias → fuzzy → embeddings)
- [ ] CV-edit reconciliation logic
- [ ] Why upsert, not insert (idempotency against Kafka's at-least-once delivery)

## Open questions / not yet decided

- Correlation ID format for tracing a request/event across services
- Job-ingestion refresh schedule (how often Celery Beat runs)
- Whether `match.invalidated` gets added as a real event later
