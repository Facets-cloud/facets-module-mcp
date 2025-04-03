import sys

from mcp.server.fastmcp import FastMCP

# Instance of FastMCP server
mcp = FastMCP("FacetsServer")

# Working directory to be set after initialization
working_directory = sys.argv[1]

ftf= 'ftf'
