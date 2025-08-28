# Basic SmartYAML Examples

This folder contains basic examples demonstrating core SmartYAML functionality.

## Examples

### `simple_config.yaml`
A straightforward configuration file without any special SmartYAML features. This shows that regular YAML files work perfectly with SmartYAML.

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/basic/simple_config.yaml')
print(data)
```

### `variables_example.yaml`
Demonstrates variable definition and substitution using `__vars` and `!expand`.

**Features shown:**
- Variable definitions in `__vars`
- String interpolation with `!expand` directive
- Nested variable usage

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/basic/variables_example.yaml')
print(f"Application: {data['application']['name']}")
print(f"API Endpoint: {data['api']['endpoint']}")
```

### `schema_validation.yaml`
Shows how to use JSON Schema validation to ensure your configuration is correct.

**Features shown:**
- Schema definition in `__schema`
- JSON Schema validation rules
- Type checking and constraints

**Run:**
```python
import smartyaml
# This will validate the configuration against the schema
data = smartyaml.load('examples/basic/schema_validation.yaml')
print("Configuration is valid!")
```

## Key Concepts

1. **`__version`**: Ensures compatibility with SmartYAML library version
2. **`__vars`**: Define variables for reuse throughout the configuration
3. **`!expand`**: Substitute variables in strings using `{{variable}}` syntax
4. **`__schema`**: Define JSON Schema for configuration validation

All metadata fields (starting with `__`) are automatically removed from the final output.
