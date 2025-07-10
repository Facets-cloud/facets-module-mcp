import os
import tempfile
import shutil
import pytest
from provider_block_validator import find_provider_blocks_in_directory

def test_provider_block_positive():
    temp_dir = tempfile.mkdtemp()
    try:
        tf_file = os.path.join(temp_dir, "main.tf")
        with open(tf_file, "w") as f:
            f.write('provider "aws" {\n  region = "us-west-2"\n}')
        result = find_provider_blocks_in_directory(temp_dir)
        assert result == ["main.tf"]
    finally:
        shutil.rmtree(temp_dir)

def test_provider_block_negative():
    temp_dir = tempfile.mkdtemp()
    try:
        tf_file = os.path.join(temp_dir, "main.tf")
        with open(tf_file, "w") as f:
            f.write('resource "aws_instance" "example" {\n  ami = "ami-123"\n}')
        result = find_provider_blocks_in_directory(temp_dir)
        assert result == []
    finally:
        shutil.rmtree(temp_dir)

def test_provider_block_nested():
    temp_dir = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(temp_dir, "subdir"))
        tf_file = os.path.join(temp_dir, "subdir", "nested.tf")
        with open(tf_file, "w") as f:
            f.write('provider "google" {\n  project = "my-proj"\n}')
        result = find_provider_blocks_in_directory(temp_dir)
        assert result == [os.path.join("subdir", "nested.tf")]
    finally:
        shutil.rmtree(temp_dir)

def test_provider_block_parse_error():
    temp_dir = tempfile.mkdtemp()
    try:
        tf_file = os.path.join(temp_dir, "bad.tf")
        with open(tf_file, "w") as f:
            f.write('this is not valid hcl!')
        with pytest.raises(Exception) as excinfo:
            find_provider_blocks_in_directory(temp_dir)
        assert "Failed to parse" in str(excinfo.value)
    finally:
        shutil.rmtree(temp_dir) 