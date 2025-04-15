# This file contains tools for working with existing Terraform modules

import os
import sys
import json
import yaml
import glob
from typing import Optional, Dict, Any, List
from config import mcp, working_directory


@mcp.tool()
def get_available_modules() -> str:
    """
    Scan the working directory recursively for facets.yaml files to identify
    all available Terraform modules. So that user can start working on existing modules as well.
    
    Returns:
        str: JSON string containing a list of modules with their details:
             - path: Path to the module directory
             - intent: The module's intent value
             - flavor: The module's flavor value
             - version: The module's version value
             - outputs: The module's outputs section
    """
    try:
        modules = []
        
        # Search recursively for facets.yaml files
        for root, dirs, files in os.walk(working_directory):
            if 'facets.yaml' in files:
                # Skip .terraform directories 
                if '.terraform' in root:
                    continue
                    
                module_path = root
                facets_path = os.path.join(root, 'facets.yaml')
                
                try:
                    # Parse the facets.yaml file
                    with open(facets_path, 'r') as f:
                        facets_content = yaml.safe_load(f)
                    
                    # Extract relevant information
                    intent = facets_content.get('intent', '')
                    flavor = facets_content.get('flavor', '')
                    version = facets_content.get('version', '')
                    outputs = facets_content.get('outputs', {})
                    
                    # Add module info to the list
                    modules.append({
                        'path': module_path,
                        'intent': intent,
                        'flavor': flavor,
                        'version': version,
                        'outputs': outputs
                    })
                except Exception as e:
                    # If there's an error parsing this file, skip it but log the error
                    print(f"Error parsing {facets_path}: {str(e)}", file=sys.stderr)
                    continue
        
        # Return JSON string with module information
        return json.dumps({
            'modules': modules,
            'count': len(modules)
        }, indent=2)
        
    except Exception as e:
        error_message = f"Error scanning for modules: {str(e)}"
        print(error_message, file=sys.stderr)
        return json.dumps({
            'error': error_message,
            'modules': [],
            'count': 0
        })
