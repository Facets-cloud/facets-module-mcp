import sys
from typing import Dict, Any, List, Optional
import os
import json

from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.ftf_command_utils import run_ftf_command, get_git_repo_info, create_temp_yaml_file
from facets_mcp.utils.file_utils import (
    generate_file_previews,
    ensure_path_in_working_directory,
    perform_text_replacement
)
from facets_mcp.utils.yaml_utils import (
    validate_yaml,
    validate_output_types,
    check_missing_output_types,
    read_and_validate_facets_yaml
)


@mcp.tool()
def generate_module_with_user_confirmation(intent: str, flavor: str, cloud: str, title: str, description: str,
                            dry_run: bool = True) -> str:
    """
    ⚠️ IMPORTANT: REQUIRES USER CONFIRMATION ⚠️
    This function performs an irreversible action

    Tool to generate a new module using FTF CLI.
    Step 1 - ALWAYS use dry_run=True first. This is an irreversible action.
    Step 2 - Present the dry run output to the user in textual format.
    Step 3 - Ask if user will like to make any changes in passed arguments and modify them
    Step 4 - Call the tool without dry run

    Args:
        intent (str): The purpose or intent of the module (e.g., "storage", "compute")
        flavor (str): The specific implementation variant (e.g., "s3", "ec2")
        cloud (str): The cloud provider (e.g., "aws", "azure", "gcp")
        title (str): Human-readable title for the module
        description (str): Detailed description of what the module does
        dry_run (bool): If True, show what would be generated without creating files

    Returns:
        str: JSON response with generation results or dry-run preview
    """
    try:
        # Construct the FTF command for module generation
        ftf_command = [
            "ftf", "module", "generate",
            "--intent", intent,
            "--flavor", flavor,
            "--cloud", cloud,
            "--title", title,
            "--description", description
        ]
        
        if dry_run:
            ftf_command.append("--dry-run")

        # Execute the FTF command
        result = run_ftf_command(ftf_command, working_directory)
        
        if dry_run:
            return json.dumps({
                "success": True,
                "message": "Dry run completed successfully. Review the output and confirm to proceed.",
                "instructions": "This is a DRY RUN. No files were created. Ask the user to confirm before proceeding with actual generation.",
                "data": {
                    "dry_run_output": result.get("output", ""),
                    "command_executed": " ".join(ftf_command),
                    "working_directory": working_directory,
                    "parameters": {
                        "intent": intent,
                        "flavor": flavor,
                        "cloud": cloud,
                        "title": title,
                        "description": description
                    }
                }
            }, indent=2)
        else:
            # Actual generation
            if result["success"]:
                return json.dumps({
                    "success": True,
                    "message": f"Successfully generated module with intent='{intent}', flavor='{flavor}', cloud='{cloud}'",
                    "instructions": "Module has been generated successfully. You can now use other tools to edit or validate the module.",
                    "data": {
                        "output": result.get("output", ""),
                        "command_executed": " ".join(ftf_command),
                        "working_directory": working_directory,
                        "module_details": {
                            "intent": intent,
                            "flavor": flavor,
                            "cloud": cloud,
                            "title": title,
                            "description": description
                        }
                    }
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Failed to generate module: {result.get('error', 'Unknown error')}",
                    "data": {
                        "output": result.get("output", ""),
                        "command_executed": " ".join(ftf_command)
                    }
                }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error in generate_module_with_user_confirmation tool: {str(e)}",
        }, indent=2)


@mcp.tool()
def write_config_files(module_path: str, facets_yaml_content: str, dry_run: bool = True) -> str:
    """
    Writes facets.yaml configuration file for a Terraform module.
    <important>Make Sure you have Called FIRST_STEP_get_instructions first before this tool.</important>

    Args:
        module_path (str): The path to the module directory where facets.yaml will be written.
        facets_yaml_content (str): The complete YAML content for the facets.yaml file.
        dry_run (bool): If True, validates and shows preview without writing the file.

    Returns:
        str: A JSON-formatted string with operation details and validation results.
    """
    try:
        # Ensure the module path is within the working directory
        safe_path = ensure_path_in_working_directory(module_path)
        facets_yaml_path = os.path.join(safe_path, "facets.yaml")

        # Validate YAML syntax
        yaml_validation = validate_yaml(facets_yaml_content)
        if not yaml_validation["valid"]:
            return json.dumps({
                "success": False,
                "error": f"Invalid YAML syntax: {yaml_validation['error']}",
                "data": {
                    "module_path": module_path,
                    "file_path": facets_yaml_path
                }
            }, indent=2)

        # Parse and validate the YAML content
        parsed_yaml = yaml_validation["parsed"]

        # Validate output types if present
        output_types_validation = validate_output_types(parsed_yaml)
        missing_output_types = check_missing_output_types(parsed_yaml)

        # Generate validation summary
        validation_summary = {
            "yaml_syntax": "✓ Valid" if yaml_validation["valid"] else f"✗ {yaml_validation['error']}",
            "output_types_validation": output_types_validation,
            "missing_output_types": missing_output_types
        }

        if dry_run:
            # Generate preview
            preview_content = generate_file_previews({
                "facets.yaml": facets_yaml_content
            })

            return json.dumps({
                "success": True,
                "message": "Dry run completed successfully. File validated and preview generated.",
                "instructions": "Review the preview and validation results. Call again with dry_run=False to write the file.",
                "data": {
                    "module_path": module_path,
                    "file_path": facets_yaml_path,
                    "validation_summary": validation_summary,
                    "preview": preview_content,
                    "file_exists": os.path.exists(facets_yaml_path)
                }
            }, indent=2)

        else:
            # Create directory if it doesn't exist
            os.makedirs(safe_path, exist_ok=True)

            # Write the file
            with open(facets_yaml_path, 'w') as f:
                f.write(facets_yaml_content)

            return json.dumps({
                "success": True,
                "message": f"Successfully wrote facets.yaml to '{module_path}'.",
                "data": {
                    "module_path": module_path,
                    "file_path": facets_yaml_path,
                    "validation_summary": validation_summary,
                    "bytes_written": len(facets_yaml_content.encode('utf-8'))
                }
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error writing facets.yaml to '{module_path}': {str(e)}",
        }, indent=2)


@mcp.tool()
def write_resource_file(module_path: str, file_name: str, file_content: str, dry_run: bool = True) -> str:
    """
    Writes a Terraform resource file (main.tf, variables.tf, etc.) to a module directory.

    This tool is designed to write Terraform configuration files excluding outputs.tf
    (use write_outputs tool for that) and facets.yaml (use write_config_files for that).

    Args:
        module_path (str): The path to the module directory where the file will be written.
        file_name (str): The name of the file to write (e.g., "main.tf", "variables.tf", "versions.tf").
        file_content (str): The complete content for the file.
        dry_run (bool): If True, shows preview without writing the file.

    Returns:
        str: A JSON-formatted string with operation details.
    """
    try:
        # Ensure the module path is within the working directory
        safe_path = ensure_path_in_working_directory(module_path)
        file_path = os.path.join(safe_path, file_name)

        # Validate that this is not outputs.tf or facets.yaml (these have dedicated tools)
        if file_name.lower() == "outputs.tf":
            return json.dumps({
                "success": False,
                "error": "Use write_outputs tool for writing outputs.tf files.",
                "data": {
                    "module_path": module_path,
                    "file_name": file_name
                }
            }, indent=2)

        if file_name.lower() == "facets.yaml":
            return json.dumps({
                "success": False,
                "error": "Use write_config_files tool for writing facets.yaml files.",
                "data": {
                    "module_path": module_path,
                    "file_name": file_name
                }
            }, indent=2)

        if dry_run:
            # Generate preview
            preview_content = generate_file_previews({
                file_name: file_content
            })

            return json.dumps({
                "success": True,
                "message": "Dry run completed successfully. File preview generated.",
                "instructions": "Review the preview. Call again with dry_run=False to write the file.",
                "data": {
                    "module_path": module_path,
                    "file_name": file_name,
                    "file_path": file_path,
                    "preview": preview_content,
                    "file_exists": os.path.exists(file_path),
                    "content_size": len(file_content)
                }
            }, indent=2)

        else:
            # Create directory if it doesn't exist
            os.makedirs(safe_path, exist_ok=True)

            # Write the file
            with open(file_path, 'w') as f:
                f.write(file_content)

            return json.dumps({
                "success": True,
                "message": f"Successfully wrote '{file_name}' to '{module_path}'.",
                "data": {
                    "module_path": module_path,
                    "file_name": file_name,
                    "file_path": file_path,
                    "bytes_written": len(file_content.encode('utf-8'))
                }
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error writing '{file_name}' to '{module_path}': {str(e)}",
        }, indent=2)


@mcp.tool()
def write_outputs(module_path: str, outputs_attributes: Dict[str, Any], outputs_interfaces: Dict[str, Any] = None, dry_run: bool = True) -> str:
    """
    Write the outputs.tf file for a module with a local block containing outputs_attributes and outputs_interfaces.

    Args:
        module_path (str): The path to the module directory where outputs.tf will be written.
        outputs_attributes (Dict[str, Any]): The attributes to include in the outputs_attributes local value.
        outputs_interfaces (Dict[str, Any], optional): The interfaces to include in the outputs_interfaces local value.
        dry_run (bool): If True, shows preview without writing the file.

    Returns:
        str: A JSON-formatted string with operation details.
    """
    try:
        # Ensure the module path is within the working directory
        safe_path = ensure_path_in_working_directory(module_path)
        outputs_file_path = os.path.join(safe_path, "outputs.tf")

        # Helper to render values correctly for Terraform
        def render_terraform_value(v):
            if isinstance(v, bool):
                return str(v).lower()
            elif isinstance(v, (int, float)):
                return str(v)
            elif isinstance(v, str):
                return f'"{v}"'
            elif isinstance(v, list):
                items = [render_terraform_value(item) for item in v]
                return f'[{", ".join(items)}]'
            elif isinstance(v, dict):
                items = [f'"{k}" = {render_terraform_value(v)}' for k, v in v.items()]
                return f'{{{", ".join(items)}}}'
            else:
                return f'"{str(v)}"'

        # Build the outputs.tf content
        content_lines = []
        content_lines.append("locals {")
        
        # Add outputs_attributes
        content_lines.append("  outputs_attributes = {")
        for key, value in outputs_attributes.items():
            rendered_value = render_terraform_value(value)
            content_lines.append(f'    "{key}" = {rendered_value}')
        content_lines.append("  }")
        
        # Add outputs_interfaces if provided
        if outputs_interfaces:
            content_lines.append("")
            content_lines.append("  outputs_interfaces = {")
            for key, value in outputs_interfaces.items():
                rendered_value = render_terraform_value(value)
                content_lines.append(f'    "{key}" = {rendered_value}')
            content_lines.append("  }")
        
        content_lines.append("}")
        
        # Join all lines
        file_content = "\n".join(content_lines) + "\n"

        if dry_run:
            # Generate preview
            preview_content = generate_file_previews({
                "outputs.tf": file_content
            })

            return json.dumps({
                "success": True,
                "message": "Dry run completed successfully. outputs.tf preview generated.",
                "instructions": "Review the preview. Call again with dry_run=False to write the file.",
                "data": {
                    "module_path": module_path,
                    "file_path": outputs_file_path,
                    "preview": preview_content,
                    "file_exists": os.path.exists(outputs_file_path),
                    "content_size": len(file_content)
                }
            }, indent=2)

        else:
            # Create directory if it doesn't exist
            os.makedirs(safe_path, exist_ok=True)

            # Write the file
            with open(outputs_file_path, 'w') as f:
                f.write(file_content)

            return json.dumps({
                "success": True,
                "message": f"Successfully wrote outputs.tf to '{module_path}'.",
                "data": {
                    "module_path": module_path,
                    "file_path": outputs_file_path,
                    "bytes_written": len(file_content.encode('utf-8')),
                    "attributes_count": len(outputs_attributes),
                    "interfaces_count": len(outputs_interfaces) if outputs_interfaces else 0
                }
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error writing outputs.tf to '{module_path}': {str(e)}",
        }, indent=2)


@mcp.tool()
def write_readme_file(module_path: str, readme_content: str, dry_run: bool = True) -> str:
    """
    Writes a README.md file for the module directory.
    This tool is intended for AI to generate the README content for the module.

    Args:
        module_path (str): The path to the module directory where README.md will be written.
        readme_content (str): The complete markdown content for the README.md file.
        dry_run (bool): If True, shows preview without writing the file.

    Returns:
        str: A JSON-formatted string with operation details.
    """
    try:
        # Ensure the module path is within the working directory
        safe_path = ensure_path_in_working_directory(module_path)
        readme_file_path = os.path.join(safe_path, "README.md")

        if dry_run:
            # Generate preview (truncate if very long for readability)
            preview_content = readme_content
            if len(preview_content) > 2000:
                preview_content = preview_content[:2000] + "\n\n... (truncated for preview)"

            preview = generate_file_previews({
                "README.md": preview_content
            })

            return json.dumps({
                "success": True,
                "message": "Dry run completed successfully. README.md preview generated.",
                "instructions": "Review the preview. Call again with dry_run=False to write the file.",
                "data": {
                    "module_path": module_path,
                    "file_path": readme_file_path,
                    "preview": preview,
                    "file_exists": os.path.exists(readme_file_path),
                    "content_size": len(readme_content)
                }
            }, indent=2)

        else:
            # Create directory if it doesn't exist
            os.makedirs(safe_path, exist_ok=True)

            # Write the file
            with open(readme_file_path, 'w') as f:
                f.write(readme_content)

            return json.dumps({
                "success": True,
                "message": f"Successfully wrote README.md to '{module_path}'.",
                "data": {
                    "module_path": module_path,
                    "file_path": readme_file_path,
                    "bytes_written": len(readme_content.encode('utf-8'))
                }
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error writing README.md to '{module_path}': {str(e)}",
        }, indent=2)


@mcp.tool()
def edit_file_block(module_path: str, file_name: str, old_content: str, new_content: str) -> str:
    """
    Apply surgical edits to specific blocks of text in a file.
    <important>Make Sure you have Called FIRST_STEP_get_instructions first before this tool.</important>

    This tool allows precise editing of files by replacing specific blocks of text.
    It's useful for making targeted changes without rewriting entire files.

    Args:
        module_path (str): The path to the module directory containing the file.
        file_name (str): The name of the file to edit.
        old_content (str): The exact text content to be replaced.
        new_content (str): The new text content to replace the old content.

    Returns:
        str: A JSON-formatted string with operation details.
    """
    try:
        # Use the utility function to perform text replacement
        result = perform_text_replacement(module_path, file_name, old_content, new_content)
        
        if result["success"]:
            return json.dumps({
                "success": True,
                "message": f"Successfully edited '{file_name}' in '{module_path}'.",
                "data": result
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": result["error"],
                "data": result
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error editing '{file_name}' in '{module_path}': {str(e)}",
        }, indent=2)
