import sys
from typing import Dict, Any
import os
import subprocess

import config
from config import mcp, working_directory  # Import from config for shared resources

from click.testing import CliRunner
from ftf_cli.cli import cli


@mcp.tool()
def run_ftf_generate_module(intent: str, flavor: str, cloud: str, title: str, description: str,
                            dry_run: bool = True) -> str:
    """
    Tool to generate a new module using FTF CLI.
    Step 1 - ALWAYS use dry_run=True first. This is an irreversible action.
    Step 2 - Present the dry run output to the user in textual format.
    Step 3 - Ask if user will like to make any changes in passed arguments and modify them
    Step 4 - Call the tool without dry run
    Step 5 - Read Instructions using get_important_module_writing_instructions

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
