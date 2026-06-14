# Notification topic
resource "oci_ons_notification_topic" "alerts" {
  compartment_id = var.compartment_ocid
  name           = "iicpc-${var.environment}-alerts"
  description    = "Alert notifications for IICPC ${var.environment}"
  defined_tags   = var.tags
}

# CPU utilization alarm
resource "oci_monitoring_alarm" "cpu_high" {
  compartment_id          = var.compartment_ocid
  display_name            = "iicpc-${var.environment}-cpu-high"
  body                    = "CPU utilization exceeded 80% for 15 minutes"
  severity                = "WARNING"
  metric_compartment_id   = var.compartment_ocid
  namespace               = "oci_computeagent"
  query                   = "CpuUtilization[1m].mean() > 80"
  resolution              = "1m"
  pending_duration        = "PT15M"
  notification_destination = var.notification_topic_id != null ? var.notification_topic_id : oci_ons_notification_topic.alerts.id
  is_enabled              = true
  defined_tags            = var.tags
}

# Memory utilization alarm
resource "oci_monitoring_alarm" "memory_high" {
  compartment_id          = var.compartment_ocid
  display_name            = "iicpc-${var.environment}-memory-high"
  body                    = "Memory utilization exceeded 85% for 15 minutes"
  severity                = "WARNING"
  metric_compartment_id   = var.compartment_ocid
  namespace               = "oci_computeagent"
  query                   = "MemoryUtilization[1m].mean() > 85"
  resolution              = "1m"
  pending_duration        = "PT15M"
  notification_destination = var.notification_topic_id != null ? var.notification_topic_id : oci_ons_notification_topic.alerts.id
  is_enabled              = true
  defined_tags            = var.tags
}

# Block volume utilization alarm
resource "oci_monitoring_alarm" "disk_full" {
  compartment_id          = var.compartment_ocid
  display_name            = "iicpc-${var.environment}-disk-high"
  body                    = "Disk utilization exceeded 85% for 30 minutes"
  severity                = "CRITICAL"
  metric_compartment_id   = var.compartment_ocid
  namespace               = "oci_blockstore"
  query                   = "VolumeUtilization[1m].mean() > 85"
  resolution              = "1m"
  pending_duration        = "PT30M"
  notification_destination = var.notification_topic_id != null ? var.notification_topic_id : oci_ons_notification_topic.alerts.id
  is_enabled              = true
  defined_tags            = var.tags
}

# Logging - service log group
resource "oci_logging_log_group" "services" {
  compartment_id = var.compartment_ocid
  display_name   = "iicpc-${var.environment}-services"
  description    = "Logs for IICPC microservices"
  defined_tags   = var.tags
}
