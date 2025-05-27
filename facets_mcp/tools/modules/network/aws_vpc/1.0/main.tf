locals {
  subnet_cird = cidrsubnet(var.instance.spec.vpc_cidr, 4, 0)
}

resource "aws_vpc" "main" {
  cidr_block = var.instance.spec.vpc_cidr
  tags = merge(var.environment.cloud_tags, {
    Name         = "${var.instance_name}-vpc"
    resourceType = "network"
    resourceName = var.instance_name
  })
}

resource "aws_subnet" "main" {
  vpc_id     = aws_vpc.main.id
  cidr_block = local.subnet_cird
  tags = {
    Name         = "${var.instance_name}-subnet"
    resourceType = "network"
    resourceName = var.instance_name
  }
  depends_on = [aws_vpc.main]
}
