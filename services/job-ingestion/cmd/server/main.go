package main

import (
	"context"
	"errors"
	"log"
	"net/http"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"

	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/config"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/database"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/handlers"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/jobsapi"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/kafka"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/repository"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/scheduler"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/service"
)

func main() {
	if err := run(); err != nil {
		log.Fatalf("fatal: %v", err)
	}
}

func run() error {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	cfg, err := config.Load()
	if err != nil {
		return err
	}
	log.Printf("Loaded config: port=%s interval=%dh kafkaTopic=%s provider=%s",
		cfg.HTTPPort, cfg.IngestionIntervalHours, cfg.KafkaTopic, cfg.JobProviderName)

	pool, err := database.Connect(ctx, cfg.DatabaseURL)
	if err != nil {
		return err
	}
	defer pool.Close()
	log.Println("Connected to PostgreSQL")

	if err := database.Migrate(ctx, pool, "migrations"); err != nil {
		return err
	}
	log.Println("Migrations applied")

	repo := repository.NewJobRepository(pool)

	producer := kafka.NewProducer(cfg.KafkaBrokers, cfg.KafkaTopic)
	defer func() {
		if err := producer.Close(); err != nil {
			log.Printf("error closing kafka producer: %v", err)
		}
	}()

	provider := jobsapi.NewRemoteOKProvider(cfg.JobAPIURL, cfg.RemoteOKAPIKey)

	ingestionSvc := service.NewIngestionService(provider, repo, producer)

	gin.SetMode(gin.ReleaseMode)
	router := gin.New()
	router.Use(gin.Recovery(), requestLogger())

	h := handlers.NewHandler(ingestionSvc)
	h.RegisterRoutes(router)

	httpServer := &http.Server{
		Addr:    ":" + cfg.HTTPPort,
		Handler: router,
	}

	serverErrCh := make(chan error, 1)
	go func() {
		log.Printf("HTTP server listening on :%s", cfg.HTTPPort)
		if err := httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			serverErrCh <- err
			return
		}
		serverErrCh <- nil
	}()

	
	interval := time.Duration(cfg.IngestionIntervalHours) * time.Hour
	sched := scheduler.NewScheduler(interval, func(ctx context.Context) error {
		_, err := ingestionSvc.Run(ctx)
		return err
	})

	schedulerDone := make(chan struct{})
	go func() {
		defer close(schedulerDone)
		sched.Start(ctx)
	}()

	select {
	case <-ctx.Done():
		log.Println("Shutdown signal received, shutting down gracefully...")
	case err := <-serverErrCh:
		if err != nil {
			log.Printf("HTTP server error: %v", err)
		}
		stop()
	}


	shutdownCtx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	if err := httpServer.Shutdown(shutdownCtx); err != nil {
		log.Printf("error shutting down HTTP server: %v", err)
	}

	<-schedulerDone
	log.Println("Shutdown complete")

	return nil
}


func requestLogger() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		c.Next()
		log.Printf("%s %s -> %d (%s)", c.Request.Method, c.Request.URL.Path, c.Writer.Status(), time.Since(start))
	}
}
