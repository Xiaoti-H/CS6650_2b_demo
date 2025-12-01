#!/bin/bash

# Environment Check Script for LocalStack Deployment
# Based on Xiaoti's Final Mastery Report

echo "================================================"
echo "  Environment Check for LocalStack Deployment"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

all_good=true

# Check 1: LocalStack Pro
echo "Checking LocalStack Pro..."
if command -v localstack &> /dev/null; then
    version=$(localstack --version)
    echo -e "${GREEN}✅ LocalStack CLI installed: $version${NC}"
    
    # Check if running
    if curl -s http://localhost:4566/_localstack/health &> /dev/null; then
        echo -e "${GREEN}✅ LocalStack is running${NC}"
    else
        echo -e "${YELLOW}⚠️  LocalStack not running (we'll start it)${NC}"
    fi
else
    echo -e "${RED}❌ LocalStack CLI not found${NC}"
    all_good=false
fi
echo ""

# Check 2: Docker
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo -e "${GREEN}✅ Docker installed: $docker_version${NC}"
    
    if docker info &> /dev/null; then
        echo -e "${GREEN}✅ Docker daemon is running${NC}"
    else
        echo -e "${RED}❌ Docker daemon not running${NC}"
        all_good=false
    fi
else
    echo -e "${RED}❌ Docker not found${NC}"
    all_good=false
fi
echo ""

# Check 3: Go (for building)
echo "Checking Go..."
if command -v go &> /dev/null; then
    go_version=$(go version)
    echo -e "${GREEN}✅ Go installed: $go_version${NC}"
else
    echo -e "${YELLOW}⚠️  Go not found (needed if building from source)${NC}"
fi
echo ""

# Check 4: Python (for testing)
echo "Checking Python..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo -e "${GREEN}✅ Python installed: $python_version${NC}"
    
    # Check for requests library
    if python3 -c "import requests" &> /dev/null; then
        echo -e "${GREEN}✅ requests library installed${NC}"
    else
        echo -e "${YELLOW}⚠️  requests library not found${NC}"
        echo "   Install: pip3 install requests"
    fi
else
    echo -e "${RED}❌ Python3 not found${NC}"
    all_good=false
fi
echo ""

# Check 5: Port 8080 availability
echo "Checking port 8080..."
if lsof -i :8080 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Port 8080 is in use${NC}"
    echo "   Current process:"
    lsof -i :8080 | grep LISTEN
    echo "   You may need to stop this process"
else
    echo -e "${GREEN}✅ Port 8080 is available${NC}"
fi
echo ""

# Summary
echo "================================================"
if [ "$all_good" = true ]; then
    echo -e "${GREEN}✅ All critical checks passed!${NC}"
    echo ""
    echo "You're ready to deploy LocalStack."
else
    echo -e "${RED}❌ Some checks failed${NC}"
    echo ""
    echo "Please fix the issues above before continuing."
fi
echo "================================================"