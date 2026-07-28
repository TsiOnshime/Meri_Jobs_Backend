package config

import (
	"fmt"
	"os"
	"strconv"
)

type Config struct {
	HTTPPort string

	DatabaseURL string

	KafkaBrokers []string
	KafkaTopic   string

	JobProviderName string
	JobAPIURL       string
	RemoteOKAPIKey  string // optional

	IngestionIntervalHours int
}

func Load() (*Config, error) {
	cfg := &Config{
		HTTPPort:        getEnv("HTTP_PORT", "8003"),
		DatabaseURL:     buildDatabaseURL(),
		KafkaTopic:      getEnv("KAFKA_TOPIC", "job.ingested"),
		JobProviderName: getEnv("JOB_PROVIDER", "remoteok"),
		JobAPIURL:       getEnv("JOB_API_URL", "https://remoteok.com/api"),
		RemoteOKAPIKey:  os.Getenv("REMOTEOK_API_KEY"),
	}

	brokers := getEnv("KAFKA_BROKER_URL", getEnv("KAFKA_BROKERS", "localhost:9092"))
	cfg.KafkaBrokers = splitAndTrim(brokers)

	intervalStr := getEnv("INGESTION_INTERVAL_HOURS", "4")
	interval, err := strconv.Atoi(intervalStr)
	if err != nil || interval <= 0 {
		return nil, fmt.Errorf("invalid INGESTION_INTERVAL_HOURS %q: must be a positive integer", intervalStr)
	}
	cfg.IngestionIntervalHours = interval

	return cfg, nil
}

func buildDatabaseURL() string {
	if v := os.Getenv("DATABASE_URL"); v != "" {
		return v
	}

	host := getEnv("POSTGRES_HOST", "localhost")
	port := getEnv("POSTGRES_PORT", "5432")
	db := getEnv("POSTGRES_DB", "merijobs")
	user := getEnv("POSTGRES_USER", "merijobs")
	password := getEnv("POSTGRES_PASSWORD", "changeme")

	return fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=disable", user, password, host, port, db)
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func splitAndTrim(s string) []string {
	var out []string
	start := 0
	for i := 0; i <= len(s); i++ {
		if i == len(s) || s[i] == ',' {
			part := trim(s[start:i])
			if part != "" {
				out = append(out, part)
			}
			start = i + 1
		}
	}
	if len(out) == 0 {
		out = []string{"localhost:9092"}
	}
	return out
}

func trim(s string) string {
	start := 0
	end := len(s)
	for start < end && (s[start] == ' ' || s[start] == '\t') {
		start++
	}
	for end > start && (s[end-1] == ' ' || s[end-1] == '\t') {
		end--
	}
	return s[start:end]
}
