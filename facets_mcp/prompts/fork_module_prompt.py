import os

from facets_mcp.config import mcp


# Enhanced prompt for forking existing modules
@mcp.prompt(name="Fork Existing Module")
def fork_existing_module() -> str:
    """
    Enhanced prompt to be used for forking an existing module. This will read from the `fork_module.md` file.

    Returns:
        The content of the prompt read from the markdown file.
    """
    guide_message = ""
    try:
        # Get the directory of the current file
        base_dir = os.path.dirname(__file__)
        # Construct the full path to the markdown file
        file_path = os.path.join(base_dir, "fork_module.md")

        with open(file_path) as file:
            guide_message = file.read()
    except FileNotFoundError:
        guide_message = "Error: The `fork_module.md` file was not found."
    return guide_message
