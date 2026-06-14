output "vcn_id" {
  description = "VCN OCID"
  value       = module.networking.vcn_id
}

output "cluster_id" {
  description = "OKE cluster OCID (null if using free tier)"
  value       = try(module.kubernetes[0].cluster_id, null)
}

output "cluster_kubeconfig" {
  description = "Kubeconfig for cluster access"
  value       = try(module.kubernetes[0].kubeconfig, "Use Kind locally (see KIND_CLUSTER.md)")
  sensitive   = true
}

output "storage_volume_ids" {
  description = "Block volume OCIDs"
  value = {
    timescaledb = module.storage.timescaledb_volume_id
    kafka       = module.storage.kafka_volume_id
    prometheus  = module.storage.prometheus_volume_id
  }
}

output "storage_volume_attachment_ids" {
  description = "Block volume attachment OCIDs"
  value = {
    timescaledb = module.storage.timescaledb_volume_attachment_id
    kafka       = module.storage.kafka_volume_attachment_id
    prometheus  = module.storage.prometheus_volume_attachment_id
  }
}

output "backup_policy_id" {
  description = "Daily backup policy OCID (null if using free tier)"
  value       = try(module.backup[0].daily_backup_policy_id, null)
}

output "cluster_state_bucket" {
  description = "Object Storage bucket for cluster state (null if using free tier)"
  value       = try(module.backup[0].cluster_state_bucket, null)
}

output "notification_topic_id" {
  description = "Monitoring notification topic OCID"
  value       = module.monitoring.notification_topic_id
}

output "log_group_id" {
  description = "Log group OCID"
  value       = module.monitoring.log_group_id
}

output "alarm_ids" {
  description = "Monitoring alarm OCIDs"
  value       = module.monitoring.alarm_ids
}

output "compartment_id" {
  description = "Compartment OCID"
  value       = var.compartment_ocid
}

output "region" {
  description = "Deployment region"
  value       = var.region
}
