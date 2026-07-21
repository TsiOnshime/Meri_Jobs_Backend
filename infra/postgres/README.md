# Postgres

Local dev uses a single Postgres instance (via `docker-compose.yml`) shared
across all 5 services, using one database with clearly-prefixed tables per
service (a reasonable shortcut at this project's scale — see
`docs/architecture.md` for the reasoning).

Drop any `.sql` init scripts in this folder — Postgres runs everything in
`docker-entrypoint-initdb.d` automatically on first container start.
