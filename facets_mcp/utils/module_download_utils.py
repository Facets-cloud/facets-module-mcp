import os
import tempfile
import requests
import zipfile
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.utils.file_utils import ensure_path_in_working_directory
from facets_mcp.config import working_directory


def download_and_extract_module_zip(module_id: str, extract_to: str) -> tuple[bool, str]:
    """
    Download the module zip file by module ID from the control plane and extract it to the specified directory.
    Ensures authentication and path safety as per repo standards.

    Args:
        module_id (str): The module ID to download.
        extract_to (str): The directory (relative or absolute) to extract the module contents into (must be within working_directory).

    Returns:
        tuple[bool, str]: (success, message) - success indicates if operation succeeded, message contains details.
    """
    try:
        # Ensure extract_to is within the working directory
        full_extract_path = ensure_path_in_working_directory(extract_to, working_directory)
        os.makedirs(full_extract_path, exist_ok=True)

        # Initialize client config (loads env or credentials file)
        if not ClientUtils.initialized:
            ClientUtils.initialize()
        cp_url = ClientUtils.cp_url
        username = ClientUtils.username
        token = ClientUtils.token

        # Build the download URL
        download_url = f"{cp_url}/cc-ui/v1/modules/{module_id}/download"

        # Download the zip file using HTTP Basic Auth
        with requests.get(download_url, auth=(username, token), stream=True) as response:
            if response.status_code != 200:
                return False, f"Failed to download module zip: {response.status_code} {response.reason}"
            # Save to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_zip.write(chunk)
                tmp_zip_path = tmp_zip.name

        # Extract the zip file
        try:
            with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(full_extract_path)
        except zipfile.BadZipFile:
            os.remove(tmp_zip_path)
            return False, "Downloaded file is not a valid zip archive."
        finally:
            # Clean up the temp zip file
            if os.path.exists(tmp_zip_path):
                os.remove(tmp_zip_path)

        return True, f"Module {module_id} downloaded and extracted to {full_extract_path}"

    except Exception as e:
        return False, f"Error downloading or extracting module: {str(e)}" 