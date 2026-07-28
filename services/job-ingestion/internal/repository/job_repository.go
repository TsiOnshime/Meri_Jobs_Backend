package repository

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/model"
)

type JobRepository struct {
	pool *pgxpool.Pool
}

func NewJobRepository(pool *pgxpool.Pool) *JobRepository {
	return &JobRepository{pool: pool}
}

func (r *JobRepository) Exists(ctx context.Context, source, externalJobID string) (bool, error) {
	const query = `SELECT EXISTS(SELECT 1 FROM job_ingestion.jobs WHERE source = $1 AND external_job_id = $2)`

	var exists bool
	if err := r.pool.QueryRow(ctx, query, source, externalJobID).Scan(&exists); err != nil {
		return false, fmt.Errorf("checking job existence: %w", err)
	}
	return exists, nil
}

func (r *JobRepository) Insert(ctx context.Context, job model.Job) (model.Job, error) {
	const query = `
		INSERT INTO job_ingestion.jobs (
			external_job_id, title, company, location, description, job_url, source, published_at,
			required_skills, min_experience, seniority_level, role_category
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
		ON CONFLICT (source, external_job_id) DO NOTHING
		RETURNING id, created_at`

	row := r.pool.QueryRow(ctx, query,
		job.ExternalJobID, job.Title, job.Company, job.Location,
		job.Description, job.JobURL, job.Source, job.PublishedAt,
		job.RequiredSkills, job.MinExperience, job.SeniorityLevel, job.RoleCategory,
	)

	if err := row.Scan(&job.ID, &job.CreatedAt); err != nil {
		if err == pgx.ErrNoRows {
		
			return model.Job{}, ErrDuplicateJob
		}
		return model.Job{}, fmt.Errorf("inserting job: %w", err)
	}

	return job, nil
}

type ListParams struct {
	Limit  int
	Offset int
	Source string
}

func (r *JobRepository) List(ctx context.Context, params ListParams) ([]model.Job, int, error) {
	var (
		rows       pgx.Rows
		err        error
		countQuery string
		listQuery  string
		args       []any
	)

	if params.Source != "" {
		countQuery = `SELECT COUNT(*) FROM job_ingestion.jobs WHERE source = $1`
		listQuery = `
			SELECT id, external_job_id, title, company, location, description, job_url, source,
			       published_at, created_at, required_skills, min_experience, seniority_level, role_category
			FROM job_ingestion.jobs
			WHERE source = $1
			ORDER BY created_at DESC
			LIMIT $2 OFFSET $3`
		args = []any{params.Source, params.Limit, params.Offset}
	} else {
		countQuery = `SELECT COUNT(*) FROM job_ingestion.jobs`
		listQuery = `
			SELECT id, external_job_id, title, company, location, description, job_url, source,
			       published_at, created_at, required_skills, min_experience, seniority_level, role_category
			FROM job_ingestion.jobs
			ORDER BY created_at DESC
			LIMIT $1 OFFSET $2`
		args = []any{params.Limit, params.Offset}
	}

	var total int
	if params.Source != "" {
		if err := r.pool.QueryRow(ctx, countQuery, params.Source).Scan(&total); err != nil {
			return nil, 0, fmt.Errorf("counting jobs: %w", err)
		}
	} else {
		if err := r.pool.QueryRow(ctx, countQuery).Scan(&total); err != nil {
			return nil, 0, fmt.Errorf("counting jobs: %w", err)
		}
	}

	rows, err = r.pool.Query(ctx, listQuery, args...)
	if err != nil {
		return nil, 0, fmt.Errorf("listing jobs: %w", err)
	}
	defer rows.Close()

	jobs := make([]model.Job, 0, params.Limit)
	for rows.Next() {
		var j model.Job
		if err := rows.Scan(
			&j.ID, &j.ExternalJobID, &j.Title, &j.Company, &j.Location,
			&j.Description, &j.JobURL, &j.Source, &j.PublishedAt, &j.CreatedAt,
			&j.RequiredSkills, &j.MinExperience, &j.SeniorityLevel, &j.RoleCategory,
		); err != nil {
			return nil, 0, fmt.Errorf("scanning job row: %w", err)
		}
		jobs = append(jobs, j)
	}
	if err := rows.Err(); err != nil {
		return nil, 0, fmt.Errorf("reading job rows: %w", err)
	}

	return jobs, total, nil
}

func (r *JobRepository) FindByID(ctx context.Context, id string) (model.Job, error) {
	const query = `
		SELECT id, external_job_id, title, company, location, description, job_url, source,
		       published_at, created_at, required_skills, min_experience, seniority_level, role_category
		FROM job_ingestion.jobs
		WHERE id = $1`

	var j model.Job
	err := r.pool.QueryRow(ctx, query, id).Scan(
		&j.ID, &j.ExternalJobID, &j.Title, &j.Company, &j.Location,
		&j.Description, &j.JobURL, &j.Source, &j.PublishedAt, &j.CreatedAt,
		&j.RequiredSkills, &j.MinExperience, &j.SeniorityLevel, &j.RoleCategory,
	)
	if err != nil {
		if err == pgx.ErrNoRows {
			return model.Job{}, ErrJobNotFound
		}
		return model.Job{}, fmt.Errorf("finding job by id: %w", err)
	}
	return j, nil
}
