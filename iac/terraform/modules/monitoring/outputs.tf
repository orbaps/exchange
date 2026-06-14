output "notification_topic_id" {
  value = oci_ons_notification_topic.alerts.id
}

output "notification_topic_endpoint" {
  value = oci_ons_notification_topic.alerts.api_endpoint
}

output "log_group_id" {
  value = oci_logging_log_group.services.id
}

output "alarm_ids" {
  value = {
    cpu    = oci_monitoring_alarm.cpu_high.id
    memory = oci_monitoring_alarm.memory_high.id
    disk   = oci_monitoring_alarm.disk_full.id
  }
}
