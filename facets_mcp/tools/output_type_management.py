import sys
from typing import Dict, Any, List, Optional
import json

from swagger_client.api.tf_output_management_api import TFOutputManagementApi
from swagger_client.rest import ApiException

from facets_mcp.config import mcp
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.utils.output_utils import (
    get_output_type_details_from_api,
    find_output_types_with_provider_from_api,
    prepare_output_type_registration,
    compare_output_types,
    infer_properties_from_interfaces_and_attributes
)

# Initialize client utility
try:
    if not ClientUtils.initialized:
        ClientUtils.initialize()
except Exception as e:
    print(f"Warning: Failed to initialize API client: {str(e)}", file=sys.stderr)


@mcp.tool()
def get_output_type_details(output_type_name: str) -> str:
    """
    Get details for a specific output type from the Facets control plane.

    Args:
        output_type_name (str): The name of the output type to retrieve details for.

    Returns:
        str: A JSON-formatted string with output type details or error message.
    """
    try:
        result = get_output_type_details_from_api(output_type_name)
        
        if result["success"]:
            return json.dumps({
                "success": True,
                "message": f"Successfully retrieved details for output type '{output_type_name}'.",
                "data": result["data"]
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": result["error"],
                "data": {
                    "output_type_name": output_type_name
                }
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error retrieving output type details: {str(e)}",
        }, indent=2)


@mcp.tool()
def find_output_types_with_provider(provider_source: str) -> str:
    """
    This tool finds all output types that include a specific provider source, which can be used as inputs for
    module configurations.

    Args:
        provider_source (str): The provider source to search for (e.g., "hashicorp/aws", "hashicorp/azurerm").

    Returns:
        str: A JSON-formatted string with matching output types or error message.
    """
    try:
        result = find_output_types_with_provider_from_api(provider_source)
        
        if result["success"]:
            return json.dumps({
                "success": True,
                "message": f"Found {len(result['data'])} output types with provider '{provider_source}'.",
                "data": {
                    "provider_source": provider_source,
                    "matching_output_types": result["data"],
                    "count": len(result["data"])
                }
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": result["error"],
                "data": {
                    "provider_source": provider_source
                }
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error finding output types with provider: {str(e)}",
        }, indent=2)


@mcp.tool()
def list_all_output_types() -> str:
    """
    List all output types from the Facets control plane.

    Returns:
        str: A JSON-formatted string with all output types or error message.
    """
    try:
        # Initialize API client
        api_instance = TFOutputManagementApi(ClientUtils.get_client())
        
        try:
            # Get all output types
            output_types = api_instance.get_all_output_types()
            
            # Extract just the names and basic info
            output_type_list = []
            for ot in output_types:
                output_type_info = {
                    "name": ot.name,
                    "description": getattr(ot, 'description', None),
                    "created_at": getattr(ot, 'created_at', None),
                    "updated_at": getattr(ot, 'updated_at', None)
                }
                output_type_list.append(output_type_info)

            return json.dumps({
                "success": True,
                "message": f"Successfully retrieved {len(output_type_list)} output types.",
                "data": {
                    "output_types": output_type_list,
                    "total_count": len(output_type_list)
                }
            }, indent=2)

        except ApiException as e:
            return json.dumps({
                "success": False,
                "error": f"API error retrieving output types: {str(e)}",
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error listing output types: {str(e)}",
        }, indent=2)


@mcp.tool()
def register_output_type(
    name: str,
    interfaces: Optional[Dict[str, Any]] = None,
    attributes: Optional[Dict[str, Any]] = None,
    providers: Optional[List[str]] = None,
    dry_run: bool = True
) -> str:
    """
    Register a new output type in the Facets control plane with interfaces and attributes and providers.

    Args:
        name (str): The name of the output type to register.
        interfaces (Dict[str, Any], optional): The interfaces configuration for the output type.
        attributes (Dict[str, Any], optional): The attributes configuration for the output type.
        providers (List[str], optional): List of provider sources (e.g., ["hashicorp/aws"]).
        dry_run (bool): If True, validate and show what would be registered without actually registering.

    Returns:
        str: A JSON-formatted string with registration results.
    """
    try:
        # Initialize API client
        api_instance = TFOutputManagementApi(ClientUtils.get_client())

        # Prepare the output type data
        result = prepare_output_type_registration(
            name=name,
            interfaces=interfaces,
            attributes=attributes,
            providers=providers
        )

        if not result["success"]:
            return json.dumps({
                "success": False,
                "error": result["error"],
                "data": {
                    "name": name
                }
            }, indent=2)

        output_type_data = result["output_type"]

        # Check if output type already exists
        try:
            existing = api_instance.get_output_type_by_name(name)
            if existing:
                # Compare with existing
                comparison = compare_output_types(existing, output_type_data)
                
                if dry_run:
                    return json.dumps({
                        "success": True,
                        "message": f"Output type '{name}' already exists. Comparison completed.",
                        "instructions": "Review the comparison. Call again with dry_run=False to update if needed.",
                        "data": {
                            "name": name,
                            "status": "exists",
                            "comparison": comparison,
                            "proposed_output_type": output_type_data
                        }
                    }, indent=2)
                else:
                    if comparison["identical"]:
                        return json.dumps({
                            "success": True,
                            "message": f"Output type '{name}' already exists with identical configuration.",
                            "data": {
                                "name": name,
                                "status": "already_exists_identical",
                                "comparison": comparison
                            }
                        }, indent=2)
                    else:
                        # Update the existing output type
                        updated = api_instance.update_output_type(name, body=output_type_data)
                        return json.dumps({
                            "success": True,
                            "message": f"Successfully updated output type '{name}'.",
                            "data": {
                                "name": name,
                                "status": "updated",
                                "comparison": comparison,
                                "updated_output_type": output_type_data
                            }
                        }, indent=2)

        except ApiException as e:
            if e.status != 404:  # 404 means it doesn't exist, which is fine
                return json.dumps({
                    "success": False,
                    "error": f"Error checking existing output type: {str(e)}",
                }, indent=2)

        # Output type doesn't exist, proceed with registration
        if dry_run:
            # Infer additional properties for preview
            inferred_props = infer_properties_from_interfaces_and_attributes(interfaces, attributes)
            
            return json.dumps({
                "success": True,
                "message": f"Output type '{name}' ready for registration. Preview completed.",
                "instructions": "Review the output type configuration. Call again with dry_run=False to register.",
                "data": {
                    "name": name,
                    "status": "ready_for_registration",
                    "output_type": output_type_data,
                    "inferred_properties": inferred_props
                }
            }, indent=2)
        else:
            # Actually register the output type
            try:
                created = api_instance.create_output_type(body=output_type_data)
                return json.dumps({
                    "success": True,
                    "message": f"Successfully registered new output type '{name}'.",
                    "data": {
                        "name": name,
                        "status": "created",
                        "output_type": output_type_data
                    }
                }, indent=2)

            except ApiException as e:
                return json.dumps({
                    "success": False,
                    "error": f"Failed to register output type '{name}': {str(e)}",
                    "data": {
                        "name": name,
                        "output_type": output_type_data
                    }
                }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error registering output type '{name}': {str(e)}",
        }, indent=2)
