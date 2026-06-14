# Daily backup policy
resource "oci_core_volume_backup_policy" "daily" {
  compartment_id = var.compartment_ocid
  display_name   = "iicpc-${var.environment}-daily-backup"
  defined_tags   = var.tags
  schedules {
    backup_type       = "FULL"
    day_of_week       = "SUNDAY"
    hour_of_day       = 2
    offset_seconds    = 0
    period            = "ONE_WEEK"
    retention_seconds = 2592000
    time_zone         = "UTC"
  }
  schedules {
    backup_type       = "INCREMENTAL"
    hour_of_day       = 2
    offset_seconds    = 0
    period            = "ONE_DAY"
    retention_seconds = 604800
    time_zone         = "UTC"
  }
}

# Object Storage bucket for cluster state
resource "oci_objectstorage_bucket" "cluster_state" {
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.this.namespace
  name           = "iicpc-${var.environment}-cluster-state"
  access_type    = "NoPublicAccess"
  storage_tier   = "Standard"
  defined_tags   = var.tags
}

data "oci_objectstorage_namespace" "this" {
  compartment_id = var.compartment_ocid
}

# Backup schedule for cluster state
resource "oci_sch_service_connector" "cluster_backup" {
  compartment_id = var.compartment_ocid
  display_name   = "iicpc-${var.environment}-cluster-backup"
  source {
    kind = "logging"
    log_sources {
      log_group_id = var.log_group_id
    }
  }
  target {
    kind       = "objectstorage"
    bucket     = oci_objectstorage_bucket.cluster_state.name
    namespace  = data.oci_objectstorage_namespace.this.namespace
    batch_size = 100
  }
  defined_tags = var.tags
}
