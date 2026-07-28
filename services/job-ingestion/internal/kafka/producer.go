package kafka

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	kafkago "github.com/segmentio/kafka-go"

	"github.com/TsiOnshime/Meri_Jobs_Backend/services/job-ingestion/internal/model"
)

type Producer struct {
	writer *kafkago.Writer
}

func NewProducer(brokers []string, topic string) *Producer {
	return &Producer{
		writer: &kafkago.Writer{
			Addr:                   kafkago.TCP(brokers...),
			Topic:                  topic,
			Balancer:               &kafkago.LeastBytes{},
			AllowAutoTopicCreation: true,
			WriteTimeout:           10 * time.Second,
			RequiredAcks:           kafkago.RequireOne,
		},
	}
}

type jobIngestedEvent struct {
	Event          string   `json:"event"`
	JobID          string   `json:"job_id"`
	RequiredSkills []string `json:"required_skills"`
	MinExperience  int      `json:"min_experience"`
	SeniorityLevel string   `json:"seniority_level"`
	RoleCategory   string   `json:"role_category"`
	Location       string   `json:"location"`
	Source         string   `json:"source"`
	Timestamp      string   `json:"timestamp"`
}

func (p *Producer) PublishJobIngested(ctx context.Context, job model.Job) error {
	evt := jobIngestedEvent{
		Event:          "job.ingested",
		JobID:          job.ID,
		RequiredSkills: job.RequiredSkills,
		MinExperience:  job.MinExperience,
		SeniorityLevel: job.SeniorityLevel,
		RoleCategory:   job.RoleCategory,
		Location:       job.Location,
		Source:         job.Source,
		Timestamp:      job.CreatedAt.UTC().Format(time.RFC3339),
	}

	payload, err := json.Marshal(evt)
	if err != nil {
		return fmt.Errorf("marshaling job.ingested event: %w", err)
	}

	msg := kafkago.Message{
		Key:   []byte(job.ID),
		Value: payload,
	}

	writeCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	if err := p.writer.WriteMessages(writeCtx, msg); err != nil {
		return fmt.Errorf("publishing to kafka: %w", err)
	}
	return nil
}

func (p *Producer) Close() error {
	return p.writer.Close()
}
