variable "database_url" {
  description = "Database URL for the service"
  type        = string
  default     = ""
  sensitive   = true
}

variable "firebase_credentials" {
  description = "Firebase service account credentials JSON"
  type        = string
  default     = ""
  sensitive   = true
}

variable "internal_api_secret" {
  description = "Internal API secret for service-to-service authentication"
  type        = string
  default     = ""
  sensitive   = true
}
