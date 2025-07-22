"""
Import tools for discovering Terraform resources and adding import declarations to facets.yaml
"""

import json
import os
from typing import Optional

from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.ftf_command_utils import run_ftf_command
from facets_mcp.utils.file_utils import ensure_path_in_working_directory


@mcp.tool()
def discover_terraform_resources(module_path: str) -> str:
    """
    Scan Terraform files in module directory to identify all resources with their types and names.
    Detects resources with count or for_each meta-arguments and returns structured list of available resources for import.
    
    Args:
        module_path (str): Path to the module directory containing Terraform files
        
    Returns:
        str: JSON response containing discovered resources or error information
    """
    try:
        # Ensure the module path is within the working directory for security
        full_module_path = ensure_path_in_working_directory(module_path, working_directory)
        
        if not os.path.exists(full_module_path):
            return json.dumps({
                "success": False,
                "message": f"Module directory not found: {module_path}",
                "error": "Directory does not exist"
            }, indent=2)
        
        # Run the ftf get-resources command
        command = ["ftf", "get-resources", full_module_path]
        
        try:
            output = run_ftf_command(command)
            
            # Parse the output to extract resource information
            resources = []
            lines = output.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('- '):
                    # Remove the '- ' prefix
                    resource_info = line[2:]
                    
                    # Check for count or for_each indicators
                    has_count = "(with count)" in resource_info
                    has_for_each = "(with for_each)" in resource_info
                    
                    # Clean the resource address
                    resource_address = resource_info.replace(" (with count)", "").replace(" (with for_each)", "")
                    
                    resource_data = {
                        "resource_address": resource_address,
                        "has_count": has_count,
                        "has_for_each": has_for_each
                    }
                    
                    resources.append(resource_data)
            
            return json.dumps({
                "success": True,
                "message": f"Found {len(resources)} resources in module",
                "data": {
                    "module_path": module_path,
                    "resources": resources,
                    "raw_output": output
                }
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "message": "Failed to discover Terraform resources",
                "error": str(e),
                "instructions": "Ensure the module directory contains valid Terraform files and the ftf CLI is properly configured"
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": "Error accessing module directory",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def add_import_declaration(
    module_path: str,
    name: Optional[str] = None,
    resource: Optional[str] = None,
    resource_address: Optional[str] = None,
    index: Optional[str] = None,
    key: Optional[str] = None,
    required: bool = True,
    interactive: bool = True
) -> str:
    """
    Add import declarations to facets.yaml file in the specified module.
    Supports both interactive (with user prompts) and non-interactive modes.
    Handles resource addressing for count/for_each resources and validates import configurations.
    
    Args:
        module_path (str): Path to the module directory
        name (str, optional): The name of the import to be added
        resource (str, optional): The Terraform resource address to import (e.g., 'aws_s3_bucket.bucket')
        resource_address (str, optional): Full resource state address (e.g., 'aws_s3_bucket.bucket[0]')
        index (str, optional): For resources with 'count', specify the index (e.g., '0', '1', or '*' for all)
        key (str, optional): For resources with 'for_each', specify the key (e.g., 'my-key' or '*' for all)
        required (bool): Flag to indicate if this import is required. Default is True
        interactive (bool): Whether to run in interactive mode. Default is True
        
    Returns:
        str: JSON response containing success/failure information
    """
    try:
        # Ensure the module path is within the working directory for security
        full_module_path = ensure_path_in_working_directory(module_path, working_directory)
        
        if not os.path.exists(full_module_path):
            return json.dumps({
                "success": False,
                "message": f"Module directory not found: {module_path}",
                "error": "Directory does not exist"
            }, indent=2)
        
        # Build the ftf add-import command
        command = ["ftf", "add-import"]
        
        # Add options based on provided parameters
        if name:
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

        # Note: interactive parameter is handled by the ftf CLI itself
        # When no parameters are provided, it runs in interactive mode

        try:
            output = run_ftf_command(command)
            
            return json.dumps({
                "success": True,
                "message": "Import declaration added successfully",
                "data": {
                    "module_path": module_path,
                    "import_name": name,
                    "resource": resource or resource_address,
                    "required": required,
                    "output": output
                }
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "message": "Failed to add import declaration",
                "error": str(e),
                "instructions": "Check that the resource address is valid and the facets.yaml file is writable. For interactive mode, ensure all required parameters are provided or run without parameters to be prompted."
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": "Error accessing module directory",
            "error": str(e)
        }, indent=2)
