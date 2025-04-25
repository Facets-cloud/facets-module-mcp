# This file contains utility functions for handling module files

import os
import sys
import difflib
from typing import Optional, Dict, Any, List

from config import mcp, working_directory
from tools.ftf_tools import run_ftf_command


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
        _validate_yaml(module_path, facets_yaml)

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
    Writes a Terraform resource file (main.tf, outputs.tf, variables.tf, etc.) to a module directory.
    Use this for ANY Terraform files including variables.tf.
    
    Args:
        module_path (str): Path to the module directory.
        file_name (str): Name of the file to write (e.g., "main.tf", "outputs.tf", "variables.tf").
        content (str): Content to write to the file.
        
    Returns:
        str: Success message or error message.
    """
    try:
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
