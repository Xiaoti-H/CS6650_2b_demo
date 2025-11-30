
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      AWS ECS + DynamoDB Deployment (Docker)           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

PROJECT_NAME="product-api"
AWS_REGION="us-east-1"
TERRAFORM_DIR="$(pwd)/terraform"
SRC_DIR="$(pwd)/../../src"

# Helper function to run terraform via Docker
terraform_docker() {
    docker run --rm -it \
        -v "$TERRAFORM_DIR":/workspace \
        -v ~/.aws:/root/.aws \
        -e AWS_ACCESS_KEY_ID \
        -e AWS_SECRET_ACCESS_KEY \
        -e AWS_SESSION_TOKEN \
        -e AWS_DEFAULT_REGION="$AWS_REGION" \
        -w /workspace \
        hashicorp/terraform:latest \
        "$@"
}

# Step 1: Terraform Plan
echo -e "${YELLOW}🔧 Step 1: Creating infrastructure plan...${NC}"
cd terraform
terraform_docker init
terraform_docker plan -out=tfplan

echo ""
echo -e "${YELLOW}📋 Review the plan above. Continue? (yes/no)${NC}"
read -r CONTINUE

if [ "$CONTINUE" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Step 2: Terraform Apply
echo ""
echo -e "${YELLOW}🚀 Step 2: Deploying infrastructure...${NC}"
terraform_docker apply tfplan

# Step 3: Get outputs
echo ""
echo -e "${YELLOW}📊 Step 3: Getting deployment info...${NC}"
ECR_URL=$(terraform_docker output -raw ecr_repository_url)
ALB_URL=$(terraform_docker output -raw alb_url)
TABLE_NAME=$(terraform_docker output -raw dynamodb_table_name)
CLUSTER_NAME=$(terraform_docker output -raw ecs_cluster_name)
SERVICE_NAME=$(terraform_docker output -raw ecs_service_name)

echo -e "${GREEN}✅ Infrastructure deployed${NC}"
echo -e "   ECR: ${ECR_URL}"
echo -e "   ALB: ${ALB_URL}"
echo -e "   DynamoDB: ${TABLE_NAME}"

cd ..

# Step 4: Build and push Docker image
echo ""
echo -e "${YELLOW}🐳 Step 4: Building and pushing Docker image...${NC}"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo -e "${BLUE}   Logging in to ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo -e "${BLUE}   Building Docker image...${NC}"
cd "$SRC_DIR"
docker build --platform linux/amd64 -t ${PROJECT_NAME}:latest .

echo -e "${BLUE}   Tagging image...${NC}"
docker tag ${PROJECT_NAME}:latest ${ECR_URL}:latest

echo -e "${BLUE}   Pushing to ECR...${NC}"
docker push ${ECR_URL}:latest

echo -e "${GREEN}✅ Docker image pushed${NC}"

cd ../deployment/aws

# Step 5: Wait for ECS service
echo ""
echo -e "${YELLOW}⏳ Step 5: Waiting for ECS service to stabilize...${NC}"
echo -e "${BLUE}   This may take 2-3 minutes...${NC}"
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION

echo -e "${GREEN}✅ ECS service is running${NC}"

# Step 6: Load data to DynamoDB
echo ""
echo -e "${YELLOW}📊 Step 6: Loading data to DynamoDB...${NC}"

cd "$SRC_DIR"
export DYNAMODB_TABLE=$TABLE_NAME
export AWS_REGION=$AWS_REGION

if [ -f "cmd/load_data/main.go" ]; then
    go run cmd/load_data/main.go
else
    echo -e "${RED}❌ load_data not found at cmd/load_data/main.go${NC}"
    echo -e "${YELLOW}Please run manually later${NC}"
fi

echo -e "${GREEN}✅ Data loaded${NC}"

cd ../../deployment/aws

# Step 7: Test deployment
echo ""
echo -e "${YELLOW}🧪 Step 7: Testing deployment...${NC}"

sleep 10

echo -e "${BLUE}   Testing /health...${NC}"
if curl -s "${ALB_URL}/health" | grep -q "healthy"; then
    echo -e "${GREEN}   ✅ Health check passed${NC}"
else
    echo -e "${RED}   ❌ Health check failed${NC}"
fi

echo -e "${BLUE}   Testing /products/search...${NC}"
if curl -s "${ALB_URL}/products/search?q=alpha&limit=100" | grep -q "products"; then
    echo -e "${GREEN}   ✅ Search endpoint working${NC}"
else
    echo -e "${RED}   ❌ Search endpoint failed${NC}"
fi

# Final summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🎉 Deployment Successful! 🎉                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📝 Deployment Summary:${NC}"
echo -e "   ALB URL: ${BLUE}${ALB_URL}${NC}"
echo -e "   DynamoDB Table: ${BLUE}${TABLE_NAME}${NC}"
echo ""
echo -e "${YELLOW}🔗 Test URLs:${NC}"
echo -e "   Health: ${BLUE}${ALB_URL}/health${NC}"
echo -e "   Search: ${BLUE}${ALB_URL}/products/search?q=alpha&limit=100${NC}"
echo ""

DEPLOYSCRIPT

chmod +x ~/Documents/NEU/CS6650-scalable-distributed-systems/HW5/Final_Mastery/deployment/aws/deploy.sh