
### 📏 Terraform Guidelines

Very Important: TF Version is 1.5.7
Terraform logic in `main.tf` must be written using only the following variable paths:

#### ✅ Allowed Variable Sources
- `var.instance_name` – use for naming resources.
- `var.instance.spec.<field>` – access developer-facing inputs.
- `var.environment.unique_name` – use for environment-level uniqueness.
- `var.inputs` – for consuming typed outputs from other modules.

✅ **VERY IMPORTANT:** Always confirm the Terraform plan or code with the user before proceeding.

#### 🛑 Rules & Guardrails
- Do **not** define `provider` blocks.
- Do **not** define `output` blocks ever.
- Use only fields declared in `variables.tf`.
- Always name resources using `var.instance_name` and `var.environment.unique_name`.
- Always show the user any tool calls that **mutate or deploy** infrastructure **before executing** them.
