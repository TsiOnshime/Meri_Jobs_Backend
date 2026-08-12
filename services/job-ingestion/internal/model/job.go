package model

import "time"

type Job struct {
	ID            string     `json:"id"`
	ExternalJobID string     `json:"externalJobId"`
	Title         string     `json:"title"`
	Company       string     `json:"company"`
	Location      string     `json:"location"`
	Description   string     `json:"description"`
	JobURL        string     `json:"jobUrl"`
	Source        string     `json:"source"`
	PublishedAt   *time.Time `json:"publishedAt,omitempty"`
	CreatedAt     time.Time  `json:"createdAt"`
	RequiredSkills []string `json:"requiredSkills"`
	MinExperience  int      `json:"minExperience"`
	SeniorityLevel string   `json:"seniorityLevel"`
	RoleCategory   string   `json:"roleCategory"`
}

type RefreshResult struct {
	Fetched   int `json:"fetched"`
	Inserted  int `json:"inserted"`
	Skipped   int `json:"skipped"`
	Published int `json:"published"`
}
