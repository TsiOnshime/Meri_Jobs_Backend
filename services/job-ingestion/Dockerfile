# syntax=docker/dockerfile:1

FROM golang:1.25-alpine AS build
WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /usr/local/bin/server ./cmd/server

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
WORKDIR /app

COPY --from=build /usr/local/bin/server /usr/local/bin/server
COPY . .

EXPOSE 8003
ENTRYPOINT ["/usr/local/bin/server"]