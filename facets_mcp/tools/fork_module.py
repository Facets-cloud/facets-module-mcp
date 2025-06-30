import json
import os
import sys
import yaml

from swagger_client.api.module_management_api import ModuleManagementApi
from swagger_client.rest import ApiException

from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.utils.module_download_utils import download_and_extract_module_zip


def _get_source_module_details(module_id: str) -> tuple[bool, dict, str]:
    """
    Get source module details from the control plane.
    
    Args:
        module_id (str): ID of the module to get details for
        
    Returns:
        tuple[bool, dict, str]: (success, module_data, error_message)
    """
    try:
        api_client = ClientUtils.get_client()
        modules_api = ModuleManagementApi(api_client)
        
        modules = modules_api.get_all_modules(can_download=True)
        source_module = None
        for module in modules:
            if module.id == module_id:
                source_module = module
                break
        
        if not source_module:
            return False, {}, f"Module with ID '{module_id}' not found"
        
        # Extract intent name
        intent_name = ""
        if source_module.intent_details and hasattr(source_module.intent_details, 'name'):
            intent_name = source_module.intent_details.name
        else:
            return False, {}, "Source module has no valid intent details"
        
        module_data = {
            "id": source_module.id,
            "intent": intent_name,
            "flavor": source_module.flavor,
            "version": source_module.version
        }
        
        return True, module_data, ""
        
    except ApiException as e:
        return False, {}, f"API error: {str(e)}"
    except Exception as e:
        return False, {}, f"Error retrieving module details: {str(e)}"


def _perform_dry_run(source_module: dict, target_info: dict) -> dict:
    """
    Perform dry run validation and return dry run response.
    
    Args:
        source_module (dict): Source module information
        target_info (dict): Target module information including path
        
    Returns:
        dict: Dry run response data
    """
    target_exists = os.path.exists(target_info["full_path"])
    
    return {
        "success": True,
        "message": f"Dry run: Fork module '{source_module['id']}' to create new module",
        "instructions": (
            "Inform User: Review the fork configuration below. "
            "Ask User: Confirm the fork parameters or request changes before proceeding with actual fork operation."
        ),
        "data": {
            "type": "dry_run",
            "source_module": source_module,
            "target_module": {
                "intent": target_info["intent"],
                "flavor": target_info["flavor"],
                "version": target_info["version"]
            },
            "target_directory": target_info["directory"],
            "full_target_path": str(target_info["full_path"]),
            "target_exists": target_exists,
            "target_exists_warning": "⚠️ Target directory already exists and will be overwritten" if target_exists else None
        }
    }


def _download_and_extract_module(module_id: str, target_directory: str) -> tuple[bool, str]:
    """
    Download and extract module to target directory.
    
    Args:
        module_id (str): ID of module to download
        target_directory (str): Target directory for extraction
        
    Returns:
        tuple[bool, str]: (success, error_message_if_failed)
    """
    success, message = download_and_extract_module_zip(module_id, target_directory)
    return success, message if not success else ""


def _update_module_metadata(facets_path: str, new_flavor: str, new_version: str) -> tuple[bool, dict, str]:
    """
    Update module metadata in facets.yaml file.
    
    Args:
        facets_path (str): Path to facets.yaml file
        new_flavor (str): New flavor value
        new_version (str): New version value
        
    Returns:
        tuple[bool, dict, str]: (success, original_metadata, error_message)
    """
    if not os.path.exists(facets_path):
        return False, {}, f"facets.yaml not found at {facets_path}"

    try:
        # Load existing facets.yaml
        with open(facets_path, 'r') as f:
            facets_config = yaml.safe_load(f)
        
        # Store original metadata for reference
        original_metadata = {
            "intent": facets_config.get("intent", ""),
            "flavor": facets_config.get("flavor", ""),
            "version": facets_config.get("version", "")
        }

        # Update metadata (intent stays the same, update flavor and version)
        facets_config["flavor"] = new_flavor
        facets_config["version"] = new_version
        
        # Also update sample.flavor and sample.version if they exist
        if "sample" in facets_config:
            if "flavor" in facets_config["sample"]:
                facets_config["sample"]["flavor"] = new_flavor
            if "version" in facets_config["sample"]:
                facets_config["sample"]["version"] = new_version

        # Write updated facets.yaml
        with open(facets_path, 'w') as f:
            yaml.dump(facets_config, f, default_flow_style=False, sort_keys=False)
            
        return True, original_metadata, ""
        
    except Exception as e:
        return False, {}, f"Error updating facets.yaml: {str(e)}"


def _list_module_files(path: str) -> list:
    """
    List all files in the module directory.
    
    Args:
        path (str): Path to module directory
        
    Returns:
        list: List of relative file paths
    """
    try:
        module_files = []
        for root, _, files in os.walk(path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), path)
                module_files.append(rel_path)
        return module_files
    except Exception:
        return ["Could not list files"]


@mcp.tool()
def list_modules_for_fork() -> str:
    """
    List all available modules from the control plane that can be forked.
    Returns basic module information in a simple format for easy selection.

    Returns:
        str: JSON formatted list of available modules with their metadata
    """
    try:
        # Initialize API client
        api_client = ClientUtils.get_client()
        modules_api = ModuleManagementApi(api_client)
        
        # Get all modules
        modules = modules_api.get_all_modules(can_download=True)
        
        if not modules:
            return json.dumps({
                "success": True,
                "message": "No modules found for forking.",
                "instructions": "Inform User: No modules are currently available for forking.",
                "data": {
                    "modules": [],
                    "count": 0
                }
            }, indent=2)
        
        # Format modules for display - compact single line format
        formatted_modules = []
        for module in modules:
            intent_name = ""
            if module.intent_details and hasattr(module.intent_details, 'name'):
                intent_name = module.intent_details.name
            
            flavor = module.flavor or ""
            version = module.version or ""
            module_line = f"{intent_name}/{flavor}/{version} (ID: {module.id})"
            formatted_modules.append(module_line)
        
        return json.dumps({
            "success": True,
            "message": f"Found {len(formatted_modules)} module(s) available for forking.",
            "instructions": "Ask user to choose the module to fork",
            "data": {
                "modules": formatted_modules,
                "count": len(formatted_modules)
            }
        }, indent=2)
        
    except ApiException as e:
        error_message = f"API error listing modules: {str(e)}"
        print(error_message, file=sys.stderr)
        return json.dumps({
            "success": False,
            "message": "Failed to retrieve modules from control plane.",
            "instructions": "Inform User: Could not retrieve the list of available modules for forking.",
            "error": error_message
        }, indent=2)
    
    except Exception as e:
        error_message = f"Error listing available modules: {str(e)}"
        print(error_message, file=sys.stderr)
        return json.dumps({
            "success": False,
            "message": "Failed to list available modules",
            "instructions": "Inform User: Could not retrieve the list of available modules for forking.",
            "error": error_message
        }, indent=2)


@mcp.tool()
def fork_existing_module(
    source_module_id: str,
    new_flavor: str,
    new_version: str = "1.0.0",
    dry_run: bool = True
) -> str:
    """
    Fork an existing module by downloading it and updating its metadata.
    
    ⚠️ IMPORTANT: REQUIRES USER CONFIRMATION ⚠️ 
    This function performs an irreversible action.
    
    Step 1 - ALWAYS use dry_run=True first. This is an irreversible action.
    Step 2 - Present the dry run output to the user showing what will be changed.
    Step 3 - Ask if user wants to make any changes to the fork parameters.
    Step 4 - Call the tool without dry run to execute the fork.

    Args:
        source_module_id (str): ID of the module to fork from the control plane
        new_flavor (str): New flavor name for the forked module
        new_version (str): New version for the forked module (default: "1.0.0")
        dry_run (bool): If True, shows what would be done without executing (default: True)

    Returns:
        str: JSON formatted response with fork operation details
    """
    try:
        # Get source module details
        success, source_module, error_msg = _get_source_module_details(source_module_id)
        if not success:
            return json.dumps({
                "success": False,
                "message": f"Source module '{source_module_id}' not found or invalid.",
                "instructions": "Inform User: The specified module could not be retrieved from the control plane.",
                "error": error_msg
            }, indent=2)
        
        # Prepare target information
        target_directory = os.path.join(source_module['intent'], new_flavor, new_version)
        full_target_path = os.path.join(working_directory, target_directory)
        
        target_info = {
            "intent": source_module["intent"],
            "flavor": new_flavor,
            "version": new_version,
            "directory": target_directory,
            "full_path": full_target_path
        }
        
        if dry_run:
            dry_run_result = _perform_dry_run(source_module, target_info)
            return json.dumps(dry_run_result, indent=2)

        # Actual fork operation
        # Step 1: Download and extract the source module
        success, error_msg = _download_and_extract_module(source_module_id, full_target_path)
        if not success:
            return json.dumps({
                "success": False,
                "message": "Failed to download source module",
                "instructions": "Inform User: Failed to download the source module for forking.",
                "error": error_msg
            }, indent=2)

        # Step 2: Update module metadata
        facets_yaml_path = os.path.join(full_target_path, "facets.yaml")
        success, original_metadata, error_msg = _update_module_metadata(facets_yaml_path, new_flavor, new_version)
        if not success:
            return json.dumps({
                "success": False,
                "message": "Failed to update module metadata",
                "instructions": "Inform User: Could not update the module configuration.",
                "error": error_msg
            }, indent=2)

        # Step 3: List module files
        module_files = _list_module_files(full_target_path)

        return json.dumps({
            "success": True,
            "message": f"Successfully forked module '{source_module_id}' to '{target_directory}'",
            "instructions": (
                f"Inform User: Module has been successfully forked to '{target_directory}'. "
                "You can now review and modify the forked module files using the edit and write tools, "
                "then use the validation and preview tools to test it."
            ),
            "data": {
                "source_module_id": source_module_id,
                "target_directory": target_directory,
                "full_path": str(full_target_path),
                "original_metadata": original_metadata,
                "new_metadata": {
                    "intent": source_module["intent"],
                    "flavor": new_flavor,
                    "version": new_version
                },
                "module_files": module_files,
                "next_steps": [
                    "Review the forked module files",
                    "Make any necessary customizations using edit_file_block and write_resource_file",
                    "Use validate_module() to check the module",
                    "Use push_preview_module_to_facets_cp() to test the module"
                ]
            }
        }, indent=2)

    except Exception as e:
        error_message = f"Error during fork operation: {str(e)}"
        print(error_message, file=sys.stderr)
        return json.dumps({
            "success": False,
            "message": "Fork operation failed",
            "instructions": "Inform User: An unexpected error occurred during the fork operation.",
            "error": error_message
        }, indent=2)
