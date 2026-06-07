# Secrets Manager Secrets (create manually or populate via tfvars)

# Database URL Secret
resource "aws_secretsmanager_secret" "database_url" {
  name_prefix = "${var.service_name}/database-url-"
  description = "Database URL for ${var.service_name}"

  recovery_window_in_days = 0  # Immediate deletion (for dev)

  tags = {
    Name = "${var.service_name}-database-url"
  }
}

# Placeholder for database URL value
# Replace with actual value or use: terraform apply -var 'database_url=...'
resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = var.database_url != "" ? var.database_url : "postgresql+asyncpg://user:pass@localhost:5432/db"
}

# Firebase Credentials Secret
resource "aws_secretsmanager_secret" "firebase_credentials" {
  name_prefix = "${var.service_name}/firebase-credentials-"
  description = "Firebase service account credentials"

  recovery_window_in_days = 0

  tags = {
    Name = "${var.service_name}-firebase-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "firebase_credentials" {
  secret_id     = aws_secretsmanager_secret.firebase_credentials.id
  secret_string = var.firebase_credentials != "" ? var.firebase_credentials : "{}"
}

# Internal API Secret
resource "aws_secretsmanager_secret" "internal_api_secret" {
  name_prefix = "${var.service_name}/internal-api-secret-"
  description = "Internal API secret for service-to-service auth"

  recovery_window_in_days = 0

  tags = {
    Name = "${var.service_name}-internal-api-secret"
  }
}

resource "aws_secretsmanager_secret_version" "internal_api_secret" {
  secret_id     = aws_secretsmanager_secret.internal_api_secret.id
  secret_string = var.internal_api_secret != "" ? var.internal_api_secret : "change-me-in-production"
}

# Outputs
output "database_url_secret_arn" {
  description = "ARN of database URL secret"
  value       = aws_secretsmanager_secret.database_url.arn
  sensitive   = true
}

output "firebase_credentials_secret_arn" {
  description = "ARN of Firebase credentials secret"
  value       = aws_secretsmanager_secret.firebase_credentials.arn
  sensitive   = true
}

output "internal_api_secret_arn" {
  description = "ARN of internal API secret"
  value       = aws_secretsmanager_secret.internal_api_secret.arn
  sensitive   = true
}
