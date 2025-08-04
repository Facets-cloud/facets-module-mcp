## 📥 Import Declarations for Terraform Modules

When users want to add import declarations to bring existing infrastructure under Terraform management:

1. **First discover resources**: Use `discover_terraform_resources(module_path)` to scan .tf files and identify available resources
2. **Then add imports**: Use `add_import_declaration()` to add import declarations to facets.yaml

---

### ✅ discover_terraform_resources
- Returns list of all Terraform resources in module
- Shows which resources use `count` or `for_each`
- Use this before adding imports to see available resources

### ✅ add_import_declaration
- Adds import declarations to facets.yaml
- Required: `module_path`, `name`
- For count resources: add `index` parameter
- For for_each resources: add `key` parameter
- Use `resource_address` for full addresses like `aws_s3_bucket.bucket[0]`

---

### 📝 Import Format in facets.yaml

```yaml
imports:
  - name: bucket
    resource_address: aws_s3_bucket.main
    required: true
```
