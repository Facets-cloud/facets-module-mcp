### ✅ How to Use a Provider from Another Module in Facets

In Facets, **providers must be passed in as inputs** from another module. You do **not** define provider blocks
directly.

To consume a provider:

```yaml
inputs:
  <input_name>:
    type: "@outputs/<type>"
    optional: false
    providers:
      - <provider_name>
```

This tells Facets that the required provider (e.g., `helm`, `kubernetes`, `google`, etc.) is expected to be available
from the module that produces the given `@outputs` type.

#### 🔁 Example:

```yaml
inputs:
  kubernetes_cluster_details:
    type: "@outputs/kubernetes_cluster_details"
    optional: false
    providers:
      - helm
```

This module expects to receive the `helm` provider configuration through the `kubernetes_cluster_details` output of
another module.

### ✅ How to Expose a Provider in a Facets Module

To expose a provider for other modules to consume, declare it under the `outputs` section in your `facets.yaml`.

```yaml
outputs:
  <output_name>:
    type: "@outputs/<output_type>"
    title: Will appear on the UI
    providers:
      <provider_name>:
        source: <provider_source>
        version: <provider_version>
        attributes:
            <field_1>: attributes.<output_field_1>
            <field_2>: attributes.<output_field_2>
            ...
```

#### 🔍 Breakdown

- **`outputs`**: Declares what this module exposes to others.
- **`type`**: Specifies the `@outputs` type identifier that consuming modules can reference. NEVER INFER IT LIST OTHER MODULES TO GET RELEVANT VALUE
- **`title`**: The title of the output that will appear on the UI.
- **`providers`**: Lists the provider configurations this module makes available.
- **`attributes`**: Maps provider-specific fields to values from the module’s `output_attributes`. These mappings
  configure the provider using data generated by this module.
