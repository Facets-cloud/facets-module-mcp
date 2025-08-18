"""
Utilities for file operations in the facets-module-mcp project.
Contains helper functions for safely handling files within the working directory.
"""

import difflib
import os
import sys


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
        str: The file's content.

    Raises:
        UnicodeDecodeError: If file cannot be decoded with supported encodings.
        OSError: If file cannot be accessed or read.
        Exception: For other file reading errors.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError as e:
        # Try with different encodings if UTF-8 fails
        try:
            with open(file_path, encoding="utf-8-sig") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding="cp1252") as f:
                    return f.read()
            except UnicodeDecodeError:
                raise UnicodeDecodeError(
                    e.encoding,
                    e.object,
                    e.start,
                    e.end,
                    f"Could not read file {file_path} with any supported encoding",
                )
    except OSError as e:
        raise OSError(f"Error reading file {file_path}: {e}")
    except Exception as e:
        raise Exception(f"Could not read file {file_path}: {e!s}")


def read_file_content(file_path: str, working_directory: str) -> str:
    """
    Reads the content of a file, ensuring it is within the working directory.

    Args:
        file_path (str): The path to the file.
        working_directory (str): The working directory.

    Returns:
        str: The content of the file.

    Raises:
        ValueError: If the path is outside the working directory.
        UnicodeDecodeError: If file cannot be decoded.
        OSError: If file cannot be accessed or read.
        Exception: For other file reading errors.
    """
    full_file_path = ensure_path_in_working_directory(file_path, working_directory)
    return get_file_content(full_file_path)


def generate_file_previews(new_content: str, current_content: str | None = None):
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
        return {"type": "diff", "content": generate_diff(current_content, new_content)}
    else:
        # Show preview of new file
        content_lines = new_content.splitlines()
        preview_lines = content_lines[: min(20, len(content_lines))]
        is_truncated = len(content_lines) > 20

        return {
            "type": "new_file",
            "content": "\n".join(preview_lines),
            "truncated": is_truncated,
            "total_lines": len(content_lines),
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
        lineterm="",
        n=3,  # Context lines
    )

    # Format the diff for readability
    diff_text = "\n".join(list(diff))

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

        with open(full_file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully wrote file to {file_path}"
    except Exception as e:
        error_message = f"Error writing file: {e!s}"
        print(error_message, file=sys.stderr)
        return error_message


def perform_text_replacement(
    content: str, old_string: str, new_string: str, expected_replacements: int
) -> tuple[bool, str, str]:
    """
    Perform text replacement with validation of expected replacement count.

    Args:
        content: Original file content
        old_string: Text to find and replace
        new_string: Replacement text
        expected_replacements: Expected number of replacements

    Returns:
        Tuple of (success, result_content_or_error_message, info_message)
    """
    if not old_string:
        return False, "Empty search strings are not allowed", ""

    # Count occurrences
    count = content.count(old_string)

    if count == 0:
        # Try to find similar text for helpful error message
        lines = content.split("\n")
        old_lines = old_string.split("\n")

        # Look for lines that contain parts of the search text
        similar_lines = []
        for line in lines:
            for old_line in old_lines:
                if old_line.strip() and old_line.strip() in line:
                    similar_lines.append(f"  Found similar: {line.strip()}")
                    break

        error_msg = "Search text not found in file"
        if similar_lines:
            error_msg += ". Found similar lines:\n" + "\n".join(similar_lines[:3])

        return False, error_msg, ""

    if count != expected_replacements:
        return (
            False,
            (
                f"Expected {expected_replacements} occurrences but found {count}. "
                f"If you want to replace all {count} occurrences, set expected_replacements to {count}. "
                f"To replace a specific occurrence, make your search string more unique by adding more context."
            ),
            "",
        )

    # Perform replacement
    new_content = content.replace(old_string, new_string)

    success_msg = f"Successfully replaced {count} occurrence{'s' if count > 1 else ''}"
    return True, new_content, success_msg
