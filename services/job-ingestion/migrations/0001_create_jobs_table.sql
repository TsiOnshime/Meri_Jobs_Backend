-- Migration: create the job_ingestion schema and its jobs table.
--
-- This service runs against the same Postgres instance as the other
-- Meri Jobs services (a shared container for local dev / a shared
-- managed instance in prod), but owns its own schema. Other services
-- do not write to job_ingestion.jobs; they learn about new/changed
-- jobs via the job.ingested Kafka event and, if they need full job
-- details, read (never write) from this schema directly.
--
-- gen_random_uuid() is built into PostgreSQL core as of v13, no
-- extension required.

CREATE SCHEMA IF NOT EXISTS job_ingestion;

CREATE TABLE IF NOT EXISTS job_ingestion.jobs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_job_id  TEXT NOT NULL,
    title            TEXT NOT NULL,
    company          TEXT NOT NULL DEFAULT '',
    location         TEXT NOT NULL DEFAULT '',
    description      TEXT NOT NULL DEFAULT '',
    job_url          TEXT NOT NULL,
    source           TEXT NOT NULL,
    published_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Enrichment fields required by the job.ingested event schema.
    -- Derived heuristically at ingest time -- see internal/enrichment.
    required_skills  TEXT[] NOT NULL DEFAULT '{}',
    min_experience   INTEGER NOT NULL DEFAULT 0,
    seniority_level  TEXT NOT NULL DEFAULT 'mid',
    role_category    TEXT NOT NULL DEFAULT 'other',

    CONSTRAINT jobs_source_external_id_unique UNIQUE (source, external_job_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_source ON job_ingestion.jobs (source);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON job_ingestion.jobs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_role_category ON job_ingestion.jobs (role_category);
