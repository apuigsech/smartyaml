# Template Examples

This folder demonstrates SmartYAML's powerful template inheritance system.

## Examples

### `base_template.yaml`
Shows how to inherit from a base template using `__template` with file path.

**Features:**
- Template inheritance with `path` directive
- Variable overrides between template and main file
- Overlay mode (merging template with current content)

**Run:**
```python
import smartyaml
# Set template_path to enable template loading
data = smartyaml.load('examples/templates/base_template.yaml',
                     template_path='examples/templates')
print(data)
```

### `template_use_example.yaml`
Demonstrates using templates with the `use` directive and dot notation.

**Features:**
- Template loading with `use: 'services.microservice'`
- Nested template loading with `!template` directive
- Multiple template composition

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/templates/template_use_example.yaml',
                     template_path='examples/templates')
print(f"Service: {data['service']['name']}")
print(f"Database: {data['database']['type']}")
```

## Template Structure

```
templates/
├── base/
│   └── service_base.yaml      # Base service template
├── services/
│   └── microservice.yaml     # Microservice-specific template
└── databases/
    └── postgres.yaml          # PostgreSQL configuration template
```

## Key Concepts

1. **Template Inheritance**: Use `__template` to inherit from base templates
2. **Template Path**: Use dot notation (e.g., `services.microservice`) to load templates
3. **Overlay Mode**: `overlay: true` merges template with current content
4. **Variable Inheritance**: Templates can define their own variables
5. **Template Directives**: Use `!template` to load templates inline

## Template Resolution Order

1. Load and process the template file
2. Merge template variables with current file variables
3. Apply overlay logic (merge or replace)
4. Process all directives in the merged result
