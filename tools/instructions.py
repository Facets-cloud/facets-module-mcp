import os
from config import mcp, working_directory


@mcp.tool()
def get_important_module_writing_instructions() -> str:
    """
    Loads important module writing instructions for Facets module development.

    This function reads the content of `instructions.md`, which contains an enhanced
    prompt used for guiding in creating or editing a Facets-compatible module.

    Returns:
        str: The content of the `instructions.md` file, or an error message if the file is not found.
    """
    guide_message = ""
    try:
        # Get the directory of the current file
        base_dir = os.path.dirname(__file__)
        # Construct the full path to the markdown file
        file_path = os.path.join(base_dir, "instructions.md")

        with open(file_path, "r") as file:
            guide_message = file.read()
    except FileNotFoundError:
        guide_message = "Error: The `instructions.md` file was not found."
    return guide_message
