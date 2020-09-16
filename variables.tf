variable "aws_region" {
  description = "The AWS region to create things in."
  default     = "us-west-2"
}
variable "name" {
  default     = null
  description = "Resource name"
  type        = string
}
variable "tags" {
  default     = {}
  description = "A map of tags to add to all resources"
  type        = map(string)
}
variable "enabled" {
  default     = true
  description = "Set to `false` to prevent the module from creating resources"
  type        = bool
}
