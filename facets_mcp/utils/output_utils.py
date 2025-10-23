"""
Utilities for handling output types in the facets-module-mcp project.
Contains helper functions for interacting with the Facets output type API.
"""

import json
import sys
from typing import Any

from swagger_client.api.tf_output_management_api import TFOutputManagementApi
from swagger_client.rest import ApiException

from facets_mcp.utils.client_utils import ClientUtils


def get_output_type_details_from_api(output_type: str) -> dict[str, Any]:
    """
    Get details for a specific output type from the Facets control plane.

    Args:
        output_type (str): The output type name in format '@namespace/name'

    Returns:
        Dict[str, Any]: Dictionary containing the output type details or error information
    """
    try:
        # Validate the name format
        if not output_type.startswith("@") or "/" not in output_type:
            return {"error": "Error: Name should be in the format '@namespace/name'."}

        # Split the name into namespace and name parts
        name_parts = output_type.split("/", 1)
        if len(name_parts) != 2:
            return {"error": "Error: Name should be in the format '@namespace/name'."}

        namespace, output_name = name_parts

        # Initialize the API client
        try:
            api_client = ClientUtils.get_client()
            output_api = TFOutputManagementApi(api_client)

            # Get output type details
            output_details = output_api.get_output_by_name(
                name=output_name, namespace=namespace
            )

            # Convert the response object to a dictionary
            if output_details:
                details_dict = {}

                # Add basic info
                details_dict["name"] = output_type
                details_dict["exists"] = True

                # Add properties
                if hasattr(output_details, "properties") and output_details.properties:
                    if hasattr(output_details.properties, "to_dict"):
                        details_dict["properties"] = output_details.properties.to_dict()
                    else:
                        details_dict["properties"] = output_details.properties

                # Add providers
                if hasattr(output_details, "providers") and output_details.providers:
                    providers_list = []
                    for provider in output_details.providers:
                        provider_dict = {
                            "name": provider.name,
                            "source": provider.source,
                            "version": provider.version,
                        }
                        providers_list.append(provider_dict)
                    details_dict["providers"] = providers_list

                # Add any other relevant fields
                if hasattr(output_details, "id"):
                    details_dict["id"] = output_details.id

                return details_dict
            else:
                return {"error": f"No details found for output type '{output_type}'"}

        except ApiException as e:
            if e.status == 404:
                return {
                    "exists": False,
                    "error": f"Output type '{output_type}' not found",
                }
            else:
                return {"error": f"Error accessing API: {e!s}"}

    except Exception as e:
        error_message = f"Error retrieving output type details: {e!s}"
        print(error_message, file=sys.stderr)
        return {"error": error_message}


def find_output_types_with_provider_from_api(provider_source: str) -> str:
    """
    Find all output types that include a specific provider source.

    Args:
        provider_source (str): The provider source name to search for.

    Returns:
        str: JSON string containing the formatted output type information.
    """
    try:
        # Initialize API client
        api_client = ClientUtils.get_client()
        output_api = TFOutputManagementApi(api_client)

        # Call the API method to get outputs by provider source
        response = output_api.get_outputs_by_provider_source(source=provider_source)

        if not response:
            return json.dumps(
                {
                    "status": "success",
                    "message": "No output types found for the specified provider source.",
                    "outputs": [],
                }
            )

        # Format the response
        formatted_outputs = []
        for output in response:
            output_data: dict[str, Any] = {"name": f"{output.namespace}/{output.name}"}

            # Add properties if available
            if hasattr(output, "properties") and output.properties:
                # Convert properties to dictionary if it has to_dict method
                if hasattr(output.properties, "to_dict"):
                    output_data["properties"] = output.properties.to_dict()
                else:
                    output_data["properties"] = output.properties

            # Add providers information
            if hasattr(output, "providers") and output.providers:
                providers_list = []
                for provider in output.providers:
                    provider_dict = {
                        "name": provider.name,
                        "source": provider.source,
                        "version": provider.version,
                    }
                    providers_list.append(provider_dict)
                output_data["providers"] = providers_list

            formatted_outputs.append(output_data)

        return json.dumps(
            {
                "status": "success",
                "count": len(formatted_outputs),
                "outputs": formatted_outputs,
            },
            indent=2,
        )

    except Exception as e:
        error_message = f"Error finding output types with provider: {e!s}"
        print(error_message, file=sys.stderr)
        return json.dumps({"status": "error", "message": error_message})


def _infer_json_type(value: Any) -> str:
    """
    Infer JSON schema type from a Python value.

    Args:
        value: The Python value to infer type from

    Returns:
        str: The JSON schema type
    """
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    else:
        return "string"  # default type


def normalize_schema_fields(schema_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize JSON schema fields by auto-adding 'type': 'object' when 'properties' is present.

    This helps AI agents who might forget to include the type field when defining object schemas.

    Args:
        schema_dict: Dictionary containing schema definitions

    Returns:
        Normalized schema dictionary
    """
    if not isinstance(schema_dict, dict):
        return schema_dict

    normalized = {}
    for key, value in schema_dict.items():
        if isinstance(value, dict):
            # If this field has 'properties' but no 'type', add 'type': 'object'
            if "properties" in value and "type" not in value:
                normalized[key] = {"type": "object", **value}
            else:
                normalized[key] = value
        else:
            normalized[key] = value

    return normalized


def validate_attributes_and_interfaces_format(
    interfaces: dict[str, Any] | None = None,
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Validate that attributes and interfaces are not incorrectly nested inside a 'properties' key.

    This is a common mistake when AI agents confuse JSON schema structure with the expected input format.

    Args:
        interfaces (Dict[str, Any], optional): Dictionary of output interfaces
        attributes (Dict[str, Any], optional): Dictionary of output attributes

    Returns:
        Dict[str, Any] | None: Error dictionary if validation fails, None if valid
    """
    error_parts = []

    # Check if attributes has only 'properties' key at top level
    if attributes and len(attributes) == 1 and "properties" in attributes:
        error_parts.append(
            "❌ Error: 'attributes' parameter is incorrectly nested inside a 'properties' key."
        )
        error_parts.append("")
        error_parts.append("❌ What you sent:")
        error_parts.append("  attributes = {")
        error_parts.append('    "properties": {')
        error_parts.append('      "field1": {"type": "string"},')
        error_parts.append('      "field2": {"type": "number"}')
        error_parts.append("    }")
        error_parts.append("  }")
        error_parts.append("")
        error_parts.append("✅ Correct format (remove the outer 'properties' wrapper):")
        error_parts.append("  attributes = {")
        error_parts.append('    "field1": {"type": "string"},')
        error_parts.append('    "field2": {"type": "number"}')
        error_parts.append("  }")
        error_parts.append("")

    # Check if interfaces has only 'properties' key at top level
    if interfaces and len(interfaces) == 1 and "properties" in interfaces:
        error_parts.append(
            "❌ Error: 'interfaces' parameter is incorrectly nested inside a 'properties' key."
        )
        error_parts.append("")
        error_parts.append("❌ What you sent:")
        error_parts.append("  interfaces = {")
        error_parts.append('    "properties": {')
        error_parts.append('      "default": {"type": "object", "properties": {...}}')
        error_parts.append("    }")
        error_parts.append("  }")
        error_parts.append("")
        error_parts.append("✅ Correct format (remove the outer 'properties' wrapper):")
        error_parts.append("  interfaces = {")
        error_parts.append('    "default": {"type": "object", "properties": {...}}')
        error_parts.append("  }")
        error_parts.append("")

    if error_parts:
        error_parts.append(
            "💡 Tip: The function expects field names directly, not wrapped in 'properties'."
        )
        error_parts.append(
            "      The function will automatically create the proper JSON schema structure."
        )
        return {"error": "\n".join(error_parts)}

    return None


def infer_properties_from_interfaces_and_attributes(
    interfaces: dict[str, Any] | None = None,
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Infer JSON schema properties from output interfaces and attributes.

    This function assumes the interfaces and attributes are already in JSON schema format.
    It generates a clean structure suitable for both schema validation and lookup trees.

    Automatically normalizes schemas by adding 'type': 'object' when 'properties' is present.

    Args:
        interfaces (Dict[str, Any], optional): Dictionary of output interfaces in JSON schema format
        attributes (Dict[str, Any], optional): Dictionary of output attributes in JSON schema format

    Returns:
        Dict[str, Any]: JSON schema properties definition
    """
    try:
        # Normalize the inputs to auto-add 'type': 'object' where needed
        if attributes:
            attributes = normalize_schema_fields(attributes)
        if interfaces:
            interfaces = normalize_schema_fields(interfaces)

        # Create base structure
        properties = {"type": "object", "properties": {}}

        # Generate the full properties structure for schema validation
        if attributes:
            attributes_properties = {}
            for attr_name, attr_schema in attributes.items():
                # Add the attribute as-is (now normalized)
                attributes_properties[attr_name] = attr_schema

            properties["properties"]["attributes"] = {
                "type": "object",
                "properties": attributes_properties,
            }

        if interfaces:
            interfaces_properties = {}
            for intf_name, intf_schema in interfaces.items():
                # Add the interface as-is (now normalized)
                interfaces_properties[intf_name] = intf_schema

            properties["properties"]["interfaces"] = {
                "type": "object",
                "properties": interfaces_properties,
            }

        return properties

    except Exception as e:
        error_message = (
            f"Error inferring properties from interfaces and attributes: {e!s}"
        )
        print(error_message, file=sys.stderr)
        return {"error": error_message}


def prepare_output_type_registration(
    name: str,
    properties: dict[str, Any],
    providers: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    Prepare data for registering a new output type.

    Args:
        name (str): The name of the output type in the format '@namespace/name'.
        properties (Dict[str, Any]): A dictionary defining the properties of the output type.
        providers (List[Dict[str, str]], optional): A list of provider dictionaries, each containing 'name', 'source', and 'version'.

    Returns:
        Dict[str, Any]: A dictionary with the prepared data or error information
    """
    try:
        # Validate the name format
        if not name.startswith("@") or "/" not in name:
            return {"error": "Error: Name should be in the format '@namespace/name'."}

        # Split the name into namespace and name parts
        name_parts = name.split("/", 1)
        if len(name_parts) != 2:
            return {"error": "Error: Name should be in the format '@namespace/name'."}

        # Prepare the YAML content
        output_type_def = {"name": name, "properties": properties}

        # Add providers if specified
        if providers:
            providers_dict = {}
            for provider in providers:
                if "name" not in provider:
                    return {"error": "Error: Each provider must have a 'name' field."}

                provider_name = provider["name"]
                providers_dict[provider_name] = {
                    "source": provider.get("source", ""),
                    "version": provider.get("version", ""),
                }

            output_type_def["providers"] = providers_dict

        return {"success": True, "data": output_type_def}

    except Exception as e:
        error_message = f"Error preparing output type data: {e!s}"
        print(error_message, file=sys.stderr)
        return {"error": error_message}


def compare_output_types(
    existing_output: Any,
    new_properties: dict[str, Any],
    new_providers: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    Compare existing output type with new properties and providers.

    Args:
        existing_output: The existing output type object from API
        new_properties: New properties to compare against
        new_providers: New providers to compare against

    Returns:
        Dict[str, Any]: Dictionary with comparison results
    """
    try:
        # Convert existing_output properties to dict for comparison
        existing_properties = existing_output.properties
        if hasattr(existing_properties, "to_dict"):
            existing_properties = existing_properties.to_dict()

        # Convert providers to comparable format
        existing_providers_dict = {}
        if existing_output.providers:
            for provider in existing_output.providers:
                existing_providers_dict[provider.name] = {
                    "source": provider.source or "",
                    "version": provider.version or "",
                }

        # Create new_providers_dict for comparison
        new_providers_dict = {}
        if new_providers:
            for provider in new_providers:
                if "name" not in provider:
                    return {"error": "Error: Each provider must have a 'name' field."}

                provider_name = provider["name"]
                new_providers_dict[provider_name] = {
                    "source": provider.get("source", ""),
                    "version": provider.get("version", ""),
                }

        # Compare properties and providers
        properties_equal = json.dumps(
            existing_properties, sort_keys=True
        ) == json.dumps(new_properties, sort_keys=True)
        providers_equal = json.dumps(
            existing_providers_dict, sort_keys=True
        ) == json.dumps(new_providers_dict, sort_keys=True)

        diff_message = ""
        if not properties_equal:
            diff_message += "\nProperties Difference:\n"
            diff_message += f"Existing: {json.dumps(existing_properties, indent=2)}\n"
            diff_message += f"New: {json.dumps(new_properties, indent=2)}\n"

        if not providers_equal:
            diff_message += "\nProviders Difference:\n"
            diff_message += (
                f"Existing: {json.dumps(existing_providers_dict, indent=2)}\n"
            )
            diff_message += f"New: {json.dumps(new_providers_dict, indent=2)}\n"

        return {
            "properties_equal": properties_equal,
            "providers_equal": providers_equal,
            "all_equal": properties_equal and providers_equal,
            "diff_message": diff_message,
        }

    except Exception as e:
        error_message = f"Error comparing output types: {e!s}"
        print(error_message, file=sys.stderr)
        return {"error": error_message}
