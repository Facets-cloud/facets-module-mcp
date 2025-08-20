# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands
- Install: `pip install -e .` or `uv pip install -e .`
- Run server (stdio): `python facets_server.py /path/to/modules`
- Run server (HTTP): `python facets_server.py /path/to/modules --transport streamable-http`
- Get help: `python facets_server.py --help`
- Validate modules: Use the `validate_module` tool within the MCP session

## Code Style Guidelines
- **Imports**: Group by standard library, third-party, then local imports
- **Types**: Always use type hints in function signatures and return types
- **Naming**: Use snake_case for functions/variables, descriptive names
- **Functions**: Document with Google-style docstrings including params and returns
- **Error Handling**: Validate paths before operations, use try/except for IO operations
- **Tools**: Define tools using the `@mcp.tool()` decorator pattern
- **Module Structure**: Keep related functionality in dedicated directories
- **Security**: Implement checks to prevent access outside working directory

## Development Workflow
- Python 3.10+ required
- Maintain modular design with clear separation of concerns
- Follow existing patterns for new tool implementations
- Document new features in README.md