package scheduler

import (
	"context"
	"log"
	"time"
)

type runFunc func(ctx context.Context) error

type Scheduler struct {
	interval time.Duration
	run      runFunc
}

func NewScheduler(interval time.Duration, run runFunc) *Scheduler {
	return &Scheduler{interval: interval, run: run}
}

func (s *Scheduler) Start(ctx context.Context) {
	s.runSafely(ctx)

	ticker := time.NewTicker(s.interval)
	defer ticker.Stop()

	log.Printf("Next run in %s...", s.interval)

	for {
		select {
		case <-ctx.Done():
			log.Println("Scheduler stopping (context canceled)")
			return
		case <-ticker.C:
			s.runSafely(ctx)
			log.Printf("Next run in %s...", s.interval)
		}
	}
}

func (s *Scheduler) runSafely(ctx context.Context) {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("scheduler: recovered from panic during ingestion run: %v", r)
		}
	}()

	if err := s.run(ctx); err != nil {
		log.Printf("scheduler: ingestion run failed: %v", err)
	}
}
