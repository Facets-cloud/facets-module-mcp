## 🏗️ Always Add the `iac` Block in facets.yaml

When generating a new module, always include an `iac` block in the `facets.yaml` file.  
This block should specify the infrastructure-as-code (IAC) implementation details for the module.

Example:
```yaml
iac:
  type: terraform
  version: 1.5.7
``` 