import os
import tempfile
import shutil
from facets_mcp.utils.yaml_utils import validate_no_provider_blocks

def test_validate_no_provider_blocks_error():
    temp_dir = tempfile.mkdtemp()
    try:
        tf_file = os.path.join(temp_dir, "main.tf")
        with open(tf_file, "w") as f:
            f.write('provider "aws" {\n  region = "us-west-2"\n}')
        success, message = validate_no_provider_blocks(temp_dir, temp_dir)
        assert not success
        assert "Provider blocks are not allowed" in message
        assert "main.tf" in message
    finally:
        shutil.rmtree(temp_dir)

def test_validate_no_provider_blocks_success():
    temp_dir = tempfile.mkdtemp()
    try:
        tf_file = os.path.join(temp_dir, "main.tf")
        with open(tf_file, "w") as f:
            f.write('resource "aws_instance" "example" {\n  ami = "ami-123"\n}')
        success, message = validate_no_provider_blocks(temp_dir, temp_dir)
        assert success
        assert "No provider blocks found" in message
    finally:
        shutil.rmtree(temp_dir) 