variable "compartment_ocid" {
  type        = string
  description = "Compartment OCID"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "tags" {
  type        = map(string)
  description = "Common tags"
}
