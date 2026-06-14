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

variable "notification_topic_id" {
  type        = string
  description = "OCID of notification topic for alarms"
  default     = null
}
