import os
import tempfile
import shutil
from facets_mcp.utils.file_utils import contains_provider_block, find_provider_blocks_in_directory

def test_contains_provider_block_positive():
    tf_content = 'provider "aws" {\n  region = "us-west-2"\n}'
    assert contains_provider_block(tf_content) is True

def test_contains_provider_block_negative():
    tf_content = 'resource "aws_instance" "example" {\n  ami = "ami-123"\n}'
    assert contains_provider_block(tf_content) is False

def test_find_provider_blocks_in_directory():
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a .tf file with a provider block
        tf_file1 = os.path.join(temp_dir, "main.tf")
        with open(tf_file1, "w") as f:
            f.write('provider "aws" {\n  region = "us-west-2"\n}')
        # Create a .tf file without a provider block
        tf_file2 = os.path.join(temp_dir, "other.tf")
        with open(tf_file2, "w") as f:
            f.write('resource "aws_instance" "example" {\n  ami = "ami-123"\n}')
        # Should only find main.tf
        result = find_provider_blocks_in_directory(temp_dir, temp_dir)
        assert len(result) == 1
        assert result[0] == "main.tf"
    finally:
        shutil.rmtree(temp_dir)

def test_find_provider_blocks_in_directory_none():
    temp_dir = tempfile.mkdtemp()
    try:
        tf_file = os.path.join(temp_dir, "main.tf")
        with open(tf_file, "w") as f:
            f.write('resource "aws_instance" "example" {\n  ami = "ami-123"\n}')
        result = find_provider_blocks_in_directory(temp_dir, temp_dir)
        assert result == []
    finally:
        shutil.rmtree(temp_dir) 