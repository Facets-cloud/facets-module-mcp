import os
from facets_mcp.config import mcp

# Enhanced prompt to derive module requirements and implement Terraform
@mcp.prompt(name="New Module Generation")
def generate_new_module() -> str:
    """
    Enhanced prompt to be used for creating a new module. This will read from the `generate_module.md` file.

    Returns:
        The content of the prompt read from the markdown file.
    """
    guide_message = ""
    try:
        # Get the directory of the current file
        base_dir = os.path.dirname(__file__)
        # Construct the full path to the markdown file
        file_path = os.path.join(base_dir, "generate_module.md")

        with open(file_path, "r") as file:
            guide_message = file.read()
    except FileNotFoundError:
        guide_message = "Error: The `generate_module.md` file was not found."
    return guide_message
