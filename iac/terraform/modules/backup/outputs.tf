output "daily_backup_policy_id" {
  value = oci_core_volume_backup_policy.daily.id
}

output "cluster_state_bucket" {
  value = oci_objectstorage_bucket.cluster_state.name
}
