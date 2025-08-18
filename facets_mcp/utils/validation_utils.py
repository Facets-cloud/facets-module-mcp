import glob
import os

import hcl
from lark import Token, Tree


def validate_no_provider_blocks(path):
    """Validate that no .tf files contain provider blocks in any directory or subdirectory."""
    # Get .tf files from root directory and all subdirectories
    tf_files = glob.glob(os.path.join(path, "*.tf")) + glob.glob(
        os.path.join(path, "**", "*.tf"), recursive=True
    )
    # Remove duplicates (in case a file is found by both patterns)
    tf_files = list(set(tf_files))
    provider_violations = []

    for tf_file in tf_files:
        try:
            with open(tf_file) as file:
                # Parse the HCL content directly from file
                terraform_tree = hcl.parse(file)
            body_node = terraform_tree.children[0]

            # Check for provider blocks
            for child in body_node.children:
                if (
                    child.data == "block"
                    and len(child.children) > 0
                    and isinstance(child.children[0], Tree)
                    and child.children[0].data == "identifier"
                    and isinstance(child.children[0].children[0], Token)
                    and child.children[0].children[0].type == "NAME"
                    and child.children[0].children[0].value == "provider"
                ):
                    # Store relative path from the base directory for better error reporting
                    relative_path = os.path.relpath(tf_file, path)
                    provider_violations.append(relative_path)
                    break  # Found one, no need to check further in this file
        except Exception:
            continue

    if provider_violations:
        file_list = ", ".join(provider_violations)
        return False, (
            f"❌ Provider blocks are not allowed in module files. "
            f"Found provider blocks in: {file_list}. "
            f"Use exposed providers in facets.yaml instead."
        )

    return True, "✅ No provider blocks found in Terraform files."
