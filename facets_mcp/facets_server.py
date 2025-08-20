import logging
import os
import sys

import click

# Import all modules to register their tools and prompts with MCP
import facets_mcp.prompts.fork_module_prompt  # noqa: F401
import facets_mcp.tools.deploy_module  # noqa: F401
import facets_mcp.tools.existing_modules  # noqa: F401
import facets_mcp.tools.fork_module  # noqa: F401
import facets_mcp.tools.ftf_tools  # noqa: F401
import facets_mcp.tools.import_tools  # noqa: F401
import facets_mcp.tools.instructions  # noqa: F401
import facets_mcp.tools.intent_management_tools  # noqa: F401
import facets_mcp.tools.module_files  # noqa: F401
from facets_mcp.config import mcp  # Import from config for shared resources
from facets_mcp.utils.client_utils import ClientUtils
from facets_mcp.utils.ftf_command_utils import run_ftf_command

logger = logging.getLogger(__name__)

# Function to initialize the environment and perform necessary checks


def init_environment(working_dir: str) -> None:
    """
    Initialize the environment, setting up the working directory and ensuring 'ftf' is installed.

    This function also performs login if necessary environment variables are set.

    Args:
        working_dir: The working directory path to use
    """
    # Update the global working directory
    from facets_mcp import config

    config.working_directory = working_dir

    # Perform login if environment variables are set
    profile = os.getenv("FACETS_PROFILE", "default")
    username = os.getenv("FACETS_USERNAME")
    token = os.getenv("FACETS_TOKEN")
    control_plane_url = os.getenv("CONTROL_PLANE_URL")
    if profile and username and token and control_plane_url:
        _ftf_login(profile, username, token, control_plane_url)
    else:
        print(
            "Environment variables not fully set; assuming already logged in.",
            file=sys.stderr,
        )
    # Initialize the Swagger client
    try:
        ClientUtils.initialize()
    except Exception as e:
        print(f"Error initializing Swagger client: {e!s}", file=sys.stderr)


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
        "ftf",
        "login",
        "-c",
        control_plane_url,
        "-u",
        username,
        "-t",
        token,
        "-p",
        profile,
    ]
    result = run_ftf_command(command)
    print(f"Login result: {result}", file=sys.stderr)


@click.command()
@click.argument("working_directory", type=click.Path(exists=True))
@click.option(
    "--transport",
    type=click.Choice(["stdio", "streamable-http"], case_sensitive=False),
    default="stdio",
    help="Transport protocol to use (default: stdio)",
)
@click.option(
    "--port",
    type=int,
    default=3000,
    help="Port to listen on for streamable-http transport (default: 3000)",
)
@click.option(
    "--host",
    type=str,
    default="localhost",
    help="Host to bind to for streamable-http transport (default: localhost)",
)
@click.option(
    "--stateless",
    is_flag=True,
    default=False,
    help="Run in stateless mode for streamable-http (no session persistence)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Use JSON responses instead of SSE streams for streamable-http",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Logging level (default: INFO)",
)
def main(
    working_directory: str,
    transport: str,
    port: int,
    host: str,
    stateless: bool,
    json_response: bool,
    log_level: str,
):
    """Run the Facets MCP server.

    WORKING_DIRECTORY is the path to the directory containing Facets modules.
    """

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize environment with working directory
    init_environment(working_directory)

    # Update FastMCP settings for streamable-http
    if transport == "streamable-http":
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.settings.stateless_http = stateless
        mcp.settings.json_response = json_response

        logger.info(f"Starting Facets MCP server on http://{host}:{port}/mcp")
        logger.info(f"Working directory: {working_directory}")
        logger.info(f"Mode: {'Stateless' if stateless else 'Stateful'}")
        logger.info(f"Response format: {'JSON' if json_response else 'SSE'}")
    else:
        logger.info("Starting Facets MCP server with stdio transport")
        logger.info(f"Working directory: {working_directory}")

    # Run the server with specified transport
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
