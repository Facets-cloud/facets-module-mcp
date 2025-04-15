import sys
import os
from config import mcp  # Import from config for shared resources
import config
from tools.ftf_tools import *
from tools.module_files import *
from tools.instructions import *
from tools.existing_modules import *
from prompts.module_prompt import *

# Say Hi tool
@mcp.tool()
def say_hi(name: str) -> str:
    """
    Tool to greet users with a welcome message.

    Args:
    - name (str): The name of the person to greet.

    Returns:
    - str: A welcome message for the user.
    """
    return f"Hi, {name}! Welcome to Facets."


# Function to initialize the environment and perform necessary checks

def init_environment() -> None:
    """
    Initialize the environment, setting up the working directory and ensuring 'ftf' is installed.

    This function also performs login if necessary environment variables are set.
    """
    # Ensure working directory is specified
    if len(sys.argv) > 2:
        print("Error: Working directory not specified.", file=sys.stderr)
        sys.exit(1)
    # Ensure 'ftf' is installed
    # ftf_install_status = ensure_ftf_installed()
    # print(ftf_install_status)

    # Perform login if environment variables are set
    profile = os.getenv('FACETS_PROFILE')
    username = os.getenv('FACETS_USERNAME')
    token = os.getenv('FACETS_TOKEN')
    control_plane_url = os.getenv('CONTROL_PLANE_URL')
    if profile and username and token and control_plane_url:
        _ftf_login(profile, username, token, control_plane_url)
    else:
        print("Environment variables not fully set; assuming already logged in.", file=sys.stderr)


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