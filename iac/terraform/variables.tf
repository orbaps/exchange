variable "region" {
  description = "OCI region"
  type        = string
  default     = "us-ashburn-1"
}

variable "tenancy_ocid" {
  description = "Tenancy OCID"
  type        = string
  sensitive   = true
}

variable "user_ocid" {
  description = "User OCID"
  type        = string
  sensitive   = true
}

variable "fingerprint" {
  description = "API key fingerprint"
  type        = string
  sensitive   = true
}

variable "private_key_path" {
  description = "Path to private API key"
  type        = string
  default     = "~/.oci/oci_api_key.pem"
}

variable "compartment_ocid" {
  description = "Compartment OCID for all resources"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "vcn_cidr" {
  description = "VCN CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "Private subnet CIDR"
  type        = string
  default     = "10.0.2.0/24"
}

variable "data_subnet_cidr" {
  description = "Data subnet CIDR (databases, message queues)"
  type        = string
  default     = "10.0.3.0/24"
}

variable "cluster_name" {
  description = "OKE cluster name"
  type        = string
  default     = "iicpc-platform"
}

variable "kubernetes_version" {
  description = "OKE Kubernetes version"
  type        = string
  default     = "v1.28.2"
}

variable "node_pool_shape" {
  description = "OKE node pool shape"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "node_pool_ocpus" {
  description = "OCPUs per node"
  type        = number
  default     = 2
}

variable "node_pool_memory_gb" {
  description = "Memory in GB per node"
  type        = number
  default     = 16
}

variable "node_pool_size" {
  description = "Number of worker nodes"
  type        = number
  default     = 3
}

variable "free_tier_arm_instances" {
  description = "Use Always Free ARM instances instead of OKE"
  type        = bool
  default     = true
}

variable "availability_domain" {
  description = "Availability domain for block volumes (required when free_tier_arm_instances = true)"
  type        = string
  default     = ""
}

variable "free_tier_instance_ids" {
  description = "Map of service names to free tier instance OCIDs for volume attachments"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    project     = "iicpc-platform"
    managed-by  = "terraform"
  }
}
