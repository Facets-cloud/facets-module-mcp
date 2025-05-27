variable "instance" {
  description = "A Network is a way of communication between devices. Adds network of AWS VPC flavor."
  type = object({
    kind    = string,
    flavor  = string,
    version = string,
    spec = object({
      vpc_cidr = string,
    }),
  })
}
variable "instance_name" {
  description = "The architectural name for the resource as added in the Facets blueprint designer."
  type        = string
}
variable "environment" {
  description = "An object containing details about the environment."
  type = object({
    name        = string,
    unique_name = string,
    cloud_tags  = map(string),
  })
}
variable "inputs" {
  description = "A map of inputs requested by the module developer."
  type = object({
    cloud_account_details = object({})
  })
}
