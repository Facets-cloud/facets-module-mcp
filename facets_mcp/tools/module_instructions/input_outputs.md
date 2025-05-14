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
<important> no need to add properties in the outputs block like inputs.<important>
      This allows consuming modules to wire only the specific part of the output they require, while still having the
      option to consume the entire object via `default`.

