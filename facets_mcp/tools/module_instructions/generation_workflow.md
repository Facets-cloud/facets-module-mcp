## ✅ Facets Module Generation Workflow

## 🎯 When Creating New Modules From Scratch

If you are helping a user create a **new Facets module from scratch**, follow this conversational, iterative, and review-based process. Every tool invocation should be **previewed** and require **confirmation**.

---

## 🔁 Step-by-Step Flow

### 🔹 Step 1: Understand the Capability

Ask the user:

> "What infrastructure capability are you trying to model as a reusable building block?"

Examples:
- GCP Databricks cluster
- AWS RDS database with backup
- Azure Key Vault with secrets rotation

---

### 🔹 Step 2: Gather Module Metadata

From the user's answer, extract or clarify the following fields:

| Field           | Description                                                 | Ask if missing                                                         |
|-----------------|-------------------------------------------------------------|------------------------------------------------------------------------|
| **Intent**      | The abstract capability (e.g., `gcp-databricks-cluster`)    | "What should be the intent name for this module?"                      |
| **Flavor**      | A specific variant (e.g., `secure-access`, `ha`)            | "Is there a flavor or variant you want to capture in the module name?" |
| **Cloud**       | Target cloud provider(s). Supports single or multiple clouds (comma-separated).<br>Examples: `aws`, `gcp`, `aws,gcp,azure`, `aws, gcp, azure` | "Which cloud provider(s) is this for?"                                    |
| **Title**       | Display name for UI (e.g., "Secure GCP Databricks Cluster") | "What's a user-friendly title for this module?"                        |
| **Description** | One-liner describing what this module does                  | "Describe this module in a sentence or two"                            |

> 🎯 Once collected, repeat the metadata back for review before proceeding to the next step.

---

### 🔹 Step 3: Define the Abstraction Style

Ask the user:

> "Would you like this module to expose a **developer-centric** abstraction (simple, intuitive inputs) or an **ops-centric** one (fine-grained platform controls)?"

#### 🧑‍💻 Developer-Centric

If the user chooses **developer-centric**, follow this:

> ✅ These inputs don't need to map directly to Terraform settings. Think about what a **developer** would want to control.
>
> Use intent-based flags or simple toggles instead of exposing every low-level config.

Examples of good inputs:
- `enable_autoscaling` → maps to a node pool config
- `performance_tier` → maps to disk type + IOPS
- `enable_gcs_access` → maps to IAM policies
- `replication_enabled` → maps to multi-region settings

#### 🧑‍🔧 Ops-Centric

If the user chooses **ops-centric**, suggest **detailed, technical fields** that mirror Terraform inputs more closely.

Examples:
- `boot_disk_type`
- `machine_type`
- `backup_config`
- `egress_cidr_ranges`

---

### 🔹 Step 4: Define Module Interface

Based on the capability and chosen abstraction style (developer-centric or ops-centric), **intelligently derive** a list of suggested inputs.

Present them in a clean, editable list like:

```txt
Here are the suggested inputs for this module:

1. `enable_autoscaling` (bool)  
   → Controls whether the cluster automatically scales based on usage.

2. `performance_tier` (string)  
   → Sets performance level: "standard", "high", or "premium".

3. `enable_gcs_access` (bool)  
   → Grants the job permission to read from GCS buckets.

4. `replication_enabled` (bool)  
   → Enables multi-zone replication for high availability.

Please review this list. You can:
- ✅ Approve all
- 📝 Edit names, types, or descriptions
- ❌ Remove any
- ➕ Suggest more
```

🛑 Do **not** call any file creation tools yet.

---

### 🔹 Step 5: Draft Complete facets.yaml Configuration

**CRITICAL STEP**: Before creating any files, draft the complete facets.yaml as an artifact for user review.

#### 📋 Complete facets.yaml Template

Use this template structure with all possible sections:

```yaml
# REQUIRED: Basic module metadata
intent: {{ intent }}
flavor: {{ flavor }}
version: "1.0"
clouds: [ {{ cloud }} ]
description: {{ description }}

# REQUIRED: Module interface definition
spec:
  title: {{ title }}
  description: {{ description }}
  type: object
  properties:
    # User-defined properties go here
  required:
    # List required fields

# OPTIONAL: Dependencies on other modules
inputs:
  input_name:
    type: "@outputs/some_type"
    optional: false
    displayName: "Display Name"
    description: "Description"
    providers:  # Only if consuming providers
      - provider_name

# REQUIRED: What this module exposes
outputs:
  default:
    type: "@outputs/{{ outputname }}"
    title: "Module Output Title"
  # Additional specific outputs if needed

# OPTIONAL: External artifacts (Docker images, etc.)
artifact_inputs:
  primary:
    attribute_path: "spec.image.name"
    artifact_type: "docker_image"

# REQUIRED only if writing a new module: Terraform files validation
iac:
  validated_files:
    - main.tf
    - variables.tf

# REQUIRED: Sample configuration
sample:
  kind: {{ intent }}
  flavor: {{ flavor }}
  version: "1.0"
  disabled: true
  spec:
    # Only include defaults defined at field level
    # Never fabricate sample values
```

Create an artifact containing the complete facets.yaml structure including:

1. **Metadata section**:
   - intent, flavor, cloud
   - title, description
   - version information

2. **Spec section**:
   - All user-defined properties with proper JSON Schema
   - Appropriate types, titles, descriptions, defaults
   - Required fields list
   - Validation rules where needed

3. **Inputs section** (if the module consumes other modules):
   - Define any `@outputs/<type>` dependencies
   - Include provider requirements if needed

4. **Outputs section** (if the module exposes functionality):
   - Define what this module exposes for other modules
   - Include provider configurations if module provides them

5. **IAC block**:
   - `validated_files` array listing all `.tf` files that will be created

6. **Sample section**:
   - Only include default values where explicitly specified at field level
   - Never fabricate sample values

Present the complete artifact to the user with:

> 🎯 **Review the complete facets.yaml configuration below. This defines the entire module interface.**
>
> Please review carefully:
> - Module metadata and description
> - Input parameters and their types
> - Any dependencies on other modules (inputs section)  
> - What this module exposes (outputs section)
> - Terraform files that will be created
>
> Only after you approve this configuration will I proceed to create the actual module files.

**🛑 WAIT FOR EXPLICIT USER APPROVAL** before proceeding to Step 6.

---

### 🔹 Step 6: Generate Module Scaffolding

**ONLY AFTER** the user approves the facets.yaml configuration:

Call `generate_module_with_user_confirmation` with the approved metadata:

```
generate_module_with_user_confirmation(
    intent="...", 
    flavor="...", 
    cloud="...", 
    title="...", 
    description="..."
)
```

Wait for explicit confirmation before executing.

---

### 🔹 Step 7: Create Configuration Files

After successful scaffolding, create all the configuration files at once using:

```
write_config_files(facets_yaml_content="...")
```

This will create:
- `facets.yaml` with the approved configuration
- `variables.tf` with proper variable definitions
- Other necessary configuration files

Wait for explicit confirmation before executing.

---

### 🔹 Step 8: Implement Terraform Logic

Once configuration files are created:

1. Use `list_files` and `read_file` to inspect the module structure
2. Implement Terraform logic in `main.tf` based ONLY on:
   - `var.instance_name` – for naming resources
   - `var.instance.spec.<field>` – for user-defined inputs
   - `var.environment.unique_name` – for environment-based uniqueness
   - `var.environment.cloud_tags` – for applying platform-defined tags
   - `var.inputs` – for consuming typed outputs from other modules

✅ **VERY IMPORTANT**: Before writing any Terraform code, **show the complete tf code to the user** and confirm it aligns with what they expect.

Use `write_resource_file` to create the `main.tf` file after user approval.

---

### 🔹 Step 9: Generate Documentation

Create the module README using:

```
write_readme_file()
```

This will analyze the module and generate appropriate documentation.

---

### 🔹 Step 10: Validate Module

After all files are created, validate the complete module using:

```
validate_module()
```

This will:
- Check facets.yaml syntax and structure
- Validate Terraform variable definitions match the spec
- Ensure all required fields are properly configured
- Verify IAC block references match created files
- Confirm module follows Facets conventions

Wait for explicit confirmation before executing the validation.

---

## 🛑 Rules & Guardrails

- Follow all Terraform conventions as defined in `tf.md`
- **IMPORTANT**: Show user **all tool calls** that create or modify files before executing them
- **CRITICAL**: The facets.yaml artifact must be approved before any file creation begins

---

## ✅ Success Criteria

- A complete facets.yaml configuration reviewed and approved by the user
- A scaffolded module with proper metadata
- Configuration files that match the approved interface design
- Terraform logic implemented based on validated inputs and following Facets conventions
- Complete documentation generated
- Every file creation step explicitly approved by the user before execution
