output "vault_id" {
  value = oci_kms_vault.this.id
}

output "vault_management_endpoint" {
  value = oci_kms_vault.this.management_endpoint
}

output "block_volume_key_id" {
  value = oci_kms_key.block_volume.id
}

output "cluster_admin_policy_id" {
  value = oci_identity_policy.cluster_admin.id
}

output "monitoring_read_policy_id" {
  value = oci_identity_policy.monitoring_read.id
}

output "service_account_policy_id" {
  value = oci_identity_policy.service_account.id
}
