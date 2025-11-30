#!/bin/bash
# ============================================================
# Project Reorganization Script
# Automatically reorganizes your project structure
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║      Project Structure Reorganization Script          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================
# Safety Check
# ============================================================

echo -e "${YELLOW}⚠️  This script will reorganize your project structure${NC}"
echo ""
echo "Current directory: $(pwd)"
echo ""
read -p "Are you in the Final_Mastery root directory? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${RED}❌ Please cd to Final_Mastery root directory first${NC}"
    exit 1
fi

echo ""
read -p "Create backup before reorganizing? (yes/no): " backup

if [ "$backup" == "yes" ]; then
    backup_name="Final_Mastery_backup_$(date +%Y%m%d_%H%M%S)"
    echo -e "${BLUE}📦 Creating backup: ../$backup_name${NC}"
    cd ..
    cp -r Final_Mastery "$backup_name"
    cd Final_Mastery
    echo -e "${GREEN}✅ Backup created${NC}"
    echo ""
fi

# ============================================================
# Step 1: Create New Directory Structure
# ============================================================

echo -e "${BLUE}📁 Step 1: Creating new directory structure...${NC}"

mkdir -p deployment/localstack
mkdir -p deployment/aws/terraform
mkdir -p testing/results/localstack
mkdir -p testing/results/aws
mkdir -p docs/architecture
mkdir -p docs/charts
mkdir -p docs/guides
mkdir -p scripts

echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# ============================================================
# Step 2: Move LocalStack Files
# ============================================================

echo -e "${BLUE}📦 Step 2: Moving LocalStack files...${NC}"

# Move docker-compose.yml
if [ -f "src/deployment/localstack/docker-compose.yml" ]; then
    mv src/deployment/localstack/docker-compose.yml deployment/localstack/
    echo "  ✓ Moved docker-compose.yml"
fi

# Move localstack-data directory
if [ -d "src/deployment/localstack/localstack-data" ]; then
    mv src/deployment/localstack/localstack-data deployment/localstack/
    echo "  ✓ Moved localstack-data/"
fi

# Move LocalStack results
if ls src/deployment/localstack/results_localstack_*.json 1> /dev/null 2>&1; then
    mv src/deployment/localstack/results_localstack_*.json testing/results/localstack/
    echo "  ✓ Moved LocalStack results"
fi

echo -e "${GREEN}✅ LocalStack files moved${NC}"
echo ""

# ============================================================
# Step 3: Move Testing Files
# ============================================================

echo -e "${BLUE}🧪 Step 3: Moving testing files...${NC}"

# Move performance_test.py
if [ -f "src/deployment/localstack/performance_test.py" ]; then
    mv src/deployment/localstack/performance_test.py testing/
    echo "  ✓ Moved performance_test.py"
fi

# Move analyze_results.py if exists
if [ -f "analyze_results.py" ]; then
    mv analyze_results.py testing/
    echo "  ✓ Moved analyze_results.py"
fi

echo -e "${GREEN}✅ Testing files moved${NC}"
echo ""

# ============================================================
# Step 4: Move AWS/Terraform Files
# ============================================================

echo -e "${BLUE}☁️  Step 4: Moving AWS/Terraform files...${NC}"

# If terraform directory exists at root
if [ -d "terraform" ]; then
    # Move terraform config files
    if [ -f "terraform/main.tf" ]; then
        mv terraform/*.tf deployment/aws/terraform/ 2>/dev/null || true
        echo "  ✓ Moved Terraform configs"
    fi
    
    # Move deploy script
    if [ -f "terraform/deploy.sh" ]; then
        mv terraform/deploy.sh deployment/aws/
        chmod +x deployment/aws/deploy.sh
        echo "  ✓ Moved deploy.sh"
    fi
    
    # Move data loading script
    if [ -f "terraform/loaddata_to_db.py" ]; then
        mv terraform/loaddata_to_db.py deployment/aws/load_data_to_dynamodb.py
        echo "  ✓ Moved load_data_to_dynamodb.py"
    elif [ -f "terraform/load_data_to_dynamodb.py" ]; then
        mv terraform/load_data_to_dynamodb.py deployment/aws/
        echo "  ✓ Moved load_data_to_dynamodb.py"
    fi
    
    # Remove empty terraform directory
    rmdir terraform 2>/dev/null || rm -rf terraform
    echo "  ✓ Cleaned up old terraform directory"
fi

echo -e "${GREEN}✅ AWS/Terraform files moved${NC}"
echo ""

# ============================================================
# Step 5: Move Documentation Files
# ============================================================

echo -e "${BLUE}📚 Step 5: Moving documentation files...${NC}"

# Move any existing docs
if [ -f "REPORT.md" ]; then
    # Keep REPORT.md at root but note it in docs
    echo "  ✓ REPORT.md stays at root"
fi

if [ -f "README.md" ]; then
    echo "  ✓ README.md stays at root"
fi

# Move any guide files to docs/guides
for guide in LOCALSTACK_SETUP.md AWS_DEPLOYMENT.md TESTING_GUIDE.md; do
    if [ -f "$guide" ]; then
        mv "$guide" docs/guides/
        echo "  ✓ Moved $guide"
    fi
done

echo -e "${GREEN}✅ Documentation organized${NC}"
echo ""

# ============================================================
# Step 6: Clean Up Old Structure
# ============================================================

echo -e "${BLUE}🧹 Step 6: Cleaning up old structure...${NC}"

# Remove empty deployment directories
if [ -d "src/deployment" ]; then
    find src/deployment -type d -empty -delete 2>/dev/null || true
    if [ -d "src/deployment" ]; then
        rmdir src/deployment 2>/dev/null || rm -rf src/deployment
    fi
    echo "  ✓ Removed old deployment structure"
fi

# Ask about backup folder
if [ -d "src_demo_backup_1759444318" ]; then
    echo ""
    read -p "Remove old backup folder 'src_demo_backup_1759444318'? (yes/no): " remove_backup
    if [ "$remove_backup" == "yes" ]; then
        rm -rf src_demo_backup_1759444318
        echo "  ✓ Removed old backup folder"
    fi
fi

echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# ============================================================
# Step 7: Create README Files
# ============================================================

echo -e "${BLUE}📝 Step 7: Creating README files...${NC}"

# Root README if it doesn't exist
if [ ! -f "README.md" ]; then
    cat > README.md << 'EOF'
# Product API: LocalStack vs AWS Performance Analysis

## Overview

This project compares the same Product Search API deployed in two environments:
1. LocalStack (local AWS emulation)
2. AWS Lambda + DynamoDB (production cloud)

## Quick Start

### LocalStack
```bash
cd deployment/localstack
docker-compose up -d
```

### AWS
```bash
cd deployment/aws
./deploy.sh
```

### Testing
```bash
cd testing
python3 performance_test.py
```

## Project Structure

- `src/` - Go API source code
- `deployment/` - Deployment configurations
- `testing/` - Performance tests and results
- `docs/` - Documentation and charts

## Report

See [REPORT.md](./REPORT.md) for complete analysis.
EOF
    echo "  ✓ Created root README.md"
fi

# LocalStack README
cat > deployment/localstack/README.md << 'EOF'
# LocalStack Deployment

## Start LocalStack

```bash
docker-compose up -d
```

## Test API

```bash
curl http://localhost:8080/health
curl "http://localhost:8080/products/search?q=alpha"
```

## Stop LocalStack

```bash
docker-compose down
```
EOF
echo "  ✓ Created deployment/localstack/README.md"

# AWS README
cat > deployment/aws/README.md << 'EOF'
# AWS Deployment

## Prerequisites

1. AWS Learner Lab credentials
2. Terraform installed
3. Go installed

## Deploy

```bash
./deploy.sh
```

## Test

```bash
export API_URL=$(cd terraform && terraform output -raw api_endpoint)
curl $API_URL/health
```

## Load Data

```bash
python3 load_data_to_dynamodb.py
```

## Destroy

```bash
cd terraform
terraform destroy
```
EOF
echo "  ✓ Created deployment/aws/README.md"

# Testing README
cat > testing/README.md << 'EOF'
# Performance Testing

## Run Tests

```bash
# Test current deployment
python3 performance_test.py
```

## Analyze Results

```bash
python3 analyze_results.py results/localstack/*.json results/aws/*.json
```

## Results

- LocalStack results: `results/localstack/`
- AWS results: `results/aws/`
- Charts: `../docs/charts/`
EOF
echo "  ✓ Created testing/README.md"

echo -e "${GREEN}✅ README files created${NC}"
echo ""

# ============================================================
# Step 8: Create This Script in scripts/
# ============================================================

cp "$0" scripts/reorganize.sh 2>/dev/null || true
chmod +x scripts/reorganize.sh 2>/dev/null || true

# ============================================================
# Summary
# ============================================================

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              🎉 Reorganization Complete!               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}✨ New Structure:${NC}"
echo ""
echo "Final_Mastery/"
echo "├── README.md"
echo "├── REPORT.md"
echo "├── src/"
echo "│   ├── main.go"
echo "│   ├── store.go"
echo "│   ├── httpx.go"
echo "│   └── ..."
echo "├── deployment/"
echo "│   ├── localstack/"
echo "│   │   ├── docker-compose.yml"
echo "│   │   ├── README.md"
echo "│   │   └── localstack-data/"
echo "│   └── aws/"
echo "│       ├── terraform/"
echo "│       ├── deploy.sh"
echo "│       └── README.md"
echo "├── testing/"
echo "│   ├── performance_test.py"
echo "│   ├── analyze_results.py"
echo "│   ├── README.md"
echo "│   └── results/"
echo "│       ├── localstack/"
echo "│       └── aws/"
echo "├── docs/"
echo "│   ├── architecture/"
echo "│   ├── charts/"
echo "│   └── guides/"
echo "└── scripts/"
echo "    └── reorganize.sh"
echo ""

echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Verify everything works:"
echo "   cd deployment/localstack && docker-compose up -d"
echo ""
echo "2. Update file paths in your code if needed"
echo ""
echo "3. Test your deployments:"
echo "   - LocalStack: deployment/localstack/"
echo "   - AWS: deployment/aws/"
echo ""
echo "4. Run performance tests:"
echo "   cd testing && python3 performance_test.py"
echo ""

if [ "$backup" == "yes" ]; then
    echo -e "${GREEN}💾 Backup saved at: ../$backup_name${NC}"
    echo ""
fi

echo -e "${GREEN}✅ Your project is now professionally organized!${NC}"
echo ""