# Facets Module MCP Instructions Directory Lookup Prompt

## Core Instruction
Before proceeding with any Facets module-related tasks, always check for additional instructions in the `facets-module-mcp_instructions` directory within the current working directory.

## Implementation Steps

1. **Root Directory Check**: First, verify if the `facets-module-mcp_instructions` directory exists at the root level of the working directory
2. **Markdown File Discovery**: If the directory exists, scan specifically for all `.md` (Markdown) files only
3. **Content Loading**: Read and parse all `.md` instruction files found in the directory
4. **Instruction Integration**: Incorporate any additional guidelines, requirements, or constraints found in these files into your workflow
5. **Priority Handling**: If there are conflicts between default instructions and files in `facets-module-mcp_instructions`, prioritize the default instructions as the primary guidance, while using `facets-module-mcp_instructions` content as supplementary or additional context

## File Types to Look For
- `*.md` - Markdown instruction files only
- Examples: `README.md`, `constraints.md`, `requirements.md`, `workflow.md`, `guidelines.md`, etc.

## Error Handling
- If `facets-module-mcp_instructions` directory doesn't exist at the root level, continue with default instructions
- If directory exists but contains no `.md` files, log this and continue with defaults
- If `.md` files exist but are unreadable, log the error and continue with defaults
- If files contain conflicting instructions, document the conflicts and ask for clarification

## Integration with Existing Workflow
This instruction lookup should be performed:
- At the beginning of any new module creation task
- Before making significant changes to existing modules

The goal is to ensure that any project-specific, team-specific, or environment-specific instructions are automatically discovered and incorporated into the module development workflow.