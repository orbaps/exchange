module "networking" {
  source = "./modules/networking"

  compartment_ocid  = var.compartment_ocid
  vcn_cidr          = var.vcn_cidr
  public_subnet_cidr  = var.public_subnet_cidr
  private_subnet_cidr = var.private_subnet_cidr
  data_subnet_cidr    = var.data_subnet_cidr
  environment       = var.environment
  tags              = merge(var.tags, { environment = var.environment })
}

module "kubernetes" {
  count = var.free_tier_arm_instances ? 0 : 1

  source = "./modules/kubernetes"

  compartment_ocid    = var.compartment_ocid
  cluster_name        = var.cluster_name
  kubernetes_version  = var.kubernetes_version
  vcn_id              = module.networking.vcn_id
  public_subnet_id    = module.networking.public_subnet_id
  private_subnet_id   = module.networking.private_subnet_id
  node_pool_shape     = var.node_pool_shape
  node_pool_ocpus     = var.node_pool_ocpus
  node_pool_memory_gb = var.node_pool_memory_gb
  node_pool_size      = var.node_pool_size
  environment         = var.environment
  tags                = merge(var.tags, { environment = var.environment })
}

module "storage" {
  source = "./modules/storage"

  compartment_ocid     = var.compartment_ocid
  availability_domain  = var.availability_domain
  environment          = var.environment
  free_tier_enabled    = var.free_tier_arm_instances
  free_tier_instance_ids = var.free_tier_instance_ids
  tags                 = merge(var.tags, { environment = var.environment })
}

module "monitoring" {
  source = "./modules/monitoring"

  compartment_ocid = var.compartment_ocid
  environment      = var.environment
  tags             = merge(var.tags, { environment = var.environment })
}

module "security" {
  source = "./modules/security"

  compartment_ocid = var.compartment_ocid
  environment      = var.environment
  tags             = merge(var.tags, { environment = var.environment })
}

module "backup" {
  count = var.free_tier_arm_instances ? 0 : 1

  source = "./modules/backup"

  compartment_ocid = var.compartment_ocid
  environment      = var.environment
  log_group_id     = module.monitoring.log_group_id
  tags             = merge(var.tags, { environment = var.environment })
}
