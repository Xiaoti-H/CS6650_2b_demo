#!/bin/bash

# LocalStack Deployment Script
# Based on Final Mastery Report architecture:
# - LocalStack: Docker container + In-memory map
# - Data: 10,000 products
# - Network: localhost:8080

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      LocalStack Deployment - Product API              ║${NC}"
echo -e "${BLUE}║      Architecture: Docker + In-Memory Map              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
CONTAINER_NAME="product-api-localstack"
IMAGE_NAME="product-api:localstack"
PORT=8080

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SRC_DIR="$SCRIPT_DIR/../../src"
DOCKERFILE_DIR="$SCRIPT_DIR/../docker"

# Step 1: Check Docker
echo -e "${YELLOW}[1/5] Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Step 2: Build Docker image
echo -e "${YELLOW}[2/5] Building Docker image...${NC}"
echo "   Source: $SRC_DIR"
echo "   Image: $IMAGE_NAME"
echo ""

cd "$SRC_DIR"

# Copy Dockerfile to src directory
cp "$DOCKERFILE_DIR/Dockerfile" .

docker build -t "$IMAGE_NAME" .

echo -e "${GREEN}✅ Docker image built successfully${NC}"
echo ""

# Step 3: Stop existing container (if any)
echo -e "${YELLOW}[3/5] Checking for existing container...${NC}"
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "   Found existing container, stopping and removing..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    echo -e "${GREEN}✅ Removed existing container${NC}"
else
    echo "   No existing container found"
fi
echo ""

# Step 4: Run container
echo -e "${YELLOW}[4/5] Starting container...${NC}"
echo "   Container name: $CONTAINER_NAME"
echo "   Port: $PORT"
echo "   Storage: In-Memory Map"
echo ""

docker run -d \
    --name "$CONTAINER_NAME" \
    -p ${PORT}:8080 \
    -e STORAGE_TYPE=memory \
    -e PORT=8080 \
    "$IMAGE_NAME"

echo -e "${GREEN}✅ Container started${NC}"
echo ""

# Step 5: Wait for service to be ready
echo -e "${YELLOW}[5/5] Waiting for service to be ready...${NC}"
sleep 3

MAX_ATTEMPTS=10
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:${PORT}/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service is ready!${NC}"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "   Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}❌ Service failed to start${NC}"
    echo ""
    echo "Check logs:"
    echo "   docker logs $CONTAINER_NAME"
    exit 1
fi

echo ""

# Verify deployment
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Deployment Verification                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Health check
echo -e "${YELLOW}Testing /health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s http://localhost:${PORT}/health)
echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
echo ""

# Search test
echo -e "${YELLOW}Testing /products/search endpoint...${NC}"
SEARCH_RESPONSE=$(curl -s "http://localhost:${PORT}/products/search?q=alpha&limit=5")
echo "$SEARCH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SEARCH_RESPONSE"
echo ""

# Final summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🎉 Deployment Successful! 🎉                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📝 Deployment Summary:${NC}"
echo -e "   API URL:        ${BLUE}http://localhost:${PORT}${NC}"
echo -e "   Container:      ${BLUE}$CONTAINER_NAME${NC}"
echo -e "   Storage:        ${BLUE}In-Memory Map (10,000 products)${NC}"
echo -e "   Environment:    ${BLUE}LocalStack${NC}"
echo ""
echo -e "${YELLOW}🔗 Test URLs:${NC}"
echo -e "   Health:  ${BLUE}http://localhost:${PORT}/health${NC}"
echo -e "   Search:  ${BLUE}http://localhost:${PORT}/products/search?q=alpha&limit=100${NC}"
echo ""
echo -e "${YELLOW}📊 Useful Commands:${NC}"
echo -e "   View logs:      ${BLUE}docker logs -f $CONTAINER_NAME${NC}"
echo -e "   Stop:           ${BLUE}docker stop $CONTAINER_NAME${NC}"
echo -e "   Restart:        ${BLUE}docker restart $CONTAINER_NAME${NC}"
echo -e "   Remove:         ${BLUE}docker rm -f $CONTAINER_NAME${NC}"
echo ""
echo -e "${YELLOW}🧪 Next Steps:${NC}"
echo -e "   1. Run performance tests"
echo -e "   2. Compare with AWS results"
echo -e "   3. Update your report"
echo ""