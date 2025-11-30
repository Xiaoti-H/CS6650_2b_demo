# ALB Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "URL to access the application"
  value       = "http://${aws_lb.main.dns_name}"
}

# DynamoDB Outputs
output "dynamodb_table_name" {
  description = "Name of the DynamoDB products table"
  value       = aws_dynamodb_table.products.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB products table"
  value       = aws_dynamodb_table.products.arn
}

# ECR Outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}

# Test URLs
output "test_urls" {
  description = "URLs for testing"
  value = {
    health = "http://${aws_lb.main.dns_name}/health"
    search = "http://${aws_lb.main.dns_name}/products/search?q=alpha&limit=100"
  }
}
