"""
Utilities for YAML processing and validation in the facets-module-mcp project.
Contains helper functions for validating YAML files against schema requirements.
"""

import os
import sys
from typing import Any

import yaml

# Import Swagger client components (used by validate_module_output_types)
from facets_mcp.utils.client_utils import ClientUtils

# Import from project modules
from facets_mcp.utils.ftf_command_utils import run_ftf_command


def validate_yaml(module_path: str, yaml_content: str) -> None:
    """
    Validate yaml content against FTF requirements.
    Writes yaml_content to a temporary file in module_path for validation, then deletes it.

    Args:
        module_path (str): The path to the module directory
        yaml_content (str): The YAML content to validate

    Returns:
        str: An error message string if validation fails, or empty string if valid.
    """
    import os

    temp_path = os.path.join(os.path.abspath(module_path), "facets.yaml.new")
    try:
        with open(temp_path, "w") as temp_file:
            temp_file.write(yaml_content)
    except Exception as e:
        raise RuntimeError(str(e))

    command = ["ftf", "validate-facets", "--filename", "facets.yaml.new", module_path]

    try:
        run_ftf_command(command)
    except Exception as e:
        raise RuntimeError(str(e))
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass


def validate_output_types(facets_yaml_content: str, output_api=None) -> dict[str, Any]:
    """
    Validate output types in facets.yaml.
    Checks if output types mentioned in both the outputs and inputs blocks exist in the Facets control plane.

    Args:
        facets_yaml_content (str): Content of facets.yaml file
        output_api: Optional UI TF Output Controller API instance

    Returns:
        Dict[str, Any]: Dictionary with validation results including missing outputs from both sources
    """
    try:
        # Parse YAML content
        facets_data = yaml.safe_load(facets_yaml_content)
        if not facets_data:
            return {}

        # Track output types separately based on their source
        output_types_from_outputs = []
        output_types_from_inputs = []

        # Extract output types from outputs block
        if "outputs" in facets_data:
            outputs = facets_data.get("outputs", {})
            for output_name, output_def in outputs.items():
                if "type" in output_def:
                    output_type = output_def["type"]
                    if output_type not in output_types_from_outputs:
                        output_types_from_outputs.append(output_type)

        # Extract output types from inputs block
        if "inputs" in facets_data:
            inputs = facets_data.get("inputs", {})
            for input_name, input_def in inputs.items():
                if isinstance(input_def, dict) and "type" in input_def:
                    input_type = input_def["type"]
                    # Check if the input is using an output type (starts with @)
                    if (
                        input_type.startswith("@")
                        and input_type not in output_types_from_inputs
                    ):
                        output_types_from_inputs.append(input_type)

        # Combine all output types for validation
        all_output_types = list(
            set(output_types_from_outputs + output_types_from_inputs)
        )

        if not all_output_types:
            return {}

        # Skip validation if no API client is provided
        if not output_api:
            return {"warning": "Output types not validated: API client not provided"}

        # Get all outputs from the API in a single call
        try:
            all_existing_outputs = output_api.get_all_outputs()
            # Create a set of existing output identifiers for fast lookup
            existing_output_ids = set()
            for output in all_existing_outputs:
                if hasattr(output, "name") and output.name:
                    namespace = getattr(output, "namespace", None) or "@outputs"
                    output_id = f"{namespace}/{output.name}"
                    existing_output_ids.add(output_id)

                    # Add both @outputs and @output variants for compatibility
                    if namespace == "@outputs":
                        existing_output_ids.add(f"@output/{output.name}")
                    elif namespace == "@output":
                        existing_output_ids.add(f"@outputs/{output.name}")
        except Exception as e:
            print(f"Error fetching all outputs: {e!s}", file=sys.stderr)
            return {"error": f"Error fetching all outputs: {e!s}"}

        # Check if output types exist in the fetched results
        missing_from_outputs = []
        missing_from_inputs = []

        for output_type in all_output_types:
            # Skip if not in @namespace/name format
            if not output_type.startswith("@") or "/" not in output_type:
                continue

            # Check if the output type exists in our fetched results
            if output_type not in existing_output_ids:
                # Determine which source this missing type comes from
                if output_type in output_types_from_outputs:
                    missing_from_outputs.append(output_type)
                if output_type in output_types_from_inputs:
                    missing_from_inputs.append(output_type)

        return {
            "missing_from_outputs": missing_from_outputs,
            "missing_from_inputs": missing_from_inputs,
        }

    except Exception as e:
        print(f"Error validating output types: {e!s}", file=sys.stderr)
        return {"error": f"Error validating output types: {e!s}"}


def check_missing_output_types(
    output_validation_results: dict[str, Any],
) -> tuple[bool, str]:
    """
    Check for missing output types and generate appropriate error messages.

    This function checks for output types that are referenced in both the outputs and inputs
    blocks of facets.yaml but don't exist in the Facets control plane. It provides different
    guidance based on whether the missing types are in outputs or inputs.

    Args:
        output_validation_results (Dict[str, Any]): Results from validate_output_types

    Returns:
        Tuple[bool, str]: (has_missing_types, error_message)
            - has_missing_types: True if missing output types were found
            - error_message: A formatted error message if missing types were found, empty string otherwise
    """
    if not output_validation_results:
        return False, ""

    missing_from_outputs = output_validation_results.get("missing_from_outputs", [])
    missing_from_inputs = output_validation_results.get("missing_from_inputs", [])

    if not missing_from_outputs and not missing_from_inputs:
        return False, ""

    error_parts = []

    # Handle missing output types from outputs block
    if missing_from_outputs:
        error_parts.append(
            "Validation failed: Missing output types in 'outputs' block:"
        )
        error_parts.append(
            "  These output types need to be registered first using register_output_type:"
        )
        for output_type in missing_from_outputs:
            error_parts.append(f"  - {output_type}")
        error_parts.append("")

    # Handle missing output types from inputs block
    if missing_from_inputs:
        error_parts.append("Validation failed: Missing output types in 'inputs' block:")
        error_parts.append(
            "  These output types are expected from other modules that don't exist yet:"
        )
        for output_type in missing_from_inputs:
            error_parts.append(f"  - {output_type}")
        error_parts.append(
            "  You need to create or configure modules that produce these output types."
        )
        error_parts.append("")

    # Add general guidance
    if missing_from_outputs and not missing_from_inputs:
        error_parts.append(
            "Please register the missing output types using register_output_type before writing the configuration."
        )
    elif not missing_from_outputs and missing_from_inputs:
        error_parts.append(
            "Please ensure that modules producing the required output types are properly configured."
        )
    else:
        error_parts.append("Please:")
        error_parts.append(
            "1. Register the missing output types using register_output_type"
        )
        error_parts.append(
            "2. Ensure that modules producing the required input types are properly configured"
        )

    return True, "\n".join(error_parts).rstrip()


def read_and_validate_facets_yaml(
    module_path: str, output_api=None
) -> tuple[bool, str, str]:
    """
    Read facets.yaml from a module path and validate output types.

    Args:
        module_path (str): Path to the module directory
        output_api: Optional UI TF Output Controller API instance

    Returns:
        Tuple[bool, str, str]: (success, facets_yaml_content, error_message)
            - success: True if facets.yaml was found and valid, False otherwise
            - facets_yaml_content: The content of facets.yaml if found, empty string otherwise
            - error_message: An error message if there was a problem, empty string otherwise
    """
    # Check if facets.yaml exists in the module path
    facets_path = os.path.join(os.path.abspath(module_path), "facets.yaml")
    if not os.path.exists(facets_path):
        return (
            False,
            "",
            "Error: facets.yaml not found in module path. Please call write_config_files first to create the facets.yaml configuration.",
        )

    # Read facets.yaml content
    try:
        with open(facets_path) as f:
            facets_yaml_content = f.read()
    except Exception as e:
        return False, "", f"Error reading facets.yaml: {e!s}"

    # Validate output types if API client is provided
    if output_api:
        output_validation_results = validate_output_types(
            facets_yaml_content, output_api
        )
        has_missing_types, error_message = check_missing_output_types(
            output_validation_results
        )

        if has_missing_types:
            return False, facets_yaml_content, error_message

    return True, facets_yaml_content, ""


def validate_module_output_types(module_path: str) -> tuple[bool, str]:
    """
    Validate output types in a module's facets.yaml file.

    Args:
        module_path (str): The path to the module directory.

    Returns:
        Tuple[bool, str]: (success, validation_message)
            - success: True if validation passed or was skipped
            - validation_message: Message describing the validation results
    """
    # Check if facets.yaml exists
    facets_path = os.path.join(module_path, "facets.yaml")
    if not os.path.exists(facets_path):
        return True, "Warning: facets.yaml not found. Output type validation skipped."

    try:
        # Initialize API client for output type validation
        api_client = ClientUtils.get_client()
        from swagger_client.api.tf_output_management_api import TFOutputManagementApi

        output_api = TFOutputManagementApi(api_client)

        # Read and validate facets.yaml
        success, facets_content, error_message = read_and_validate_facets_yaml(
            module_path, output_api
        )

        if not success:
            return False, f"Output type validation failed: {error_message}"
        else:
            return True, "✓ All output types validation passed successfully."

    except Exception as e:
        return (
            True,
            f"Warning: Output type validation encountered an error: {e!s}\nThis may be due to API connectivity issues or invalid configuration.",
        )
