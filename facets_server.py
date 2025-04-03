from typing import Dict, Any
import sys
import os
import subprocess
from config import mcp  # Import from config for shared resources
from tools import run_ftf_command
import config
from tools.ftf_tools import derive_module_path, run_ftf_generate_module, run_ftf_add_variable, \
    run_ftf_validate_directory, run_ftf_preview_module, run_ftf_expose_provider, run_ftf_add_input
from prompts.module_prompt import generate_new_module


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
    ftf_install_status = ensure_ftf_installed()
    print(ftf_install_status)

    # Perform login if environment variables are set
    profile = os.getenv('FACETS_PROFILE')
    username = os.getenv('FACETS_USERNAME')
    token = os.getenv('FACETS_TOKEN')
    control_plane_url = os.getenv('CONTROL_PLANE_URL')

    if profile and username and token and control_plane_url:
        _ftf_login(profile, username, token, control_plane_url)
    else:
        print("Environment variables not fully set; assuming already logged in.", file=sys.stderr)


# Function to check if 'ftf' is installed and install if not

def ensure_ftf_installed() -> str:
    """
    Check if 'ftf' is installed. If not, attempt to install it.

    Returns:
    - str: A message indicating the installation status.
    """
    env = os.environ.copy()

    try:
        # Check if 'ftf' is available
        result = subprocess.run(
            ['ftf'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
            env=env
        )
        print(result.stderr.strip())
        result = subprocess.run(
            ['which','ftf'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=False,
            env=env
        )
        config.ftf = result.stdout.strip()
        return "'ftf' is already installed.\n" + result.stdout.strip()

    except FileNotFoundError:
        print("'ftf' not found. Attempting installation from GitHub...")

        try:
            install_process = subprocess.run(
                [sys.executable, '-m', 'pip', 'install',
                 'git+https://github.com/Facets-cloud/module-development-cli.git'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell= True,
                env=env
            )
            print(install_process.stdout.strip())
            result = subprocess.run(
                ['ftf'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=True,
                env=env
            )
            print(result.stdout.strip())
            return "'ftf' was not found, but has now been installed from the GitHub repository.\n" + install_process.stdout.strip()

        except subprocess.CalledProcessError as e:
            print(e.stderr.strip(), file=sys.stderr)
            exit(f"Failed to install 'ftf'. Error:\n{e.stderr.strip()}")

    except subprocess.CalledProcessError as e:
        print(e.stderr.strip(), file=sys.stderr)
        return f"Error checking 'ftf' version:\n{e.stderr.strip()}"


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


# Main execution
if __name__ == "__main__":
    # Initialize environment
    init_environment()
    # Original main execution for MCP server
    mcp.run(transport='stdio')
