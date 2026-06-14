# Staging environment - uses OKE with managed node pool

module "networking" {
  source = "../../modules/networking"

  compartment_ocid  = var.compartment_ocid
  vcn_cidr          = "10.0.0.0/16"
  public_subnet_cidr  = "10.0.1.0/24"
  private_subnet_cidr = "10.0.2.0/24"
  data_subnet_cidr    = "10.0.3.0/24"
  environment       = "staging"
  tags              = var.tags
}

module "kubernetes" {
  source = "../../modules/kubernetes"

  compartment_ocid  = var.compartment_ocid
  cluster_name      = "iicpc-platform"
  kubernetes_version = var.kubernetes_version
  vcn_id            = module.networking.vcn_id
  public_subnet_id  = module.networking.public_subnet_id
  private_subnet_id = module.networking.private_subnet_id
  node_pool_shape   = "VM.Standard.E4.Flex"
  node_pool_ocpus   = 2
  node_pool_memory_gb = 16
  node_pool_size    = 2
  environment       = "staging"
  tags              = var.tags
}

module "storage" {
  source = "../../modules/storage"

  compartment_ocid    = var.compartment_ocid
  availability_domain = var.availability_domain
  environment         = "staging"
  free_tier_enabled   = false
  tags                = var.tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  compartment_ocid = var.compartment_ocid
  environment      = "staging"
  tags             = var.tags
}

module "security" {
  source = "../../modules/security"

  compartment_ocid = var.compartment_ocid
  environment      = "staging"
  tags             = var.tags
}

module "backup" {
  source = "../../modules/backup"

  compartment_ocid = var.compartment_ocid
  environment      = "staging"
  log_group_id     = module.monitoring.log_group_id
  tags             = var.tags
}
