# This file contains utility functions for handling module files

import os
from config import mcp, working_directory

@mcp.tool()
def list_files(module_path: str) -> list:
    """
    Lists all files in the given module path, ensuring we stay within the working directory.

    Args:
        module_path (str): The path to the module directory.

    Returns:
        list: A list of file paths (strings) found in the module directory.
    """
    file_list = []
    full_module_path = os.path.abspath(module_path)
    if not full_module_path.startswith(os.path.abspath(working_directory)):
        raise ValueError("Attempt to access files outside of the working directory.")
    try:
        for root, dirs, files in os.walk(full_module_path):
            for file in files:
                file_list.append(os.path.join(root, file))
    except OSError as e:
        print(f"Error accessing module path {module_path}: {e}")
    return file_list

@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Reads the content of a file, ensuring it is within the working directory.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    full_file_path = os.path.abspath(file_path)
    if not full_file_path.startswith(os.path.abspath(working_directory)):
        raise ValueError("Attempt to access files outside of the working directory.")
    try:
        with open(full_file_path, 'r') as f:
            return f.read()
    except OSError as e:
        print(f"Error reading file {file_path}: {e}")
        return "Error reading file."

@mcp.tool()
def write_file(file_path: str, content: str) -> str:
    """
    Writes content to a file, ensuring it is within the working directory.

    Args:
        file_path (str): The path to the file.
        content (str): The content to be written to the file.

    Returns:
        str: Success message or error message if writing fails.
    """
    full_file_path = os.path.abspath(file_path)
    if not full_file_path.startswith(os.path.abspath(working_directory)):
        raise ValueError("Attempt to write files outside of the working directory.")
    try:
        with open(full_file_path, 'w') as f:
            f.write(content)
        return "File written successfully."
    except OSError as e:
        error_message = f"Error writing to file {file_path}: {e}"
        print(error_message)
        return error_message
