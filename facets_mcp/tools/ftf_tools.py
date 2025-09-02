import json
import os
from typing import Any

# Import Swagger client components
from swagger_client.api.tf_output_management_api import TFOutputManagementApi
from swagger_client.rest import ApiException

from facets_mcp.config import (
    mcp,
    working_directory,
)  # Import from config for shared resources
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.utils.ftf_command_utils import (
    create_temp_yaml_file,
    get_git_repo_info,
    run_ftf_command,
)
from facets_mcp.utils.intent_utils import check_intent_and_intent_details
from facets_mcp.utils.output_utils import (
    compare_output_types,
    infer_properties_from_interfaces_and_attributes,
    prepare_output_type_registration,
)
from facets_mcp.utils.validation_utils import validate_no_provider_blocks
from facets_mcp.utils.yaml_utils import validate_module_output_types


@mcp.tool()
def generate_module_with_user_confirmation(
    intent: str,
    flavor: str,
    cloud: str,
    title: str,
    description: str,
    dry_run: bool = True,
) -> str:
    """
    ⚠️ IMPORTANT: REQUIRES USER CONFIRMATION ⚠️
    This function performs an irreversible action

    Tool to generate a new module using FTF CLI.
    Step 1 - ALWAYS use dry_run=True first. This is an irreversible action.
    Step 2 - Present the dry run output to the user in textual format.
    Step 3 - Ask if user will like to make any changes in passed arguments and modify them
    Step 4 - Call the tool without dry run

    Args:
    - intent (str): The intent for the module.
    - flavor (str): The flavor of the module.
    - cloud (str): The cloud provider.
    - title (str): The title of the module.
    - description (str): The description of the module.
    - dry_run (bool): If True, returns a description of the generation without executing. MUST set to True initially.

    Returns:
    - str: A JSON string with the output from the FTF command execution.
    """
    if dry_run:
        return json.dumps(
            {
                "success": True,
                "message": (
                    f"Dry run: The following module will be generated with intent='{intent}', flavor='{flavor}', cloud='{cloud}', title='{title}', description='{description}'. "
                    f"Get confirmation from the user before running with dry_run=False to execute the generation."
                ),
                "instructions": (
                    "Inform User: The module will be generated with the following configuration."
                    "Ask User: Review and confirm or request changes before proceeding with actual generation."
                ),
                "data": {
                    "intent": intent,
                    "flavor": flavor,
                    "cloud": cloud,
                    "title": title,
                    "description": description,
                },
            },
            indent=2,
        )

    command = [
        "ftf",
        "generate-module",
        "-i",
        intent,
        "-f",
        flavor,
        "-c",
        cloud,
        "-t",
        title,
        "-d",
        description,
        working_directory,
    ]

    try:
        output = run_ftf_command(command)
        return json.dumps(
            {
                "success": True,
                "message": "Module generation successful.",
                "data": {"output": output},
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Module generation failed.",
                "instructions": "Inform User: An error occurred while generating the module.",
                "error": str(e),
            },
            indent=2,
        )


@mcp.tool()
def register_output_type(
    name: str,
    interfaces: dict[str, Any] | None = None,
    attributes: dict[str, Any] | None = None,
    providers: list[dict[str, str]] | None = None,
    override_confirmation: bool = False,
) -> str:
    """
    Tool to register a new output type in the Facets control plane.

    This tool first checks if the output type already exists:
    - If it doesn't exist, it proceeds with registration
    - If it exists, it compares properties and providers to determine if an update is needed

    Args:
    - name (str): The name of the output type in the format '@namespace/name'.
    - interfaces (Dict[str, Any], optional): A dictionary defining the output interfaces, similar to write_outputs, but as json schema.
    - attributes (Dict[str, Any], optional): A dictionary defining the output attributes, similar to write_outputs, but as json schema.
    - providers (List[Dict[str, str]], optional): A list of provider dictionaries, each containing 'name', 'source', and 'version'.
    - override_confirmation (bool): Flag to confirm overriding the existing output type if found with different properties/providers.

    Returns:
    - str: A JSON string with the output from the FTF command execution, error message, or request for confirmation.
    """
    try:
        # Validate inputs
        if interfaces is None and attributes is None:
            return json.dumps(
                {
                    "success": False,
                    "instructions": "Please provide at least one of interfaces or attributes.",
                    "error": "Neither interfaces nor attributes provided.",
                },
                indent=2,
            )

        # Validate the name format
        if not name.startswith("@") or "/" not in name:
            return json.dumps(
                {
                    "success": False,
                    "message": "Invalid output type name format. Name should be in the format '@namespace/name'.",
                    "instructions": "Ask User: Please provide name in the format '@namespace/name'.",
                    "error": "Name should be in the format '@namespace/name'.",
                },
                indent=2,
            )

        # Split the name into namespace and name parts
        name_parts = name.split("/", 1)
        if len(name_parts) != 2:
            return json.dumps(
                {
                    "success": False,
                    "message": "Invalid output type name format. Name should be in the format '@namespace/name'.",
                    "instructions": "Ask User: Please provide name in the format '@namespace/name'.",
                    "error": "Name should be in the format '@namespace/name'.",
                },
                indent=2,
            )

        namespace, output_name = name_parts

        # Infer properties from interfaces and attributes
        properties = infer_properties_from_interfaces_and_attributes(
            interfaces, attributes
        )

        if "error" in properties:
            return json.dumps(
                {
                    "success": False,
                    "message": "Failed to infer properties from interfaces and attributes.",
                    "instructions": "Inform User: Failed to infer properties from interfaces and attributes.",
                    "error": properties["error"],
                },
                indent=2,
            )

        # Initialize the API client
        api_client = ClientUtils.get_client()
        output_api = TFOutputManagementApi(api_client)

        # Check if the output already exists
        output_exists = True
        existing_output = None
        try:
            existing_output = output_api.get_output_by_name(
                name=output_name, namespace=namespace
            )
        except ApiException as e:
            if e.status == 404:
                output_exists = False
            else:
                return json.dumps(
                    {
                        "success": False,
                        "message": "Error accessing API.",
                        "instructions": "Inform User: Error accessing API.",
                        "error": f"Error accessing API: {e!s}",
                    },
                    indent=2,
                )
        # If output exists, compare properties and providers
        if output_exists and existing_output:
            comparison_result = compare_output_types(
                existing_output, properties, providers
            )

            if "error" in comparison_result:
                return json.dumps(
                    {
                        "success": False,
                        "message": "Failed to compare existing output type with new properties and providers.",
                        "instructions": "Inform User: Failed to compare existing output type with new properties and providers.",
                        "error": comparison_result["error"],
                    },
                    indent=2,
                )
            # If properties or providers are different and no override confirmation, ask for confirmation
            if not comparison_result["all_equal"] and not override_confirmation:
                diff_message = (
                    "The output type already exists with different configuration:\n"
                )
                diff_message += comparison_result["diff_message"]
                return json.dumps(
                    {
                        "success": False,
                        "message": diff_message,
                        "instructions": "Ask User: To override the existing configuration, please call this function again with override_confirmation=True.",
                    },
                    indent=2,
                )

            elif comparison_result["all_equal"]:
                return json.dumps(
                    {
                        "success": True,
                        "message": f"Output type '{name}' already exists with the same configuration. No changes needed.",
                        "instructions": f"Inform User: Output type '{name}' already exists with the same configuration. No changes needed.",
                    },
                    indent=2,
                )

        # Prepare the output type data
        prepared_data = prepare_output_type_registration(name, properties, providers)
        if "error" in prepared_data:
            return json.dumps(
                {
                    "success": False,
                    "message": "Error preparing data for registering a new output type.",
                    "instructions": "Inform User: Error preparing data for registering a new output type.",
                    "error": prepared_data["error"],
                },
                indent=2,
            )

        output_type_def = prepared_data["data"]

        # Create a temporary YAML file
        try:
            temp_file_path = create_temp_yaml_file(output_type_def)

            # Build the command
            command = [
                "ftf",
                "register-output-type",
                temp_file_path,
                "--inferred-from-module",
            ]

            # Run the command
            result = run_ftf_command(command)

            # If we're overriding an existing output, add a note to the result
            if output_exists and override_confirmation:
                result = (
                    f"Successfully overrode existing output type '{name}'.\n\n{result}"
                )

            return json.dumps(
                {
                    "success": True,
                    "message": result,
                    "instructions": f"Inform User: Successfully overrode existing output type '{name}'.",
                },
                indent=2,
            )

        finally:
            # Clean up the temporary file
            if "temp_file_path" in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error registering a new output type in the Facets control plane.",
                "instructions": "Inform User: Error registering a new output type in the Facets control plane.",
                "error": str(e),
            },
            indent=2,
        )


@mcp.tool()
def validate_module(
    module_path: str,
    check_only: bool = False,
    skip_terraform_validation_if_provider_not_found: bool = False,
) -> str:
    """
    Tool to validate a module directory using FTF CLI.

    This tool checks if a Terraform module directory meets the FTF standards.
    It validates the structure, formatting, required files, and output types of the module.
    It also checks that all output types referenced in outputs and inputs blocks exist
    in the Facets control plane.

    Args:
    - module_path (str): The path to the module.
    - check_only (bool): Flag to only check formatting without applying changes.
    - skip_terraform_validation_if_provider_not_found (bool): Flag to skip terraform validation during the process - send as true only if you see "Provider configuration not present" while validating.

    Returns:
    - str: A JSON string with the output from the FTF command execution or error message if validation fails.
    """
    try:
        # Validate module path exists
        if not os.path.exists(module_path):
            return json.dumps(
                {
                    "success": False,
                    "message": f"Module path '{module_path}' does not exist.",
                    "instructions": "Inform User: Module path does not exist.",
                    "error": f"Module path '{module_path}' does not exist.",
                },
                indent=2,
            )
        # Validate module path is a directory
        if not os.path.isdir(module_path):
            return json.dumps(
                {
                    "success": False,
                    "message": f"Module path '{module_path}' is not a directory.",
                    "instructions": "Inform User: Module path is not a directory.",
                    "error": f"Module path '{module_path}' is not a directory.",
                },
                indent=2,
            )

        # First, run the standard FTF validation
        # Create command
        command = ["ftf", "validate-directory", module_path]
        if check_only:
            command.append("--check-only")
        if skip_terraform_validation_if_provider_not_found:
            command.extend(["--skip-terraform-validation", "true"])

        # Run command
        run_ftf_command(command)

        # Validate no provider blocks in Terraform files
        provider_validation_success, provider_validation_message = (
            validate_no_provider_blocks(module_path)
        )
        if not provider_validation_success:
            return json.dumps(
                {
                    "success": False,
                    "instructions": "Failed provider block validation. Inform user about the issue and suggest using exposed providers in facets.yaml instead.",
                    "error": provider_validation_message,
                },
                indent=2,
            )

        # Use the utility function for output type validation
        success, validation_message = validate_module_output_types(module_path)
        if not success:
            return json.dumps(
                {
                    "success": False,
                    "instructions": "Failed to validate module directory using FTF CLI. Try to fix the issues and run again, or ask the user to fix it if unclear what might be the issue.",
                    "error": f"Failed to validate module directory using FTF CLI. {validation_message}",
                },
                indent=2,
            )

        # INTENT VALIDATION (at the end)
        intent_ok, intent_message = check_intent_and_intent_details(module_path)
        if not intent_ok:
            return json.dumps(
                {
                    "success": False,
                    "instructions": intent_message,
                },
                indent=2,
            )

        # Return combined results
        return json.dumps(
            {"success": True, "message": "Module directory is valid!"}, indent=2
        )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "instructions": "Module validation failed. Try to resolve the error if possible and retry, otherwise inform the user.",
                "error": str(e),
            },
            indent=2,
        )


@mcp.tool()
def push_preview_module_to_facets_cp(
    module_path: str,
    auto_create_intent: bool = True,
    publishable: bool = False,
    skip_terraform_validation_if_provider_not_found: bool = False,
) -> str:
    """
    Tool to preview a module using FTF CLI. This will push a Test version of module to control plane.
    Git repository details are automatically extracted from the local working directory's .git folder.

    Args:
    - module_path (str): The path to the module.
    - auto_create_intent (bool): Flag to auto-create intent if not exists.
    - publishable (bool): Flag to indicate if the module is publishable.
    - skip_terraform_validation_if_provider_not_found (bool): Flag to skip terraform validation during the process - send as true only if you see "Provider configuration not present" while validating.

    Returns:
    - str: A JSON string with the output from the FTF command execution.
    """
    try:
        # INTENT VALIDATION (before running FTF command)
        intent_ok, intent_message = check_intent_and_intent_details(module_path)
        if not intent_ok:
            return json.dumps(
                {
                    "success": False,
                    "instructions": intent_message,
                    "error": intent_message,
                },
                indent=2,
            )
        # Get git repository details
        git_info = get_git_repo_info(working_directory)
        git_repo_url = git_info["url"]
        git_ref = git_info["ref"]

        command = ["ftf", "preview-module", module_path]
        if auto_create_intent:
            command.extend(["-a", str(auto_create_intent)])
        if publishable:
            command.extend(["-f", str(publishable)])
        if skip_terraform_validation_if_provider_not_found:
            command.extend(["--skip-terraform-validation", "true"])

        # Always include git details (now from local repository)
        command.extend(["-g", git_repo_url])
        command.extend(["-r", git_ref])

        # do not update the output type - it should have already been created using register_output_type tool
        command.extend(["--skip-output-write", "true"])

        message = run_ftf_command(command)

        return json.dumps(
            {
                "success": True,
                "message": message,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "instructions": "Try to resolve the error if possible, otherwise inform the user: Failed to push module preview to the control plane.",
                "error": str(e),
            },
            indent=2,
        )
