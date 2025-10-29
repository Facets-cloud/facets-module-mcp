## 🏗️ Knowledge Base: How to populate other fields of YAML 

Use these tags in your module's `facets.yaml`. Each gives a capability on the behavior of metadata of the module.

### Tags present at root level

```yaml
name_length_limit: 25 # restricts the length of the resource name to the value provided (optional)
```

```yaml
name_regex: "^[A-Za-z][A-Za-z0-9-]{0,19}$"  # any resource added will comply with this regex format (optional)
```