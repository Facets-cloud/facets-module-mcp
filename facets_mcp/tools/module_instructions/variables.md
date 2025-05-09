## 🧠 Knowledge Base: Adding Developer Inputs in a Facets Module

This article describes how to define **developer-facing inputs** (`spec:`) in a Facets module using supported JSON
Schema patterns and synchronize them with Terraform.

A Facets module can be designed for either developer self-service or operations usage. For developer self-service, the
organization’s defaults are predefined in the code and modeling, with only the necessary options for developers exposed.
These options may be further abstracted to simplify the user experience. In contrast, for operations usage, the module
can expose the corresponding cloud configurations based on the specific requirements provided by the user.


---

### 📂 Section: `spec` in `facets.yaml`

#### ✅ Purpose:

Defines inputs that developers can configure when using the module.

#### 🔤 Supported Types:

- `string`
- `number`
- `boolean`
- `enum` (must be `type: string` with an `enum` list)

#### 🧹 Supported Fields:

- `type`
- `title`
- `description`
- `default`
- `enum`
- `pattern`
- `minimum`, `maximum`
- `minLength`, `maxLength`

#### ⚠️ Not Supported:

- Arrays directly under `spec:`  
  ➔ Use `patternProperties` to define maps with structured values instead.

---

### 📘 JSON Schema Patterns in Facets

#### 1. **Nested Objects**

Group related inputs.

```yaml
type: object
properties:
  ...
```

---

### 🗾️ Mapping to Terraform (`variables.tf`)

For every `spec:` property in `facets.yaml`, mirror it in `variables.tf`:

```hcl
variable "instance" {
  type = object({
    spec = object({
      <variable_name> = <hcl_type>
      } )
  })
}
```

📌 For pattern-based maps:

```hcl
services = map(object({
  service_api = string
}))
```

Make sure to include Terraform variable validations for each spec field with appropriate error messages. The validations must be only from var.instance and var.inputs.
---

### ✅ Validation

Use the Facets CLI to validate schema and Terraform sync:

```bash
ftf validate
```

Run this before starting Terraform development.

---

### 🔍 Example

#### Add a boolean field: `enable_encryption`

**facets.yaml**

```yaml
spec:
  properties:
    enable_encryption:
      type: boolean
      title: Enable Encryption
      default: true
  required:
    - enable_encryption
```

**variables.tf**

```hcl
variable "instance" {
  type = object({
    spec = object({
      enable_encryption = bool
    })
  })
}
```

**VERY VERY IMPORTANT: In Facets YAML Sample section only put the default values where specified at field level. Never
fabricate a value**