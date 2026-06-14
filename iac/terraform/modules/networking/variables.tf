variable "compartment_ocid" {
  type        = string
  description = "Compartment OCID"
}

variable "vcn_cidr" {
  type        = string
  description = "VCN CIDR block"
}

variable "public_subnet_cidr" {
  type        = string
  description = "Public subnet CIDR"
}

variable "private_subnet_cidr" {
  type        = string
  description = "Private subnet CIDR"
}

variable "data_subnet_cidr" {
  type        = string
  description = "Data subnet CIDR"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "tags" {
  type        = map(string)
  description = "Common tags"
}
