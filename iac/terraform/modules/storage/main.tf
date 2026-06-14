# TimescaleDB block volume (100 GB free tier allowance per volume)
resource "oci_core_volume" "timescaledb" {
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_ocid
  display_name        = "iicpc-${var.environment}-timescaledb"
  size_in_gbs         = 100
  vpus_per_gb         = 10
  defined_tags        = var.tags
}

# Kafka block volume
resource "oci_core_volume" "kafka" {
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_ocid
  display_name        = "iicpc-${var.environment}-kafka"
  size_in_gbs         = 50
  vpus_per_gb         = 10
  defined_tags        = var.tags
}

# Prometheus block volume
resource "oci_core_volume" "prometheus" {
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_ocid
  display_name        = "iicpc-${var.environment}-prometheus"
  size_in_gbs         = 50
  vpus_per_gb         = 10
  defined_tags        = var.tags
}

# Volume attachments for free tier compute instances
resource "oci_core_volume_attachment" "timescaledb" {
  count           = var.free_tier_enabled ? 1 : 0
  attachment_type = "iscsi"
  instance_id     = var.free_tier_instance_ids["timescaledb"]
  volume_id       = oci_core_volume.timescaledb.id
  display_name    = "iicpc-${var.environment}-timescaledb-attach"
}

resource "oci_core_volume_attachment" "kafka" {
  count           = var.free_tier_enabled ? 1 : 0
  attachment_type = "iscsi"
  instance_id     = var.free_tier_instance_ids["kafka"]
  volume_id       = oci_core_volume.kafka.id
  display_name    = "iicpc-${var.environment}-kafka-attach"
}

resource "oci_core_volume_attachment" "prometheus" {
  count           = var.free_tier_enabled ? 1 : 0
  attachment_type = "iscsi"
  instance_id     = var.free_tier_instance_ids["prometheus"]
  volume_id       = oci_core_volume.prometheus.id
  display_name    = "iicpc-${var.environment}-prometheus-attach"
}

# Backup policy
resource "oci_core_volume_backup_policy_assignment" "timescaledb" {
  asset_id  = oci_core_volume.timescaledb.id
  policy_id = oci_core_volume_backup_policy.daily.id
}

resource "oci_core_volume_backup_policy_assignment" "kafka" {
  asset_id  = oci_core_volume.kafka.id
  policy_id = oci_core_volume_backup_policy.daily.id
}

resource "oci_core_volume_backup_policy_assignment" "prometheus" {
  asset_id  = oci_core_volume.prometheus.id
  policy_id = oci_core_volume_backup_policy.daily.id
}
