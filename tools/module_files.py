# This file contains utility functions for handling module files

import os
import sys
import difflib
import json
import yaml
from typing import Optional, Dict, Any, List

from config import mcp, working_directory
from tools.ftf_tools import run_ftf_command, register_output_type
from swagger_client.api.ui_tf_output_controller_api import UiTfOutputControllerApi
from swagger_client.rest import ApiException
from utils.client_utils import ClientUtils

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
    file_list = []
    full_module_path = os.path.abspath(module_path)
    if not full_module_path.startswith(os.path.abspath(working_directory)):
        raise ValueError("Attempt to access files outside of the working directory.")
    try:
        for root, dirs, files in os.walk(full_module_path):
            for file in files:
                file_list.append(os.path.join(root, file))
    except OSError as e:
        print(f"Error accessing module path {module_path}: {e}")
    return file_list


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
    full_file_path = os.path.abspath(file_path)
    if not full_file_path.startswith(os.path.abspath(working_directory)):
        raise ValueError("Attempt to access files outside of the working directory.")
    try:
        with open(full_file_path, 'r') as f:
            return f.read()
    except OSError as e:
        print(f"Error reading file {file_path}: {e}")
        return "Error reading file."


@mcp.tool()
def write_config_files(module_path: str, facets_yaml: str, dry_run: bool = True) -> str:
    """
    Writes facets.yaml configuration file for a Terraform module.
    <important>Make Sure you have Called FIRST_STEP_get_instructions first before this tool.</important>

    Steps for safe variable update:

    1. Always run with `dry_run=True` first  2 this is an irreversible action.
    2. Parse and display a diff:
       

 Added
        Modified (old  new)
        Removed
    3. Ask user if they want to edit or add variables and wait for his input.
    4. Only if user **explicitly confirms**, run again with `dry_run=False`.
    
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
        full_module_path = os.path.abspath(module_path)
        if not full_module_path.startswith(os.path.abspath(working_directory)):
            return "Error: Attempt to write files outside of the working directory."

        # Ensure module directory exists
        if not os.path.exists(full_module_path):
            os.makedirs(full_module_path, exist_ok=True)

        # Run validation method on facets_yaml and module_path
        validation_error = _validate_yaml(module_path, facets_yaml)
        if validation_error:
            return f"Error validating facets.yaml: {validation_error}"

        # Check for outputs and validate output types
        output_validation_results = _validate_output_types(facets_yaml)
        if output_validation_results and "missing_outputs" in output_validation_results:
            missing_outputs = output_validation_results["missing_outputs"]
            if missing_outputs:
                missing_types_msg = f"Warning: The following output types do not exist and should be registered first using register_output_type:\n"
                
                for output_type in missing_outputs:
                    missing_types_msg += f"- {output_type}\n"
                
                missing_types_msg += "\nPlease register these output types using register_output_type before writing the configuration."
                
                return missing_types_msg

        changes = []
        current_facets_content = ""

        # Handle facets.yaml
        facets_path = os.path.join(full_module_path, "facets.yaml")

        # Check if file exists and read its content
        if os.path.exists(facets_path):
            try:
                with open(facets_path, 'r') as f:
                    current_facets_content = f.read()
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
                with open(facets_path, 'w') as f:
                    f.write(facets_yaml)
                changes.append(f"Successfully wrote facets.yaml to {facets_path}")
            except Exception as e:
                error_msg = f"Error writing facets.yaml: {str(e)}"
                changes.append(error_msg)
                print(error_msg, file=sys.stderr)

        if dry_run:
            # Create structured output with JSON
            file_preview = generate_file_previews(facets_yaml, current_facets_content)
            
            import json
            result = {
                "type": "dry_run",
                "module_path": module_path,
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


def generate_file_previews(facets_yaml: str, current_facets_yaml: Optional[str] = None):
    """
    Generate preview or diff of facets.yaml content for dry run mode.
    
    Args:
        facets_yaml: New content for facets.yaml file
        current_facets_yaml: Current content of facets.yaml file (for diff)
        
    Returns:
        dict: Structured data with file preview or diff information
    """
    # If we have current content, generate a diff
    if current_facets_yaml:
        return {
            "type": "diff",
            "content": generate_diff(current_facets_yaml, facets_yaml)
        }
    else:
        # Show preview of new file
        content_lines = facets_yaml.splitlines()
        preview_lines = content_lines[:min(20, len(content_lines))]
        is_truncated = len(content_lines) > 20
        
        return {
            "type": "new_file",
            "content": "\n".join(preview_lines),
            "truncated": is_truncated,
            "total_lines": len(content_lines)
        }


def generate_diff(current_content: str, new_content: str) -> str:
    """
    Generate a unified diff between current and new content.
    
    Args:
        current_content: The current file content
        new_content: The new file content to be written
        
    Returns:
        str: A formatted diff showing changes
    """
    current_lines = current_content.splitlines()
    new_lines = new_content.splitlines()
    
    diff = difflib.unified_diff(
        current_lines, 
        new_lines,
        lineterm='',
        n=3  # Context lines
    )
    
    # Format the diff for readability
    diff_text = '\n'.join(list(diff))
    
    # If the diff is very long, truncate it
    diff_lines = diff_text.splitlines()
    
    return diff_text


@mcp.tool()
def write_resource_file(module_path: str, file_name: str, content: str) -> str:
    """
    Writes a Terraform resource file (main.tf, variables.tf, etc.) to a module directory.
    
    Does NOT allow writing outputs.tf here. To update outputs.tf, use write_outputs().

    Args:
        module_path (str): Path to the module directory.
        file_name (str): Name of the file to write (e.g., "main.tf", "variables.tf").
        content (str): Content to write to the file.
        
    Returns:
        str: Success message or error message.
    """
    try:
        if file_name == "outputs.tf":
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

def _validate_yaml(module_path: str, facets_yaml: str) -> str:
    """
    Private method to validate facets_yaml content.
    Writes facets_yaml to facets.yaml.new in module_path for validation, then deletes it.
    Returns an error message string if validation fails, or empty string if valid.
    """
    import os

    temp_path = os.path.join(os.path.abspath(module_path), "facets.yaml.new")
    try:
        with open(temp_path, 'w') as temp_file:
            temp_file.write(facets_yaml)
    except Exception as e:
        return f"Error writing temporary validation file: {str(e)}"
    command = [
        "ftf", "validate-facets",
        "--filename", "facets.yaml.new",
        module_path
    ]

    validation_error = run_ftf_command(command)

    try:
        os.remove(temp_path)
    except Exception:
        pass

    if validation_error.startswith("Error executing command"):
        raise RuntimeError(validation_error)

    return validation_error


def _validate_output_types(facets_yaml_content: str) -> Dict[str, Any]:
    """
    Private method to validate output types in facets.yaml.
    Checks if output types mentioned in the outputs block exist in the Facets control plane.
    
    Args:
        facets_yaml_content (str): Content of facets.yaml file
        
    Returns:
        Dict[str, Any]: Dictionary with validation results including missing outputs
    """
    try:
        # Parse YAML content
        facets_data = yaml.safe_load(facets_yaml_content)
        if not facets_data:
            return {}
        
        # Check if outputs block exists
        if 'outputs' not in facets_data:
            return {}
        
        outputs = facets_data.get('outputs', {})
        if not outputs:
            return {}
        
        # Extract output types from outputs block
        output_types = []
        for output_name, output_def in outputs.items():
            if 'type' in output_def:
                output_type = output_def['type']
                if output_type not in output_types:
                    output_types.append(output_type)
        
        if not output_types:
            return {}
        
        # Check if output types exist in Facets control plane
        missing_output_types = []
        
        # Initialize API client
        try:
            api_client = ClientUtils.get_client()
            output_api = UiTfOutputControllerApi(api_client)
            
            for output_type in output_types:
                # Skip if not in @namespace/name format
                if not output_type.startswith('@') or '/' not in output_type:
                    continue
                
                # Split the name into namespace and name parts
                name_parts = output_type.split('/', 1)
                if len(name_parts) != 2:
                    continue
                
                namespace, output_name = name_parts
                
                # Check if the output exists
                try:
                    output_api.get_output_by_name_using_get(name=output_name, namespace=namespace)
                except ApiException as e:
                    if e.status == 404:
                        missing_output_types.append(output_type)
                    else:
                        print(f"Error checking output type {output_type}: {str(e)}", file=sys.stderr)
        
        except Exception as e:
            print(f"Error initializing API client: {str(e)}", file=sys.stderr)
            return {"error": f"Error checking output types: {str(e)}"}
        
        return {"missing_outputs": missing_output_types}
    
    except Exception as e:
        print(f"Error validating output types: {str(e)}", file=sys.stderr)
        return {"error": f"Error validating output types: {str(e)}"}

@mcp.tool()
def write_outputs(module_path: str, outputs_attributes: dict, outputs_interfaces: dict) -> str:
    """
    Write the outputs.tf file for a module with a local block containing outputs_attributes and outputs_interfaces.
    
    This function requires facets.yaml to exist in the module path before writing outputs.tf.
    If facets.yaml doesn't exist, it will fail with a message instructing to call write_config_files first.

    Args:
        module_path (str): Path to the module directory.
        outputs_attributes (dict): Map of output attributes.
        outputs_interfaces (dict): Map of output interfaces.

    Returns:
        str: Success or error message.
    """
    try:
        full_module_path = os.path.abspath(module_path)
        if not full_module_path.startswith(os.path.abspath(working_directory)):
            return "Error: Attempt to write files outside of the working directory."

        # Check if facets.yaml exists in the module path
        facets_path = os.path.join(full_module_path, "facets.yaml")
        if not os.path.exists(facets_path):
            return "Error: facets.yaml not found in module path. Please call write_config_files first to create the facets.yaml configuration."

        os.makedirs(full_module_path, exist_ok=True)

        # Generate outputs.tf content with local block
        content_lines = ["local {"]
        if outputs_attributes:
            content_lines.append("  outputs_attributes = {")
            for k, v in outputs_attributes.items():
                content_lines.append(f"    {k} = {json.dumps(v)}")
            content_lines.append("  }")
        if outputs_interfaces:
            content_lines.append("  outputs_interfaces = {")
            for k, v in outputs_interfaces.items():
                content_lines.append(f"    {k} = {json.dumps(v)}")
            content_lines.append("  }")
        content_lines.append("}")

        content = "\n".join(content_lines)

        file_path = os.path.join(full_module_path, "outputs.tf")
        with open(file_path, 'w') as f:
            f.write(content)

        return f"Successfully wrote outputs.tf to {file_path}"
    except Exception as e:
        error_message = f"Error writing outputs.tf: {str(e)}"
        print(error_message, file=sys.stderr)
        return error_message


