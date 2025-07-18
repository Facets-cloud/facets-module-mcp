"""
Utilities for running FTF commands in the facets-module-mcp project.
Contains helper functions for executing FTF CLI commands safely.
"""

import os
import sys
import subprocess
import tempfile
import yaml
from typing import List, Dict, Any
# from ftf_cli.cli import cli


def run_ftf_command(command: list) -> str:
    """
    Runs an FTF command using subprocess to avoid dependency conflicts.
    Args:
        command (List[str]): The FTF command as a list of strings.
    Returns:
        str: The output from the command execution.
    """
    if not command[0] == 'ftf':
        return "Error: Only 'ftf' commands are allowed."

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise Exception(f"FTF command failed: {e.stderr}")


def get_git_repo_info(working_directory: str) -> Dict[str, str]:
    """
    Get git repository URL and reference from the local working directory.
    
    Args:
        working_directory (str): The working directory.
        
    Returns:
        Dict[str, str]: A dictionary with 'url' and 'ref' keys.
    """
    git_repo_url = "temp"  # Default fallback value
    git_ref = "ai"         # Default fallback value
    
    try:
        # Extract remote URL from git config
        result = subprocess.run(["git", "config", "--get", "remote.origin.url"], 
                               cwd=working_directory,
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode == 0 and result.stdout.strip():
            git_repo_url = result.stdout.strip()
        
        # Extract current branch name
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                               cwd=working_directory,
                               capture_output=True,
                               text=True,
                               check=False)
        if result.returncode == 0 and result.stdout.strip():
            git_ref = result.stdout.strip()
            
    except Exception as e:
        print(f"Error extracting git details: {str(e)}. Using defaults.", file=sys.stderr)
    
    return {"url": git_repo_url, "ref": git_ref}


def create_temp_yaml_file(data: Dict[str, Any]) -> str:
    """
    Create a temporary YAML file with the given data.
    
    Args:
        data (Dict[str, Any]): Data to write to the YAML file.
        
    Returns:
        str: Path to the temporary file.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as temp_file:
            yaml.dump(data, temp_file, default_flow_style=False)
            return temp_file.name
    except Exception as e:
        error_message = f"Error creating temporary file: {str(e)}"
        print(error_message, file=sys.stderr)
        raise
