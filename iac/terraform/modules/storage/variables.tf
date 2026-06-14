variable "compartment_ocid" {
  type        = string
  description = "Compartment OCID"
}

variable "availability_domain" {
  type        = string
  description = "Availability domain for block volumes"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "tags" {
  type        = map(string)
  description = "Common tags"
}

variable "free_tier_enabled" {
  type        = bool
  description = "Whether to attach volumes to free tier instances"
  default     = true
}

variable "free_tier_instance_ids" {
  type        = map(string)
  description = "Map of service names to free tier instance OCIDs"
  default     = {}
}

