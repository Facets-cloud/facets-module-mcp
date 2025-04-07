## 🧠 AI Initialization – Read and Understand the Facets Module MCP Codebase

Welcome, agent. Before you begin coding, your first responsibility is to **carefully read and understand** the structure, logic, and intentions behind the **Facets Module MCP** system.

You will later be expected to **write new code or modify existing logic based on user instructions**, so your comprehension must be deep and context-aware.

---

### 📚 What to Study:

1. **📁 Codebase Structure and Key Files**:
   - **`facets_server.py`**: Entry point of the MCP server. Understand how it initializes the environment and orchestrates operations.
   - **`tools/` directory**:
     - `ftf_tools.py`: Core functions for creating and managing Terraform modules via the FTF CLI.
     - `module_files.py`: Utilities for secure file I/O, scoped to safe working directories.
   - **`prompts/` directory**:
     - `generate_module.md`: Blueprint for guiding conversational module creation.
   - **`ai/` directory**:
     - Context files for bootstrapping intelligent module workflows and initialization logic.

2. **🌐 External Protocol (must-read)**:
   - [Model Context Protocol – Full Spec](https://modelcontextprotocol.io/llms-full.txt): This defines how you, as an LLM, should behave in tooling environments. Read this carefully to align your reasoning and actions with broader system expectations.

---

### ✅ Your Objective:

> **Absorb this context deeply. You will not act immediately.**  
> Once the user gives you a command, you will be expected to apply your understanding of this system to:
> - Generate or modify Python code.
> - Extend prompts or scaffolding logic.
> - Add tools or workflows that align with secure, modular infrastructure-as-code development.

Until then: **read, reason, and prepare.**
