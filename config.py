import sys

from mcp.server.fastmcp import FastMCP

# Instance of FastMCP server
mcp = FastMCP("Facets ModGenie: "+ sys.argv[1])

# Working directory to be set after initialization
working_directory = sys.argv[1]

