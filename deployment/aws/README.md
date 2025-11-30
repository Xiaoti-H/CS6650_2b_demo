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
