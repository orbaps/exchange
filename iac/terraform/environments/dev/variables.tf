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
  description = "Compartment OCID"
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

variable "availability_domain" {
  description = "Availability domain for block volumes"
  type        = string
  default     = ""
}

variable "free_tier_instance_ids" {
  description = "Map of service names to free tier instance OCIDs"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default = {
    project     = "iicpc-platform"
    environment = "dev"
    managed-by  = "terraform"
  }
}
