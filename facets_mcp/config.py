import sys

from mcp.server.fastmcp import FastMCP

# Use default argument if sys.argv[1] is not provided (e.g., during imports, tests)
arg_value = sys.argv[1] if len(sys.argv) > 1 else "default"
mcp = FastMCP("Facets ModGenie: " + arg_value)

# Working directory to be set after initialization with fallback default
working_directory = arg_value
