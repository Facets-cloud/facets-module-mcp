locals {
  output_interfaces = {}
  output_attributes = {
    vpc_id    = aws_vpc.main.id
    subnet_id = aws_subnet.main.id
  }
}
