"""
Intent management tools for querying and creating/updating intents in the control plane.
"""

import json
import os
import yaml
from typing import Optional, Dict, Any, List

from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.utils.file_utils import ensure_path_in_working_directory
from swagger_client.api.intent_management_api import IntentManagementApi
from swagger_client.models.intent_request_dto import IntentRequestDTO
from swagger_client.models.intent_output import IntentOutput
from swagger_client.rest import ApiException


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
            if hasattr(intent, 'name') and intent.name == intent_name:
                target_intent = intent
                break
        
        if target_intent:
            # Extract intent details
            intent_data = {
                "name": getattr(target_intent, 'name', ''),
                "type": getattr(target_intent, 'type', ''),
                "display_name": getattr(target_intent, 'display_name', ''),
                "description": getattr(target_intent, 'description', ''),
                "icon_url": getattr(target_intent, 'icon_url', '')
            }
            
            return json.dumps({
                "success": True,
                "message": f"Intent '{intent_name}' found in control plane.",
                "data": {
                    "exists": True,
                    "intent": intent_data
                }
            }, indent=2)
        else:
            return json.dumps({
                "success": True,
                "message": f"Intent '{intent_name}' not found in control plane.",
                "data": {
                    "exists": False,
                    "intent": None
                }
            }, indent=2)
            
    except ApiException as e:
        return json.dumps({
            "success": False,
            "message": "Failed to query intent from control plane.",
            "error": f"API error: {str(e)}",
            "instructions": "Check your control plane connection and credentials."
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": "Error querying intent.",
            "error": str(e),
            "instructions": "Ensure the control plane client is properly configured."
        }, indent=2)


@mcp.tool()
def create_or_update_intent(
    name: str,
    intent_type: str,
    display_name: str,
    description: str,
    icon_url: Optional[str] = None,
    outputs: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Create a new intent or update an existing one in the control plane.
    
    Args:
        name (str): The intent name (e.g., 'kubernetes_cluster')
        intent_type (str): The intent type/category (e.g., 'K8s', 'Storage')
        display_name (str): Human-readable display name
        description (str): Description of the intent
        icon_url (str, optional): URL to SVG icon (optional)
        outputs (List[Dict], optional): List of output definitions with 'name' and 'type' keys
        
    Returns:
        str: JSON response containing success/failure information
    """
    try:
        # Initialize API client
        api_client = ClientUtils.get_client()
        intent_api = IntentManagementApi(api_client)

        # Prepare intent outputs
        intent_outputs = []
        if outputs:
            for output in outputs:
                intent_output = IntentOutput(
                    name=output.get("name", "default"),
                    type=output.get("type", f"@{name.replace('_', '-')}/cluster"),
                    title=output.get("title", output.get("name", "default"))
                )
                intent_outputs.append(intent_output)
        else:
            # Default output structure
            default_output = IntentOutput(
                name="default",
                type=f"@{name.replace('_', '-')}/cluster",
                title="Default Output"
            )
            intent_outputs.append(default_output)

        # Create the intent request DTO
        intent_request = IntentRequestDTO(
            name=name,
            type=intent_type,
            display_name=display_name,
            description=description,
            icon_url=icon_url,
            intent_outputs=intent_outputs,
            inferred_from_module=False
        )

        # Create or update the intent using the correct API method
        try:
            response = intent_api.create_or_update_intent(intent_request)

            return json.dumps({
                "success": True,
                "message": f"Intent '{name}' created/updated successfully.",
                "data": {
                    "intent_name": name,
                    "response": {
                        "name": getattr(response, 'name', ''),
                        "type": getattr(response, 'type', ''),
                        "display_name": getattr(response, 'display_name', ''),
                        "description": getattr(response, 'description', ''),
                        "icon_url": getattr(response, 'icon_url', '')
                    }
                }
            }, indent=2)
            
        except ApiException as e:
            # Handle specific API errors
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                return json.dumps({
                    "success": False,
                    "message": f"Intent '{name}' already exists and could not be updated.",
                    "error": error_msg,
                    "instructions": f"Use get_intent('{name}') to check existing intent details, or modify the intent name."
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "message": f"Failed to create/update intent '{name}'.",
                    "error": error_msg,
                    "instructions": "Check the intent data format and your permissions."
                }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": "Error creating/updating intent.",
            "error": str(e),
            "instructions": "Ensure the control plane client is properly configured and all required parameters are provided."
        }, indent=2)


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
                "name": getattr(intent, 'name', ''),
                "type": getattr(intent, 'type', ''),
                "display_name": getattr(intent, 'display_name', ''),
                "description": getattr(intent, 'description', ''),
                "icon_url": getattr(intent, 'icon_url', '')
            }
            intents_list.append(intent_info)
            
            if intent_info["type"]:
                unique_types.add(intent_info["type"])
        
        return json.dumps({
            "success": True,
            "message": f"Found {len(intents_list)} intents in control plane.",
            "data": {
                "intents": intents_list,
                "total_count": len(intents_list),
                "unique_types": sorted(list(unique_types))
            }
        }, indent=2)
        
    except ApiException as e:
        return json.dumps({
            "success": False,
            "message": "Failed to list intents from control plane.",
            "error": f"API error: {str(e)}",
            "instructions": "Check your control plane connection and credentials."
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": "Error listing intents.",
            "error": str(e),
            "instructions": "Ensure the control plane client is properly configured."
        }, indent=2)
