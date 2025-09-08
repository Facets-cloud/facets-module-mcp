### 🔹 `inputs`

Defines the values this module requires as inputs from other modules.

#### ✅ Syntax:

```yaml
inputs:
  <input_name>:
    type: @outputs/<type>
    optional: true|false
    displayName: Display name for UI
    description: Description of the input
```

#### 🔑 Common Fields:

- **`type`**: Required. Specifies the output type from another module (e.g. `@outputs/kubernetes-cluster`).
- **`optional`**: Boolean. Whether this input is required (default: `false`).
- **`displayName`**: String. Human-readable name shown in the UI.
- **`description`**: String. Explanation of what this input is used for.

#### 💡 Example:

```yaml
inputs:
  cluster_config:
    type: "@outputs/kubernetes-cluster"
    optional: false
    displayName: "Kubernetes Cluster"
    description: "The target Kubernetes cluster for deployment"
  
  storage_account:
    type: "@outputs/azure-storage-account"
    optional: true
    displayName: "Storage Account (Optional)"
    description: "Azure storage account for persistent data"
```

---

### 🔹 `outputs`

Defines the values this module exposes for consumption by other modules.

#### ✅ Syntax:

```yaml
outputs:
  <output_name>:
    type: @outputs/<type>
    title: Will appear on the UI
```

#### 🔑 Common Fields:

- **`type`**: Required. Specifies the classification of the output (e.g. `@outputs/databricks-account`).
    - **Use hyphens** (`-`) in the type name instead of underscores (`_`) if needed.
- **`output_attributes` and `output_interfaces` local variables**: These generate Terraform `output` blocks in **runtime**:
    - `output_attributes` → corresponds to `output "attributes" { ... }`
    - `output_interfaces` → corresponds to `output "interfaces" { ... }`

<important> Never generate output blocks for facets modules</important>

#### 💡 Special Notes:

- **`default`** is a **reserved keyword** that refers to the full output of the module. It is treated as the default
  export and typically maps to the entire structured response from Terraform.
- A module can expose **multiple outputs**, including specific nested fields within the primary structure.
    - Use dot notation to reference these nested fields explicitly:

      ```yaml
      outputs:
        default:
          type: "@outputs/gcp-project"
          title: "The GCP Project"
        attributes.project_id:
          type: "@outputs/project-id"
          title: "The GCP Project id"
      ```
<important> no need to add properties in the outputs block like inputs.</important>
      This allows consuming modules to wire only the specific part of the output they require, while still having the
      option to consume the entire object via `default`.

---

### 🔐 Marking Output Fields as Sensitive

When calling `write_outputs`, every field requires both `value` and `sensitive` keys. The value can be any type (string, bool, number, list, dict).

```python
write_outputs(
    module_path="/path/to/module",
    output_attributes={
        # String values
        "instance_id": {"value": "aws_instance.main.id", "sensitive": False},
        "api_key": {"value": "var.api_key", "sensitive": True},
        
        # Complex types
        "config": {"value": {"region": "us-east-1", "zones": ["a", "b"]}, "sensitive": False},
        # Do not commit literal secrets to VCS; use variables or data sources
        "credentials": {"value": ["data.aws_secretsmanager_secret.api_key.secret_string", "data.aws_secretsmanager_secret.db_password.secret_string"], "sensitive": True},
        "enabled": {"value": True, "sensitive": False}
    }
)
```

Generates:
```hcl
locals {
  output_attributes = {
    instance_id = aws_instance.main.id
    api_key = sensitive(var.api_key)
    config = {
      region = "us-east-1"
      zones = ["a", "b"]
    }
    credentials = sensitive(["token1", "token2"])
    enabled = true
    secrets = ["api_key", "credentials"]  # Auto-generated for Facets UI
  }
}
```

<important>Mark any field containing passwords, tokens, keys, or credentials as sensitive.</important>

---

