import os
import glob
import hcl2
import io

def find_provider_blocks_in_directory(module_path: str) -> list:
    """
    Scans all .tf files in the given directory (recursively) for provider blocks.
    Args:
        module_path (str): The path to the module directory.
    Returns:
        list: List of file paths (relative to module_path) that contain provider blocks.
    Raises:
        Exception: If any .tf file cannot be parsed as valid HCL.
    """
    offending_files = []
    full_module_path = os.path.abspath(module_path)
    tf_files = glob.glob(os.path.join(full_module_path, "**", "*.tf"), recursive=True)
    for tf_file in tf_files:
        try:
            with open(tf_file, "r", encoding="utf-8") as fp:
                content = fp.read()
                with io.StringIO(content) as sio:
                    parsed = hcl2.load(sio)
                if 'provider' in parsed and parsed['provider']:
                    rel_path = os.path.relpath(tf_file, full_module_path)
                    offending_files.append(rel_path)
        except Exception as e:
            raise Exception(f"❌ Failed to parse {tf_file}: {e}")
    return offending_files

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python provider_block_validator.py <module_path>")
        sys.exit(1)
    module_path = sys.argv[1]
    try:
        offending = find_provider_blocks_in_directory(module_path)
        if offending:
            print(f"\u274C Provider blocks found in:\n  - " + "\n  - ".join(offending))
            sys.exit(1)
        else:
            print("No provider blocks found in any .tf file.")
            sys.exit(0)
    except Exception as e:
        print(str(e))
        sys.exit(2) 