## 🧠 Knowledge Base: Adding Developer Inputs in a Facets Module

This article describes how to define **developer-facing inputs** (`spec:`) in a Facets module using supported JSON Schema patterns and synchronize them with Terraform.

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

#### 2. **Pattern-based Maps**
Used to define dynamic keys with structured values.

```yaml
services:
  type: object
  patternProperties:
    "^[a-zA-Z0-9_.\\/\\-]*$":   # Facets-specific key pattern
      type: object
      properties:
        service_api:
          type: string
```

✅ **Recommended Key Pattern:**  
`"^[a-zA-Z0-9_.\\/\\-]*$"`  
Supports keys like `compute.googleapis.com`, `storage/v1`.

#### ❌ Do NOT Use:
```yaml
type: array
items:
  type: string
```

---

### 🗾️ Mapping to Terraform (`variables.tf`)

For every `spec:` property in `facets.yaml`, mirror it in `variables.tf`:

```hcl
variable "instance" {
  type = object({
    spec = object({
      <variable_name> = <hcl_type>
    })
  })
}
```

📌 For pattern-based maps:

```hcl
services = map(object({
  service_api = string
}))
```

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