import os

from facets_mcp.config import mcp


@mcp.prompt(name="Generate Facets Actions")
def generate_facets_actions() -> str:
    """
    Interactive prompt to guide users through creating Facets Actions workflows.
    This reads from the `facets_actions.md` file for detailed workflow guidance.

    Returns:
        The content of the prompt read from the markdown file.
    """
    guide_message = ""
    try:
        # Get the directory of the current file
        base_dir = os.path.dirname(__file__)
        # Construct the full path to the markdown file
        file_path = os.path.join(base_dir, "facets_actions.md")

        with open(file_path) as file:
            guide_message = file.read()
    except FileNotFoundError:
        guide_message = "Error: The `facets_actions.md` file was not found."
    return guide_message