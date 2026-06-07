variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "service_name" {
  description = "Service name (lowercase, no spaces)"
  type        = string
  default     = "aggr-user-service"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.service_name))
    error_message = "Service name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "github_repo" {
  description = "GitHub repository (e.g., alexxqq/aggr-user-service)"
  type        = string
  default     = "alexxqq/aggr-user-service"
}

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = "thesis-cluster"
}

variable "ecs_task_cpu" {
  description = "ECS task CPU (256, 512, 1024, etc.)"
  type        = string
  default     = "256"
}

variable "ecs_task_memory" {
  description = "ECS task memory in MB"
  type        = string
  default     = "512"
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1

  validation {
    condition     = var.ecs_desired_count > 0
    error_message = "Desired count must be greater than 0."
  }
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8002
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}
