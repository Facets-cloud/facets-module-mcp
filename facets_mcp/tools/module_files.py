# This file contains utility functions for handling module files

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, Field
from swagger_client.api.tf_output_management_api import TFOutputManagementApi

from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.utils.file_utils import (
    ensure_path_in_working_directory,
    generate_file_previews,
    list_files_in_directory,
    perform_text_replacement,
    read_file_content,
)
from facets_mcp.utils.output_utils import (
    find_output_types_with_provider_from_api,
    get_output_type_details_from_api,
)
from facets_mcp.utils.yaml_utils import (
    check_missing_output_types,
    read_and_validate_facets_yaml,
    validate_output_types,
    validate_yaml,
)

# Initialize client utility
try:
    if not ClientUtils.initialized:
        ClientUtils.initialize()
except Exception as e:
    print(f"Warning: Failed to initialize API client: {e!s}", file=sys.stderr)


@mcp.tool()
def list_files(module_path: str) -> str:
    """
    Lists all files in the given module path, ensuring we stay within the working directory.
    Always ask User if he wants to add any variables or use any other FTF commands

    Args:
        module_path (str): The absolute path to the module directory.

    Returns:
        str: A JSON-formatted string with operation details and file list found in module directory.
    """
    try:
        file_list = list_files_in_directory(module_path, working_directory)
        return json.dumps(
            {
                "success": True,
                "message": f"Successfully listed files in '{module_path}'.",
                "data": {"files": file_list},
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": f"Failed to list files in '{module_path}'.",
                "instructions": (
                    "Inform User: There was an error listing the files."
                    "Ask User: Would you like to try a different path?"
                ),
                "error": str(e),
            },
            indent=2,
        )


@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Reads the content of a file, ensuring it is within the working directory.
    <important>Make Sure you have Called FIRST_STEP_get_instructions first before this tool.</important>

    Args:
        file_path (str): The path to the file.

    Returns:
        str: JSON formatted response with file content or error information.
    """
    try:
        # Assuming working_directory is defined elsewhere in your code
        file_content = read_file_content(file_path, working_directory)
        return json.dumps(
            {
                "success": True,
                "message": "File read successfully.",
                "data": {"file_content": file_content},
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Failed to read the file.",
                "instructions": "Inform User: An error occurred while reading the file. Please check the file path.",
                "error": str(e),
            },
            indent=2,
        )


@mcp.tool()
def write_config_files(module_path: str, facets_yaml: str, dry_run: bool = True) -> str:
    """
    Writes facets.yaml configuration file for a Terraform module.
    <important>Make Sure you have Called FIRST_STEP_get_instructions first before this tool.</important>

    Steps for safe variable update:

    1. Always run with `dry_run=True` first. This is an irreversible action.
    2. Parse and display a diff:

       Added
       Modified (old -> new)
       Removed
    3. Ask the user if they want to edit or add variables and wait for his input.
    4. Only if the user **explicitly confirms**, run again with `dry_run=False`.

    Args:
        module_path (str): Path to the module directory.
        facets_yaml (str): Content for facets.yaml file.
        dry_run (bool): If True, returns a preview of changes without making them. Default is True.

    Returns:
        str: Success message, diff preview (if dry_run=True), or error message.
    """
    if not facets_yaml:
        return json.dumps(
            {
                "success": False,
                "message": "No content provided for facets_yaml.",
                "instructions": "Please provide valid content for facets_yaml before proceeding.",
                "error": "facets_yaml argument is empty.",
            },
            indent=2,
        )

    try:
        # Normalize paths using Path for consistent handling across platforms
        full_module_path = Path(module_path).resolve()
        working_dir = Path(working_directory).resolve()

        # Check if the module path is within working directory
        try:
            full_module_path.relative_to(working_dir)
        except ValueError:
            return json.dumps(
                {
                    "success": False,
                    "message": "Module path is outside the working directory.",
                    "instructions": "Inform User: Please provide a valid module path within the working directory.",
                    "error": f"Attempt to write files outside of the working directory. Module path: {full_module_path}, Working directory: {working_dir}",
                },
                indent=2,
            )

        # Ensure module directory exists
        full_module_path.mkdir(parents=True, exist_ok=True)

        # Run validation method on facets_yaml and module_path
        try:
            validate_yaml(str(full_module_path), facets_yaml)
        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "message": "facets.yaml validation failed.",
                    "instructions": "Fix the facets.yaml file and try again.",
                    "error": str(e),
                },
                indent=2,
            )

        # Check for outputs and validate output types
        api_client = ClientUtils.get_client()
        output_api = TFOutputManagementApi(api_client)
        output_validation_results = validate_output_types(facets_yaml, output_api)

        has_missing_types, error_message = check_missing_output_types(
            output_validation_results
        )
        if has_missing_types:
            return json.dumps(
                {
                    "success": False,
                    "message": "Output type validation failed.",
                    "instructions": "Register the missing output types first and try again.",
                    "error": error_message,
                },
                indent=2,
            )

        changes = []
        current_facets_content = ""

        # Handle facets.yaml
        facets_path = full_module_path / "facets.yaml"

        # Check if file exists and read its content
        if facets_path.exists():
            try:
                current_facets_content = facets_path.read_text(encoding="utf-8")
            except Exception as e:
                return json.dumps(
                    {
                        "success": False,
                        "message": "Failed to read existing facets.yaml.",
                        "instructions": "Inform User: Failed to read existing facets.yaml.",
                        "error": str(e),
                    },
                    indent=2,
                )

        # Generate diff for facets.yaml
        if dry_run:
            if not current_facets_content:
                changes.append("Would create new file: facets.yaml")
            else:
                changes.append("Would update existing file: facets.yaml")
        # Write facets.yaml if not in dry run mode
        else:
            try:
                facets_path.write_text(facets_yaml, encoding="utf-8")
                changes.append(f"Successfully wrote facets.yaml to {facets_path}")
            except Exception as e:
                error_msg = f"Error writing facets.yaml: {e!s}"
                changes.append(error_msg)
                print(error_msg, file=sys.stderr)

        if dry_run:
            # Create structured output with JSON
            file_preview = generate_file_previews(facets_yaml, current_facets_content)
            return json.dumps(
                {
                    "success": True,
                    "message": "Dry run completed. No files were written.",
                    "instructions": "Analyze the diff to identify variable definitions being added, modified, or removed. Present a clear summary to the user about what schema fields are changing. Ask the user explicitly if they want to proceed with these changes and wait for his input. Only if the user confirms, run the write_config_files function again with dry_run=False.",
                    "data": {
                        "type": "dry_run",
                        "module_path": str(full_module_path),
                        "changes": changes,
                        "file_preview": file_preview,
                    },
                },
                indent=2,
            )
        else:
            return json.dumps(
                {
                    "success": True,
                    "message": "facets.yaml was successfully written.",
                    "data": {
                        "module_path": str(full_module_path),
                        "changes": "\n".join(changes),
                    },
                },
                indent=2,
            )

    except Exception as e:
        error_message = f"Error processing facets.yaml: {e!s}"
        print(error_message, file=sys.stderr)
        return json.dumps(
            {
                "success": False,
                "message": "An unexpected error occurred while processing facets.yaml.",
                "instructions": "Inform User: An unexpected error occurred while processing facets.yaml.",
                "error": error_message,
            },
            indent=2,
        )


@mcp.tool()
def write_resource_file(module_path: str, file_name: str, content: str) -> str:
    """
    Writes a Terraform resource file (main.tf, variables.tf, etc.) to a module directory.

    Does NOT allow writing output(s).tf here. To update outputs.tf, use write_outputs().

    Args:
        module_path (str): Path to the module directory.
        file_name (str): Name of the file to write (e.g., "main.tf", "variables.tf").
        content (str): Content to write to the file.

    Returns:
        str: JSON string with success, message, instructions, and optional error/data fields.
    """
    try:
        if file_name == "outputs.tf" or file_name == "output.tf":
            return json.dumps(
                {
                    "success": False,
                    "message": "Writing 'outputs.tf' is not allowed through this function.",
                    "instructions": "Inform User: Please use the write_outputs() tool instead.",
                    "error": "Writing 'outputs.tf' is not allowed through write_resource_file.",
                },
                indent=2,
            )

        # Validate inputs
        if not file_name.endswith(".tf") and not file_name.endswith(".tf.tmpl"):
            return json.dumps(
                {
                    "success": False,
                    "message": f"File name must end with .tf or .tf.tmpl, got: {file_name}",
                    "instructions": "Inform User: Please provide a valid Terraform file name ending with .tf or .tf.tmpl.",
                    "error": f"Invalid file extension for file: {file_name}",
                },
                indent=2,
            )

        if file_name == "facets.yaml":
            return json.dumps(
                {
                    "success": False,
                    "message": "For facets.yaml, please use write_config_files() instead.",
                    "instructions": "Inform User: Use the write_config_files() tool for facets.yaml.",
                    "error": "Attempted to write facets.yaml via write_resource_file.",
                },
                indent=2,
            )

        full_module_path = os.path.abspath(module_path)
        if not full_module_path.startswith(os.path.abspath(working_directory)):
            return json.dumps(
                {
                    "success": False,
                    "message": "Attempt to write files outside of the working directory.",
                    "instructions": "Inform User: Please provide a valid module path within the working directory.",
                    "error": "Security restriction: Attempt to write files outside working directory.",
                },
                indent=2,
            )

        # Create module directory if it doesn't exist
        os.makedirs(full_module_path, exist_ok=True)

        file_path = os.path.join(full_module_path, file_name)

        # Write the file
        with open(file_path, "w") as f:
            f.write(content)

        return json.dumps(
            {
                "success": True,
                "message": f"Successfully wrote {file_name} to {file_path}",
                "data": {"file_path": file_path, "file_name": file_name},
            },
            indent=2,
        )

    except Exception as e:
        error_message = f"Error writing resource file: {e!s}"
        print(error_message, file=sys.stderr)
        return json.dumps(
            {
                "success": False,
                "message": "An exception occurred while writing the resource file.",
                "instructions": "Inform User: Error writing resource file.",
                "error": error_message,
            },
            indent=2,
        )


@mcp.tool()
def get_output_type_details(output_type: str) -> str:
    """
    Get details for a specific output type from the Facets control plane.

    This tool calls the get_output_by_name_using_get API endpoint to retrieve
    information about an output type, including its properties and providers.

    Args:
        output_type (str): The output type name in format '@namespace/name'

    Returns:
        str: JSON-formatted string with result status, message, instructions, output type details or error information
    """
    result = get_output_type_details_from_api(output_type)

    if "error" in result:
        return json.dumps(
            {
                "success": False,
                "message": f"Failed to retrieve output type '{output_type}'.",
                "instructions": f"Inform User: Failed to retrieve output type '{output_type}'.",
                "error": result["error"],
            },
            indent=2,
        )

    return json.dumps(
        {
            "success": True,
            "message": f"Successfully retrieved output type '{output_type}'.",
            "data": result,
        },
        indent=2,
    )


@mcp.tool()
def find_output_types_with_provider(provider_source: str) -> str:
    """
    This tool finds all output types that include a specific provider source, which can be used as inputs for
    module configurations.

    Args:
        provider_source (str): The provider source name to search for.

    Returns:
        str: JSON string containing the formatted output type information.
    """
    raw_response = find_output_types_with_provider_from_api(provider_source)
    parsed_response = json.loads(raw_response)

    if parsed_response.get("status") == "success":
        outputs = parsed_response.get("outputs", [])
        return json.dumps(
            {
                "success": True,
                "message": f"Found {len(outputs)} output type(s) for provider source '{provider_source}'.",
                "data": {"outputs": outputs, "count": len(outputs)},
            },
            indent=2,
        )
    else:
        return json.dumps(
            {
                "success": False,
                "message": f"Failed to retrieve output types for provider source {provider_source}.",
                "instructions": f"Inform User: Failed to retrieve output types for provider source {provider_source}.",
                "error": parsed_response.get("message", "Unknown error occurred."),
            },
            indent=2,
        )


@mcp.tool()
def list_all_output_types() -> str:
    """
    List all output types from the Facets control plane.

    Returns:
        str: List of output types.
    """
    try:
        api_client = ClientUtils.get_client()
        output_api = TFOutputManagementApi(api_client)
        response = output_api.get_all_outputs()
        if not response:
            return json.dumps(
                {
                    "success": True,
                    "message": "No output types found.",
                    "data": {"output_names": []},
                },
                indent=2,
            )
        if not isinstance(response, list):
            response = [response]
        output_names = []
        for output in response:
            namespace = getattr(output, "namespace", None) or "@outputs"
            name = getattr(output, "name", None)
            if namespace and name:
                output_names.append(f"{namespace}/{name}")
        return json.dumps(
            {
                "success": True,
                "message": f"Found {len(output_names)} output type(s).",
                "data": {"output_names": output_names, "count": len(output_names)},
            },
            indent=2,
        )
    except Exception as e:
        error_message = f"Error listing all output types: {e!s}"
        print(error_message, file=sys.stderr)
        return json.dumps(
            {
                "success": False,
                "message": "Failed to list all output types.",
                "instructions": "Inform User: Failed to list all output types.",
                "error": error_message,
            },
            indent=2,
        )


# Pydantic models for structured output fields
class OutputField(BaseModel):
    """Model for a single output field with required sensitive flag."""

    value: Any = Field(..., description="The actual value of the field")
    sensitive: bool = Field(
        ..., description="Whether this field contains sensitive data (required)"
    )


@mcp.tool()
def write_outputs(
    module_path: str,
    output_attributes: Dict[str, OutputField] = None,
    output_interfaces: Dict[str, OutputField] = None,
) -> str:
    """
    Write the outputs.tf file for a module with properly formatted Terraform locals block.

    Each field must have 'value' (any type: string, bool, number, list, dict) and 'sensitive' (bool) keys.

    Args:
        module_path (str): Path to the module directory (must contain facets.yaml).
        output_attributes (dict): Map where each field is: {"value": <any type>, "sensitive": bool}
        output_interfaces (dict): Map where each field is: {"value": <any type>, "sensitive": bool}

    Example:
        write_outputs(
            module_path="/path/to/module",
            output_attributes={
                "instance_id": {"value": "aws_instance.example.id", "sensitive": False},
                "config": {"value": {"region": "us-east-1", "zone": "a"}, "sensitive": False},
                "api_keys": {"value": ["key1", "key2"], "sensitive": True},
                "enabled": {"value": True, "sensitive": False}
            }
        )

    Returns:
        str: JSON formatted success or error message.
    """
    try:
        # Handle None defaults
        if output_attributes is None:
            output_attributes = {}
        if output_interfaces is None:
            output_interfaces = {}

        full_module_path = ensure_path_in_working_directory(
            module_path, working_directory
        )

        # Initialize API client for validation
        api_client = ClientUtils.get_client()
        output_api = TFOutputManagementApi(api_client)

        # Read and validate facets.yaml
        success, facets_yaml_content, error_message = read_and_validate_facets_yaml(
            module_path, output_api
        )
        if not success:
            return json.dumps(
                {
                    "success": False,
                    "message": "Failed to validate facets.yaml file.",
                    "instructions": "Inform User: Failed to validate facets.yaml file.",
                    "error": error_message,
                },
                indent=2,
            )

        # Helper function to validate and process output fields
        def process_output_fields(fields_dict, field_type_name):
            """Validate fields and return processed dict with sensitive field list."""
            validated = {}
            sensitive_fields = []

            for key, field_data in fields_dict.items():
                try:
                    # If it's already an OutputField instance, use it directly
                    if isinstance(field_data, OutputField):
                        validated_field = field_data
                    # Otherwise try to parse it as a dict
                    elif isinstance(field_data, dict):
                        validated_field = OutputField(**field_data)
                    else:
                        raise ValueError(
                            "Field must be an OutputField instance or dict with 'value' and 'sensitive' keys"
                        )

                    validated[key] = validated_field
                    if validated_field.sensitive:
                        sensitive_fields.append(key)

                except Exception as e:
                    return None, json.dumps(
                        {
                            "success": False,
                            "message": f"Invalid structure for field '{key}' in {field_type_name}",
                            "error": str(e),
                            "instructions": "Each field must have 'value' and 'sensitive' keys: {'value': <any>, 'sensitive': bool}",
                        },
                        indent=2,
                    )

            return validated, sensitive_fields

        # Process attributes
        validated_attributes, result = process_output_fields(
            output_attributes, "output_attributes"
        )
        if validated_attributes is None:
            return result  # result contains the error message
        sensitive_attributes = result  # result contains the sensitive field list

        # Process interfaces
        validated_interfaces, result = process_output_fields(
            output_interfaces, "output_interfaces"
        )
        if validated_interfaces is None:
            return result  # result contains the error message
        sensitive_interfaces = result  # result contains the sensitive field list

        # Helper to render values correctly for Terraform
        def render_terraform_value(v):
            # Standard rendering for values
            if isinstance(v, bool):
                return str(v).lower()
            elif isinstance(v, (int, float)):
                return str(v)
            elif isinstance(v, str):
                if "." in v and not v.startswith("${"):
                    return v
                else:
                    return json.dumps(v)
            elif isinstance(v, list):
                return "[" + ", ".join(render_terraform_value(i) for i in v) + "]"
            elif isinstance(v, dict):
                tf_lines = ["{"]
                for k, val in v.items():
                    tf_lines.append(f"  {k} = {render_terraform_value(val)}")
                tf_lines.append("}")
                return "\n".join(tf_lines)
            else:
                return json.dumps(v)

        # Helper to build terraform block for a field set
        def build_terraform_block(block_name, validated_fields, sensitive_fields):
            """Build terraform configuration block for output fields."""
            lines = []
            if validated_fields:
                lines.append(f"  {block_name} = {{")
                for k, field_model in validated_fields.items():
                    rendered_value = render_terraform_value(field_model.value)
                    if field_model.sensitive:
                        lines.append(f"    {k} = sensitive({rendered_value})")
                    else:
                        lines.append(f"    {k} = {rendered_value}")

                # Add secrets array if there are sensitive fields
                if sensitive_fields:
                    secrets_str = (
                        "["
                        + ", ".join(f'"{field}"' for field in sensitive_fields)
                        + "]"
                    )
                    lines.append(f"    secrets = {secrets_str}")

                lines.append("  }")
            return lines

        # Build outputs.tf content
        content_lines = ["locals {"]
        content_lines.extend(
            build_terraform_block(
                "output_attributes", validated_attributes, sensitive_attributes
            )
        )
        content_lines.extend(
            build_terraform_block(
                "output_interfaces", validated_interfaces, sensitive_interfaces
            )
        )
        content_lines.append("}")

        content = "\n".join(content_lines)

        # Write to outputs.tf
        file_path = os.path.join(full_module_path, "outputs.tf")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return json.dumps(
            {
                "success": True,
                "message": f"Successfully wrote outputs.tf to {file_path}",
            },
            indent=2,
        )

    except Exception as e:
        error_message = f"Error writing outputs.tf: {e!s}"
        print(error_message, file=sys.stderr)
        return json.dumps(
            {
                "success": False,
                "message": "Error writing outputs.tf.",
                "instructions": "Inform User: Error writing outputs.tf.",
                "error": error_message,
            },
            indent=2,
        )


@mcp.tool()
def write_readme_file(module_path: str, content: str) -> str:
    """
    Writes a README.md file for the module directory.
    This tool is intended for AI to generate the README content for the module.

    Args:
        module_path (str): Path to the module directory.
        content (str): Content to write to README.md.

    Returns:
        str: JSON string with success status, message, instructions, and optional error/data.
    """
    try:
        full_module_path = os.path.abspath(module_path)
        if not full_module_path.startswith(os.path.abspath(working_directory)):
            return json.dumps(
                {
                    "success": False,
                    "message": "Attempt to write files outside of the working directory.",
                    "instructions": "Inform User: Attempt to write files outside of the working directory.",
                    "error": f"Invalid module path: '{module_path}' is outside of the working directory '{working_directory}'.",
                },
                indent=2,
            )

        # Create module directory if it doesn't exist
        os.makedirs(full_module_path, exist_ok=True)

        readme_path = os.path.join(full_module_path, "README.md")

        with open(readme_path, "w") as f:
            f.write(content)

        return json.dumps(
            {
                "success": True,
                "message": f"Successfully wrote README.md to {readme_path}",
                "data": {"readme_path": readme_path},
            },
            indent=2,
        )
    except Exception as e:
        error_message = f"Error writing README.md file: {e!s}"
        print(error_message, file=sys.stderr)
        return json.dumps(
            {
                "success": False,
                "message": "Unexpected error occurred while writing the README.md file.",
                "instructions": "Inform User: Error writing README.md file",
                "error": str(e),
            },
            indent=2,
        )


@mcp.tool()
def write_generic_file(module_path: str, file_name: str, content: str) -> str:
    """
    Writes a generic file to the module directory, except for .tf files, facets.yaml, or README.md.
    Can be used to add supporting files like Python or Bash scripts if needed by the module.

    Fails if trying to write a forbidden file. Checks working directory as in other tools.

    Args:
        module_path (str): Path to the module directory.
        file_name (str): Name of the file to write.
        content (str): Content to write to the file.

    Returns:
        str: JSON string with success status, message, instructions, and optional error/data.
    """
    forbidden = ["facets.yaml", "README.md"]
    if file_name.lower().endswith(".tf") or file_name in forbidden:
        return json.dumps(
            {
                "success": False,
                "message": f"Writing '{file_name}' is not allowed with this tool.",
                "instructions": "Use the dedicated tool for .tf, facets.yaml, or README.md files.",
                "error": f"Forbidden file type: {file_name}",
            },
            indent=2,
        )
    try:
        full_module_path = Path(module_path).resolve()
        working_dir = Path(working_directory).resolve()
        # Check if the module path is within working directory
        try:
            full_module_path.relative_to(working_dir)
        except ValueError:
            return json.dumps(
                {
                    "success": False,
                    "message": "Module path is outside the working directory.",
                    "instructions": "Inform User: Please provide a valid module path within the working directory.",
                    "error": f"Attempt to write files outside of the working directory. Module path: {full_module_path}, Working directory: {working_dir}",
                },
                indent=2,
            )
        # Ensure module directory exists
        full_module_path.mkdir(parents=True, exist_ok=True)
        file_path = full_module_path / file_name
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return json.dumps(
            {
                "success": True,
                "message": f"Successfully wrote {file_name} to {file_path}",
                "data": {"file_path": str(file_path), "file_name": file_name},
            },
            indent=2,
        )
    except Exception as e:
        error_message = f"Error writing file: {e!s}"
        return json.dumps(
            {
                "success": False,
                "message": "Unexpected error occurred while writing the file.",
                "instructions": "Inform User: Error writing file.",
                "error": error_message,
            },
            indent=2,
        )


@mcp.tool()
def edit_file_block(
    file_path: str, old_string: str, new_string: str, expected_replacements: int = 1
) -> str:
    """
    Apply surgical edits to specific blocks of text in a file.
    <important>Make Sure you have Called FIRST_STEP_get_instructions first before this tool.</important>

    Makes precise changes to files by finding and replacing exact text matches.
    This is safer than rewriting entire files.

    RESTRICTIONS:
    - Cannot edit outputs.tf files - use write_outputs tool instead
    - Cannot edit facets.yaml files - use write_config_files tool instead

    Best practices:
    - Include enough context in old_string to make it unique
    - Use expected_replacements=1 for safety (default)
    - For multiple replacements, specify the exact count expected

    Args:
        file_path (str): Path to the file to edit (must be within working directory)
        old_string (str): Exact text to find and replace (include context for uniqueness)
        new_string (str): Replacement text
        expected_replacements (int): Expected number of matches (default: 1, prevents unintended changes)

    Returns:
        str: JSON formatted response with success status, message, and optional error details
    """
    try:
        # Check for forbidden files before any other processing
        file_name = os.path.basename(file_path)

        # Block editing of outputs.tf files
        if file_name.lower() in ["outputs.tf", "output.tf"]:
            return json.dumps(
                {
                    "success": False,
                    "message": "Editing outputs.tf files is not allowed with this tool.",
                    "error": "Use write_outputs tool to update outputs.tf file",
                    "instructions": "Use write_outputs tool to update outputs.tf file",
                },
                indent=2,
            )

        # Block editing of facets.yaml files
        if file_name.lower() == "facets.yaml":
            return json.dumps(
                {
                    "success": False,
                    "message": "Editing facets.yaml files is not allowed with this tool.",
                    "error": "Use write_config_files tool to update facets.yaml file",
                    "instructions": "Use write_config_files tool to update facets.yaml file",
                },
                indent=2,
            )

        # Validate file path is within working directory
        full_file_path = ensure_path_in_working_directory(file_path, working_directory)

        # Read current file content
        try:
            current_content = read_file_content(file_path, working_directory)
        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "message": f"Failed to read file '{file_path}'",
                    "error": str(e),
                },
                indent=2,
            )

        # Perform the text replacement
        success, result, info_message = perform_text_replacement(
            current_content, old_string, new_string, expected_replacements
        )

        if not success:
            return json.dumps(
                {
                    "success": False,
                    "message": "Text replacement failed",
                    "error": result,  # result contains error message when success=False
                },
                indent=2,
            )

        # Write the modified content back to file
        try:
            with open(full_file_path, "w", encoding="utf-8") as f:
                f.write(result)  # result contains new content when success=True

            return json.dumps(
                {
                    "success": True,
                    "message": f"{info_message} in '{file_path}'",
                    "data": {
                        "file_path": file_path,
                        "replacements_made": expected_replacements,
                    },
                },
                indent=2,
            )

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "message": "Failed to write changes to file",
                    "error": str(e),
                },
                indent=2,
            )

    except Exception as e:
        error_message = f"Error during file edit operation: {e!s}"
        return json.dumps({"success": False, "error": error_message}, indent=2)
