variable "compartment_ocid" {
  type        = string
  description = "Compartment OCID"
}

variable "cluster_name" {
  type        = string
  description = "OKE cluster name"
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version"
}

variable "vcn_id" {
  type        = string
  description = "VCN OCID"
}

variable "public_subnet_id" {
  type        = string
  description = "Public subnet for load balancers"
}

variable "private_subnet_id" {
  type        = string
  description = "Private subnet for worker nodes"
}

variable "node_pool_shape" {
  type        = string
  description = "Instance shape for node pool"
}

variable "node_pool_ocpus" {
  type        = number
  description = "OCPUs per node"
}

variable "node_pool_memory_gb" {
  type        = number
  description = "Memory in GB per node"
}

variable "node_pool_size" {
  type        = number
  description = "Number of worker nodes"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "tags" {
  type        = map(string)
  description = "Common tags"
}
