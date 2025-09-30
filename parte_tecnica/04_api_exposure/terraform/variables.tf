# Variables for Steel Price Predictor Terraform configuration

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "cdo-yacosta"
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone for compute resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# Cloud Run configuration
variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 2
}

variable "log_level" {
  description = "Logging level for the application"
  type        = string
  default     = "INFO"
}

# Scheduling configuration
variable "prediction_schedule" {
  description = "Cron schedule for daily predictions"
  type        = string
  default     = "0 6 * * *" # 6 AM daily
}

variable "data_update_schedule" {
  description = "Cron schedule for LME data updates"
  type        = string
  default     = "0 7 * * *" # 7 AM daily
}

variable "model_retrain_schedule" {
  description = "Cron schedule for model retraining"
  type        = string
  default     = "0 2 * * 1" # 2 AM every Monday
}

# Monitoring configuration
variable "notification_channels" {
  description = "List of notification channels for alerts"
  type        = list(string)
  default     = []
}

# Data pipeline configuration
variable "lme_data_sources" {
  description = "LME data source configurations"
  type = map(object({
    url              = string
    file_pattern     = string
    update_frequency = string
  }))
  default = {
    steel_rebar = {
      url              = "https://example.com/lme/steel-rebar"
      file_pattern     = "SR_Closing_Prices_*.xlsx"
      update_frequency = "daily"
    }
    steel_scrap = {
      url              = "https://example.com/lme/steel-scrap"
      file_pattern     = "SC_Closing_Prices_*.xlsx"
      update_frequency = "daily"
    }
  }
}

# Model training configuration
variable "training_machine_type" {
  description = "Machine type for model training"
  type        = string
  default     = "n1-standard-4"
}

variable "training_disk_size_gb" {
  description = "Disk size in GB for training instances"
  type        = number
  default     = 100
}

# BigQuery configuration
variable "dataset_location" {
  description = "Location for BigQuery datasets"
  type        = string
  default     = "US"
}

variable "table_expiration_days" {
  description = "Default expiration for BigQuery tables in days"
  type        = number
  default     = 90
}

# Feature flags
variable "enable_a_b_testing" {
  description = "Enable A/B testing capability"
  type        = bool
  default     = true
}

variable "enable_explainability" {
  description = "Enable model explainability endpoint"
  type        = bool
  default     = true
}

variable "enable_monitoring_dashboard" {
  description = "Enable custom monitoring dashboard"
  type        = bool
  default     = true
}

# Alert configuration
variable "alert_email" {
  description = "Email address for alert notifications"
  type        = string
  default     = "dra.acostas@gmail.com"
}

variable "billing_account_id" {
  description = "GCP billing account ID for budget alerts"
  type        = string
  default     = "" # Must be provided by user
}

# API Security
variable "api_key_secret_name" {
  description = "Secret Manager secret name for API keys"
  type        = string
  default     = "steel-predictor-api-keys"
}

variable "rate_limit_requests" {
  description = "Number of requests allowed per hour"
  type        = number
  default     = 100
}

variable "cache_ttl_seconds" {
  description = "Cache TTL for predictions in seconds"
  type        = number
  default     = 3600 # 1 hour
}

# Cloud Run configuration details
variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run"
  type        = string
  default     = "1"
}

variable "cloud_run_memory" {
  description = "Memory allocation for Cloud Run"
  type        = string
  default     = "512Mi"
}

# Model configuration
variable "model_version" {
  description = "Current model version"
  type        = string
  default     = "v1.0"
}

# Timezone for schedules
variable "schedule_timezone" {
  description = "Timezone for all scheduled jobs"
  type        = string
  default     = "America/Mexico_City"
}
