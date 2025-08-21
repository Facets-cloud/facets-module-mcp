"""
Import tools for discovering Terraform resources and adding import declarations to facets.yaml
"""

import json
import os

from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.file_utils import ensure_path_in_working_directory
from facets_mcp.utils.ftf_command_utils import run_ftf_command


@mcp.tool()
def discover_terraform_resources(module_path: str) -> str:
    """
    Discover all Terraform resources in a module directory. Use this first to see what resources are available for import.
    Returns list of resources with their addresses and whether they use count/for_each.

    Args:
        module_path (str): Path to the module directory containing Terraform files

    Returns:
        str: JSON with resources list, showing resource_address, has_count, has_for_each for each resource
    """
    try:
        # Ensure the module path is within the working directory for security
        full_module_path = ensure_path_in_working_directory(
            module_path, working_directory
        )

        if not os.path.exists(full_module_path):
            return json.dumps(
                {
                    "success": False,
                    "message": f"Module directory not found: {module_path}",
                    "error": "Directory does not exist",
                },
                indent=2,
            )

        # Run the ftf get-resources command
        command = ["ftf", "get-resources", full_module_path]

        try:
            output = run_ftf_command(command)

            # Parse the output to extract resource information
            resources = []
            lines = output.strip().split("\n")

            for line in lines:
                line = line.strip()
                if line.startswith("- "):
                    # Remove the '- ' prefix
                    resource_info = line[2:]

                    # Check for count or for_each indicators
                    has_count = "(with count)" in resource_info
                    has_for_each = "(with for_each)" in resource_info

                    # Clean the resource address
                    resource_address = resource_info.replace(
                        " (with count)", ""
                    ).replace(" (with for_each)", "")

                    resource_data = {
                        "resource_address": resource_address,
                        "has_count": has_count,
                        "has_for_each": has_for_each,
                    }

                    resources.append(resource_data)

            return json.dumps(
                {
                    "success": True,
                    "message": f"Found {len(resources)} resources in module",
                    "data": {
                        "module_path": module_path,
                        "resources": resources,
                        "raw_output": output,
                    },
                },
                indent=2,
            )

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "message": "Failed to discover Terraform resources",
                    "error": str(e),
                    "instructions": "Ensure the module directory contains valid Terraform files and the ftf CLI is properly configured",
                },
                indent=2,
            )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error accessing module directory",
                "error": str(e),
            },
            indent=2,
        )


@mcp.tool()
def add_import_declaration(
    module_path: str,
    name: str,
    resource: str | None = None,
    resource_address: str | None = None,
    index: str | None = None,
    key: str | None = None,
    required: bool = True,
) -> str:
    """
    Add import declaration to facets.yaml. Use after discovering resources with discover_terraform_resources.
    For count resources, add index parameter. For for_each resources, add key parameter.

    Args:
        module_path (str): Path to the module directory
        name (str): Name for the import declaration
        resource (str, optional): Resource address like 'aws_s3_bucket.bucket'
        resource_address (str, optional): Full address like 'aws_s3_bucket.bucket[0]'
        index (str, optional): Index for count resources ('0', '1', or '*')
        key (str, optional): Key for for_each resources ('prod', 'dev', or '*')
        required (bool): Whether import is required (default: True)

    Returns:
        str: JSON response with success status and details
    """
    try:
        # Ensure the module path is within the working directory for security
        full_module_path = ensure_path_in_working_directory(
            module_path, working_directory
        )

        if not os.path.exists(full_module_path):
            return json.dumps(
                {
                    "success": False,
                    "message": f"Module directory not found: {module_path}",
                    "error": "Directory does not exist",
                },
                indent=2,
            )

        # Build the ftf add-import command
        command = ["ftf", "add-import"]

        # Add required parameters
        command.extend(["-n", name])

        if required:
            command.append("-r")

        if resource:
            command.extend(["--resource", resource])

        if resource_address:
            command.extend(["--resource-address", resource_address])

        if index:
            command.extend(["--index", index])

        if key:
            command.extend(["--key", key])

        # Add the module path
        command.append(full_module_path)

        try:
            output = run_ftf_command(command)

            return json.dumps(
                {
                    "success": True,
                    "message": "Import declaration added successfully",
                    "data": {
                        "module_path": module_path,
                        "import_name": name,
                        "resource": resource or resource_address,
                        "required": required,
                        "output": output,
                    },
                },
                indent=2,
            )

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "message": "Failed to add import declaration",
                    "error": str(e),
                    "instructions": "Check that the resource address is valid and the facets.yaml file is writable.",
                },
                indent=2,
            )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error accessing module directory",
                "error": str(e),
            },
            indent=2,
        )
