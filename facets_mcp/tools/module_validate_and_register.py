import sys
from typing import Dict, Any, Optional
import os
import json

from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.ftf_command_utils import run_ftf_command, get_git_repo_info
from facets_mcp.utils.yaml_utils import validate_module_output_types


@mcp.tool()
def validate_module(module_path: str) -> str:
    """
    Tool to validate a module directory using FTF CLI.
    
    This tool runs 'ftf module validate' on the specified module directory
    to ensure it meets all FTF standards and requirements.

    Args:
        module_path (str): The path to the module directory to validate.

    Returns:
        str: A JSON-formatted string with validation results.
    """
    try:
        # Construct the full path to the module
        full_module_path = os.path.join(working_directory, module_path)
        
        # Verify the module directory exists
        if not os.path.exists(full_module_path):
            return json.dumps({
                "success": False,
                "error": f"Module directory '{module_path}' does not exist.",
                "data": {
                    "module_path": module_path,
                    "full_path": full_module_path
                }
            }, indent=2)

        # Check if facets.yaml exists
        facets_yaml_path = os.path.join(full_module_path, "facets.yaml")
        if not os.path.exists(facets_yaml_path):
            return json.dumps({
                "success": False,
                "error": f"Module directory '{module_path}' is missing facets.yaml file.",
                "data": {
                    "module_path": module_path,
                    "full_path": full_module_path,
                    "facets_yaml_path": facets_yaml_path
                }
            }, indent=2)

        # Run additional validation: check output types
        try:
            output_types_validation = validate_module_output_types(full_module_path)
        except Exception as e:
            output_types_validation = {
                "success": False,
                "error": f"Error validating output types: {str(e)}"
            }

        # Construct the FTF command for validation
        ftf_command = ["ftf", "module", "validate", module_path]
        
        # Execute the FTF command
        result = run_ftf_command(ftf_command, working_directory)
        
        if result["success"]:
            return json.dumps({
                "success": True,
                "message": f"Module '{module_path}' passed validation successfully.",
                "data": {
                    "module_path": module_path,
                    "validation_output": result.get("output", ""),
                    "command_executed": " ".join(ftf_command),
                    "output_types_validation": output_types_validation
                }
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": f"Module validation failed: {result.get('error', 'Unknown error')}",
                "data": {
                    "module_path": module_path,
                    "validation_output": result.get("output", ""),
                    "command_executed": " ".join(ftf_command),
                    "output_types_validation": output_types_validation
                }
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error validating module '{module_path}': {str(e)}",
        }, indent=2)


@mcp.tool()
def push_preview_module_to_facets_cp(module_path: str) -> str:
    """
    Tool to preview a module using FTF CLI. This will push a Test version of module to control plane.
    Git repository details are automatically extracted from the local working directory's .git folder.

    Args:
        module_path (str): The path to the module directory to preview.

    Returns:
        str: A JSON-formatted string with preview results.
    """
    try:
        # Construct the full path to the module
        full_module_path = os.path.join(working_directory, module_path)
        
        # Verify the module directory exists
        if not os.path.exists(full_module_path):
            return json.dumps({
                "success": False,
                "error": f"Module directory '{module_path}' does not exist.",
                "data": {
                    "module_path": module_path,
                    "full_path": full_module_path
                }
            }, indent=2)

        # Check if facets.yaml exists
        facets_yaml_path = os.path.join(full_module_path, "facets.yaml")
        if not os.path.exists(facets_yaml_path):
            return json.dumps({
                "success": False,
                "error": f"Module directory '{module_path}' is missing facets.yaml file.",
                "data": {
                    "module_path": module_path,
                    "full_path": full_module_path,
                    "facets_yaml_path": facets_yaml_path
                }
            }, indent=2)

        # Extract git repository information automatically
        git_info = get_git_repo_info(working_directory)
        
        # Construct the FTF command for preview
        ftf_command = ["ftf", "module", "preview", module_path]
        
        # Add git information if available
        if git_info.get("repo_url"):
            ftf_command.extend(["--git-repo", git_info["repo_url"]])
        
        if git_info.get("branch"):
            ftf_command.extend(["--git-branch", git_info["branch"]])
            
        if git_info.get("commit_hash"):
            ftf_command.extend(["--git-commit", git_info["commit_hash"]])

        # Execute the FTF command
        result = run_ftf_command(ftf_command, working_directory)
        
        if result["success"]:
            return json.dumps({
                "success": True,
                "message": f"Module '{module_path}' has been successfully previewed on the control plane.",
                "instructions": "Use test_already_previewed_module to test this module in a test project.",
                "data": {
                    "module_path": module_path,
                    "preview_output": result.get("output", ""),
                    "command_executed": " ".join(ftf_command),
                    "git_info": git_info
                }
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": f"Module preview failed: {result.get('error', 'Unknown error')}",
                "data": {
                    "module_path": module_path,
                    "preview_output": result.get("output", ""),
                    "command_executed": " ".join(ftf_command),
                    "git_info": git_info
                }
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error previewing module '{module_path}': {str(e)}",
        }, indent=2)
