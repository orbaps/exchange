# Vault for encryption keys and secrets
resource "oci_kms_vault" "this" {
  compartment_id = var.compartment_ocid
  display_name   = "iicpc-${var.environment}-vault"
  vault_type     = "DEFAULT"
  defined_tags   = var.tags
}

# Encryption key for block volumes
resource "oci_kms_key" "block_volume" {
  compartment_id = var.compartment_ocid
  display_name   = "iicpc-${var.environment}-bv-key"
  key_shape {
    algorithm = "AES"
    length    = 32
  }
  protection_mode = "SOFTWARE"
  defined_tags    = var.tags
  management_endpoint = oci_kms_vault.this.management_endpoint
}

# IAM policy for cluster management
resource "oci_identity_policy" "cluster_admin" {
  compartment_id = var.compartment_ocid
  name           = "iicpc-${var.environment}-cluster-admin"
  description    = "Policy for managing OKE cluster and related resources"
  statements = [
    "Allow group iicpc-${var.environment}-admins to manage clusters in compartment id ${var.compartment_ocid}",
    "Allow group iicpc-${var.environment}-admins to manage cluster-node-pools in compartment id ${var.compartment_ocid}",
    "Allow group iicpc-${var.environment}-admins to manage instances in compartment id ${var.compartment_ocid}",
    "Allow group iicpc-${var.environment}-admins to manage volumes in compartment id ${var.compartment_ocid}",
    "Allow group iicpc-${var.environment}-admins to read objectstorage-buckets in compartment id ${var.compartment_ocid}",
  ]
}

# IAM policy for read-only monitoring
resource "oci_identity_policy" "monitoring_read" {
  compartment_id = var.compartment_ocid
  name           = "iicpc-${var.environment}-monitoring-read"
  description    = "Read-only access for monitoring"
  statements = [
    "Allow group iicpc-${var.environment}-readers to read all-resources in compartment id ${var.compartment_ocid}",
  ]
}

# IAM policy for service account
resource "oci_identity_policy" "service_account" {
  compartment_id = var.compartment_ocid
  name           = "iicpc-${var.environment}-service-acct"
  description    = "Permissions for the IICPC platform service account"
  statements = [
    "Allow dynamic-group iicpc-${var.environment}-dynamic-group to manage objects in compartment id ${var.compartment_ocid} where target.bucket.name = 'iicpc-${var.environment}-*'",
    "Allow dynamic-group iicpc-${var.environment}-dynamic-group to use ons-topics in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group iicpc-${var.environment}-dynamic-group to read metrics in compartment id ${var.compartment_ocid}",
  ]
}
