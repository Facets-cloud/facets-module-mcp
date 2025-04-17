## 📘 Facets Module: `inputs` and `outputs` Reference

This document outlines the structure and purpose of `inputs` and `outputs` in a Facets module’s `facets.yaml` file.
These fields enable composability and inter-module wiring within the Facets platform.

---

### 🔹 `inputs`

Defines what data this module expects from other modules or user configuration.

#### ✅ Syntax:

```yaml
inputs:
  <input_name>:
    type: <@outputs/type> | <primitive_type>
```

#### 🔑 Common Fields:

- **`type`**: Required. Can reference:
    - Another module’s output (e.g. `@outputs/custom-databricks-account`) ALWAYS INCLUDE CUSTOM PREFIX FOR TYPES
    - Primitive type (e.g. `string`, `number`, `object`)

#### 🛠 Terraform Mapping

When a module consumes outputs from another module, the `inputs` field must be reflected in the consuming module’s
`variables.tf`:

```hcl
variable "inputs" {
  description = "A map of inputs requested by the module developer."
  type = object({
    <input_name> = object({
    <derived_output_attribute> : <type>
    } )
    })
}
```

The input type object is derived from the `outputs.tf` of the producing module using:

```hcl
locals {
  output_interfaces = {}
  output_attributes = {}
}
```

These act as contracts for consuming modules. 

IMPORTANT: read terraform code of outputting module to get schema of the outputs

---

### 🔹 `outputs`

Defines the values this module makes available to other modules.

#### ✅ Syntax:

```yaml
outputs:
  <output_name>:
    type: <@outputs/type>
```

#### 🔑 Common Fields:

- **`type`**: Required. Output classification, typically `@outputs/<type>`. Always use - in type instead of _ if required
- **`attributes`**: Logical-to-Terraform mapping for each exposed output value.

#### 💡 Example:

```yaml
outputs:
  default:
    type: "@outputs/databricks-account"
```

---
Properly defined `inputs` and `outputs` make modules interoperable, composable, and reusable in Facets' orchestrated
environments.