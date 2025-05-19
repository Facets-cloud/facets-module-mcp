locals {
  // Default values and computed local variables
  ssh_source_cidr = try(var.instance.spec.security_groups.ssh_access.source_cidr, "0.0.0.0/0")
  ssh_key_name    = try(var.instance.spec.security_groups.ssh_access.key_name, "")
  create_key_pair = local.ssh_key_name == ""
  used_key_name   = local.create_key_pair ? "${var.instance_name}-${var.environment.unique_name}-key" : local.ssh_key_name

  // Custom ingress and egress rules processing
  ingress_rules   = try(var.instance.spec.security_groups.ingress_rules.rules, {})
  restrict_egress = try(var.instance.spec.security_groups.egress_rules.restrict_default, false)
  egress_rules    = try(var.instance.spec.security_groups.egress_rules.rules, {})

  // IAM instance profile configuration
  iam_config            = try(var.instance.spec.iam.instance_profile_config, "none")
  use_existing_profile  = local.iam_config == "existing"
  create_new_profile    = local.iam_config == "create_new"
  existing_profile_name = try(var.instance.spec.iam.existing_instance_profile_name, "")

  // Optional policy JSON parsing (default to empty policy if invalid JSON)
  policy_json = try(local.create_new_profile ? jsondecode(var.instance.spec.iam.create_instance_profile.policy_json) : {}, {})
  has_policy  = local.create_new_profile && length(local.policy_json) > 0

  // The instance profile name to use for the EC2 instance
  instance_profile_name = local.use_existing_profile ? local.existing_profile_name : (
    local.create_new_profile ? aws_iam_instance_profile.instance_profile[0].name : null
  )

  // Process custom tags
  custom_tags = try(var.instance.spec.tags, {})
  processed_custom_tags = {
    for tag_id, tag_obj in local.custom_tags :
    tag_obj.key => tag_obj.value
  }

  // Merge tags for EC2 instance
  instance_tags = merge(
    var.environment.cloud_tags,
    {
      Name         = "${var.instance_name}-${var.environment.unique_name}-vm"
      resourceType = "cloud_compute"
      resourceName = var.instance_name
    },
    local.processed_custom_tags
  )

  // Hostname configuration
  hostname = try(var.instance.spec.hostname, "") != "" ? var.instance.spec.hostname : "${var.instance_name}-${var.environment.unique_name}"

  // Enable additional volume if configured
  create_additional_volume = try(var.instance.spec.additional_volumes.enabled, false) && var.instance.spec.additional_volumes != null

  // Additional volume parameters - using required fields directly
  additional_volume_device_name = local.create_additional_volume ? var.instance.spec.additional_volumes.volumes.data_volume.device_name : null
  additional_volume_size        = local.create_additional_volume ? var.instance.spec.additional_volumes.volumes.data_volume.size : null
  additional_volume_type        = local.create_additional_volume ? var.instance.spec.additional_volumes.volumes.data_volume.type : null
  additional_volume_encrypted   = local.create_additional_volume ? try(var.instance.spec.additional_volumes.volumes.data_volume.encrypted, true) : true
}

// Get latest Amazon Linux 2 AMI if no specific AMI is provided
data "aws_ami" "default" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

// Create SSH key pair if not using an existing one and SSH is enabled
resource "tls_private_key" "ssh_key" {
  count     = local.create_key_pair ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "aws_key_pair" "deployer" {
  count      = local.create_key_pair ? 1 : 0
  key_name   = local.used_key_name
  public_key = tls_private_key.ssh_key[0].public_key_openssh
}

// IAM role and instance profile creation if requested
resource "aws_iam_role" "instance_role" {
  count = local.create_new_profile ? 1 : 0
  name  = "${var.instance_name}-${var.environment.unique_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.environment.cloud_tags, {
    Name         = "${var.instance_name}-${var.environment.unique_name}-role"
    resourceType = "cloud_compute"
    resourceName = var.instance_name
  })
}

resource "aws_iam_policy" "instance_policy" {
  count       = local.has_policy ? 1 : 0
  name        = "${var.instance_name}-${var.environment.unique_name}-policy"
  description = "Policy for ${var.instance_name} EC2 instance"
  policy      = var.instance.spec.iam.create_instance_profile.policy_json

  tags = merge(var.environment.cloud_tags, {
    Name         = "${var.instance_name}-${var.environment.unique_name}-policy"
    resourceType = "cloud_compute"
    resourceName = var.instance_name
  })
}

resource "aws_iam_role_policy_attachment" "policy_attachment" {
  count      = local.has_policy ? 1 : 0
  role       = aws_iam_role.instance_role[0].name
  policy_arn = aws_iam_policy.instance_policy[0].arn
}

resource "aws_iam_instance_profile" "instance_profile" {
  count = local.create_new_profile ? 1 : 0
  name  = "${var.instance_name}-${var.environment.unique_name}-profile"
  role  = aws_iam_role.instance_role[0].name
}

// Security group for EC2 instance
resource "aws_security_group" "instance_sg" {
  name        = "${var.instance_name}-${var.environment.unique_name}-sg"
  description = "Security group for ${var.instance_name} EC2 instance"
  vpc_id      = var.inputs.network_details.vpc_id

  // SSH access is always enabled by default
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [local.ssh_source_cidr]
    description = "SSH access"
  }

  // Custom ingress rules
  dynamic "ingress" {
    for_each = local.ingress_rules
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = split(",", ingress.value.cidr_blocks)
      description = ingress.value.description
    }
  }

  // Default egress rule if not restricted
  dynamic "egress" {
    for_each = local.restrict_egress ? [] : [1]
    content {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
      description = "Allow all outbound traffic"
    }
  }

  // Custom egress rules if restriction is enabled
  dynamic "egress" {
    for_each = local.restrict_egress ? local.egress_rules : {}
    content {
      from_port   = egress.value.from_port
      to_port     = egress.value.to_port
      protocol    = egress.value.protocol
      cidr_blocks = split(",", egress.value.cidr_blocks)
      description = egress.value.description
    }
  }

  tags = merge(var.environment.cloud_tags, {
    Name         = "${var.instance_name}-${var.environment.unique_name}-sg"
    resourceType = "cloud_compute"
    resourceName = var.instance_name
  })
}

// Additional EBS volume if enabled
resource "aws_ebs_volume" "additional_volume" {
  count             = local.create_additional_volume ? 1 : 0
  availability_zone = aws_instance.vm.availability_zone
  size              = local.additional_volume_size
  type              = local.additional_volume_type
  encrypted         = local.additional_volume_encrypted

  tags = merge(var.environment.cloud_tags, {
    Name         = "${var.instance_name}-${var.environment.unique_name}-data-volume"
    resourceType = "cloud_compute"
    resourceName = var.instance_name
  })
}

// Attach additional volume if enabled
resource "aws_volume_attachment" "additional_volume_attachment" {
  count       = local.create_additional_volume ? 1 : 0
  device_name = local.additional_volume_device_name
  volume_id   = aws_ebs_volume.additional_volume[0].id
  instance_id = aws_instance.vm.id

  # Force detach to avoid Terraform errors when rebuilding the instance
  skip_destroy = false
  force_detach = true
}

// EC2 instance
resource "aws_instance" "vm" {
  ami                    = var.instance.spec.ami_id != "" ? var.instance.spec.ami_id : data.aws_ami.default.id
  instance_type          = var.instance.spec.instance_type
  subnet_id              = var.inputs.network_details.subnet_id
  vpc_security_group_ids = [aws_security_group.instance_sg.id]
  key_name               = local.used_key_name

  // IAM instance profile if enabled
  iam_instance_profile = local.instance_profile_name

  // Networking options
  associate_public_ip_address = try(var.instance.spec.associate_public_ip, true)
  monitoring                  = try(var.instance.spec.enable_detailed_monitoring, false)

  // Hostname and user data configuration
  user_data = try(var.instance.spec.user_data, "") != "" ? var.instance.spec.user_data : <<-EOF
    #!/bin/bash
    hostnamectl set-hostname ${local.hostname}
    echo "127.0.0.1 ${local.hostname}" >> /etc/hosts
  EOF

  // Root volume configuration with required fields
  root_block_device {
    volume_size = var.instance.spec.root_volume_size
    volume_type = var.instance.spec.root_volume_type
    encrypted   = true
    tags = merge(var.environment.cloud_tags, {
      Name         = "${var.instance_name}-${var.environment.unique_name}-root-volume"
      resourceType = "cloud_compute"
      resourceName = var.instance_name
    })
  }

  // Tags
  tags = local.instance_tags

  // Wait for the instance to be created before proceeding
  lifecycle {
    create_before_destroy = true
  }

  // Make sure IAM resources are created before the instance
  depends_on = [
    aws_iam_instance_profile.instance_profile,
    aws_iam_role_policy_attachment.policy_attachment
  ]
}