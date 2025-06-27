import sys
import os
from facets_mcp.config import mcp  # Import from config for shared resources
from facets_mcp.tools.ftf_tools import *
from facets_mcp.tools.module_files import *
from facets_mcp.tools.instructions import *
from facets_mcp.tools.existing_modules import *
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.prompts.module_prompt import *
from facets_mcp.tools.deploy_module import *
from facets_mcp.tools.fork_module import *
from facets_mcp.prompts.fork_module_prompt import *


# Function to initialize the environment and perform necessary checks

def init_environment() -> None:
    """
    Initialize the environment, setting up the working directory and ensuring 'ftf' is installed.

    This function also performs login if necessary environment variables are set.
    """
    # Ensure working directory is specified
    if len(sys.argv) < 2:
        print("Error: Working directory not specified.", file=sys.stderr)
        sys.exit(1)

    # Perform login if environment variables are set
    profile = os.getenv('FACETS_PROFILE', "default")
    username = os.getenv('FACETS_USERNAME')
    token = os.getenv('FACETS_TOKEN')
    control_plane_url = os.getenv('CONTROL_PLANE_URL')
    if profile and username and token and control_plane_url:
        _ftf_login(profile, username, token, control_plane_url)
    else:
        print("Environment variables not fully set; assuming already logged in.", file=sys.stderr)
    # Initialize the Swagger client
    try:
        ClientUtils.initialize()
    except Exception as e:
        print(f"Error initializing Swagger client: {str(e)}", file=sys.stderr)


# Private method to perform login using ftf

def _ftf_login(profile: str, username: str, token: str, control_plane_url: str) -> None:
    """
    Perform login using ftf login command.

    Uses provided environment variables for credentials.

    Args:
    - profile (str): User profile for storing credentials.
    - username (str): User's username.
    - token (str): User's access token.
    - control_plane_url (str): URL of the control plane.
    """
    command = [
        "ftf", "login",
        "-c", control_plane_url,
        "-u", username,
        "-t", token,
        "-p", profile
    ]
    result = run_ftf_command(command)
    print(f"Login result: {result}", file=sys.stderr)


def main():
    # Initialize environment
    init_environment()
    # Original main execution for MCP server
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
