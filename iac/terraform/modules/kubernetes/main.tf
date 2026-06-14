# OKE Cluster
resource "oci_containerengine_cluster" "this" {
  compartment_id     = var.compartment_ocid
  name               = "${var.cluster_name}-${var.environment}"
  kubernetes_version = var.kubernetes_version
  vcn_id             = var.vcn_id
  image_policy_config {
    is_policy_enabled = false
  }
  options {
    service_lb_subnet_ids = [var.public_subnet_id]
    add_ons {
      is_kubernetes_dashboard_enabled = false
      is_tiller_enabled               = false
    }
    kubernetes_network_config {
      pods_cidr     = "10.244.0.0/16"
      services_cidr = "10.96.0.0/16"
    }
  }
  defined_tags = var.tags
}

# Node Pool
resource "oci_containerengine_node_pool" "this" {
  compartment_id     = var.compartment_ocid
  cluster_id         = oci_containerengine_cluster.this.id
  name               = "${var.cluster_name}-${var.environment}-pool"
  kubernetes_version = var.kubernetes_version
  node_source_details {
    source_type = "IMAGE"
    image_id    = data.oci_core_images.olk.images[0].id
  }
  node_shape = var.node_pool_shape
  node_shape_config {
    ocpus         = var.node_pool_ocpus
    memory_in_gbs = var.node_pool_memory_gb
  }
  node_config_details {
    size = var.node_pool_size
    placement_configs {
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
      subnet_id           = var.private_subnet_id
    }
    placement_configs {
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[1].name
      subnet_id           = var.private_subnet_id
    }
  }
  defined_tags = var.tags
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

data "oci_core_images" "olk" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.node_pool_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}
