## 🏗️ Knowledge Base: How to populate other fields of YAML 

Use these tags in your module's `facets.yaml`. Each gives a capability on the behavior of metadata of the module.

### Tags present at root level

```yaml
controlPlaneUISettings: # tag to define all fields that will govern UI behavior of the resource, apart from the form.
    name_regex: "^[A-Za-z][A-Za-z0-9-]{0,19}$"  # any resource added will comply with this regex format (optional)
    enableKubernetesExplorer: true # any module that will be running in kuberenetes cluster will show Kubernetes Dashboard if this flag is enabled.
```