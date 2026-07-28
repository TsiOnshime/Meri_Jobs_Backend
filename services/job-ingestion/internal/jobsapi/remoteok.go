package jobsapi

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"time"

	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/enrichment"
	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/model"
)

const providerNameRemoteOK = "remoteok"

type RemoteOKProvider struct {
	apiURL string
	apiKey string 
	client *http.Client
}


func NewRemoteOKProvider(apiURL, apiKey string) *RemoteOKProvider {
	return &RemoteOKProvider{
		apiURL: apiURL,
		apiKey: apiKey,
		client: &http.Client{
			Timeout: 15 * time.Second,
		},
	}
}

func (p *RemoteOKProvider) Name() string {
	return providerNameRemoteOK
}

type remoteOKJob struct {
	ID       json.Number `json:"id"`
	Slug     string      `json:"slug"`
	Company  string      `json:"company"`
	Position string      `json:"position"`
	Location string      `json:"location"`
	Description string   `json:"description"`
	URL         string   `json:"url"`
	ApplyURL    string   `json:"apply_url"`
	Date        string   `json:"date"`
	Tags        []string `json:"tags"`
}

func (p *RemoteOKProvider) FetchJobs(ctx context.Context) ([]model.Job, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, p.apiURL, nil)
	if err != nil {
		return nil, fmt.Errorf("remoteok: building request: %w", err)
	}
	req.Header.Set("User-Agent", "job-ingestion-service/1.0 (+https://github.com/jobgen)")
	req.Header.Set("Accept", "application/json")
	if p.apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+p.apiKey)
	}

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("remoteok: request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 512))
		return nil, fmt.Errorf("remoteok: unexpected status %d: %s", resp.StatusCode, string(body))
	}

	var raw []remoteOKJob
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return nil, fmt.Errorf("remoteok: decoding response: %w", err)
	}

	jobs := make([]model.Job, 0, len(raw))
	for _, r := range raw {

		idStr := r.ID.String()
		if idStr == "" || idStr == "0" {
			continue
		}
		if r.Position == "" {
			continue
		}

		jobURL := r.URL
		if jobURL == "" {
			jobURL = r.ApplyURL
		}
		if jobURL == "" {
		
			continue
		}

		var publishedAt *time.Time
		if r.Date != "" {
			if t, err := time.Parse(time.RFC3339, r.Date); err == nil {
				publishedAt = &t
			}
		}

		externalID := idStr
		if externalID == "" {
			externalID = r.Slug
		}
		if externalID == "" {
			externalID = jobURL
		}

		enriched := enrichment.Derive(r.Position, r.Tags)

		jobs = append(jobs, model.Job{
			ExternalJobID:  externalID,
			Title:          r.Position,
			Company:        r.Company,
			Location:       r.Location,
			Description:    r.Description,
			JobURL:         jobURL,
			Source:         providerNameRemoteOK,
			PublishedAt:    publishedAt,
			RequiredSkills: enriched.RequiredSkills,
			MinExperience:  enriched.MinExperience,
			SeniorityLevel: enriched.SeniorityLevel,
			RoleCategory:   enriched.RoleCategory,
		})
	}

	return jobs, nil
}

func parseNumericID(n json.Number) (int64, error) {
	return strconv.ParseInt(n.String(), 10, 64)
}
