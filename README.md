# Facets Module MCP

MCP Server for Facets Module, designed to generate new capabilities by writing new Terraform modules for the platform. It offers robust file operations to assist with Terraform code writing, ensuring efficient module management and execution within a cloud environment.

### Features

- **Secure File Operations**: Ensures all file reads and writes are conducted within the working directory, assisting in Terraform code management.
- **MCP Tool Integration**: Leverage MCP tools for modular and extensible utility functions, enhancing Terraform module generation.
- **Facets Module Generation**: Utilize prompts to guide the creation of Terraform modules with FTF CLI support.
- **Cloud-ready Architecture**: Designed to work seamlessly within cloud environments, supporting dynamic infrastructure needs.

## Tools

### Module Tools
1. **`list_files`**
   - Lists all files in a given module path securely within the working directory.
   - Inputs:
     - `module_path` (string): The path to the module directory
   - Returns: A list of file paths

2. **`read_file`**
   - Reads the content of a specified file, ensuring security constraints.
   - Inputs:
     - `file_path` (string): The path to the file
   - Returns: The file content as a string

3. **`write_file`**
   - Writes content to a file, with safeguards to maintain the working directory integrity.
   - Inputs:
     - `file_path` (string): The path to the file
     - `content` (string): Content to be written
   - Returns: Confirmation of success or an error message

### FTF Tools
4. **`run_ftf_generate_module`**
   - Generates a new module using FTF CLI.
   - Handles module scaffolding based on user input.

5. **`run_ftf_add_variable`**
   - Adds a new variable to a Terraform module.

6. **`run_ftf_validate_directory`**
   - Validates a module directory using the FTF CLI.

7. **`run_ftf_preview_module`**
   - Previews a module, optionally publishing it if required.

8. **`run_ftf_expose_provider`**
   - Exposes a provider in a module output using FTF CLI.

9. **`run_ftf_add_input`**
   - Adds an input for a predefined output.

## Setup

### Prerequisites

Ensure you have Python and necessary dependencies installed. Configure your working directory in `config.py`.

### Usage

Integrate with your cloud environment and leverage the tools and prompts provided:

- Use `list_files`, `read_file`, and `write_file` for secure and efficient Terraform code management.
- Utilize `run_ftf_generate_module` to scaffold new Terraform modules.
- Employ prompts like `generate_new_module` to facilitate module requirements gathering.

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software as per the terms of the MIT License.
