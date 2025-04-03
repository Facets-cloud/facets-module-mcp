import sys
from typing import Dict, Any
import os
import subprocess

import config
from config import mcp, working_directory  # Import from config for shared resources


# Define your tools here
@mcp.tool()
def derive_module_path(relative_path: str, intent: str, flavor: str) -> str:
    """
    Tool to derive the complete module path based on parameters.

    Args:
    - relative_path (str): The relative path for the module.
    - intent (str): The intent for the module.
    - flavor (str): The flavor of the module.

    Returns:
    - str: The complete module path.
    """
    return os.path.join(working_directory, relative_path, intent, flavor, '1.0')


@mcp.tool()
def run_ftf_generate_module(intent: str, flavor: str, cloud: str, title: str, description: str) -> str:
    """
    Tool to generate a new module using FTF CLI.

    Args:
    - module_path (str): The path to the module.
    - intent (str): The intent for the module.
    - flavor (str): The flavor of the module.
    - cloud (str): The cloud provider.
    - title (str): The title of the module.
    - description (str): The description of the module.

    Returns:
    - str: The output from the FTF command execution.
    """
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
def run_ftf_add_variable(module_path: str, variable_name: str, variable_type: str, variable_description: str) -> str:
    """
    Tool to add a variable to a module configuration.

    Args:
    - module_path (str): The path to the module.
    - variable_name (str): The name of the variable to add.
    - variable_type (str): The type of the variable.
    - variable_description (str): A description for the variable.

    Returns:
    - str: The output from the FTF command execution.
    """
    command = [
        "ftf", "add-variable",
        "-n", variable_name,
        "-t", variable_type,
        "-d", variable_description,
        module_path
    ]
    return run_ftf_command(command)


@mcp.tool()
def run_ftf_validate_directory(module_path: str, check_only: bool = False) -> str:
    """
    Tool to validate a module directory using FTF CLI.

    Args:
    - module_path (str): The path to the module.
    - check_only (bool): Flag to only check formatting without applying changes.

    Returns:
    - str: The output from the FTF command execution.
    """
    check_flag = "--check-only" if check_only else ""
    command = [
        "ftf", "validate-directory",
        module_path
    ]
    if check_flag:
        command.append(check_flag)
    return run_ftf_command(command)


@mcp.tool()
def run_ftf_preview_module(module_path: str, profile: str, auto_create_intent: bool = False, publishable: bool = False,
                           git_repo_url: str = "", git_ref: str = "", publish: bool = False) -> str:
    """
    Tool to preview a module using FTF CLI.

    Args:
    - module_path (str): The path to the module.
    - profile (str): Profile to use for the operation.
    - auto_create_intent (bool): Flag to auto-create intent if not exists.
    - publishable (bool): Flag to indicate if the module is publishable.
    - git_repo_url (str): Git repository URL.
    - git_ref (str): Git reference or branch name.
    - publish (bool): Flag to publish the module after preview.

    Returns:
    - str: The output from the FTF command execution.
    """
    command = [
        "ftf", "preview-module",
        module_path,
        "-p", profile
    ]
    if auto_create_intent:
        command.append("-a")
    if publishable:
        command.append("-f")
    if git_repo_url:
        command.extend(["-g", git_repo_url])
    if git_ref:
        command.extend(["-r", git_ref])
    if publish:
        command.append("--publish")
    return run_ftf_command(command)


@mcp.tool()
def run_ftf_expose_provider(module_path: str, provider_name: str, source: str, version: str, attributes: str,
                            output: str) -> str:
    """
    Tool to expose a provider in a module output using FTF CLI.

    Args:
    - module_path (str): The path to the module.
    - provider_name (str): The name of the provider.
    - source (str): The source of the provider.
    - version (str): The version of the provider.
    - attributes (str): Attributes of the provider.
    - output (str): The output to expose provider as a part of.

    Returns:
    - str: The output from the FTF command execution.
    """
    command = [
        "ftf", "expose-provider",
        "-n", provider_name,
        "-s", source,
        "-v", version,
        "-a", attributes,
        "-o", output,
        module_path
    ]
    return run_ftf_command(command)


@mcp.tool()
def run_ftf_add_input(module_path: str, profile: str, input_name: str, display_name: str, description: str,
                      output_type: str) -> str:
    """
    Tool to add an input for a predefined output using FTF CLI.

    Args:
    - module_path (str): The path to the module.
    - profile (str): Profile to use for the operation.
    - input_name (str): Name of the input.
    - display_name (str): Display name of the input.
    - description (str): Description of the input.
    - output_type (str): The type of registered output type to be added as input.

    Returns:
    - str: The output from the FTF command execution.
    """
    command = [
        "ftf", "add-input",
        module_path, "-p", profile,
        "-n", input_name,
        "-dn", display_name,
        "-d", description,
        "-o", output_type
    ]
    return run_ftf_command(command)


def run_ftf_command(command) -> str:
    if not command[0] == 'ftf':
        return "Error: Only 'ftf' commands are allowed."
    env = os.environ.copy()
    result = subprocess.run(
        command,
        check=True,
        cwd="/Users/anshulsao/PycharmProjects/codeAssist/venv/bin/",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True,
        env=env
    )

    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)

    combined_output = result.stdout.strip() + '\n Error: ' + result.stderr.strip() if result.stderr else result.stdout.strip()
    return combined_output
