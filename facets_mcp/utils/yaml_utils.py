"""
Utilities for YAML processing and validation in the facets-module-mcp project.
Contains helper functions for validating YAML files against schema requirements.
"""

import os
import sys
import yaml
from typing import Dict, Any, List, Optional, Tuple

# Import from project modules
from facets_mcp.utils.ftf_command_utils import run_ftf_command


def validate_yaml(module_path: str, yaml_content: str) -> str:
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
        with open(temp_path, 'w') as temp_file:
            temp_file.write(yaml_content)
    except Exception as e:
        return f"Error writing temporary validation file: {str(e)}"
    
    command = [
        "ftf", "validate-facets",
        "--filename", "facets.yaml.new",
        module_path
    ]

    validation_error = run_ftf_command(command)

    try:
        os.remove(temp_path)
    except Exception:
        pass

    if validation_error.startswith("Error executing command"):
        raise RuntimeError(validation_error)

    return validation_error


def validate_output_types(facets_yaml_content: str, output_api=None) -> Dict[str, Any]:
    """
    Validate output types in facets.yaml.
    Checks if output types mentioned in the outputs block exist in the Facets control plane.
    
    Args:
        facets_yaml_content (str): Content of facets.yaml file
        output_api: Optional UI TF Output Controller API instance
        
    Returns:
        Dict[str, Any]: Dictionary with validation results including missing outputs
    """
    try:
        # Parse YAML content
        facets_data = yaml.safe_load(facets_yaml_content)
        if not facets_data:
            return {}
        
        # Check if outputs block exists
        if 'outputs' not in facets_data:
            return {}
        
        outputs = facets_data.get('outputs', {})
        if not outputs:
            return {}
        
        # Extract output types from outputs block
        output_types = []
        for output_name, output_def in outputs.items():
            if 'type' in output_def:
                output_type = output_def['type']
                if output_type not in output_types:
                    output_types.append(output_type)
        
        if not output_types:
            return {}
        
        # Skip validation if no API client is provided
        if not output_api:
            return {"warning": "Output types not validated: API client not provided"}
        
        # Check if output types exist in Facets control plane
        missing_output_types = []
        
        for output_type in output_types:
            # Skip if not in @namespace/name format
            if not output_type.startswith('@') or '/' not in output_type:
                continue
            
            # Split the name into namespace and name parts
            name_parts = output_type.split('/', 1)
            if len(name_parts) != 2:
                continue
            
            namespace, output_name = name_parts
            
            # Check if the output exists
            try:
                output_api.get_output_by_name_using_get(name=output_name, namespace=namespace)
            except Exception as e:
                if hasattr(e, 'status') and e.status == 404:
                    missing_output_types.append(output_type)
                else:
                    print(f"Error checking output type {output_type}: {str(e)}", file=sys.stderr)
        
        return {"missing_outputs": missing_output_types}
    
    except Exception as e:
        print(f"Error validating output types: {str(e)}", file=sys.stderr)
        return {"error": f"Error validating output types: {str(e)}"}


def check_missing_output_types(output_validation_results: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check for missing output types and generate an appropriate error message.
    
    Args:
        output_validation_results (Dict[str, Any]): Results from validate_output_types
        
    Returns:
        Tuple[bool, str]: (has_missing_types, error_message)
            - has_missing_types: True if missing output types were found
            - error_message: A formatted error message if missing types were found, empty string otherwise
    """
    if not output_validation_results or "missing_outputs" not in output_validation_results:
        return False, ""
        
    missing_outputs = output_validation_results["missing_outputs"]
    if not missing_outputs:
        return False, ""
        
    missing_types_msg = f"Warning: The following output types do not exist and should be registered first using register_output_type:\n"
    
    for output_type in missing_outputs:
        missing_types_msg += f"- {output_type}\n"
    
    missing_types_msg += "\nPlease register these output types using register_output_type before writing the configuration."
    
    return True, missing_types_msg


def read_and_validate_facets_yaml(module_path: str, output_api=None) -> Tuple[bool, str, str]:
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
        return False, "", "Error: facets.yaml not found in module path. Please call write_config_files first to create the facets.yaml configuration."
        
    # Read facets.yaml content
    try:
        with open(facets_path, 'r') as f:
            facets_yaml_content = f.read()
    except Exception as e:
        return False, "", f"Error reading facets.yaml: {str(e)}"
        
    # Validate output types if API client is provided
    if output_api:
        output_validation_results = validate_output_types(facets_yaml_content, output_api)
        has_missing_types, error_message = check_missing_output_types(output_validation_results)
        
        if has_missing_types:
            return False, facets_yaml_content, error_message
            
    return True, facets_yaml_content, ""
