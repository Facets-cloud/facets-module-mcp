import sys
from typing import Dict, Any
import os
import subprocess

import config
from config import mcp, working_directory  # Import from config for shared resources

from click.testing import CliRunner
from ftf_cli.cli import cli


@mcp.tool()
def generate_module_with_user_confirmation(intent: str, flavor: str, cloud: str, title: str, description: str,
                            dry_run: bool = True) -> str:
    """
    ⚠️ IMPORTANT: REQUIRES USER CONFIRMATION ⚠️
    This function performs an irreversible action

    Tool to generate a new module using FTF CLI.
    Step 1 - ALWAYS use dry_run=True first. This is an irreversible action.
    Step 2 - Present the dry run output to the user in textual format.
    Step 3 - Ask if user will like to make any changes in passed arguments and modify them
    Step 4 - Call the tool without dry run

    Args:
    - module_path (str): The path to the module.
    - intent (str): The intent for the module.
    - flavor (str): The flavor of the module.
    - cloud (str): The cloud provider.
    - title (str): The title of the module.
    - description (str): The description of the module.
    - dry_run (bool): If True, returns a description of the generation without executing. MUST set to True initially.

    Returns:
    - str: The output from the FTF command execution.
    """
    if dry_run:
        return (f"Dry run: The following module will be generated with intent='{intent}', flavor='{flavor}', cloud='{cloud}', title='{title}', description='{description}'. "
                f"Get confirmation from the user before running with dry_run=False to execute the generation.")

    command = [
        "ftf", "generate-module",
        "-i", intent,
        "-f", flavor,
        "-c", cloud,
        "-t", title,
        "-d", description,
        working_directory
    ]
    return run_ftf_command(command)

@mcp.tool()
def run_ftf_validate_directory(module_path: str, check_only: bool = False) -> str:
    """
    Tool to validate a module directory using FTF CLI.
    
    This tool checks if a Terraform module directory meets the FTF standards.
    It validates the structure, formatting, and required files of the module.

    Args:
    - module_path (str): The path to the module.
    - check_only (bool): Flag to only check formatting without applying changes.

    Returns:
    - str: The output from the FTF command execution or error message if validation fails.
    """
    try:
        # Validate module path exists
        if not os.path.exists(module_path):
            return f"Error: Module path '{module_path}' does not exist."
        
        # Validate module path is a directory
        if not os.path.isdir(module_path):
            return f"Error: Module path '{module_path}' is not a directory."
            
        # Create command
        check_flag = "--check-only" if check_only else ""
        command = [
            "ftf", "validate-directory",
            module_path
        ]
        if check_flag:
            command.append(check_flag)
            
        # Run command and return output
        return run_ftf_command(command)
    except Exception as e:
        error_message = f"Error validating module directory: {str(e)}"
        print(error_message, file=sys.stderr)
        return error_message


def run_ftf_command(command) -> str:
    if not command[0] == 'ftf':
        return "Error: Only 'ftf' commands are allowed."

    runner = CliRunner()

    # Remove starting 'ftf' from command to align with Click command structure
    result = runner.invoke(cli, command[1:])

    if result.exit_code != 0:
        error_message = f"Error executing command: {result.output}"
        print(error_message, file=sys.stderr)
        return error_message

    output_message = result.output
    return output_message

@mcp.tool()
def run_ftf_preview_module(module_path: str, auto_create_intent: bool = True, publishable: bool = False) -> str:
    """
    Tool to preview a module using FTF CLI.
    Git repository details are automatically extracted from the local working directory's .git folder.

    Args:
    - module_path (str): The path to the module.
    - auto_create_intent (bool): Flag to auto-create intent if not exists.
    - publishable (bool): Flag to indicate if the module is publishable.

    Returns:
    - str: The output from the FTF command execution.
    """
    # Get git repository URL from .git/config
    git_repo_url = "temp"  # Default fallback value
    git_ref = "ai"        # Default fallback value
    
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
            
        print(f"Using git repo: {git_repo_url}, git ref: {git_ref}", file=sys.stderr)
    except Exception as e:
        print(f"Error extracting git details: {str(e)}. Using defaults.", file=sys.stderr)
    
    command = [
        "ftf", "preview-module",
        module_path
    ]
    if auto_create_intent:
        command.extend(["-a", str(auto_create_intent)])
    if publishable:
        command.extend(["-f", str(publishable)])
    
    # Always include git details (now from local repository)
    command.extend(["-g", git_repo_url])
    command.extend(["-r", git_ref])
    
    return run_ftf_command(command)