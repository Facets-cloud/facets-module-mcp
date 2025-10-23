"""
Intent management tools for querying and creating/updating intents in the control plane.

Also includes helpers to map a local module's intent to a control-plane project type (intent type).
"""

import json
import os

import yaml
from swagger_client.api.intent_management_api import IntentManagementApi
from swagger_client.models.intent_request_dto import IntentRequestDTO
from swagger_client.rest import ApiException

from facets_mcp.config import mcp
from facets_mcp.utils.client_utils import ClientUtils


@mcp.tool()
def get_intent(intent_name: str) -> str:
    """
    Query whether an intent exists in the control plane by name.
    Returns intent details if found, or indicates if intent doesn't exist.

    Args:
        intent_name (str): The name of the intent to query

    Returns:
        str: JSON response containing intent details or not found status
    """
    try:
        # Initialize API client
        api_client = ClientUtils.get_client()
        intent_api = IntentManagementApi(api_client)

        # Get all intents and search for the specific one
        all_intents = intent_api.get_all_intents()

        # Find the intent by name
        target_intent = None
        for intent in all_intents:
            if hasattr(intent, "name") and intent.name == intent_name:
                target_intent = intent
                break

        if target_intent:
            # Extract intent details
            intent_data = {
                "name": getattr(target_intent, "name", ""),
                "type": getattr(target_intent, "type", ""),
                "display_name": getattr(target_intent, "display_name", ""),
                "description": getattr(target_intent, "description", ""),
                "icon_url": getattr(target_intent, "icon_url", ""),
            }

            return json.dumps(
                {
                    "success": True,
                    "message": f"Intent '{intent_name}' found in control plane.",
                    "data": {"exists": True, "intent": intent_data},
                },
                indent=2,
            )
        else:
            return json.dumps(
                {
                    "success": True,
                    "message": f"Intent '{intent_name}' not found in control plane.",
                    "data": {"exists": False, "intent": None},
                },
                indent=2,
            )

    except ApiException as e:
        return json.dumps(
            {
                "success": False,
                "message": "Failed to query intent from control plane.",
                "error": f"API error: {e!s}",
                "instructions": "Check your control plane connection and credentials.",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error querying intent.",
                "error": str(e),
                "instructions": "Ensure the control plane client is properly configured.",
            },
            indent=2,
        )


@mcp.tool()
def create_or_update_intent(
    name: str,
    intent_type: str,
    display_name: str,
    description: str,
    icon_url: str | None = None,
) -> str:
    """
    Create a new intent or update an existing one in the control plane.

    Args:
        name (str): The intent name (e.g., 'kubernetes_cluster')
        intent_type (str): The intent type/category (e.g., 'K8s', 'Storage')
        display_name (str): Human-readable display name
        description (str): Description of the intent
        icon_url (str, optional): URL to SVG icon (optional). NEVER send this unless the user explicitly provides it.

    Returns:
        str: JSON response containing success/failure information
    """
    try:
        # Initialize API client
        api_client = ClientUtils.get_client()
        intent_api = IntentManagementApi(api_client)

        # Create the intent request DTO
        intent_kwargs = {
            "name": name,
            "type": intent_type,
            "display_name": display_name,
            "description": description,
            "inferred_from_module": False,
        }
        if icon_url is not None:
            intent_kwargs["icon_url"] = icon_url
        intent_request = IntentRequestDTO(**intent_kwargs)

        # Create or update the intent using the correct API method
        try:
            response = intent_api.create_or_update_intent(intent_request)

            return json.dumps(
                {
                    "success": True,
                    "message": f"Intent '{name}' created/updated successfully.",
                    "data": {
                        "intent_name": name,
                        "response": {
                            "name": getattr(response, "name", ""),
                            "type": getattr(response, "type", ""),
                            "display_name": getattr(response, "display_name", ""),
                            "description": getattr(response, "description", ""),
                            "icon_url": getattr(response, "icon_url", ""),
                        },
                    },
                },
                indent=2,
            )

        except ApiException as e:
            # Handle specific API errors
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                return json.dumps(
                    {
                        "success": False,
                        "message": f"Intent '{name}' already exists and could not be updated.",
                        "error": error_msg,
                        "instructions": f"Use get_intent('{name}') to check existing intent details, or modify the intent name.",
                    },
                    indent=2,
                )
            else:
                return json.dumps(
                    {
                        "success": False,
                        "message": f"Failed to create/update intent '{name}'.",
                        "error": error_msg,
                        "instructions": "Check the intent data format and your permissions.",
                    },
                    indent=2,
                )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error creating/updating intent.",
                "error": str(e),
                "instructions": "Ensure the control plane client is properly configured and all required parameters are provided.",
            },
            indent=2,
        )


@mcp.tool()
def list_all_intents() -> str:
    """
    List all available intents in the control plane.
    Useful for discovering existing intent types and names.

    Returns:
        str: JSON response containing list of all intents
    """
    try:
        # Initialize API client
        api_client = ClientUtils.get_client()
        intent_api = IntentManagementApi(api_client)

        # Get all intents
        all_intents = intent_api.get_all_intents()

        # Extract intent information
        intents_list = []
        unique_types = set()

        for intent in all_intents:
            intent_info = {
                "name": getattr(intent, "name", ""),
                "type": getattr(intent, "type", ""),
            }
            intents_list.append(intent_info)

            if intent_info["type"]:
                unique_types.add(intent_info["type"])

        return json.dumps(
            {
                "success": True,
                "message": f"Found {len(intents_list)} intents in control plane.",
                "data": {
                    "intents": intents_list,
                    "total_count": len(intents_list),
                    "unique_types": sorted(list(unique_types)),
                },
            },
            indent=2,
        )
    except ApiException as e:
        return json.dumps(
            {
                "success": False,
                "message": "Failed to list intents from control plane.",
                "error": f"API error: {e!s}",
                "instructions": "Check your control plane connection and credentials.",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error listing intents.",
                "error": str(e),
                "instructions": "Ensure the control plane client is properly configured.",
            },
            indent=2,
        )


def _read_module_intent(module_path: str) -> tuple[bool, str, str]:
    """
    Internal: Read the module intent from facets.yaml.
    Returns (ok, intent, error_message)
    """
    facets_path = os.path.join(os.path.abspath(module_path), "facets.yaml")
    if not os.path.exists(facets_path):
        return False, "", "facets.yaml not found in module path."
    try:
        with open(facets_path) as f:
            facets_yaml = yaml.safe_load(f)
        intent = facets_yaml.get("intent")
        if not intent:
            return False, "", "No 'intent' field found in facets.yaml."
        return True, intent, ""
    except Exception as e:
        return False, "", f"Error reading facets.yaml: {e!s}"


@mcp.tool()
def map_module_to_project_type(
    module_path: str,
    project_type: str,
    display_name: str | None = None,
    description: str | None = None,
    icon_url: str | None = None,
) -> str:
    """
    Map the module's intent to a control-plane project type by creating/updating the intent type.

    Note: Built-in intents cannot be modified. If you need to modify an intent that is built-in,
    you should create a new custom intent with a different name.

    Args:
        module_path: Path containing facets.yaml with 'intent'
        project_type: Desired intent type to set in control plane
        display_name: Optional display name override (defaults to existing)
        description: Optional description override (defaults to existing)
        icon_url: Optional icon URL (only if explicitly provided)

    Returns:
        JSON string with success/error information

    Example:
        # For a custom intent:
        map_module_to_project_type('/path/to/module', 'custom_type')

        # For a built-in intent, you'll need to create a new intent first:
        create_or_update_intent(
            name='my-custom-mongo',
            intent_type='database',
            display_name='My Custom Mongo',
            description='Custom MongoDB intent'
        )
    """
    ok, intent, err = _read_module_intent(module_path)
    if not ok:
        return json.dumps(
            {
                "success": False,
                "message": err,
                "instructions": "Inform User: Fix facets.yaml and retry.",
            },
            indent=2,
        )

    try:
        api_client = ClientUtils.get_client()
        intent_api = IntentManagementApi(api_client)

        # Fetch existing intent if present to preserve fields
        existing = None
        all_intents = intent_api.get_all_intents()
        for i in all_intents:
            if getattr(i, "name", "") == intent:
                existing = i
                # Check if this is a built-in intent
                if getattr(i, "built_in", False) or getattr(i, "is_builtin", False):
                    return json.dumps(
                        {
                            "success": False,
                            "message": f"Cannot modify built-in intent '{intent}'",
                            "error": "Built-in intents cannot be modified",
                            "instructions": (
                                "This is a built-in intent and cannot be modified.\n"
                                "To proceed, you can either:\n"
                                "1. Use the intent as-is without modification\n"
                                "2. Create a new custom intent using create_or_update_intent()\n"
                                "3. Use list_all_intents() to see available intents"
                            ),
                            "is_builtin": True,
                        },
                        indent=2,
                    )
                break

        # Prepare payload preserving existing values if not provided
        payload_kwargs = {
            "name": intent,
            "type": project_type,
            "display_name": (
                display_name
                if display_name is not None
                else getattr(existing, "display_name", intent)
            ),
            "description": (
                description
                if description is not None
                else getattr(existing, "description", f"Intent '{intent}'")
            ),
            "inferred_from_module": False,
        }
        if icon_url is not None:
            payload_kwargs["icon_url"] = icon_url
        payload = IntentRequestDTO(**payload_kwargs)

        response = intent_api.create_or_update_intent(payload)
        return json.dumps(
            {
                "success": True,
                "message": f"Mapped intent '{intent}' to project type '{project_type}'.",
                "data": {
                    "intent": intent,
                    "project_type": project_type,
                    "response": {
                        "name": getattr(response, "name", ""),
                        "type": getattr(response, "type", ""),
                        "display_name": getattr(response, "display_name", ""),
                        "description": getattr(response, "description", ""),
                        "icon_url": getattr(response, "icon_url", ""),
                    },
                },
            },
            indent=2,
        )
    except ApiException as e:
        error_msg = str(e)
        if "Cannot update a built-in intent" in error_msg:
            return json.dumps(
                {
                    "success": False,
                    "message": f"Cannot modify built-in intent '{intent}'",
                    "error": error_msg,
                    "instructions": (
                        "This is a built-in intent and cannot be modified.\n"
                        "To proceed, you can either:\n"
                        "1. Use the intent as-is without modification\n"
                        "2. Create a new custom intent using create_or_update_intent()\n"
                        "3. Use list_all_intents() to see available intents"
                    ),
                    "is_builtin": True,
                },
                indent=2,
            )
        return json.dumps(
            {
                "success": False,
                "message": f"Failed to map intent '{intent}' to project type '{project_type}'.",
                "error": f"API error: {error_msg}",
                "instructions": "Check the intent name and your permissions, then try again.",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error mapping project type.",
                "error": str(e),
            },
            indent=2,
        )
