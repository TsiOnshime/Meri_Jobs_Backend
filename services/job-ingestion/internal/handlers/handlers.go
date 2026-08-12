package handlers

import (
	"context"
	"log"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"

	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/model"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/repository"
)

const (
	defaultLimit = 20
	maxLimit     = 200
)

type IngestionRunner interface {
	Run(ctx context.Context) (model.RefreshResult, error)
	ListJobs(ctx context.Context, params repository.ListParams) ([]model.Job, int, error)
}

type Handler struct {
	service IngestionRunner
}

func NewHandler(service IngestionRunner) *Handler {
	return &Handler{service: service}
}

func (h *Handler) RegisterRoutes(r *gin.Engine) {
	r.GET("/health", h.Health)
	r.POST("/internal/jobs/refresh", h.RefreshJobs)
	r.GET("/internal/jobs", h.ListJobs)
}

func (h *Handler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func (h *Handler) RefreshJobs(c *gin.Context) {
	result, err := h.service.Run(c.Request.Context())
	if err != nil {
		log.Printf("handlers: manual refresh failed: %v", err)
		c.JSON(http.StatusBadGateway, gin.H{
			"error": "ingestion run failed, see server logs for details",
		})
		return
	}
	c.JSON(http.StatusOK, result)
}


func (h *Handler) ListJobs(c *gin.Context) {
	limit := parseIntDefault(c.Query("limit"), defaultLimit)
	if limit <= 0 {
		limit = defaultLimit
	}
	if limit > maxLimit {
		limit = maxLimit
	}

	offset := parseIntDefault(c.Query("offset"), 0)
	if offset < 0 {
		offset = 0
	}

	source := c.Query("source")

	jobs, total, err := h.service.ListJobs(c.Request.Context(), repository.ListParams{
		Limit:  limit,
		Offset: offset,
		Source: source,
	})
	if err != nil {
		log.Printf("handlers: listing jobs failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to list jobs, see server logs for details",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"total":  total,
		"limit":  limit,
		"offset": offset,
		"jobs":   jobs,
	})
}

func parseIntDefault(s string, fallback int) int {
	if s == "" {
		return fallback
	}
	v, err := strconv.Atoi(s)
	if err != nil {
		return fallback
	}
	return v
}
