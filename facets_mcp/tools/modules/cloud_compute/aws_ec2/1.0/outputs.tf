locals {
  output_attributes = {
    vpc_id      = var.inputs.network_details.vpc_id
    subnet_id   = var.inputs.network_details.subnet_id
    instance_id = aws_instance.vm.id
    public_ip   = aws_instance.vm.public_ip
    private_ip  = aws_instance.vm.private_ip
    hostname    = local.hostname
    custom_tags = local.processed_custom_tags
    secrets     = ["ssh"]
    ssh = {
      host        = aws_instance.vm.public_ip
      port        = 22
      user        = "ec2-user"
      public_key  = local.create_key_pair ? tls_private_key.ssh_key[0].public_key_openssh : null
      private_key = local.create_key_pair ? sensitive(base64encode(tls_private_key.ssh_key[0].private_key_pem)) : null
    }
    instance_details = {
      instance_type        = var.instance.spec.instance_type
      root_volume_size     = var.instance.spec.root_volume_size
      root_volume_type     = var.instance.spec.root_volume_type
      security_group_id    = aws_security_group.instance_sg.id
      iam_role             = local.create_new_profile ? aws_iam_role.instance_role[0].name : null
      iam_enabled          = local.iam_config != "none"
      ssh_enabled          = true
      additional_volumes   = local.create_additional_volume
      monitoring_enabled   = try(var.instance.spec.enable_detailed_monitoring, false)
      iam_instance_profile = local.instance_profile_name
      public_ip_associated = try(var.instance.spec.associate_public_ip, true)
    }
  }
  output_interfaces = {
  }
}