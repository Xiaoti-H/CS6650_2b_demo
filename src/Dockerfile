# Build stage
FROM --platform=linux/amd64 golang:1.23-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the application for linux/amd64
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o server main.go

# Runtime stage
FROM --platform=linux/amd64 alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/server .

# Expose port
EXPOSE 8080

# Set default environment variables
ENV PORT=8080
ENV STORAGE_TYPE=memory

# Run the application
CMD ["./server"]