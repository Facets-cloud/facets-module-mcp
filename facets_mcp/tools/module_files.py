# This file contains utility functions for handling module files

import os
import sys
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.file_utils import (
    list_files_in_directory, 
    read_file_content, 
    generate_file_previews,
    write_file_safely,
    ensure_path_in_working_directory
)
from facets_mcp.utils.yaml_utils import (
    validate_yaml, 
    validate_output_types, 
    check_missing_output_types,
    read_and_validate_facets_yaml
)
from swagger_client.api.ui_tf_output_controller_api import UiTfOutputControllerApi
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.utils.output_utils import (
    get_output_type_details_from_api,
    find_output_types_with_provider_from_api
)

# Initialize client utility
try:
    if not ClientUtils.initialized:
        ClientUtils.initialize()
except Exception as e:
    print(f"Warning: Failed to initialize API client: {str(e)}", file=sys.stderr)


@mcp.tool()
def list_files(module_path: str) -> list:
    """
    Lists all files in the given module path, ensuring we stay within the working directory.
    Always ask User if he wants to add any variables or use any other FTF commands

    Args:
        module_path (str): The path to the module directory.

    Returns:
        list: A list of file paths (strings) found in the module directory.
    """
    return list_files_in_directory(module_path, working_directory)


@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Reads the content of a file, ensuring it is within the working directory.
    <important>Make Sure you have Called FIRST_STEP_get_instructions first before this tool.</important>

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    return read_file_content(file_path, working_directory)


@mcp.tool()
def write_config_files(module_path: str, facets_yaml: str, dry_run: bool = True) -> str:
    """
    Writes facets.yaml configuration file for a Terraform module.
    <important>Make Sure you have Called FIRST_STEP_get_instructions first before this tool.</important>

    Steps for safe variable update:

    1. Always run with `dry_run=True` first. This is an irreversible action.
    2. Parse and display a diff:

       Added
       Modified (old -> new)
       Removed
    3. Ask the user if they want to edit or add variables and wait for his input.
    4. Only if the user **explicitly confirms**, run again with `dry_run=False`.
    
    Args:
        module_path (str): Path to the module directory.
        facets_yaml (str): Content for facets.yaml file.
        dry_run (bool): If True, returns a preview of changes without making them. Default is True.
        
    Returns:
        str: Success message, diff preview (if dry_run=True), or error message.
    """
    if not facets_yaml:
        return "Error: You must provide content for facets_yaml."
    
    try:
        # Normalize paths using Path for consistent handling across platforms
        full_module_path = Path(module_path).resolve()
        working_dir = Path(working_directory).resolve()
        
        # Check if the module path is within working directory
        try:
            full_module_path.relative_to(working_dir)
        except ValueError:
            return f"Error: Attempt to write files outside of the working directory. Module path: {full_module_path}, Working directory: {working_dir}"

        # Ensure module directory exists
        full_module_path.mkdir(parents=True, exist_ok=True)

        # Run validation method on facets_yaml and module_path
        validation_error = validate_yaml(str(full_module_path), facets_yaml)

        # Check for outputs and validate output types
        api_client = ClientUtils.get_client()
        output_api = UiTfOutputControllerApi(api_client)
        output_validation_results = validate_output_types(facets_yaml, output_api)
        
        has_missing_types, error_message = check_missing_output_types(output_validation_results)
        if has_missing_types:
            return error_message

        changes = []
        current_facets_content = ""

        # Handle facets.yaml
        facets_path = full_module_path / "facets.yaml"

        # Check if file exists and read its content
        if facets_path.exists():
            try:
                current_facets_content = facets_path.read_text(encoding='utf-8')
            except Exception as e:
                return f"Error reading existing facets.yaml: {str(e)}"

        # Generate diff for facets.yaml
        if dry_run:
            if not current_facets_content:
                changes.append(f"Would create new file: facets.yaml")
            else:
                changes.append(f"Would update existing file: facets.yaml")
        # Write facets.yaml if not in dry run mode
        else:
            try:
                facets_path.write_text(facets_yaml, encoding='utf-8')
                changes.append(f"Successfully wrote facets.yaml to {facets_path}")
            except Exception as e:
                error_msg = f"Error writing facets.yaml: {str(e)}"
                changes.append(error_msg)
                print(error_msg, file=sys.stderr)

        if dry_run:
            # Create structured output with JSON
            file_preview = generate_file_previews(facets_yaml, current_facets_content)
            
            result = {
                "type": "dry_run",
                "module_path": str(full_module_path),
                "changes": changes,
                "file_preview": file_preview,
                "instructions": "Analyze the diff to identify variable definitions being added, modified, or removed. Present a clear summary to the user about what schema fields are changing. Ask the user explicitly if they want to proceed with these changes and wait for his input. Only if the user confirms, run the write_config_files function again with dry_run=False."
            }
            
            return json.dumps(result, indent=2)
        else:
            return "\n".join(changes)
            
    except Exception as e:
        error_message = f"Error processing facets.yaml: {str(e)}"
        print(error_message, file=sys.stderr)
        return error_message


@mcp.tool()
def write_resource_file(module_path: str, file_name: str, content: str) -> str:
    """
    Writes a Terraform resource file (main.tf, variables.tf, etc.) to a module directory.
    
    Does NOT allow writing output(s).tf here. To update outputs.tf, use write_outputs().

    Args:
        module_path (str): Path to the module directory.
        file_name (str): Name of the file to write (e.g., "main.tf", "variables.tf").
        content (str): Content to write to the file.
        
    Returns:
        str: Success message or error message.
    """
    try:
        if file_name == "outputs.tf" or file_name == "output.tf":
            return ("Error: Writing 'outputs.tf' is not allowed through this function. "
                    "Please use the write_outputs() tool instead.")

        # Validate inputs
        if not file_name.endswith(".tf") and not file_name.endswith(".tf.tmpl"):
            return f"Error: File name must end with .tf or .tf.tmpl, got: {file_name}"
            
        if file_name == "facets.yaml":
            return "Error: For facets.yaml, please use write_config_files() instead."

        full_module_path = os.path.abspath(module_path)
        if not full_module_path.startswith(os.path.abspath(working_directory)):
            return "Error: Attempt to write files outside of the working directory."
            
        # Create module directory if it doesn't exist
        os.makedirs(full_module_path, exist_ok=True)

        file_path = os.path.join(full_module_path, file_name)
        
        # Write the file
        with open(file_path, 'w') as f:
            f.write(content)
            
        return f"Successfully wrote {file_name} to {file_path}"
    except Exception as e:
        error_message = f"Error writing resource file: {str(e)}"
        print(error_message, file=sys.stderr)
        return error_message


@mcp.tool()
def get_output_type_details(output_type: str) -> Dict[str, Any]:
    """
    Get details for a specific output type from the Facets control plane.
    
    This tool calls the get_output_by_name_using_get API endpoint to retrieve 
    information about an output type, including its properties and providers.
    
    Args:
        output_type (str): The output type name in format '@namespace/name'
        
    Returns:
        Dict[str, Any]: Dictionary containing the output type details or error information
    """
    return get_output_type_details_from_api(output_type)


@mcp.tool()
def find_output_types_with_provider(provider_source: str) -> str:
    """
    This tool finds all output types that include a specific provider source, which can be used as inputs for
    module configurations.
    
    Args:
        provider_source (str): The provider source name to search for.
        
    Returns:
        str: JSON string containing the formatted output type information.
    """
    return find_output_types_with_provider_from_api(provider_source)


@mcp.tool()
def write_outputs(module_path: str, output_attributes: dict = {}, output_interfaces: dict = {}) -> str:
    """
    Write the outputs.tf file for a module with a local block containing outputs_attributes and outputs_interfaces.

    This function requires facets.yaml to exist in the module path before writing outputs.tf.
    If facets.yaml doesn't exist, it will fail with a message instructing to call write_config_files first.

    Args:
        module_path (str): Path to the module directory.
        output_attributes (dict): Map of output attributes.
        output_interfaces (dict): Map of output interfaces.

    Returns:
        str: Success or error message.
    """
    try:
        full_module_path = ensure_path_in_working_directory(module_path, working_directory)

        # Initialize API client for validation
        api_client = ClientUtils.get_client()
        output_api = UiTfOutputControllerApi(api_client)

        # Read and validate facets.yaml
        success, facets_yaml_content, error_message = read_and_validate_facets_yaml(module_path, output_api)
        if not success:
            return error_message

        # Helper to render values correctly for Terraform
        def render_terraform_value(v):
            if isinstance(v, bool):
                return  str(v).lower()
            elif isinstance(v, (int,float)):
                return str(v)
            elif isinstance(v, str):
                if '.' in v and not v.startswith('${'):
                    return v
                else:
                    return json.dumps(v)
            elif isinstance(v, list):
                return '[' + ', '.join(render_terraform_value(i) for i in v) + ']'
            elif isinstance(v, dict):
                tf_lines = ["{"]
                for k, val in v.items():
                    tf_lines.append(f"  {k} = {render_terraform_value(val)}")
                tf_lines.append("}")
                return '\n'.join(tf_lines)
            else:
                return json.dumps(v)

        # Build outputs.tf content
        content_lines = ["locals {"]
        if output_attributes is not None:
            content_lines.append("  output_attributes = {")
            for k, v in output_attributes.items():
                content_lines.append(f"    {k} = {render_terraform_value(v)}")
            content_lines.append("  }")
        if output_interfaces is not None:
            content_lines.append("  output_interfaces = {")
            for k, v in output_interfaces.items():
                content_lines.append(f"    {k} = {render_terraform_value(v)}")
            content_lines.append("  }")
        content_lines.append("}")

        content = "\n".join(content_lines)

        # Write to outputs.tf
        file_path = os.path.join(full_module_path, "outputs.tf")
        if os.path.exists(file_path):
            os.remove(file_path)

        with open(file_path, 'w') as f:
            f.write(content)

        return f"Successfully wrote outputs.tf to {file_path}"

    except Exception as e:
        error_message = f"Error writing outputs.tf: {str(e)}"
        print(error_message, file=sys.stderr)
        return error_message

@mcp.tool()
def write_readme_file(module_path: str, content: str) -> str:
    """
    Writes a README.md file for the module directory.
    This tool is intended for AI to generate the README content for the module.

    Args:
        module_path (str): Path to the module directory.
        content (str): Content to write to README.md.

    Returns:
        str: Success message or error message.
    """
    try:
        full_module_path = os.path.abspath(module_path)
        if not full_module_path.startswith(os.path.abspath(working_directory)):
            return "Error: Attempt to write files outside of the working directory."

        # Create module directory if it doesn't exist
        os.makedirs(full_module_path, exist_ok=True)

        readme_path = os.path.join(full_module_path, "README.md")

        with open(readme_path, 'w') as f:
            f.write(content)

        return f"Successfully wrote README.md to {readme_path}"
    except Exception as e:
        error_message = f"Error writing README.md file: {str(e)}"
        print(error_message, file=sys.stderr)
        return error_message