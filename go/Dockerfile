# Go 1.24
FROM golang:1.24-alpine AS builder
WORKDIR /app
COPY go.mod .
RUN go mod download
COPY cmd ./cmd
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o server ./cmd

FROM alpine:3.20
WORKDIR /app
COPY --from=builder /app/server .
ENV GOMAXPROCS=1
EXPOSE 8082
ENTRYPOINT ["./server"]
