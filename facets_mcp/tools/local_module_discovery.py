import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any
from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.file_utils import (
    list_files_in_directory,
    read_file_content,
    ensure_path_in_working_directory
)


def read_facets_file(facets_file):
    """Helper function to read a facets.yaml file."""
    with open(facets_file, 'r') as f:
        return yaml.safe_load(f)


def fetch_modules(search_string: str = None):
    """Utility function to fetch modules based on optional search string."""
    modules = []
    root_path = Path(working_directory)

    # Collect all matching facets.yaml files
    facets_files = list(root_path.rglob("facets.yaml"))  

    # Iterate through the files and filter modules
    for facets_file in facets_files:
        if ".terraform" in facets_file.parts:
            continue

        facets_content = read_facets_file(facets_file)
        
        # Module metadata
        module_dir = facets_file.parent
        module_data = {
            "module_path": str(module_dir.relative_to(root_path)),
            "module_absolute_path": str(module_dir),
            "facets_yaml_content": facets_content
        }

        # Search filtering logic
        if search_string:
            facets_yaml_str = yaml.dump(facets_content).lower()
            
            if search_string.lower() in facets_yaml_str:
                modules.append(module_data)
        else:
            modules.append(module_data)

    return modules


@mcp.tool()
def get_local_modules() -> str:
    """
    Scan the working directory recursively for facets.yaml files to identify
    all available Terraform modules. Also fetch content of outputs.tf if it exists.

    Returns:
        str: A JSON-formatted string containing all discovered modules with
             their metadata and outputs content.
    """
    try:
        modules = fetch_modules()
        
        # For each module, also check if outputs.tf exists and read its content
        for module in modules:
            outputs_file = os.path.join(module["module_absolute_path"], "outputs.tf")
            if os.path.exists(outputs_file):
                try:
                    with open(outputs_file, 'r') as f:
                        module["outputs_tf_content"] = f.read()
                except Exception as e:
                    module["outputs_tf_content"] = f"Error reading outputs.tf: {str(e)}"
            else:
                module["outputs_tf_content"] = None

        return json.dumps({
            "success": True,
            "message": f"Found {len(modules)} Terraform modules in the working directory.",
            "data": {
                "modules": modules,
                "total_count": len(modules)
            }
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error scanning for modules: {str(e)}",
        }, indent=2)


@mcp.tool()
def search_modules_after_confirmation(search_string: str, max_results: int = 10, offset: int = 0) -> str:
    """
    Search for a specific string in all facets.yaml files to filter modules.
    This tool should only be used after confirming search intent with the user.

    Args:
        search_string (str): The string to search for in facets.yaml files
        max_results (int): Maximum number of results to return (default: 10)
        offset (int): Number of results to skip for pagination (default: 0)

    Returns:
        str: A JSON-formatted string containing matching modules
    """
    try:
        # Fetch modules with search filtering
        all_matches = fetch_modules(search_string)
        
        # Apply pagination
        start_idx = offset
        end_idx = start_idx + max_results
        paginated_modules = all_matches[start_idx:end_idx]
        
        # For each matched module, also check if outputs.tf exists and read its content
        for module in paginated_modules:
            outputs_file = os.path.join(module["module_absolute_path"], "outputs.tf")
            if os.path.exists(outputs_file):
                try:
                    with open(outputs_file, 'r') as f:
                        module["outputs_tf_content"] = f.read()
                except Exception as e:
                    module["outputs_tf_content"] = f"Error reading outputs.tf: {str(e)}"
            else:
                module["outputs_tf_content"] = None

        has_more = end_idx < len(all_matches)
        
        return json.dumps({
            "success": True,
            "message": f"Found {len(all_matches)} modules matching '{search_string}'. Showing {len(paginated_modules)} results (offset: {offset}).",
            "data": {
                "modules": paginated_modules,
                "pagination": {
                    "total_matches": len(all_matches),
                    "returned_count": len(paginated_modules),
                    "offset": offset,
                    "max_results": max_results,
                    "has_more": has_more,
                    "next_offset": end_idx if has_more else None
                }
            }
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error searching modules: {str(e)}",
        }, indent=2)


@mcp.tool()
def list_files(module_path: str) -> str:
    """
    Lists all files in the given module path, ensuring we stay within the working directory.
    Always ask User if he wants to add any variables or use any other FTF commands

    Args:
        module_path (str): The path to the module directory.

    Returns:
        str: A JSON-formatted string with operation details and file list found in module directory.
    """
    try:
        # Use the utility function to list files
        result = list_files_in_directory(module_path)
        
        return json.dumps({
            "success": True,
            "message": f"Successfully listed files in '{module_path}'.",
            "instructions": "Always ask User if he wants to add any variables or use any other FTF commands",
            "data": result
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error listing files in '{module_path}': {str(e)}",
        }, indent=2)


@mcp.tool()
def read_file(module_path: str, file_name: str) -> str:
    """
    Reads the content of a file, ensuring it is within the working directory.
    <important>Make Sure you have Called FIRST_STEP_get_instructions first before this tool.</important>

    Args:
        module_path (str): The path to the module directory.
        file_name (str): The name of the file to read.

    Returns:
        str: A JSON-formatted string with operation details and file content.
    """
    try:
        # Use the utility function to read file content
        content = read_file_content(module_path, file_name)
        
        return json.dumps({
            "success": True,
            "message": f"Successfully read file '{file_name}' from '{module_path}'.",
            "data": {
                "file_path": f"{module_path}/{file_name}",
                "content": content
            }
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error reading file '{file_name}' from '{module_path}': {str(e)}",
        }, indent=2)
