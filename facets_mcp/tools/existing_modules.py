import json
import sys
from pathlib import Path

import yaml

from facets_mcp.config import mcp, working_directory


def read_facets_file(facets_file):
    """Helper function to read a facets.yaml file."""
    with open(facets_file) as f:
        return yaml.safe_load(f)


def fetch_modules(search_string: str = None):
    """Utility function to fetch modules based on optional search string."""
    modules = []
    root_path = Path(working_directory)

    # Collect all matching facets.yaml files
    facets_files = list(root_path.rglob("facets.yaml"))

    # Iterate through the files and filter modules
    for facets_file in facets_files:
        if ".terraform" in facets_file.parts:
            continue

        facets_content = read_facets_file(facets_file)

        # Read outputs.tf if present
        outputs_tf_path = facets_file.parent / "outputs.tf"
        outputs_tf_content = ""
        if outputs_tf_path.exists():
            outputs_tf_content = outputs_tf_path.read_text()

        # Only filter if search_string is provided
        if search_string:
            if (
                search_string in str(facets_content.get("intent", ""))
                or search_string in str(facets_content.get("flavor", ""))
                or search_string in str(facets_content.get("version", ""))
            ):
                modules.append(
                    {
                        "path": str(facets_file.parent),
                        "intent": facets_content.get("intent", ""),
                        "flavor": facets_content.get("flavor", ""),
                        "version": facets_content.get("version", ""),
                        "outputs_tf": outputs_tf_content,  # Include outputs_tf
                    }
                )
        else:
            # If no search string, fetch all modules
            modules.append(
                {
                    "path": str(facets_file.parent),
                    "intent": facets_content.get("intent", ""),
                    "flavor": facets_content.get("flavor", ""),
                    "version": facets_content.get("version", ""),
                    "outputs_tf": outputs_tf_content,  # Include outputs_tf
                }
            )

    return modules


@mcp.tool()
def get_local_modules() -> str:
    """
    Scan the working directory recursively for facets.yaml files to identify
    all available Terraform modules. Also fetch content of outputs.tf if it exists.
    <important>ALWAYS Call this call_always_for_instruction first before calling any other tool of this mcp.</important>

    Returns:
        str: JSON string with success, message, instructions, and optional error/data fields. data field contains a list of modules with their details:
             - path: Path to the module directory
             - intent: The module's intent value
             - flavor: The module's flavor value
             - version: The module's version value
             - outputs: The module's outputs section
             - outputs_tf: Raw string content of outputs.tf (if present)
    """
    try:
        modules = fetch_modules()  # Use utility function to get all modules
        total_modules_count = len(modules)  # Total count of files

        # Limit to the first 10 modules and prepare additional instruction
        limited_modules = modules[:10]
        instruction = "Inform User: For more modules, use the `find module` command to search for and work on a specific module."

        # Create appropriate message based on whether we're showing all or limited results
        if total_modules_count <= 10:
            message = f"Found {total_modules_count} modules."
        else:
            message = f"Found {len(limited_modules)} modules (showing first 10 of {total_modules_count})."

        return json.dumps(
            {
                "success": True,
                "message": message,
                "instructions": instruction,
                "data": {
                    "modules": limited_modules,
                    "count": len(limited_modules),
                    "total_count": total_modules_count,
                },
            },
            indent=2,
        )

    except Exception as e:
        error_message = f"Error scanning for modules: {e!s}"
        print(error_message, file=sys.stderr)
        return json.dumps(
            {
                "success": False,
                "message": "Failed to scan for modules.",
                "instructions": "Inform User: Error scanning for modules.",
                "error": error_message,
                "data": {"modules": [], "count": 0, "total_count": 0},
            },
            indent=2,
        )


@mcp.tool()
def search_modules_after_confirmation(search_string: str, page: int = 1) -> str:
    """
        Search for a specific string in all facets.yaml files to filter modules.
        This tool should only be used after confirming search intent with the user.
    For exploratory searches, first explain search capabilities before executing.

        Args:
            search_string (str): The string to search for in modules.
            page (int): The page number for pagination.

        Returns:
            str: JSON string with success, message, instructions, and optional error/data fields. data field contains the filtered modules along with their details.
    """
    try:
        items_per_page: int = 10
        matched_modules = fetch_modules(
            search_string
        )  # Use utility function to fetch filtered modules
        total_count = len(matched_modules)  # Total count of filtered modules

        # Calculate start and end indices for pagination
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page

        # Limit to the items in the current page
        limited_modules = matched_modules[start_index:end_index]

        # Instruction for pagination
        instructions = ""
        if total_count > items_per_page:
            instructions = (
                "Inform User: There are more modules available. "
                "Please refine your search or use pagination to view additional results."
            )

        return json.dumps(
            {
                "success": True,
                "message": f"Found {total_count} matching module(s). Showing page {page}.",
                "instructions": instructions,
                "data": {
                    "modules": limited_modules,
                    "count": len(limited_modules),
                    "total_count": total_count,
                    "page": page,
                    "items_per_page": items_per_page,
                },
            },
            indent=2,
        )

    except Exception as e:
        error_message = f"Error searching for modules: {e!s}"
        print(error_message, file=sys.stderr)
        return json.dumps(
            {
                "success": False,
                "message": "Failed to search modules.",
                "instructions": "Inform User: Error searching for modules.",
                "error": error_message,
                "data": {
                    "matched_modules": [],
                    "count": 0,
                    "total_count": 0,
                },
            },
            indent=2,
        )
