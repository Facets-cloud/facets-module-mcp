import os

import yaml
from swagger_client.api.intent_management_api import IntentManagementApi
from swagger_client.rest import ApiException

from facets_mcp.utils.client_utils import ClientUtils


def check_intent_and_intent_details(module_path: str) -> tuple[bool, str]:
    """
    Checks if the intent in facets.yaml exists in the control plane. If not, checks for presence of intentDetails.
    Returns (success, message). If not success, message contains user instructions and suggestions.
    """
    facets_path = os.path.join(os.path.abspath(module_path), "facets.yaml")
    if not os.path.exists(facets_path):
        return False, "facets.yaml not found in module path."

    # Read facets.yaml
    try:
        with open(facets_path) as f:
            facets_yaml = yaml.safe_load(f)
    except Exception as e:
        return False, f"Error reading facets.yaml: {e!s}"

    intent = facets_yaml.get("intent")
    if not intent:
        return (
            False,
            "No 'intent' field found in facets.yaml. Please add an 'intent' field.",
        )

    # Fetch all existing intents from the API
    try:
        api_client = ClientUtils.get_client()
        intent_api = IntentManagementApi(api_client)
        all_intents = intent_api.get_all_intents()
    except ApiException as e:
        return False, f"Error fetching intents from control plane: {e!s}"
    except Exception as e:
        return False, f"Error initializing API client: {e!s}"

    # Check if intent exists
    existing_intent_names = [i.name for i in all_intents if hasattr(i, "name")]
    if intent in existing_intent_names:
        return True, "Intent already exists in control plane."

    # If not, check for intentDetails block
    if "intentDetails" in facets_yaml:
        return (
            True,
            "Intent does not exist in control plane, but intentDetails block is present.",
        )

    # Gather all unique types for suggestion
    unique_types = sorted(
        set(i.type for i in all_intents if hasattr(i, "type") and i.type)
    )
    type_suggestions = "\n".join(f"  - {t}" for t in unique_types)
    type_note = "You may also specify a new value for type if none of these fit."

    # Prepare YAML snippet
    yaml_snippet = (
        "intentDetails:\n"
        "  type: to group the intent into <choose from below or specify a new value>\n"
        f"  description: <Description of the intent {intent}>\n"
        f"  displayName: <Human readable display name of the intent {intent}>\n"
        "  # iconUrl: <svg file link> - only include if the user provides a specific icon URL, otherwise skip this field"
    )

    message = (
        f"The intent '{intent}' does not exist in the control plane, and no intentDetails block was found in facets.yaml.\n\n"
        "You have two options to resolve this:\n\n"
        "OPTION 1 - Create the intent using MCP tools (Recommended):\n"
        f"Use create_or_update_intent() to create the intent programmatically:\n"
        f"- name: '{intent}'\n"
        f"- intent_type: <choose from types below or specify new>\n"
        f"- display_name: <human readable name>\n"
        f"- description: <description of the intent>\n"
        f"- icon_url: <optional SVG URL>\n\n"
        "OPTION 2 - Add intentDetails block to facets.yaml:\n"
        f"{yaml_snippet}\n\n"
        "Available type options from existing intents:\n"
        f"{type_suggestions}\n"
        f"{type_note}\n\n"
        "Use list_all_intents() to see all existing intents and their types.\n"
        "Use get_intent('<name>') to check if a specific intent exists.\n\n"
        "Note: iconUrl is optional - only include it if you have a specific SVG file URL."
    )
    return False, message
