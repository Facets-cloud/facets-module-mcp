import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any
from config import mcp, working_directory


@mcp.tool()
def get_local_modules() -> str:
    """
    Scan the working directory recursively for facets.yaml files to identify
    all available Terraform modules. Also fetch content of outputs.tf if it exists.
    After:
        read instructions using get_all_module_writing_instructions

    Returns:
        str: JSON string containing a list of modules with their details:
             - path: Path to the module directory
             - intent: The module's intent value
             - flavor: The module's flavor value
             - version: The module's version value
             - outputs: The module's outputs section
             - outputs_tf: Raw string content of outputs.tf (if present)
    """
    try:
        modules = []
        root_path = Path(working_directory)

        for facets_file in root_path.rglob("facets.yaml"):
            if ".terraform" in facets_file.parts:
                continue

            module_path = facets_file.parent
            try:
                with open(facets_file, 'r') as f:
                    facets_content = yaml.safe_load(f)

                # Read outputs.tf if present
                outputs_tf_path = module_path / "outputs.tf"
                outputs_tf_content = ""
                if outputs_tf_path.exists():
                    outputs_tf_content = outputs_tf_path.read_text()

                modules.append({
                    "path": str(module_path),
                    "intent": facets_content.get("intent", ""),
                    "flavor": facets_content.get("flavor", ""),
                    "version": facets_content.get("version", ""),
                    "outputs": facets_content.get("outputs", {}),
                    "outputs_tf": outputs_tf_content
                })

            except Exception as e:
                print(f"Error parsing {facets_file}: {str(e)}", file=sys.stderr)
                continue

        return json.dumps({
            "modules": modules,
            "count": len(modules)
        }, indent=2)

    except Exception as e:
        error_message = f"Error scanning for modules: {str(e)}"
        print(error_message, file=sys.stderr)
        return json.dumps({
            "error": error_message,
            "modules": [],
            "count": 0
        })
