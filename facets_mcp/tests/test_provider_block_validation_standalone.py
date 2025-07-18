import os
import tempfile
from facets_mcp.utils.file_utils import validate_no_provider_blocks

def write_tf(path, content):
    with open(path, 'w') as f:
        f.write(content)

def test_no_provider_block():
    with tempfile.TemporaryDirectory() as tmpdir:
        write_tf(os.path.join(tmpdir, 'main.tf'), 'resource "aws_instance" "foo" {}')
        ok, msg = validate_no_provider_blocks(tmpdir)
        print('test_no_provider_block:', ok, msg)
        assert ok
        assert "No provider blocks" in msg

def test_provider_block_present():
    with tempfile.TemporaryDirectory() as tmpdir:
        write_tf(os.path.join(tmpdir, 'main.tf'), 'provider "aws" { region = \"us-west-2\" }')
        ok, msg = validate_no_provider_blocks(tmpdir)
        print('test_provider_block_present:', ok, msg)
        assert not ok
        assert "Provider blocks are not allowed" in msg

def test_parse_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        write_tf(os.path.join(tmpdir, 'bad.tf'), 'this is not valid hcl')
        ok, msg = validate_no_provider_blocks(tmpdir)
        print('test_parse_error:', ok, msg)
        assert not ok
        assert "Failed to parse" in msg

def test_nested_provider_block():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'subdir'))
        write_tf(os.path.join(tmpdir, 'subdir', 'nested.tf'), 'provider \"google\" {}')
        ok, msg = validate_no_provider_blocks(tmpdir)
        print('test_nested_provider_block:', ok, msg)
        assert not ok
        assert "nested.tf" in msg

if __name__ == '__main__':
    test_no_provider_block()
    test_provider_block_present()
    test_parse_error()
    test_nested_provider_block()
    print('All standalone provider block validation tests passed.') 