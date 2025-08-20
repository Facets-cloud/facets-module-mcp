from mcp.server.fastmcp import FastMCP

# Initialize FastMCP with a static name
mcp = FastMCP("Facets ModGenie")

# Working directory will be set by facets_server.py during initialization
# Default to current directory for imports/tests
working_directory = "."
