## 🎯 Intent Management for Terraform Modules

When users need to create or query intents in the control plane:

1. **First check if intent exists**: Use `get_intent(intent_name)` to query existing intents
2. **Create new intents**: Use `create_or_update_intent()` to create or update intents programmatically
3. **List all intents**: Use `list_all_intents()` to discover existing intent types and names

---

### ✅ get_intent
- Queries whether an intent exists in the control plane by name
- Returns intent details if found, or indicates if intent doesn't exist
- Use this before creating new intents to avoid duplicates

### ✅ create_or_update_intent
- Creates a new intent or updates an existing one in the control plane
- Required: `name`, `intent_type`, `display_name`, `description`
- Optional: `icon_url`, `outputs`
- Automatically handles create vs update logic

### ✅ list_all_intents
- Lists all available intents in the control plane
- Shows unique intent types for reference
- Useful for discovering existing patterns

---

### 📝 Intent Structure

Intents follow this structure in the control plane:

```json
{
  "name": "kubernetes_cluster",
  "type": "K8s",
  "displayName": "Kubernetes Cluster",
  "description": "A group of computing nodes that run containerized applications",
  "iconUrl": "https://example.com/icon.svg",
  "outputs": [
    { "name": "default", "type": "@kubernetes/cluster" }
  ]
}
```

### 🔄 Workflow for Missing Intents

When validation fails due to missing intent:

1. Use `get_intent(intent_name)` to confirm intent doesn't exist
2. Use `list_all_intents()` to see available intent types
3. Use `create_or_update_intent()` with appropriate parameters
4. Re-run module validation

### 📋 Common Intent Types

Use `list_all_intents()` to see current types, common ones include:
- `K8s` - Kubernetes resources
- `Storage` - Storage solutions
- `Database` - Database services
- `Networking` - Network components
- `Security` - Security tools
