# Facets Module MCP Server

This MCP (Model Context Protocol) Server for the Facets Module assists in creating and managing Terraform modules for infrastructure as code. It integrates with Facets.cloud's FTF CLI, providing secure and robust tools for module generation, validation, and management to support cloud-native infrastructure workflows.

## Key Features

* **Secure File Operations**  
  Limits all file operations to within the working directory to ensure safety and integrity.

* **Modular MCP Tools**  
  Offers comprehensive tools for file listing, reading, writing, module generation, validation, and previews. All destructive or irreversible commands require explicit user confirmation and support dry-run previews.

* **Facets Module Generation**  
  Interactive prompt-driven workflows facilitate generation of Terraform modules with metadata, variable, and input management using FTF CLI.

* **Module Forking**  
  Fork existing modules from the Facets control plane to create customized variants. Supports discovering available modules, updating metadata, and customizing functionality while preserving the original module structure.

* **Supplementary Instructions Support**  
  Automatically reads additional project-specific instructions from the `mcp_instructions` directory at the root level, allowing teams to define custom requirements, constraints, and guidelines that supplement the default module generation behavior.

* **Module Preview and Testing**  
  Comprehensive deployment workflow supporting module preview, testing in dedicated test projects, and real-time deployment monitoring with status checks and logs. You will need a test project with a running environment and an enabled resource added for the module being tested (to be done manually from the Facets UI).

* **Cloud Environment Integration**  
  Supports multiple cloud providers and automatically extracts git repository metadata to enrich module previews.

## Available MCP Tools

| Tool Name                                | Description                                                                                                                              |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `FIRST_STEP_get_instructions`            | Loads all module writing instructions from the `module_instructions` directory and supplementary instructions from `mcp_instructions`. Always call this first. |
| `list_files`                             | Lists all files in the specified module directory securely within the working directory.                                                 |
| `read_file`                              | Reads the content of a file within the working directory.                                                                                |
| `edit_file_block`                        | Apply surgical edits to specific blocks of text in files. Makes precise changes without rewriting entire files.                        |
| `write_config_files`                     | Writes and validates `facets.yaml` configuration files with dry-run and diff previews.                                                   |
| `write_resource_file`                    | Writes Terraform resource files (`main.tf`, `variables.tf`, etc.) safely. Excludes `outputs.tf` and `facets.yaml`.                     |
| `write_outputs`                          | Writes the `outputs.tf` file for a module with output attributes and interfaces in a local block.                                       |
| `write_readme_file`                      | Writes a `README.md` file for the module directory with AI-generated content.                                                           |
| `generate_module_with_user_confirmation` | Generates a new Terraform module scaffold with dry-run preview and user confirmation.                                                    |
| `validate_module`                        | Validates a Terraform module directory using FTF CLI standards and checks output types.                                                 |
| `push_preview_module_to_facets_cp`       | Previews a module by pushing a test version to the control plane with git context extracted automatically.                             |
| `register_output_type`                   | Registers a new output type in the Facets control plane with interfaces and attributes and providers.                                                  |
| `get_output_type_details`                | Retrieves details for a specific output type from the Facets control plane.                                                             |
| `find_output_types_with_provider`        | Finds all output types that include a specific provider source for module configurations.                                               |
| `get_local_modules`                      | Scans and lists all local Terraform modules by searching for `facets.yaml` recursively, including loading outputs.tf content if present. |
| `search_modules_after_confirmation`      | Searches modules by filtering for a string within facets.yaml files, supports pagination, and returns matched modules with details.      |
| `list_test_projects`                     | Retrieves and returns the names of all available test projects for deployment.                                                           |
| `test_already_previewed_module`          | Tests a module that has been previewed by deploying it to a specified test project.                                                      |
| `check_deployment_status`                | Checks the status of a deployment with optional waiting for completion.                                                                  |
| `get_deployment_logs`                    | Retrieves logs for a specific deployment.                                                                                               |
| `list_modules_for_fork`                  | Lists all available modules from the control plane that can be forked, displaying them in a compact format for easy selection.          |
| `fork_existing_module`                   | Forks an existing module by downloading it and updating its metadata (flavor and version). Supports dry-run preview and user confirmation. |

## Prerequisites

The MCP Server requires [uv](https://github.com/astral-sh/uv) for MCP orchestration.

The package is available on PyPI: [facets-module-mcp](https://pypi.org/project/facets-module-mcp/)

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

For a locally cloned repository, use:

```json
{
  "mcpServers": {
    "facets-module": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/your/cloned/facets-module-mcp/facets_mcp",
        "run",
        "facets_server.py",
        "/path/to/working-directory"
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

- Use core tools (`list_files`, `read_file`, `edit_file_block`, `write_config_files`, etc.) for Terraform code management.

- Use FTF CLI integration tools for module scaffolding, validation, and preview workflows.

- Complete deployment flow: preview modules with `push_preview_module_to_facets_cp`, test on dedicated test projects with `test_already_previewed_module`, and monitor progress using `check_deployment_status` and `get_deployment_logs`.

- Employ MCP prompts like `generate_new_module` to guide module generation interactively, or use `fork_existing_module` to customize existing modules.

- All destructive actions require explicit user confirmation and dry-run previews.

---

## Module Forking Use Cases

The MCP server now supports forking existing modules from the Facets control plane. Use the **"Fork Existing Module"** prompt to access a guided workflow for:

- **Security enhancements**: Fork a basic module to add additional security controls or compliance requirements  
- **Cloud provider adaptations**: Adapt modules for different cloud providers while maintaining core functionality
- **Performance optimizations**: Create high-performance variants of existing modules with enhanced configurations
- **Feature customizations**: Add organization-specific features or integrations to existing modules
- **Version updates**: Modernize older modules with updated provider versions or new Terraform features

The fork workflow maintains the original module structure while allowing you to customize metadata, variables, resources, and outputs to meet your specific requirements.

---

## Example Usage

For a comprehensive example of how to use this MCP server with Claude, check out this chat session:
[Creating a Terraform Module with Facets MCP](https://claude.ai/share/2ebe981f-48f4-4648-881e-4929ebbf0f59)

This example demonstrates the complete workflow from module generation to testing and deployment.

---
## 📘 Additional Guide

For a detailed, real-world walkthrough of building a secure S3 bucket module with AI on the Facets platform, check out  
**[GUIDE.md – Building Facets Modules with AI: A Practical Guide](./GUIDE.md)**

This guide demonstrates the full conversation flow—requirements, design refinement, implementation review, validation, testing, and iteration—using a developer-focused example tailored for a banking use case.

---

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute it under its terms.