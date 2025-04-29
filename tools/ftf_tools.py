import sys
from typing import Dict, Any, List
import os
import subprocess
import tempfile
import yaml
import json

import config
from config import mcp, working_directory  # Import from config for shared resources

from click.testing import CliRunner
from ftf_cli.cli import cli

# Import Swagger client components
from swagger_client.api.ui_tf_output_controller_api import UiTfOutputControllerApi
from swagger_client.rest import ApiException
from swagger_client.configuration import Configuration
from swagger_client.api_client import ApiClient
from utils.client_utils import ClientUtils


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
def register_output_type(
    name: str,
    properties: Dict[str, Any],
    providers: List[Dict[str, str]] = None,
    override_confirmation: bool = False
) -> str:
    """
    Tool to register a new output type in the Facets control plane.
    
    This tool first checks if the output type already exists:
    - If it doesn't exist, it proceeds with registration
    - If it exists, it compares properties and providers to determine if an update is needed
    
    Args:
    - name (str): The name of the output type in the format '@namespace/name'.
    - properties (Dict[str, Any]): A dictionary defining the properties of the output type.
    - providers (List[Dict[str, str]], optional): A list of provider dictionaries, each containing 'name', 'source', and 'version'.
    - override_confirmation (bool): Flag to confirm overriding the existing output type if found with different properties/providers.
    
    Returns:
    - str: The output from the FTF command execution, error message, or request for confirmation.
    """
    try:
        # Validate the name format
        if not name.startswith('@') or '/' not in name:
            return "Error: Name should be in the format '@namespace/name'."

        # Split the name into namespace and name parts
        name_parts = name.split('/', 1)
        if len(name_parts) != 2:
            return "Error: Name should be in the format '@namespace/name'."
        
        namespace, output_name = name_parts
        
        # Initialize the API client
        api_client = ClientUtils.get_client()
        output_api = UiTfOutputControllerApi(api_client)
        
        # Check if the output already exists
        output_exists = True
        existing_output = None
        try:
            existing_output = output_api.get_output_by_name_using_get(name=output_name, namespace=namespace)
        except ApiException as e:
            if e.status == 404:
                output_exists = False
            else:
                return f"Error accessing API: {str(e)}"
        
        # If output exists, compare properties and providers
        if output_exists and existing_output:
            # Convert existing_output properties to dict for comparison
            existing_properties = existing_output.properties
            # We need to ensure proper JSON comparison
            if hasattr(existing_properties, 'to_dict'):
                existing_properties = existing_properties.to_dict()
            
            # Convert providers to comparable format
            existing_providers_dict = {}
            if existing_output.providers:
                for provider in existing_output.providers:
                    existing_providers_dict[provider.name] = {
                        "source": provider.source or "",
                        "version": provider.version or ""
                    }
            
            # Create new_providers_dict for comparison
            new_providers_dict = {}
            if providers:
                for provider in providers:
                    if 'name' not in provider:
                        return "Error: Each provider must have a 'name' field."
                    
                    provider_name = provider['name']
                    new_providers_dict[provider_name] = {
                        "source": provider.get('source', ''),
                        "version": provider.get('version', '')
                    }
            
            # Compare properties and providers
            properties_equal = json.dumps(existing_properties, sort_keys=True) == json.dumps(properties, sort_keys=True)
            providers_equal = json.dumps(existing_providers_dict, sort_keys=True) == json.dumps(new_providers_dict, sort_keys=True)
            
            # If properties or providers are different and no override confirmation, ask for confirmation
            if (not properties_equal or not providers_equal) and not override_confirmation:
                diff_message = "The output type already exists with different configuration:\n"
                
                if not properties_equal:
                    diff_message += "\nProperties Difference:\n"
                    diff_message += f"Existing: {json.dumps(existing_properties, indent=2)}\n"
                    diff_message += f"New: {json.dumps(properties, indent=2)}\n"
                
                if not providers_equal:
                    diff_message += "\nProviders Difference:\n"
                    diff_message += f"Existing: {json.dumps(existing_providers_dict, indent=2)}\n"
                    diff_message += f"New: {json.dumps(new_providers_dict, indent=2)}\n"
                
                diff_message += "\nTo override the existing configuration, please call this function again with override_confirmation=True"
                return diff_message
            elif properties_equal and providers_equal:
                return f"Output type '{name}' already exists with the same configuration. No changes needed."
        
        # Prepare the YAML content
        output_type_def = {
            "name": name,
            "properties": properties
        }
        
        # Add providers if specified
        if providers:
            providers_dict = {}
            for provider in providers:
                if 'name' not in provider:
                    return "Error: Each provider must have a 'name' field."
                
                provider_name = provider['name']
                providers_dict[provider_name] = {
                    "source": provider.get('source', ''),
                    "version": provider.get('version', '')
                }
            
            output_type_def["providers"] = providers_dict
        
        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as temp_file:
            yaml.dump(output_type_def, temp_file, default_flow_style=False)
            temp_file_path = temp_file.name
        
        try:
            # Build the command
            command = ["ftf", "register-output-type", temp_file_path]
            
            # Run the command
            result = run_ftf_command(command)
            
            # If we're overriding an existing output, add a note to the result
            if output_exists and override_confirmation:
                result = f"Successfully overrode existing output type '{name}'.\n\n{result}"
            
            return result
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    except Exception as e:
        error_message = f"Error registering output type: {str(e)}"
        print(error_message, file=sys.stderr)
        return error_message

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