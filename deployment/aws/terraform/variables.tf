variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "product-api"
}

variable "aws_account_id" {
  description = "AWS Account ID (from Learner Lab)"
  type        = string
  default     = "120306667922"
}

variable "lab_role_arn" {
  description = "ARN of the existing LabRole"
  type        = string
  default     = "arn:aws:iam::120306667922:role/LabRole"
}

variable "container_port" {
  description = "Port on which the container listens"
  type        = number
  default     = 8080
}

variable "app_count" {
  description = "Number of ECS tasks to run"
  type        = number
  default     = 2
}

variable "fargate_cpu" {
  description = "Fargate instance CPU units (1 vCPU = 1024 units)"
  type        = string
  default     = "256"
}

variable "fargate_memory" {
  description = "Fargate instance memory in MB"
  type        = string
  default     = "512"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for products"
  type        = string
  default     = "products"
}
