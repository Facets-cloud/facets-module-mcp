import sys
from typing import Dict, Any, List
import os

from facets_mcp.config import mcp, working_directory  # Import from config for shared resources
from facets_mcp.utils.ftf_command_utils import run_ftf_command, get_git_repo_info, create_temp_yaml_file
from facets_mcp.utils.output_utils import prepare_output_type_registration, compare_output_types
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.utils.yaml_utils import validate_module_output_types

# Import Swagger client components
from swagger_client.api.ui_tf_output_controller_api import UiTfOutputControllerApi
from swagger_client.rest import ApiException


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
    - properties (Dict[str, Any]): A dictionary defining the properties of the output type, as a json schema.
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
            comparison_result = compare_output_types(existing_output, properties, providers)

            if "error" in comparison_result:
                return comparison_result["error"]

            # If properties or providers are different and no override confirmation, ask for confirmation
            if not comparison_result["all_equal"] and not override_confirmation:
                diff_message = "The output type already exists with different configuration:\n"
                diff_message += comparison_result["diff_message"]
                diff_message += "\nTo override the existing configuration, please call this function again with override_confirmation=True"
                return diff_message
            elif comparison_result["all_equal"]:
                return f"Output type '{name}' already exists with the same configuration. No changes needed."

        # Prepare the output type data
        prepared_data = prepare_output_type_registration(name, properties, providers)
        if "error" in prepared_data:
            return prepared_data["error"]

        output_type_def = prepared_data["data"]

        # Create a temporary YAML file
        try:
            temp_file_path = create_temp_yaml_file(output_type_def)

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
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except Exception as e:
        error_message = f"Error registering output type: {str(e)}"
        print(error_message, file=sys.stderr)
        return error_message


@mcp.tool()
def validate_module(module_path: str, check_only: bool = False) -> str:
    """
    Tool to validate a module directory using FTF CLI.
    
    This tool checks if a Terraform module directory meets the FTF standards.
    It validates the structure, formatting, required files, and output types of the module.
    It also checks that all output types referenced in outputs and inputs blocks exist
    in the Facets control plane.

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
        
        # First, run the standard FTF validation
        # Create command
        check_flag = "--check-only" if check_only else ""
        command = [
            "ftf", "validate-directory",
            module_path
        ]
        if check_flag:
            command.append(check_flag)
            
        # Run command
        ftf_result = run_ftf_command(command)
        
        # Check if FTF validation passed
        validation_results = []
        validation_results.append("FTF Validation Results:")
        validation_results.append("=" * 40)
        validation_results.append(ftf_result)
        validation_results.append("")
        
        # Now perform output type validation
        validation_results.append("Output Type Validation:")
        validation_results.append("=" * 40)
        
        # Use the utility function for output type validation
        success, validation_message = validate_module_output_types(module_path)
        validation_results.append(validation_message)
        
        # Return combined results
        return "\n".join(validation_results)
        
    except Exception as e:
        error_message = f"Error validating module directory: {str(e)}"
        print(error_message, file=sys.stderr)
        return error_message


@mcp.tool()
def push_preview_module_to_facets_cp(module_path: str, auto_create_intent: bool = True, publishable: bool = False) -> str:
    """
    Tool to preview a module using FTF CLI. This will push a Test version of module to control plane.
    Git repository details are automatically extracted from the local working directory's .git folder.

    Args:
    - module_path (str): The path to the module.
    - auto_create_intent (bool): Flag to auto-create intent if not exists.
    - publishable (bool): Flag to indicate if the module is publishable.

    Returns:
    - str: The output from the FTF command execution.
    """
    # Get git repository details
    git_info = get_git_repo_info(working_directory)
    git_repo_url = git_info["url"]
    git_ref = git_info["ref"]

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
