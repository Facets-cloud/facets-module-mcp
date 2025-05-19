# Network Module

This module provisions an AWS Virtual Private Cloud (VPC) and subnet with configurable CIDR blocks. Requires `@outputs/cloud_account` type as input and uses custom providers exposed by it.

## Functionality

- Creates a VPC with a specified CIDR block.
- Creates a subnet with in the VPC created as part of this module.

## Configurability

| Name     | Description                        | Type   | Default | Required |
| -------- | ---------------------------------- | ------ | ------- | -------- |
| vpc_cidr | CIDR block of mask /16 for the VPC | string | n/a     | yes      |

## Outputs

| Name      | Description                             |
| --------- | --------------------------------------- |
| vpc_id    | The ID of the created VPC               |
| subnet_id | ID of the subnet created within the VPC |
