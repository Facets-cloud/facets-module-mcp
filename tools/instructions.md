**Facets Module: Guided Variable Addition Workflow**

This guide helps an LLM-powered assistant collaborate with the user to define and add new **developer-facing inputs** (
under `spec:`) to a Facets module following the standard module development workflow.

---

### 🔹 Step 1: Collaborate with the User to Define New Variables



---

### 🔹 Step 2: Add Developer Inputs (`spec:`)

For each developer input:

#### 1. **Update `facets.yaml` under `spec:`**

The `spec:` block in `facets.yaml` must follow standard **JSON Schema** rules.

**Allowed types:**
- `string`
- `number`
- `boolean`
- `enum` *(with `type: string` + `enum` list)*

**Supported fields:**
- `type`, `title`, `description`, `default`
- `enum`, `pattern`, `minimum`, `maximum`, `minLength`, `maxLength`

**We do not support Arrays instead use patternProperties**

Facets supports advanced patterns in `spec:` for complex developer inputs:

- **Nested Objects**  
  Group related fields using:
  ```yaml
  type: object
  properties:
    ...
  ```

- **Pattern-based Maps (Object with dynamic keys)**  
  Use `patternProperties` to allow a flexible object map with structured values.

---

✅ **In Facets (`keyPattern` syntax)**  
Facets uses a custom field: `keyPattern` inside `patternProperties`.

```yaml
services:
  type: object
  title: Services
  description: A list of the Google Service APIs to be enabled in the project.
  patternProperties:
    keyPattern: '^[a-zA-Z0-9_.\/-]*$'
    type: object
    title: Service API Settings
    properties:
      service_api:
        type: string
        title: Service API Name
```

❌ **Standard JSON Schema (not supported in Facets)**  
This is the conventional way, but not valid in Facets:

```yaml
services:
  type: object
  patternProperties:
    "^[a-zA-Z0-9_.\\/\\-]*$":
      type: object
      properties:
        service_api:
          type: string
```

> 🧠 In `variables.tf`, declare this as:
```hcl
services = map(object({
  service_api = string
}))
```
```yaml
spec:
  properties:
    <variable_name>:
      type: <type>
      title: <Human Readable Title>
      default: <default_value>  # optional
  required:
    - <variable_name>  # if required
```

#### 2. **Update `variables.tf` under `spec` inside `instance`**

```hcl
variable "instance" {
  type = object({
    ...
    spec = object({
      ...
      <variable_name> = <hcl_type>
      } )
    })
}
```

---

### 🔹 Step 3: Validate the Module

Use the Facets CLI to validate the structure:

```bash
ftf validate
```

Only proceed with Terraform development once validation passes.

---

### 🧪 Example: Adding `enable_encryption` (Developer Input)

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

---

