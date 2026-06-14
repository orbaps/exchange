# Dev environment - uses Oracle Free Tier ARM instances
# OKE is replaced by manual k3s on free tier compute

module "networking" {
  source = "../../modules/networking"

  compartment_ocid  = var.compartment_ocid
  vcn_cidr          = "10.0.0.0/16"
  public_subnet_cidr  = "10.0.1.0/24"
  private_subnet_cidr = "10.0.2.0/24"
  data_subnet_cidr    = "10.0.3.0/24"
  environment       = "dev"
  tags              = var.tags
}

module "storage" {
  source = "../../modules/storage"

  compartment_ocid     = var.compartment_ocid
  availability_domain  = var.availability_domain
  environment          = "dev"
  free_tier_enabled    = true
  free_tier_instance_ids = var.free_tier_instance_ids
  tags                 = var.tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  compartment_ocid = var.compartment_ocid
  environment      = "dev"
  tags             = var.tags
}

module "security" {
  source = "../../modules/security"

  compartment_ocid = var.compartment_ocid
  environment      = "dev"
  tags             = var.tags
}
