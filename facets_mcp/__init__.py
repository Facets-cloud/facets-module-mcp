"""
Facets MCP - Model Context Protocol Server for Terraform module development
"""

try:
    from facets_mcp._version import __version__
except ImportError:
    __version__ = "0.0.0"  # Fallback version

# Import the main function from facets_server for entry point access
from facets_mcp.facets_server import main
