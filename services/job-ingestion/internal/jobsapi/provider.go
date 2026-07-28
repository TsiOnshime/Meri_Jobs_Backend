package jobsapi

import (
	"context"

	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/model"
)

type JobProvider interface {
	FetchJobs(ctx context.Context) ([]model.Job, error)

	Name() string
}
