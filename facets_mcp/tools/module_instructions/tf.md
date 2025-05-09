## 📘 Knowledge Base: Terraform Usage in Facets Modules

### Supported Version

All modules must be authored using **Terraform v1.5.7**.

---

### Auto-Injected Variables

Every Facets module automatically receives the following variables:

- `instance_name`: A unique architectural name for the resource, defined by the blueprint designer.
- `environment`: An object with environment-specific metadata:
  - `name`: Logical environment name.
  - `unique_name`: Globally unique environment identifier.
  - `cloud_tags`: Standard tags applied to all resources for control plane traceability.

These are injected automatically and do not need to be declared manually.

---

### Allowed Variable Access in Terraform Code

Terraform logic in `main.tf` must only use:

- `var.instance_name` – For naming resources.
- `var.environment.unique_name` – For environment-based uniqueness.
- `var.environment.cloud_tags` – For applying platform-defined tags.
- `var.instance.spec.<field>` – For developer-facing configuration.
- `var.inputs` – For consuming typed outputs from other modules.

---

### Rules & Restrictions

- Do **not** define `provider` blocks. Providers must be injected through inputs.
- Do **not** define `output` blocks. Use `locals.output_attributes` to expose values.
- Reference only variables defined in `variables.tf`.
- Always derive names from `instance_name` and `environment.unique_name` unless specified by user.