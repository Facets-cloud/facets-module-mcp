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
    `module_instructions` directory and loads all sample terraform module files to enhance the knowledge base.

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
                with open(file_path, "r") as file:
                    instructions[filename] = file.read()

    except FileNotFoundError as e:
        return json.dumps({"error": str(e)})

    # Add sample modules context
    instructions["sample_modules"] = load_sample_modules_context()
    return json.dumps(instructions, indent=2)


def load_sample_modules_context() -> dict:
    """
    Loads sample module files (facets.yaml, variables.tf, main.tf, outputs.tf) from the modules directory
    for reference in module generation.
    Returns:
        dict: {module_path: {file_name: file_content, ...}, ...}
    """
    modules_dir = os.path.join(os.path.dirname(__file__), "modules")
    sample_context = {}
    for root, dirs, files in os.walk(modules_dir):
        module_files = {}
        for fname in [
            "facets.yaml",
            "variables.tf",
            "main.tf",
            "outputs.tf",
            "README.md",
            "locals.tf",
        ]:
            fpath = os.path.join(root, fname)
            if os.path.isfile(fpath):
                with open(fpath, "r") as f:
                    module_files[fname] = f.read()
        if module_files:
            # Use relative path from modules_dir as key
            rel_path = os.path.relpath(root, modules_dir)
            sample_context[rel_path] = module_files
    return sample_context
