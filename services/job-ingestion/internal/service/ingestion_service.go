package service

import (
	"context"
	"errors"
	"log"

	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/jobsapi"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/model"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/repository"
)

type JobRepository interface {
	Exists(ctx context.Context, source, externalJobID string) (bool, error)
	Insert(ctx context.Context, job model.Job) (model.Job, error)
	List(ctx context.Context, params repository.ListParams) ([]model.Job, int, error)
}

type EventPublisher interface {
	PublishJobIngested(ctx context.Context, job model.Job) error
}

type IngestionService struct {
	provider  jobsapi.JobProvider
	repo      JobRepository
	publisher EventPublisher
}

func NewIngestionService(provider jobsapi.JobProvider, repo JobRepository, publisher EventPublisher) *IngestionService {
	return &IngestionService{
		provider:  provider,
		repo:      repo,
		publisher: publisher,
	}
}

func (s *IngestionService) Run(ctx context.Context) (model.RefreshResult, error) {
	log.Println("Starting ingestion...")

	jobs, err := s.provider.FetchJobs(ctx)
	if err != nil {
		log.Printf("ingestion: fetching from provider %q failed: %v", s.provider.Name(), err)
		return model.RefreshResult{}, err
	}

	result := model.RefreshResult{Fetched: len(jobs)}

	for _, job := range jobs {
		exists, err := s.repo.Exists(ctx, job.Source, job.ExternalJobID)
		if err != nil {
			log.Printf("ingestion: checking existence for job %q: %v", job.ExternalJobID, err)
			continue
		}
		if exists {
			result.Skipped++
			continue
		}

		inserted, err := s.repo.Insert(ctx, job)
		if err != nil {
			if errors.Is(err, repository.ErrDuplicateJob) {
			
				result.Skipped++
				continue
			}
			log.Printf("ingestion: inserting job %q: %v", job.ExternalJobID, err)
			continue
		}
		result.Inserted++

		if err := s.publisher.PublishJobIngested(ctx, inserted); err != nil {

			log.Printf("ingestion: publishing kafka event for job %q: %v", inserted.ExternalJobID, err)
			continue
		}
		result.Published++
	}

	log.Printf(
		"Fetched %d jobs\nInserted %d new jobs\nSkipped %d existing jobs\nPublished %d Kafka events",
		result.Fetched, result.Inserted, result.Skipped, result.Published,
	)

	return result, nil
}

func (s *IngestionService) ListJobs(ctx context.Context, params repository.ListParams) ([]model.Job, int, error) {
	return s.repo.List(ctx, params)
}
