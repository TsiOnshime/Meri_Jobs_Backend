# Event Catalog

Every event this system uses, in one place. If you're not sure what an event
contains or who reacts to it, check here before writing code.

**Rule:** if you need to change a schema file in this folder, get a review
from whoever owns a service that consumes that event — see `CONTRIBUTING.md`.

---

## `cv.parsed`
**Schema:** `cv_parsed.schema.json`
**Publisher:** `cv-parser`
**Consumers:** `matching-engine`

Fired once a CV upload has been extracted into structured fields. Carries
**raw** skill strings — resolution to canonical skill IDs happens inside
`matching-engine`, not here.

---

## `job.ingested`
**Schema:** `job_ingested.schema.json`
**Publisher:** `job-ingestion`
**Consumers:** `matching-engine`

Fired when a new or updated job listing is fetched from an external source
(Indeed, RemoteOK, Upwork). Also carries raw skill strings, same reasoning
as above. `source_url` must be a direct, stable link — it's what the
frontend's Apply button uses.

---

## `match.found`
**Schema:** `match_found.schema.json`
**Publisher:** `matching-engine`
**Consumers:** `interview-prep` (pre-generates mock questions), and
potentially a future notifications piece.

Fired once per CV/job pair that passes the gate and gets scored. This is a
"fat" event — it carries the full explainable breakdown, not just a
reference, so consumers don't need to call back into `matching-engine` for
the details.

Only fires for pairs that pass the gate. There is no "match rejected" event
— absence of a `match.found` event (or deletion of the underlying row) is
the rejection/invalidation signal for now.

---

## Adding a new event

1. Add the schema file here, following the same shape as the existing ones.
2. Add a section to this README.
3. Open a PR, tag the intended consumer's owner for review.
4. Only then start relying on it in service code.
