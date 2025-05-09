# Facets Module MCP Server

This MCP (Model Context Protocol) Server for the Facets Module assists in creating and managing Terraform modules for infrastructure as code. It integrates with Facets.cloud's FTF CLI, providing secure and robust tools for module generation, validation, and management to support cloud-native infrastructure workflows.

## Key Features

* **Secure File Operations**  
  Limits all file operations to within the working directory to ensure safety and integrity.

* **Modular MCP Tools**  
  Offers comprehensive tools for file listing, reading, writing, module generation, validation, and previews. All destructive or irreversible commands require explicit user confirmation and support dry-run previews.

* **Facets Module Generation**  
  Interactive prompt-driven workflows facilitate generation of Terraform modules with metadata, variable, and input management using FTF CLI.

* **Cloud Environment Integration**  
  Supports multiple cloud providers and automatically extracts git repository metadata to enrich module previews.

## Available MCP Tools

| Tool Name                                | Description                                                                                                                              |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `list_files`                             | Lists all files in the specified module directory securely within the working directory.                                                 |
| `read_file`                              | Reads the content of a file within the working directory.                                                                                |
| `write_config_files`                     | Writes and validates `facets.yaml` configuration files with dry-run and diff previews.                                                   |
| `write_resource_file`                    | Writes Terraform resource files (`main.tf`, `outputs.tf`, etc.) safely.                                                                  |
| `generate_module_with_user_confirmation` | Generates a new Terraform module scaffold with dry-run preview and user confirmation.                                                    |
| `run_ftf_validate_directory`             | Validates a Terraform module directory using FTF CLI standards.                                                                          |
| `run_ftf_preview_module`                 | Previews a module with git context extracted automatically.                                                                              |
| `get_local_modules`                      | Scans and lists all local Terraform modules by searching for `facets.yaml` recursively, including loading outputs.tf content if present. |
| `search_modules_after_confirmation`      | Searches modules by filtering for a string within facets.yaml files, supports pagination, and returns matched modules with details.      |

## Prerequisites

The MCP Server requires [uv](https://github.com/astral-sh/uv) for MCP orchestration.

#### Install `uv` with Homebrew:
```bash
brew install uv
```

For other methods, see the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### Integration with Claude

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "facets-module": {
      "command": "uvx",
      "args": [
        "facets-module-mcp@<VERSION>",
        "/Path/to/working-directory"  # This should be the directory where your Terraform modules are checked out or a subdirectory containing the modules you want to work with
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "FACETS_PROFILE": "default",
        "FACETS_USERNAME": "<YOUR_USERNAME>",
        "FACETS_TOKEN": "<YOUR_TOKEN>",
        "CONTROL_PLANE_URL": "<YOUR_CONTROL_PLANE_URL>"
      }
    }
  }
}
```

⚠ Replace `<YOUR_USERNAME>`, `<YOUR_TOKEN>`, and `<YOUR_CONTROL_PLANE_URL>` with your actual authentication data.

The `uv` runner automatically manages environment and dependency setup using the `pyproject.toml` file in the MCP directory.

If you have already logged into FTF, specifying `FACETS_PROFILE` is sufficient.

---

For token generation and authentication setup, please refer to the official Facets documentation:  
[https://readme.facets.cloud/reference/authentication-setup](https://readme.facets.cloud/reference/authentication-setup)
 

Note: Similar setup is available in Cursor read [here](https://docs.cursor.com/context/model-context-protocol)
---

## Usage Highlights

- Use core tools (`list_files`, `read_file`, `write_config_files`, etc.) for Terraform code management.

- Use FTF CLI integration tools for module scaffolding, validation, and preview workflows.

- Employ MCP prompts like `generate_new_module` to guide module generation interactively.

- All destructive actions require explicit user confirmation and dry-run previews.

---

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute it under its terms.
