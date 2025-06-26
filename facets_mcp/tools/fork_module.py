import json
import os
import sys
import yaml
from pathlib import Path
from typing import Optional

from swagger_client.api.module_management_api import ModuleManagementApi
from swagger_client.rest import ApiException

from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.utils.file_utils import ensure_path_in_working_directory
from facets_mcp.utils.module_download_utils import download_and_extract_module_zip


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
        modules = modules_api.get_all_modules()
        
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
        # First, get the source module details to extract the intent
        api_client = ClientUtils.get_client()
        modules_api = ModuleManagementApi(api_client)
        
        # Find the source module to get its intent
        try:
            modules = modules_api.get_all_modules()
            source_module = None
            for module in modules:
                if module.id == source_module_id:
                    source_module = module
                    break
            
            if not source_module:
                return json.dumps({
                    "success": False,
                    "message": f"Source module '{source_module_id}' not found.",
                    "instructions": "Inform User: The specified module ID was not found in the control plane.",
                    "error": f"Module with ID '{source_module_id}' not found"
                }, indent=2)
            
            # Extract intent name
            intent_name = ""
            if source_module.intent_details and hasattr(source_module.intent_details, 'name'):
                intent_name = source_module.intent_details.name
            else:
                return json.dumps({
                    "success": False,
                    "message": "Source module has no valid intent details.",
                    "instructions": "Inform User: The source module does not have valid intent information.",
                    "error": "Source module intent details are missing or invalid"
                }, indent=2)
            
        except ApiException as e:
            return json.dumps({
                "success": False,
                "message": "Failed to retrieve source module details.",
                "instructions": "Inform User: Could not retrieve source module information from control plane.",
                "error": f"API error: {str(e)}"
            }, indent=2)
        
        # Determine target directory: intent/new_flavor/new_version
        target_directory = f"{intent_name}/{new_flavor}/{new_version}"
        full_target_path = ensure_path_in_working_directory(target_directory, working_directory)
        
        if dry_run:
            # Check if target directory already exists
            target_exists = os.path.exists(full_target_path)
            
            return json.dumps({
                "success": True,
                "message": f"Dry run: Fork module '{source_module_id}' to create new module",
                "instructions": (
                    "Inform User: Review the fork configuration below. "
                    "Ask User: Confirm the fork parameters or request changes before proceeding with actual fork operation."
                ),
                "data": {
                    "type": "dry_run",
                    "source_module": {
                        "id": source_module_id,
                        "intent": intent_name,
                        "flavor": source_module.flavor,
                        "version": source_module.version
                    },
                    "target_module": {
                        "intent": intent_name,
                        "flavor": new_flavor,
                        "version": new_version
                    },
                    "target_directory": target_directory,
                    "full_target_path": str(full_target_path),
                    "target_exists": target_exists,
                    "target_exists_warning": "⚠️ Target directory already exists and will be overwritten" if target_exists else None
                }
            }, indent=2)

        # Actual fork operation
        # Step 1: Download and extract the source module
        extract_result = download_and_extract_module_zip(source_module_id, target_directory)
        
        if "Error" in extract_result or "Failed" in extract_result:
            return json.dumps({
                "success": False,
                "message": "Failed to download source module",
                "instructions": "Inform User: Failed to download the source module for forking.",
                "error": extract_result
            }, indent=2)

        # Step 2: Read and modify facets.yaml
        facets_yaml_path = os.path.join(full_target_path, "facets.yaml")
        
        if not os.path.exists(facets_yaml_path):
            return json.dumps({
                "success": False,
                "message": "No facets.yaml found in downloaded module",
                "instructions": "Inform User: Downloaded module does not contain facets.yaml file.",
                "error": f"facets.yaml not found at {facets_yaml_path}"
            }, indent=2)

        # Load existing facets.yaml
        try:
            with open(facets_yaml_path, 'r') as f:
                facets_config = yaml.safe_load(f)
        except Exception as e:
            return json.dumps({
                "success": False,
                "message": "Failed to parse facets.yaml",
                "instructions": "Inform User: Could not parse the downloaded module's facets.yaml file.",
                "error": f"Error parsing facets.yaml: {str(e)}"
            }, indent=2)

        # Store original metadata for reference
        original_metadata = {
            "intent": facets_config.get("intent", ""),
            "flavor": facets_config.get("flavor", ""),
            "version": facets_config.get("version", "")
        }

        # Step 3: Update metadata (intent stays the same, update flavor and version)
        facets_config["flavor"] = new_flavor
        facets_config["version"] = new_version
        
        # Also update sample.flavor and sample.version if they exist
        if "sample" in facets_config:
            if "flavor" in facets_config["sample"]:
                facets_config["sample"]["flavor"] = new_flavor
            if "version" in facets_config["sample"]:
                facets_config["sample"]["version"] = new_version

        # Step 4: Write updated facets.yaml
        try:
            with open(facets_yaml_path, 'w') as f:
                yaml.dump(facets_config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            return json.dumps({
                "success": False,
                "message": "Failed to write updated facets.yaml",
                "instructions": "Inform User: Could not save the updated module configuration.",
                "error": f"Error writing facets.yaml: {str(e)}"
            }, indent=2)

        # Step 5: List the forked module files
        try:
            module_files = []
            for root, dirs, files in os.walk(full_target_path):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), full_target_path)
                    module_files.append(rel_path)
        except Exception:
            module_files = ["Could not list files"]

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
                    "intent": intent_name,
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
