# Terraform configuration for Steel Price Predictor API
# Project: cdo-yacosta
# Account: dra.acostas@gmail.com

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  # Backend configuration for state storage
  backend "gcs" {
    bucket = "cdo-yacosta-terraform-state"
    prefix = "steel-predictor/state"
  }
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudscheduler.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "artifactregistry.googleapis.com"
  ])

  service            = each.value
  disable_on_destroy = false
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "steel-predictor-sa"
  display_name = "Steel Price Predictor Service Account"
  description  = "Service account for Cloud Run steel price predictor"
}

# IAM roles for service account
resource "google_project_iam_member" "cloud_run_roles" {
  for_each = toset([
    "roles/datastore.user",
    "roles/storage.objectViewer",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"

  depends_on = [google_project_service.apis]
}

# Cloud Storage bucket for model and predictions
resource "google_storage_bucket" "model_bucket" {
  name          = "${var.project_id}-models"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age        = 30
      with_state = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

# Upload model to bucket (placeholder - actual model uploaded separately)
resource "google_storage_bucket_object" "model_placeholder" {
  name   = "models/TWO_STAGE_MODEL.pkl"
  bucket = google_storage_bucket.model_bucket.name
  source = "/dev/null" # Placeholder - actual model uploaded via CI/CD

  lifecycle {
    ignore_changes = [source, content]
  }
}

# Firestore database for rate limiting
resource "google_firestore_database" "rate_limit_db" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.apis]
}

# Secret Manager for API keys
resource "google_secret_manager_secret" "api_keys" {
  secret_id = "steel-predictor-api-keys"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

# Default API key version
resource "google_secret_manager_secret_version" "api_key_v1" {
  secret = google_secret_manager_secret.api_keys.id

  secret_data = jsonencode({
    keys = {
      "default-key" = random_password.default_api_key.result
    }
  })
}

# Generate default API key
resource "random_password" "default_api_key" {
  length  = 32
  special = true
}

# Cloud Run service
resource "google_cloud_run_service" "steel_predictor" {
  name     = "steel-predictor"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.cloud_run_sa.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/steel-predictor/api:latest"

        resources {
          limits = {
            cpu    = "0.25"
            memory = "256Mi"
          }
        }

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "MODEL_BUCKET"
          value = google_storage_bucket.model_bucket.name
        }

        env {
          name  = "FIRESTORE_DATABASE"
          value = google_firestore_database.rate_limit_db.name
        }

        env {
          name  = "API_KEYS_SECRET"
          value = google_secret_manager_secret.api_keys.secret_id
        }

        env {
          name  = "LOG_LEVEL"
          value = var.log_level
        }

        ports {
          container_port = 8080
        }
      }

      # Cold start mitigation
      container_concurrency = 80
      timeout_seconds       = 60
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"  = var.min_instances
        "autoscaling.knative.dev/maxScale"  = var.max_instances
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.apis,
    google_project_iam_member.cloud_run_roles
  ]
}

# Allow unauthenticated access to Cloud Run
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.steel_predictor.name
  location = google_cloud_run_service.steel_predictor.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Scheduler for daily predictions
resource "google_cloud_scheduler_job" "daily_prediction" {
  name             = "update-steel-prediction"
  description      = "Daily update of steel price prediction"
  schedule         = var.prediction_schedule
  time_zone        = "America/Mexico_City"
  attempt_deadline = "320s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.steel_predictor.status[0].url}/internal/update-prediction"

    headers = {
      "X-API-Key" = random_password.scheduler_api_key.result
    }

    oidc_token {
      service_account_email = google_service_account.cloud_run_sa.email
    }
  }

  depends_on = [google_project_service.apis]
}

# Generate scheduler API key
resource "random_password" "scheduler_api_key" {
  length  = 32
  special = true
}

# Monitoring alert for high latency
resource "google_monitoring_alert_policy" "latency_alert" {
  display_name = "Steel Predictor High Latency"
  combiner     = "OR"

  conditions {
    display_name = "Request latency > 1.5s"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"steel-predictor\" AND metric.type=\"run.googleapis.com/request_latencies\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 1500

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_95"
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "86400s"
  }

  depends_on = [google_project_service.apis]
}

# Monitoring uptime check
resource "google_monitoring_uptime_check_config" "health_check" {
  display_name = "Steel Predictor Health Check"
  timeout      = "10s"
  period       = "300s" # 5 minutes

  http_check {
    path         = "/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "cloud_run_revision"
    labels = {
      project_id    = var.project_id
      service_name  = google_cloud_run_service.steel_predictor.name
      location      = google_cloud_run_service.steel_predictor.location
      revision_name = google_cloud_run_service.steel_predictor.status[0].latest_ready_revision_name
    }
  }

  depends_on = [google_project_service.apis]
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "steel-predictor"
  description   = "Docker repository for steel price predictor"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]
}

