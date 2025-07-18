## 🏗️ Always Add and Update the `iac.validated_files` Block in facets.yaml

When generating a new module, always include an `iac` block in the `facets.yaml` file.  
The `iac` block must contain a `validated_files` array listing the names of all `.tf` files created for the module.

Example:
```yaml
iac:
  validated_files:
    - main.tf
    - variables.tf
    - outputs.tf
```

Whenever you create a new `.tf` file (such as `main.tf`, `variables.tf`, or any additional Terraform file), add its filename to the `iac.validated_files` array in `facets.yaml`. 

> **Note:** No need to add `validated_files` block for files of existing modules that you are editing. This is only required for new modules or new `.tf` files you create. 