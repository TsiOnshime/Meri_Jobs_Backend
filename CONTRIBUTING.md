# Contributing

## Branching

`service/<service-name>/<short-feature-description>`

Examples:
- `service/matching-engine/skill-normalization`
- `service/cv-parser/pdf-extraction`
- `service/api-gateway/jwt-auth`

If you're changing something in `shared/` rather than one service:
`shared/<short-description>` (e.g. `shared/add-match-invalidated-event`)

## Commits

Keep them scoped to one service where possible. Prefix with the service name
if it helps: `[matching-engine] add fuzzy matching fallback`.

## Pull requests

1. Open a PR into `main`. No direct pushes to `main`.
2. Keep PRs scoped to **one service**. If your change touches `shared/events/`,
   say so explicitly in the PR description and tag whoever consumes that event.
3. If you're changing an event schema in `shared/events/*.schema.json`:
   - Update `shared/events/README.md` to match.
   - Get a review from at least one person who owns a service that
     consumes (or will consume) that event.
4. At least one other teammate reviews before merging — doesn't need to be
   a deep review if it's routine, but someone else should look at it.

## Local setup

```bash
cp .env.example .env
docker-compose up --build
```

To work on a single service without running everything:
```bash
cd services/<your-service>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver <port>
```
(You'll still need Kafka/Redis/Postgres running via `docker-compose up kafka redis postgres`
if your service needs them.)

## Before you open a PR

- [ ] Does this change match the schema in `shared/events/`, if it touches events?
- [ ] Did you use `update_or_create` (not `create`) for anything that could be
      affected by Kafka redelivering an event?
- [ ] Does `docker-compose up --build` still work end to end?
