import os
import json
from facets_mcp.config import mcp, working_directory
from facets_mcp.utils.file_utils import (
    get_file_content
)
from pathlib import Path

@mcp.resource(uri="resource://facets_modules_knowledge", name="Facets Knowledge Base")
def call_always_for_instruction() -> str:
    return FIRST_STEP_get_instructions()


@mcp.tool()
def FIRST_STEP_get_instructions() -> str:
    """
    <important>ALWAYS Call this tool first before calling any other tool of this mcp.</important>
    Loads all module writing instructions for Facets module development found in the
    `module_instructions` directory and supplementary instructions from the
    `mcp_instructions` directory at the root level of the working directory.

    Returns:
        str: A JSON string containing the content of all instruction files,
              with each file's content stored under its filename as key.
    """
    def read_markdown_files(directory_path: str) -> dict:
        """
        Reads all markdown files from a specified directory.

        Args:
            directory_path (str): Path to the directory containing markdown files

        Returns:
            dict: Dictionary with filename as key and file content as value
        """
        files_content = {}

        try:
            if os.path.exists(directory_path):
                for filename in os.listdir(directory_path):
                    if filename.endswith(".md"):
                        file_path = os.path.join(directory_path, filename)
                        files_content[filename] = get_file_content(file_path)
        except Exception as e:
            files_content["_error"] = f"Error reading directory {directory_path}: {str(e)}"

        return files_content

    instructions = {}
    # Get the directory for module instructions
    base_dir = os.path.join(os.path.dirname(__file__), "module_instructions")

    # Read all markdown files in the directory (using helper function)
    instructions.update(read_markdown_files(base_dir))

    # Read supplementary instructions from mcp_instructions directory
    working_dir = Path(working_directory).resolve()
    supplementary_dir = os.path.join(working_dir, "mcp_instructions")
    supplementary_instructions = read_markdown_files(supplementary_dir)

    # Add supplementary instructions with prefix to distinguish them
    for filename, content in supplementary_instructions.items():
        instructions[f"supplementary_{filename}"] = content

    return json.dumps({
        "success": True,
        "message": "Instructions loaded successfully.",
        "instructions": "Inform User: Instructions loaded successfully.",
        "data": instructions
    }, indent=2)

