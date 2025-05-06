## 🏗️ Knowledge Base: Configuring Artifact Inputs in a Facets Module

This article describes how to define **artifact inputs** in a Facets module when the module requires external artifacts such as Docker images or other resources.

---

### 📂 Section: `artifact_inputs` in `facets.yaml`

#### ✅ Purpose:

Specifies external artifacts that the module requires to function properly. These artifacts are referenced and used by the module during deployment.

#### 🎯 When to use:

- When your module requires a Docker image
- When your module depends on any external artifact that must be provided

#### 🔑 Structure:

```yaml
artifact_inputs:
  primary:
    attribute_path: "<json_path_to_reference>"
    artifact_type: "<type_of_artifact>"
```

#### 🧹 Required Fields:

- **`primary`**: The main artifact input that the module depends on.
  - **`attribute_path`**: Mandatory. The JSON path in the resource where the artifact is expected to be read from.
    - Example: `"spec.release.image"` for a Docker image path in the resource JSON.
  - **`artifact_type`**: Mandatory. The type of artifact being referenced.
    - Supported values:
      - `docker_image`: For Docker container images
      - `freestyle`: For other types of artifacts

#### ⚠️ Important Notes:

- Both `attribute_path` and `artifact_type` fields are mandatory
- The `primary` key is required and represents the main artifact dependency
- Ensure that the `attribute_path` correctly points to where the artifact is expected in the resource JSON

---

### 🔍 Example

#### Configuring a Docker image artifact input

**facets.yaml**

```yaml
artifact_inputs:
  primary:
    attribute_path: "spec.release.image"
    artifact_type: "docker_image"
```

This configuration indicates that:
- The module requires a Docker image
- The image path will be read from `spec.release.image` in the resource JSON
- The artifact is of type `docker_image`

---

### 🔄 Usage Context

When a module has `artifact_inputs` defined:
1. The system knows to expect and process the corresponding artifact
2. The module can reference the artifact at the specified path
3. Infrastructure as Code tools can appropriately handle the artifact dependencies

Remember to document the artifact requirement in your module's README to ensure users are aware of what artifacts they need to provide when using the module.