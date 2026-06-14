output "timescaledb_volume_id" {
  value = oci_core_volume.timescaledb.id
}

output "kafka_volume_id" {
  value = oci_core_volume.kafka.id
}

output "prometheus_volume_id" {
  value = oci_core_volume.prometheus.id
}

output "timescaledb_volume_attachment_id" {
  value = try(oci_core_volume_attachment.timescaledb[0].id, null)
}

output "kafka_volume_attachment_id" {
  value = try(oci_core_volume_attachment.kafka[0].id, null)
}

output "prometheus_volume_attachment_id" {
  value = try(oci_core_volume_attachment.prometheus[0].id, null)
}
