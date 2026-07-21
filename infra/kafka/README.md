# Kafka Topics

Local dev uses a single-broker Kafka via `docker-compose.yml` (auto-creates
topics on first publish, since `KAFKA_AUTO_CREATE_TOPICS_ENABLE` defaults to
true on the Confluent image).

## Topics in use

| Topic | Publisher | Consumers |
|---|---|---|
| `cv.parsed` | cv-parser | matching-engine |
| `job.ingested` | job-ingestion | matching-engine |
| `match.found` | matching-engine | interview-prep |

See `shared/events/README.md` for payload details.

## Consumer groups

Give each consuming service its own consumer group ID (e.g.
`matching-engine-group`) so Kafka tracks their offsets independently.
