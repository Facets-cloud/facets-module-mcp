import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.file_utils import ensure_path_in_working_directory


@mcp.tool()
def write_tekton_file(
    module_path: str,
    workflows: List[Dict[str, Any]],
    dry_run: bool = True
) -> str:
    """
    Writes a tekton.tf file with Facets Actions workflows to a module directory.
    
    Steps for safe tekton.tf creation:
    1. Always run with `dry_run=True` first. This is an irreversible action.
    2. Preview the generated tekton.tf content
    3. Ask the user to confirm before proceeding
    4. Only if the user **explicitly confirms**, run again with `dry_run=False`.

    Args:
        module_path (str): Path to the module directory.
        workflows (List[Dict]): List of workflow configurations with:
            - name (str): Kebab-case workflow name
            - description (str): Workflow description
            - params (List[Dict], optional): Parameters with name, type, description, default
            - steps (List[Dict]): Steps with name, image, script, env_vars (optional)
        dry_run (bool): If True, returns a preview without creating the file. Default is True.

    Returns:
        str: Success message, preview content (if dry_run=True), or error message.
    """
    if not workflows:
        return json.dumps({
            "success": False,
            "message": "No workflows provided.",
            "instructions": "Please provide at least one workflow configuration.",
            "error": "workflows argument is empty."
        }, indent=2)

    try:
        # Validate and normalize module path
        full_module_path = Path(module_path).resolve()
        working_dir = Path(working_directory).resolve()
        
        # Security check - ensure within working directory
        try:
            full_module_path.relative_to(working_dir)
        except ValueError:
            return json.dumps({
                "success": False,
                "message": "Module path is outside the working directory.",
                "instructions": "Inform User: Please provide a valid module path within the working directory.",
                "error": f"Attempt to write files outside of the working directory. Module path: {full_module_path}, Working directory: {working_dir}"
            }, indent=2)

        # Generate tekton.tf content
        tekton_content = _generate_tekton_content(workflows)
        
        if dry_run:
            return json.dumps({
                "success": True,
                "message": "Tekton.tf content generated (dry run).",
                "instructions": "Review the content below and confirm to proceed with actual file creation.",
                "preview": tekton_content,
                "data": {
                    "workflow_count": len(workflows),
                    "file_path": str(full_module_path / "tekton.tf")
                }
            }, indent=2)

        # Ensure module directory exists
        full_module_path.mkdir(parents=True, exist_ok=True)
        
        # Write tekton.tf file
        tekton_file = full_module_path / "tekton.tf"
        tekton_file.write_text(tekton_content, encoding="utf-8")

        return json.dumps({
            "success": True,
            "message": f"Successfully wrote tekton.tf with {len(workflows)} workflow(s).",
            "instructions": "Tekton.tf file has been created. You can now validate the module.",
            "data": {
                "file_path": str(tekton_file),
                "workflow_count": len(workflows),
                "workflows": [w.get("name", "unnamed") for w in workflows]
            }
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "message": "Failed to write tekton.tf file.",
            "instructions": "An error occurred while generating the tekton.tf file. Please check the workflow configurations.",
            "error": str(e)
        }, indent=2)


def _generate_tekton_content(workflows: List[Dict[str, Any]]) -> str:
    """
    Generate the tekton.tf file content from workflow configurations.
    
    Args:
        workflows: List of workflow configurations
        
    Returns:
        str: Generated tekton.tf content
    """
    tekton_modules = []
    
    for workflow in workflows:
        module_content = _generate_workflow_module(workflow)
        tekton_modules.append(module_content)
    
    return "\n\n".join(tekton_modules) + "\n"


def _generate_workflow_module(workflow: Dict[str, Any]) -> str:
    """
    Generate a single workflow module block.
    
    Args:
        workflow: Workflow configuration dictionary
        
    Returns:
        str: Generated module block
    """
    name = workflow.get("name", "unnamed-workflow")
    description = workflow.get("description", "")
    params = workflow.get("params", [])
    steps = workflow.get("steps", [])
    
    # Generate module header
    module_name = f"{name.replace('-', '_')}_task"
    
    lines = [
        f'module "{module_name}" {{',
        '  source = "github.com/Facets-cloud/facets-utility-modules//facets-workflows/kubernetes?ref=workflows"',
        f'  name   = "{name}"',
        '',
        '  instance_name    = var.instance_name',
        '  environment      = var.environment',
        '  instance         = var.instance',
        '  auth_secret_name = module.legacy_eks.legacy_attributes.k8s_details.workflows_auth_secret_name',
        '  providers = {',
        '    helm = "helm.release-pod"',
        '  }',
        ''
    ]
    
    # Add description
    if description:
        lines.append(f'  description = "{description}"')
    
    # Add params if any
    if params:
        lines.append('  params = [')
        for param in params:
            param_block = _generate_param_block(param)
            lines.append(f'    {param_block}')
        lines.append('  ]')
    
    # Add steps
    if steps:
        lines.append('  steps = [')
        for step in steps:
            step_block = _generate_step_block(step)
            lines.extend([f'    {line}' for line in step_block.split('\n')])
        lines.append('  ]')
    
    lines.append('}')
    
    return '\n'.join(lines)


def _generate_param_block(param: Dict[str, Any]) -> str:
    """Generate a parameter block."""
    name = param.get("name", "")
    param_type = param.get("type", "string")
    description = param.get("description", "")
    default = param.get("default", "")
    
    lines = [
        '{',
        f'      name        = "{name}"',
        f'      type        = "{param_type}"',
        f'      description = "{description}"'
    ]
    
    if default:
        if param_type == "array":
            default_str = json.dumps(default) if isinstance(default, list) else f'[{default}]'
        else:
            default_str = f'"{default}"'
        lines.append(f'      default     = {default_str}')
    
    lines.append('    }')
    return '\n'.join(lines)


def _generate_step_block(step: Dict[str, Any]) -> str:
    """Generate a step block with intelligent env var handling."""
    name = step.get("name", "")
    image = step.get("image", "bitnami/kubectl:latest")
    script = step.get("script", "#!/bin/bash\necho 'Task completed successfully!'")
    env_vars = step.get("env_vars", {})
    
    lines = [
        '{',
        f'      name      = "{name}"',
        f'      image     = "{image}"',
        '      resources = {}'
    ]
    
    # Handle environment variables
    if env_vars:
        lines.append('      env = [')
        for env_name, env_value in env_vars.items():
            # Determine if this is a secret/sensitive value that needs env wrapping
            if _is_sensitive_value(env_value):
                lines.append('        {')
                lines.append(f'          name  = "{env_name}"')
                lines.append(f'          value = {env_value}')
                lines.append('        }')
            else:
                # For non-sensitive values, still add to env for consistency
                lines.append('        {')
                lines.append(f'          name  = "{env_name}"')
                lines.append(f'          value = {env_value}')
                lines.append('        }')
        lines.append('      ]')
    else:
        lines.append('      env = []')
    
    # Add script with proper heredoc formatting
    lines.extend([
        '      script = <<-EOT',
        f'        {script}',
        '      EOT'
    ])
    
    lines.append('    }')
    return '\n'.join(lines)


def _is_sensitive_value(value: str) -> bool:
    """
    Determine if a value is sensitive and should be passed via environment variables.
    
    Args:
        value: The terraform value/reference
        
    Returns:
        bool: True if sensitive, False otherwise
    """
    sensitive_patterns = [
        r'\.secret',
        r'\.token',
        r'\.password',
        r'\.key',
        r'\.credential',
        r'_secret',
        r'_token',
        r'_password',
        r'_key'
    ]
    
    for pattern in sensitive_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    
    return False