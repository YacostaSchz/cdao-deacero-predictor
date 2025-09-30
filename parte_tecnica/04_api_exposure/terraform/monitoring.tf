# Monitoring and Observability for Steel Price Predictor
# Implements the "Optional but Valued" features

# Enable monitoring dashboard feature flag check
locals {
  enable_dashboard = var.enable_monitoring_dashboard
  enable_ab_test   = var.enable_a_b_testing
  enable_explain   = var.enable_explainability
}

# Custom monitoring dashboard
resource "google_monitoring_dashboard" "steel_predictor" {
  count = local.enable_dashboard ? 1 : 0

  display_name = "Steel Price Predictor Dashboard"
  project      = var.project_id

  dashboard_json = jsonencode({
    displayName = "Steel Price Predictor Dashboard"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          # API Response Time (p95)
          width  = 6
          height = 4
          widget = {
            title = "API Response Time (p95)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_PERCENTILE_95"
                      crossSeriesReducer = "REDUCE_MEAN"
                      groupByFields      = ["resource.service_name"]
                    }
                  }
                }
                plotType = "LINE"
              }]
              yAxis = {
                label = "Latency (ms)"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          # Prediction Accuracy (MAPE)
          width  = 6
          height = 4
          xPos   = 6
          widget = {
            title = "Model Accuracy (MAPE)"
            scorecard = {
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"custom.googleapis.com/steel_predictor/mape\""
                  aggregation = {
                    alignmentPeriod  = "3600s"
                    perSeriesAligner = "ALIGN_MEAN"
                  }
                }
              }
              sparkChartView = {
                sparkChartType = "SPARK_LINE"
              }
              thresholds = [
                {
                  value = 5
                  color = "GREEN"
                },
                {
                  value = 10
                  color = "YELLOW"
                },
                {
                  value = 15
                  color = "RED"
                }
              ]
            }
          }
        },
        {
          # Request Count
          width  = 4
          height = 4
          yPos   = 4
          widget = {
            title = "API Requests (per minute)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
                plotType = "STACKED_AREA"
              }]
            }
          }
        },
        {
          # Error Rate
          width  = 4
          height = 4
          xPos   = 4
          yPos   = 4
          widget = {
            title = "Error Rate (%)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class!=\"2xx\""
                    aggregation = {
                      alignmentPeriod  = "300s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
                plotType = "LINE"
              }]
              yAxis = {
                scale = "LINEAR"
              }
            }
          }
        },
        {
          # Data Freshness
          width  = 4
          height = 4
          xPos   = 8
          yPos   = 4
          widget = {
            title = "Data Freshness Status"
            scorecard = {
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"custom.googleapis.com/steel_predictor/data_age_hours\""
                  aggregation = {
                    alignmentPeriod  = "300s"
                    perSeriesAligner = "ALIGN_MAX"
                  }
                }
              }
              thresholds = [
                {
                  value = 24
                  color = "GREEN"
                },
                {
                  value = 48
                  color = "YELLOW"
                },
                {
                  value = 72
                  color = "RED"
                }
              ]
            }
          }
        },
        {
          # Cost Tracking
          width  = 6
          height = 4
          yPos   = 8
          widget = {
            title = "Daily Cost Tracking"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"global\" AND metric.type=\"billing.googleapis.com/project/cost\""
                    aggregation = {
                      alignmentPeriod  = "86400s" # Daily
                      perSeriesAligner = "ALIGN_SUM"
                    }
                  }
                }
                plotType = "STACKED_BAR"
              }]
              yAxis = {
                label = "Cost (USD)"
              }
            }
          }
        },
        {
          # A/B Test Performance (if enabled)
          width  = 6
          height = 4
          xPos   = 6
          yPos   = 8
          widget = {
            title = "A/B Model Performance"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"custom.googleapis.com/steel_predictor/model_mape\" AND metric.labels.model_version=\"v1\""
                      aggregation = {
                        alignmentPeriod  = "3600s"
                        perSeriesAligner = "ALIGN_MEAN"
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                },
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "metric.type=\"custom.googleapis.com/steel_predictor/model_mape\" AND metric.labels.model_version=\"v2\""
                      aggregation = {
                        alignmentPeriod  = "3600s"
                        perSeriesAligner = "ALIGN_MEAN"
                      }
                    }
                  }
                  plotType   = "LINE"
                  targetAxis = "Y1"
                }
              ]
            }
          }
        }
      ]
    }
  })

  depends_on = [google_project_service.apis]
}

# Custom metrics for model performance
resource "google_logging_metric" "mape_metric" {
  name   = "steel_predictor_mape"
  filter = "resource.type=\"cloud_run_revision\" AND jsonPayload.metric_type=\"mape\""

  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "DOUBLE"
    unit        = "1" # Percentage

    labels {
      key         = "model_version"
      value_type  = "STRING"
      description = "Version of the model"
    }
  }

  value_extractor = "EXTRACT(jsonPayload.mape_value)"

  label_extractors = {
    "model_version" = "EXTRACT(jsonPayload.model_version)"
  }
}

# Custom metrics for data freshness
resource "google_logging_metric" "data_freshness_metric" {
  name   = "steel_predictor_data_freshness"
  filter = "resource.type=\"cloud_run_revision\" AND jsonPayload.metric_type=\"data_freshness\""

  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "INT64"
    unit        = "h" # Hours

    labels {
      key         = "data_source"
      value_type  = "STRING"
      description = "Source of the data"
    }
  }

  value_extractor = "EXTRACT(jsonPayload.hours_since_update)"

  label_extractors = {
    "data_source" = "EXTRACT(jsonPayload.data_source)"
  }
}

# Alert for model performance degradation
resource "google_monitoring_alert_policy" "model_performance_alert" {
  display_name = "Steel Predictor Model Performance Alert"
  combiner     = "OR"

  conditions {
    display_name = "MAPE exceeds threshold"

    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/steel_predictor_mape\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10 # Alert if MAPE > 10%

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.notification_channels

  documentation {
    content = "Model MAPE has exceeded 10%. Check for data quality issues or model drift."
  }

  alert_strategy {
    auto_close = "86400s"
  }
}

# SLO for API availability
resource "google_monitoring_slo" "api_availability" {
  service      = google_monitoring_service.steel_predictor_service.service_id
  display_name = "99.5% Availability SLO"

  goal                = 0.995
  rolling_period_days = 30

  request_based_sli {
    good_total_ratio {
      good_service_filter  = "metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"2xx\""
      total_service_filter = "metric.type=\"run.googleapis.com/request_count\""
    }
  }
}

# Service for SLO
resource "google_monitoring_service" "steel_predictor_service" {
  service_id   = "steel-predictor-api"
  display_name = "Steel Predictor API Service"

  basic_service {
    service_type = "CLOUD_RUN"
    service_labels = {
      service_name = google_cloud_run_service.steel_predictor.name
      location     = var.region
    }
  }
}

# Budget alert
resource "google_billing_budget" "monthly_budget" {
  billing_account = var.billing_account_id
  display_name    = "Steel Predictor Monthly Budget"

  budget_filter {
    projects = ["projects/${var.project_id}"]
    services = [
      "run.googleapis.com",
      "storage.googleapis.com",
      "bigquery.googleapis.com",
      "cloudfunctions.googleapis.com"
    ]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = "4" # $4 to stay under $5 limit
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }

  threshold_rules {
    threshold_percent = 0.8
  }

  threshold_rules {
    threshold_percent = 1.0
  }

  all_updates_rule {
    monitoring_notification_channels = var.notification_channels
  }
}

# Notification channel for alerts
resource "google_monitoring_notification_channel" "email" {
  display_name = "Steel Predictor Email Alerts"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}

# Uptime check for API health
resource "google_monitoring_uptime_check_config" "api_health" {
  display_name = "Steel Predictor API Health"
  timeout      = "10s"
  period       = "300s" # 5 minutes

  http_check {
    path         = "/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true

    accepted_response_status_codes {
      status_class = "STATUS_CLASS_2XX"
    }
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = google_cloud_run_service.steel_predictor.status[0].url
    }
  }

  content_matchers {
    content = "\"status\":\"healthy\""
    matcher = "CONTAINS_STRING"
  }
}

# Log sink for long-term storage
resource "google_logging_project_sink" "prediction_logs" {
  name        = "steel-predictor-predictions"
  destination = "storage.googleapis.com/${google_storage_bucket.log_archive.name}"

  filter = "resource.type=\"cloud_run_revision\" AND jsonPayload.log_type=\"prediction\""

  unique_writer_identity = true
}

# Bucket for log archival
resource "google_storage_bucket" "log_archive" {
  name          = "${var.project_id}-prediction-logs"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 365 # Keep logs for 1 year
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

# Grant log sink permission to write
resource "google_storage_bucket_iam_binding" "log_sink_writer" {
  bucket = google_storage_bucket.log_archive.name
  role   = "roles/storage.objectCreator"

  members = [
    google_logging_project_sink.prediction_logs.writer_identity
  ]
}

# Output dashboard URL
output "monitoring_dashboard_url" {
  value = local.enable_dashboard ? "https://console.cloud.google.com/monitoring/dashboards/custom/${google_monitoring_dashboard.steel_predictor[0].id}?project=${var.project_id}" : "Dashboard not enabled"
}

# Output alert policies
output "alert_policies" {
  value = {
    latency           = google_monitoring_alert_policy.latency_alert.name
    data_freshness    = google_monitoring_alert_policy.data_freshness.name
    model_performance = google_monitoring_alert_policy.model_performance_alert.name
  }
}

