"""
Utilities for file operations in the facets-module-mcp project.
Contains helper functions for safely handling files within the working directory.
"""

import os
import sys
import difflib
from typing import Optional, Dict, Any

def ensure_path_in_working_directory(path: str, working_directory: str) -> str:
    """
    Ensure a file path is within the working directory.
    
    Args:
        path (str): The path to check.
        working_directory (str): The working directory.
        
    Returns:
        str: The absolute path.
        
    Raises:
        ValueError: If the path is outside of the working directory.
    """
    full_path = os.path.abspath(path)
    if not full_path.startswith(os.path.abspath(working_directory)):
        raise ValueError("Attempt to access files outside of the working directory.")
    return full_path


def list_files_in_directory(module_path: str, working_directory: str) -> list:
    """
    Lists all files in the given module path, ensuring we stay within the working directory.
    
    Args:
        module_path (str): The path to the module directory.
        working_directory (str): The working directory.

    Returns:
        list: A list of file paths (strings) found in the module directory.
    """
    file_list = []
    full_module_path = ensure_path_in_working_directory(module_path, working_directory)
    try:
        for root, dirs, files in os.walk(full_module_path):
            for file in files:
                file_list.append(os.path.join(root, file))
    except OSError as e:
        print(f"Error accessing module path {module_path}: {e}")
    return file_list

def get_file_content(file_path: str) -> str:
    """
    Reads the content of a file with robust error handling.

    Args:
        file_path (str): The absolute path to the file to read.

    Returns:
        str: The file’s content, or a descriptive error message if reading fails.
    """
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except OSError as e:
        print(f"Error reading file {file_path}: {e}")
        return "Error reading file."
    except Exception as file_error:
        error_message = f"Could not read file: {str(file_error)}"
        print(error_message)
        return error_message

def read_file_content(file_path: str, working_directory: str) -> str:
    """
    Reads the content of a file, ensuring it is within the working directory.
    
    Args:
        file_path (str): The path to the file.
        working_directory (str): The working directory.

    Returns:
        str: The content of the file.
    """
    full_file_path = ensure_path_in_working_directory(file_path, working_directory)
    return get_file_content(full_file_path)


def generate_file_previews(new_content: str, current_content: Optional[str] = None):
    """
    Generate preview or diff of file content for dry run mode.
    
    Args:
        new_content: New content for the file
        current_content: Current content of the file (for diff)
        
    Returns:
        dict: Structured data with file preview or diff information
    """
    # If we have current content, generate a diff
    if current_content:
        return {
            "type": "diff",
            "content": generate_diff(current_content, new_content)
        }
    else:
        # Show preview of new file
        content_lines = new_content.splitlines()
        preview_lines = content_lines[:min(20, len(content_lines))]
        is_truncated = len(content_lines) > 20
        
        return {
            "type": "new_file",
            "content": "\n".join(preview_lines),
            "truncated": is_truncated,
            "total_lines": len(content_lines)
        }


def generate_diff(current_content: str, new_content: str) -> str:
    """
    Generate a unified diff between current and new content.
    
    Args:
        current_content: The current file content
        new_content: The new file content to be written
        
    Returns:
        str: A formatted diff showing changes
    """
    current_lines = current_content.splitlines()
    new_lines = new_content.splitlines()
    
    diff = difflib.unified_diff(
        current_lines, 
        new_lines,
        lineterm='',
        n=3  # Context lines
    )
    
    # Format the diff for readability
    diff_text = '\n'.join(list(diff))
    
    return diff_text


def write_file_safely(file_path: str, content: str, working_directory: str) -> str:
    """
    Writes content to a file, ensuring the path is within the working directory.
    
    Args:
        file_path (str): The path to the file.
        content (str): The content to write.
        working_directory (str): The working directory.
        
    Returns:
        str: Success message or error message.
    """
    try:
        full_file_path = ensure_path_in_working_directory(file_path, working_directory)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
        
        with open(full_file_path, 'w') as f:
            f.write(content)
            
        return f"Successfully wrote file to {file_path}"
    except Exception as e:
        error_message = f"Error writing file: {str(e)}"
        print(error_message, file=sys.stderr)
        return error_message
