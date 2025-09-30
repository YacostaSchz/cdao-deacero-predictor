# Data Pipelines for Steel Price Predictor
# This file manages the data ingestion and model training pipelines

# BigQuery dataset for raw and processed data
resource "google_bigquery_dataset" "steel_data" {
  dataset_id                  = "steel_price_data"
  friendly_name               = "Steel Price Data"
  description                 = "Raw and processed data for steel price prediction"
  location                    = var.dataset_location
  default_table_expiration_ms = var.table_expiration_days * 24 * 60 * 60 * 1000

  labels = {
    environment = var.environment
    purpose     = "ml-data"
  }

  depends_on = [google_project_service.apis]
}

# Tables for different data sources (based on actual data used)
locals {
  data_tables = {
    # Daily updated data
    lme_rebar = {
      table_id    = "lme_steel_rebar_daily"
      description = "LME Steel Rebar FOB Turkey (Platts) - Daily prices M01-M15"
      schema      = file("${path.module}/schemas/lme_rebar.json")
    }
    lme_scrap = {
      table_id    = "lme_steel_scrap_daily"
      description = "LME Steel Scrap CFR Turkey - Daily prices M01-M15"
      schema      = file("${path.module}/schemas/lme_scrap.json")
    }
    fx_rates = {
      table_id    = "usd_mxn_daily"
      description = "USD/MXN exchange rates from Banxico - Daily"
      schema      = file("${path.module}/schemas/fx_rates.json")
    }
    tiie_rates = {
      table_id    = "tiie_28d_daily"
      description = "TIIE 28 days interest rate from Banxico - Daily"
      schema      = file("${path.module}/schemas/tiie_rates.json")
    }

    # Monthly updated data
    banxico_macro = {
      table_id    = "banxico_indicators_monthly"
      description = "Banxico macroeconomic indicators - INPC, IGAE, Inflation"
      schema      = file("${path.module}/schemas/banxico_macro.json")
    }
    epu_indices = {
      table_id    = "epu_uncertainty_indices"
      description = "Economic Policy Uncertainty indices - Mexico, USA, China, Turkey"
      schema      = file("${path.module}/schemas/epu_indices.json")
    }
    gas_natural = {
      table_id    = "gas_natural_ipgn_monthly"
      description = "Mexican Natural Gas Price Index (IPGN) - Monthly"
      schema      = file("${path.module}/schemas/gas_natural.json")
    }

    # Processed data
    model_features = {
      table_id    = "processed_features"
      description = "Processed features for Two-Stage model training"
      schema      = file("${path.module}/schemas/model_features.json")
    }
    predictions = {
      table_id    = "predictions_history"
      description = "Historical predictions and actuals for monitoring"
      schema      = file("${path.module}/schemas/predictions.json")
    }
  }
}

# Create BigQuery tables
resource "google_bigquery_table" "data_tables" {
  for_each = local.data_tables

  dataset_id = google_bigquery_dataset.steel_data.dataset_id
  table_id   = each.value.table_id

  description = each.value.description

  time_partitioning {
    type  = "DAY"
    field = "date"
  }

  schema = each.value.schema

  labels = {
    source           = replace(each.key, "_", "-")
    update_frequency = contains(["lme_rebar", "lme_scrap", "fx_rates", "tiie_rates"], each.key) ? "daily" : "monthly"
  }

  depends_on = [google_bigquery_dataset.steel_data]
}

# Cloud Storage buckets for data staging
resource "google_storage_bucket" "data_staging" {
  name          = "${var.project_id}-data-staging"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 7 # Clean up staging files after 7 days
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

# Bucket for processed data and backups
resource "google_storage_bucket" "data_processed" {
  name          = "${var.project_id}-data-processed"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age        = 90
      with_state = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

# Bucket for Excel file storage and processing
resource "google_storage_bucket" "excel_storage" {
  name          = "${var.project_id}-excel-files"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true # Keep versions of Excel files
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 5 # Keep last 5 versions
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

# Cloud Functions for data ingestion (corrected for actual data sources)
locals {
  data_ingestion_functions = {
    # LME Excel Processor
    # LME closes at 17:00 London time (GMT/BST)
    # Data typically available after 18:00 London
    # In Mexico City: 12:00 PM (summer) or 12:00 PM (winter)
    lme_excel_processor = {
      name        = "lme-excel-processor"
      description = "Processes LME Excel files (SR & SC Closing Prices) - Runs after London market close"
      schedule    = "0 14 * * 1-5" # 2:00 PM Mexico City (Mon-Fri) - gives buffer after LME close
      sources     = ["SR Closing Prices.xlsx", "SC Closing Prices.xlsx"]
      frequency   = "daily"
      type        = "excel_processor"
    }

    # Banxico API Data (real-time available)
    banxico_daily_updater = {
      name        = "banxico-daily-updater"
      description = "Updates USD/MXN (SF43718) and TIIE 28d (SF43783) from Banxico API"
      schedule    = "30 8 * * 1-5"         # 8:30 AM Mexico City (Mon-Fri)
      sources     = ["SF43718", "SF43783"] # Banxico series IDs
      frequency   = "daily"
      type        = "api_fetcher"
    }

    # Banxico monthly indicators
    banxico_monthly_updater = {
      name        = "banxico-monthly-updater"
      description = "Updates INPC (SP1), IGAE (SR16734), Inflation (SP74665) from Banxico API"
      schedule    = "0 10 3 * *"                  # 10:00 AM on 3rd of month
      sources     = ["SP1", "SR16734", "SP74665"] # Banxico series IDs
      frequency   = "monthly"
      type        = "api_fetcher"
    }

    # EPU Excel files (updated monthly)
    epu_excel_processor = {
      name        = "epu-excel-processor"
      description = "Processes EPU Excel files for Mexico, USA, China, Turkey"
      schedule    = "0 11 1 * *" # 11:00 AM on 1st of month
      sources = [
        "Mexico_Policy_Uncertainty_Data.xlsx",
        "US_Policy_Uncertainty_Data.xlsx",
        "China_Policy_Uncertainty_Data.xlsx",
        "ECSU_Index.xls" # Turkey EPU
      ]
      frequency = "monthly"
      type      = "excel_processor"
    }

    # Gas Natural Excel (IPGN)
    gas_natural_processor = {
      name        = "gas-natural-processor"
      description = "Processes Mexican Natural Gas Price Index Excel file"
      schedule    = "0 12 5 * *" # 12:00 PM on 5th of month
      sources     = ["Índice de Precios de Gas Natural.xlsx"]
      frequency   = "monthly"
      type        = "excel_processor"
    }
  }
}

# Cloud Function source code bucket
resource "google_storage_bucket" "function_source" {
  name          = "${var.project_id}-function-source"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.apis]
}

# Upload function source code based on processor type
resource "google_storage_bucket_object" "function_sources" {
  for_each = local.data_ingestion_functions

  name   = "data-ingestion/${each.key}.zip"
  bucket = google_storage_bucket.function_source.name
  source = each.value.type == "excel_processor" ? "${path.module}/functions/excel_processor_template.zip" : "${path.module}/functions/api_fetcher_template.zip"

  lifecycle {
    ignore_changes = [content, source]
  }
}

# Cloud Functions for data ingestion
resource "google_cloudfunctions2_function" "data_ingesters" {
  for_each = local.data_ingestion_functions

  name        = each.value.name
  location    = var.region
  description = each.value.description

  build_config {
    runtime     = "python39"
    entry_point = each.value.type == "excel_processor" ? "process_excel" : "fetch_api_data"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_sources[each.key].name
      }
    }
  }

  service_config {
    max_instance_count    = 1
    min_instance_count    = 0
    timeout_seconds       = 540   # 9 minutes
    available_memory      = "1Gi" # More memory for Excel processing
    service_account_email = google_service_account.cloud_run_sa.email

    environment_variables = {
      PROJECT_ID       = var.project_id
      DATASET_ID       = google_bigquery_dataset.steel_data.dataset_id
      STAGING_BUCKET   = google_storage_bucket.data_staging.name
      EXCEL_BUCKET     = google_storage_bucket.excel_storage.name
      DATA_SOURCES     = jsonencode(each.value.sources)
      UPDATE_FREQUENCY = each.value.frequency
      PROCESSOR_TYPE   = each.value.type
    }
  }

  depends_on = [google_project_service.apis]
}

# Cloud Scheduler jobs for data ingestion
resource "google_cloud_scheduler_job" "data_ingestion_schedules" {
  for_each = local.data_ingestion_functions

  name             = "${each.value.name}-schedule"
  description      = "Schedule for ${each.value.description}"
  schedule         = each.value.schedule
  time_zone        = "America/Mexico_City"
  attempt_deadline = "600s"

  retry_config {
    retry_count = 2
  }

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.data_ingesters[each.key].service_config[0].uri

    oidc_token {
      service_account_email = google_service_account.cloud_run_sa.email
    }
  }

  depends_on = [google_cloudfunctions2_function.data_ingesters]
}

# Cloud Build trigger for model training
resource "google_cloudbuild_trigger" "model_training" {
  name        = "steel-model-training"
  description = "Trains the Two-Stage steel price prediction model"

  # Trigger on schedule via Cloud Scheduler
  webhook_config {
    secret = google_secret_manager_secret.build_webhook_secret.id
  }

  build {
    # Step 1: Build training container
    step {
      name = "gcr.io/cloud-builders/docker"
      args = ["build", "-t", "gcr.io/${var.project_id}/model-trainer:latest", "-f", "Dockerfile.training", "."]
    }

    # Step 2: Run training job
    step {
      name = "gcr.io/${var.project_id}/model-trainer:latest"
      env = [
        "PROJECT_ID=${var.project_id}",
        "DATASET_ID=${google_bigquery_dataset.steel_data.dataset_id}",
        "MODEL_BUCKET=${google_storage_bucket.model_bucket.name}",
        "MACHINE_TYPE=${var.training_machine_type}"
      ]
      args = ["python", "train_two_stage_model.py"]
    }

    # Step 3: Upload trained model
    step {
      name = "gcr.io/cloud-builders/gsutil"
      args = ["cp", "TWO_STAGE_MODEL.pkl", "gs://${google_storage_bucket.model_bucket.name}/models/"]
    }

    # Step 4: Update model version in Cloud Run
    step {
      name = "gcr.io/cloud-builders/gcloud"
      args = [
        "run", "services", "update", "steel-predictor",
        "--update-env-vars", "MODEL_VERSION=$BUILD_ID",
        "--region", var.region
      ]
    }
  }

  options {
    machine_type = var.training_machine_type
    disk_size_gb = var.training_disk_size_gb
    logging      = "CLOUD_LOGGING_ONLY"
  }

  depends_on = [google_project_service.apis]
}

# Secret for build webhook
resource "google_secret_manager_secret" "build_webhook_secret" {
  secret_id = "build-webhook-secret"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

# Cloud Scheduler for model retraining
resource "google_cloud_scheduler_job" "model_retraining" {
  name             = "model-retraining-schedule"
  description      = "Weekly model retraining schedule"
  schedule         = var.model_retrain_schedule
  time_zone        = "America/Mexico_City"
  attempt_deadline = "1800s" # 30 minutes

  http_target {
    http_method = "POST"
    uri         = "https://cloudbuild.googleapis.com/v1/projects/${var.project_id}/triggers/${google_cloudbuild_trigger.model_training.trigger_id}:webhook"

    body = base64encode(jsonencode({
      message = "Scheduled weekly model retraining"
    }))

    oauth_token {
      service_account_email = google_service_account.cloud_run_sa.email
    }
  }

  depends_on = [google_cloudbuild_trigger.model_training]
}

# Data quality monitoring with timezone awareness
resource "google_monitoring_alert_policy" "data_freshness" {
  display_name = "Steel Data Freshness Alert"
  combiner     = "OR"

  conditions {
    display_name = "LME data not updated after London close"

    condition_absent {
      filter   = "resource.type=\"cloud_function\" AND metric.type=\"cloudfunctions.googleapis.com/function/execution_count\" AND resource.labels.function_name=\"lme-excel-processor\""
      duration = "86400s" # 24 hours

      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_COUNT"
      }
    }
  }

  conditions {
    display_name = "Banxico daily data is stale"

    condition_absent {
      filter   = "resource.type=\"cloud_function\" AND metric.type=\"cloudfunctions.googleapis.com/function/execution_count\" AND resource.labels.function_name=\"banxico-daily-updater\""
      duration = "86400s" # 24 hours

      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_COUNT"
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "86400s"
  }

  depends_on = [google_project_service.apis]
}

# Outputs with corrected information
output "data_staging_bucket" {
  value = google_storage_bucket.data_staging.name
}

output "excel_storage_bucket" {
  value = google_storage_bucket.excel_storage.name
}

output "data_processed_bucket" {
  value = google_storage_bucket.data_processed.name
}

output "bigquery_dataset" {
  value = google_bigquery_dataset.steel_data.dataset_id
}

output "data_update_schedule" {
  value = {
    daily = {
      lme_excel   = "2:00 PM Mexico City (after London close)"
      banxico_api = "8:30 AM Mexico City"
    }
    monthly = {
      banxico_macro = "3rd of month, 10:00 AM"
      epu_excel     = "1st of month, 11:00 AM"
      gas_natural   = "5th of month, 12:00 PM"
    }
    timezone_notes = {
      lme    = "LME closes 17:00 London, data available ~18:00 London (12:00 PM Mexico)"
      mexico = "All schedules in America/Mexico_City timezone"
    }
  }
}

output "data_sources_summary" {
  value = {
    excel_files = {
      lme = ["SR Closing Prices.xlsx", "SC Closing Prices.xlsx"]
      epu = ["Mexico_Policy_Uncertainty_Data.xlsx", "US_Policy_Uncertainty_Data.xlsx", "China_Policy_Uncertainty_Data.xlsx", "ECSU_Index.xls"]
      gas = ["Índice de Precios de Gas Natural.xlsx"]
    }
    api_sources = {
      banxico_daily   = ["SF43718 (USD/MXN)", "SF43783 (TIIE 28d)"]
      banxico_monthly = ["SP1 (INPC)", "SR16734 (IGAE)", "SP74665 (Inflation)"]
    }
  }
}
