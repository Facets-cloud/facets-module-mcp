import os
import json
from facets_mcp.config import mcp, working_directory


@mcp.resource(uri="resource://facets_modules_knowledge", name="Facets Knowledge Base")
def call_always_for_instruction() -> str:
    return FIRST_STEP_get_instructions()


@mcp.tool()
def FIRST_STEP_get_instructions() -> str:
    """
    <important>ALWAYS Call this tool first before calling any other tool of this mcp.</important>
    Loads all module writing instructions for Facets module development found in the
    `module_instructions` directory.
    
    Returns:
        str: A JSON string containing the content of all instruction files, 
              with each file's content stored under its filename as key.
    """
    instructions = {}
    try:
        # Get the directory for module instructions
        base_dir = os.path.join(os.path.dirname(__file__), "module_instructions")

        # Read all markdown files in the directory
        for filename in os.listdir(base_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(base_dir, filename)
                with open(file_path, "r", encoding='utf-8') as file:
                    instructions[filename] = file.read()

    except FileNotFoundError as e:
        return json.dumps({"error": str(e)})

    return json.dumps(instructions, indent=2)
