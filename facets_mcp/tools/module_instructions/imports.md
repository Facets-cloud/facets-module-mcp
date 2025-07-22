# Import Declarations in Terraform Modules

## Overview

Import declarations specify Terraform resources that should be imported when using a module, enabling existing infrastructure to be brought under Terraform management. The MCP server provides tools to discover resources and add import declarations to your modules.

## Import Declaration Format

Import declarations are added to the `facets.yaml` file in the following format:

```yaml
imports:
  - name: s3_bucket
    resource_address: aws_s3_bucket.bucket
    required: true
```

Each import declaration consists of:

- **name**: A unique identifier for the import
- **resource_address**: The Terraform resource address to import
- **required**: Whether the import is required (default: true)

## MCP Tools for Import Management

### 1. discover_terraform_resources

This tool scans Terraform files in a module directory to identify all resources with their types and names. It detects resources with count or for_each meta-arguments and returns a structured list of available resources for import.

**Usage:**
```
discover_terraform_resources(module_path)
```

**Parameters:**
- `module_path`: Path to the module directory containing Terraform files

**Example Response:**
```json
{
  "success": true,
  "message": "Found 3 resources in module",
  "data": {
    "module_path": "/path/to/module",
    "resources": [
      {
        "resource_address": "aws_s3_bucket.bucket",
        "has_count": false,
        "has_for_each": false
      },
      {
        "resource_address": "aws_instance.web",
        "has_count": true,
        "has_for_each": false
      },
      {
        "resource_address": "aws_security_group.sg",
        "has_count": false,
        "has_for_each": true
      }
    ]
  }
}
```

### 2. add_import_declaration

This tool adds import declarations to the facets.yaml file in a module. It supports both interactive (with user prompts) and non-interactive modes, handles resource addressing for count/for_each resources, and validates import configurations.

**Usage:**
```
add_import_declaration(
    module_path,
    name=None,
    resource=None,
    resource_address=None,
    index=None,
    key=None,
    required=True,
    interactive=True
)
```

**Parameters:**
- `module_path`: Path to the module directory
- `name`: The name of the import to be added (optional in interactive mode)
- `resource`: The Terraform resource address to import (e.g., 'aws_s3_bucket.bucket')
- `resource_address`: Full resource state address (e.g., 'aws_s3_bucket.bucket[0]')
- `index`: For resources with 'count', specify the index (e.g., '0', '1', or '*' for all)
- `key`: For resources with 'for_each', specify the key (e.g., 'my-key' or '*' for all)
- `required`: Flag to indicate if this import is required (default: True)
- `interactive`: Whether to run in interactive mode (default: True)

**Example Response:**
```json
{
  "success": true,
  "message": "Import declaration added successfully",
  "data": {
    "module_path": "/path/to/module",
    "import_name": "s3_bucket",
    "resource": "aws_s3_bucket.bucket",
    "required": true,
    "output": "✅ Import declaration added to facets.yaml"
  }
}
```

## Usage Examples

### Discovering Available Resources

First, discover the resources available in your module:

```
discover_terraform_resources("/path/to/module")
```

### Adding an Import Declaration (Interactive Mode)

In interactive mode, the tool will prompt you to select a resource and provide a name:

```
add_import_declaration("/path/to/module")
```

### Adding an Import Declaration (Non-Interactive Mode)

For automation or scripting, use non-interactive mode with all required parameters:

```
add_import_declaration(
    module_path="/path/to/module",
    name="s3_bucket",
    resource="aws_s3_bucket.bucket",
    required=True,
    interactive=False
)
```

### Adding an Import for a Resource with Count

For resources using the count meta-argument:

```
add_import_declaration(
    module_path="/path/to/module",
    name="web_server",
    resource="aws_instance.web",
    index="0",
    interactive=False
)
```

### Adding an Import for a Resource with For Each

For resources using the for_each meta-argument:

```
add_import_declaration(
    module_path="/path/to/module",
    name="security_group",
    resource="aws_security_group.sg",
    key="prod",
    interactive=False
)
```
