"""
Intent management tools for querying and creating/updating intents in the control plane.

Also includes helpers to map a local module's intent to a control-plane project type (intent type).
"""

import json
import os

import yaml
from swagger_client.api.intent_management_api import IntentManagementApi
from swagger_client.api.ui_project_type_controller_api import UiProjectTypeControllerApi
from swagger_client.models.intent_request_dto import IntentRequestDTO
from swagger_client.models.project_type_mapped_resource import ProjectTypeMappedResource
from swagger_client.models.project_type_request import ProjectTypeRequest
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
    abs_path = os.path.abspath(module_path)
    if not os.path.isdir(abs_path):
        return False, "", f"Module path '{module_path}' is not a valid directory."
    facets_path = os.path.join(abs_path, "facets.yaml")
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


def _read_module_intent_and_flavor(module_path: str) -> tuple[bool, str, str, str]:
    """
    Internal: Read the module intent and flavor from facets.yaml.
    Returns (ok, intent, flavor, error_message)
    """
    abs_path = os.path.abspath(module_path)
    if not os.path.isdir(abs_path):
        return False, "", "", f"Module path '{module_path}' is not a valid directory."
    facets_path = os.path.join(abs_path, "facets.yaml")
    if not os.path.exists(facets_path):
        return False, "", "", "facets.yaml not found in module path."
    try:
        with open(facets_path) as f:
            facets_yaml = yaml.safe_load(f)
        intent = facets_yaml.get("intent")
        if not intent:
            return False, "", "", "No 'intent' field found in facets.yaml."
        flavor = facets_yaml.get("flavor", "default")
        return True, intent, flavor, ""
    except Exception as e:
        return False, "", "", f"Error reading facets.yaml: {e!s}"


@mcp.tool()
def map_module_to_project_type(
    module_path: str,
    project_type_name: str,
) -> str:
    """
    Map the module's intent and flavor to a project type's mapped resources.

    This adds the module's intent+flavor combination to the specified project type's
    list of mapped resources using the UI Project Type Controller API.

    Args:
        module_path: Path containing facets.yaml with 'intent' and 'flavor'
        project_type_name: Name of the project type to map this module to

    Returns:
        JSON string with success/error information

    Example:
        map_module_to_project_type('/path/to/mongo-module', 'database-stack')
    """
    # Read intent and flavor from module
    ok, intent, flavor, err = _read_module_intent_and_flavor(module_path)
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
        project_type_api = UiProjectTypeControllerApi(api_client)
        intent_api = IntentManagementApi(api_client)

        # Get intent details to find intent_type
        intent_type = None
        all_intents = intent_api.get_all_intents()
        for i in all_intents:
            if getattr(i, "name", "") == intent:
                intent_type = getattr(i, "type", None)
                break

        if not intent_type:
            return json.dumps(
                {
                    "success": False,
                    "message": f"Intent '{intent}' not found in control plane.",
                    "instructions": (
                        f"The intent '{intent}' must exist before mapping to a project type.\n"
                        f"Use create_or_update_intent() to create it first, or use list_all_intents() to see existing intents."
                    ),
                },
                indent=2,
            )

        # Get all project types and find the target one
        all_project_types = project_type_api.get_all_project_types()
        target_project_type = None
        for pt in all_project_types:
            if getattr(pt, "name", "") == project_type_name:
                target_project_type = pt
                break

        if not target_project_type:
            return json.dumps(
                {
                    "success": False,
                    "message": f"Project type '{project_type_name}' not found.",
                    "instructions": (
                        f"The project type '{project_type_name}' does not exist.\n"
                        "Please create it in the control plane UI first or use an existing project type."
                    ),
                },
                indent=2,
            )

        # Check if this intent+flavor is already mapped
        existing_mapped_resources = (
            getattr(target_project_type, "mapped_resources", []) or []
        )
        already_mapped = False
        for resource in existing_mapped_resources:
            if (
                getattr(resource, "intent", "") == intent
                and getattr(resource, "flavor", "") == flavor
            ):
                already_mapped = True
                break

        if already_mapped:
            return json.dumps(
                {
                    "success": True,
                    "message": f"Intent '{intent}' with flavor '{flavor}' is already mapped to project type '{project_type_name}'.",
                    "data": {
                        "intent": intent,
                        "flavor": flavor,
                        "intent_type": intent_type,
                        "project_type": project_type_name,
                        "action": "already_exists",
                    },
                },
                indent=2,
            )

        # Add the new mapping
        new_mapped_resource = ProjectTypeMappedResource(
            intent=intent,
            intent_type=intent_type,
            flavor=flavor,
        )
        updated_mapped_resources = list(existing_mapped_resources) + [
            new_mapped_resource
        ]

        # Prepare update request
        update_request = ProjectTypeRequest(
            name=target_project_type.name,
            allowed_clouds=target_project_type.allowed_clouds,
            description=target_project_type.description,
            template_git_details=target_project_type.template_git_details,
            mapped_resources=updated_mapped_resources,
            iac_tool=target_project_type.iac_tool,
        )

        # Update the project type
        project_type_api.update_project_type(update_request, target_project_type.id)

        return json.dumps(
            {
                "success": True,
                "message": f"Successfully mapped intent '{intent}' with flavor '{flavor}' to project type '{project_type_name}'.",
                "data": {
                    "intent": intent,
                    "flavor": flavor,
                    "intent_type": intent_type,
                    "project_type": project_type_name,
                    "action": "added",
                },
            },
            indent=2,
        )

    except ApiException as e:
        return json.dumps(
            {
                "success": False,
                "message": f"API error while mapping to project type '{project_type_name}'.",
                "error": str(e),
                "instructions": "Check your permissions and try again.",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error mapping to project type.",
                "error": str(e),
            },
            indent=2,
        )
