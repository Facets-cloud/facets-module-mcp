## 📘 Knowledge Base: `x-ui` Tags in Facets Module Forms

Use these tags inside `spec.properties.<field>` of your module's `facets.yaml`. Each enhances form rendering or behavior in the developer UI.

---

### 🔄 Dynamic Data Sources

```yaml
x-ui-output-type: "@outputs/kubernetes_service"  # Select from modules exporting this output type. Use this when the field can be derived from another module reference
```

```yaml
x-ui-secret-ref: true  # Reference a secret defined at the project level. Use this when a field has to be secret
```

```yaml
x-ui-variable-ref: true  # Reference a variable defined at the project level. Use this when same value can be referenced by other modules.
```

```yaml
x-ui-dynamic-enum: spec.runtime.ports.*.port  # Populate dropdown based on another field's value, * also supported
```

---

### 🌍 Environment Management

```yaml
x-ui-overrides-only: true  # Show only when overriding per environment. Use this when the variable cannot have a sensible defualt for all environments. like CIDR
```

```yaml
x-ui-override-disable: true  # Prevent overrides in any environment. Use this when it does not make sense for value to be changed per env. e.g. service port
```

---

### 🧩 Form Layout & Presentation

```yaml
x-ui-toggle: true  # Render this field group as collapsible. Use this to keep the advanced or any other block collapsed by default.
```

```yaml
x-ui-yaml-editor: true  # Use YAML editor for complex object input. Use this when you want to surface a yaml editor, use this for complex objects only
```
DONT OVERUSE THIS FIELD, WE WOULD LIKE TO KNOW SCHEMA AS MUCH AS POSSIBLE
---

### ❗ Validation & Conditional Display

```yaml
x-ui-error-message: "CIDR must be a valid private IP block"  # Custom error for validation failure
```

```yaml
x-ui-visible-if:
  field: spec.deployment_type # IMPORTANT: path from spec till the field location
  values: [ReplicaSet]  # Show only if another field has a specific value(s)
```