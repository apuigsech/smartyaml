# File Operations Examples

This folder demonstrates SmartYAML's file inclusion capabilities using various directives.

## Examples

### `basic_include.yaml`
Demonstrates basic file inclusion using `!include` and `!include_yaml`.

**Features:**
- YAML file inclusion with directive processing
- Text file inclusion (SQL, Markdown, certificates)
- Raw YAML inclusion without directive processing
- Mixed content types in a single configuration

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/file_operations/basic_include.yaml')
print("Database config:", data['application']['database'])
print("API Documentation length:", len(data['api_documentation']))
print("Get users query:", data['queries']['get_users'][:100] + "...")
```

### `conditional_include.yaml`
Shows conditional file inclusion using `!include_if` and `!include_yaml_if`.

**Features:**
- Environment-based conditional inclusion
- Feature flag-driven configuration loading
- Conditional documentation and query loading
- Mixed conditional and unconditional includes

**Test with environment variables:**
```bash
export DEVELOPMENT="true"
export ENABLE_CACHING="true"
export ENABLE_MONITORING="true"
export ADVANCED_SECURITY="true"
export ENABLE_PAYMENTS="true"
export DEBUG_MODE="true"
```

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/file_operations/conditional_include.yaml')
print("Included features:")
for feature in data.get('features', {}):
    print(f"- {feature}")
```

## File Structure

```
file_operations/
├── configs/                    # Configuration files
│   ├── database.yaml          # Database configuration with SmartYAML processing
│   ├── logging.yaml           # Logging configuration with environment switches
│   ├── external_service.yaml  # Raw YAML (directives not processed)
│   └── cors_config.yaml       # CORS configuration with environment-based origins
├── data/                      # Static data files
│   └── api_guide.md          # API documentation (Markdown)
├── sql/                       # SQL query files
│   ├── get_users.sql         # User retrieval query
│   ├── create_user.sql       # User creation query
│   └── update_user.sql       # User update query
├── basic_include.yaml         # Basic file inclusion example
├── conditional_include.yaml   # Conditional inclusion example
└── README.md                  # This file
```

## File Inclusion Directives

### `!include 'filepath'`
Includes and processes a file through the full SmartYAML pipeline.

**Features:**
- Processes all SmartYAML directives in the included file
- Supports YAML files with metadata and variables
- Text files are included as strings
- Recursive processing of nested includes

**Examples:**
```yaml
# Include and process YAML configuration
database: !include 'configs/database.yaml'

# Include text file as string
sql_query: !include 'sql/get_users.sql'

# Include documentation
readme: !include 'docs/README.md'
```

### `!include_if ['CONDITION', 'filepath']`
Conditionally includes a file based on an environment variable.

**Condition evaluation:**
- Truthy values: `true`, `yes`, `1`, `on`, `enabled` (case-insensitive)
- Falsy values: `false`, `no`, `0`, `off`, `disabled`, empty string
- Missing environment variables are treated as falsy

**Examples:**
```yaml
# Include only if DEBUG is set and truthy
debug_config: !include_if ['DEBUG', 'configs/debug.yaml']

# Include only in production
prod_config: !include_if ['PRODUCTION', 'configs/production.yaml']
```

### `!include_yaml 'filepath'`
Includes raw YAML content without processing SmartYAML directives.

**Use cases:**
- Including third-party configuration files
- Preserving directive syntax for later processing
- Including templates that should not be processed

**Examples:**
```yaml
# Include raw YAML (directives preserved)
external_config: !include_yaml 'third_party/config.yaml'

# Include template without processing
template: !include_yaml 'templates/raw_template.yaml'
```

### `!include_yaml_if ['CONDITION', 'filepath']`
Conditionally includes raw YAML content.

**Examples:**
```yaml
# Conditionally include raw configuration
legacy_config: !include_yaml_if ['LEGACY_MODE', 'configs/legacy.yaml']
```

## Supported File Types

### YAML Files
- **With `!include`**: Full SmartYAML processing (metadata, directives, variables)
- **With `!include_yaml`**: Raw YAML parsing only, directives preserved as strings

### Text Files
- SQL queries
- Configuration files (JSON, TOML, etc.)
- Documentation (Markdown, plain text)
- Certificates and keys
- Scripts and code snippets

### Processing Behavior

| File Extension | `!include` | `!include_yaml` |
|----------------|------------|------------------|
| `.yaml`, `.yml` | Full SmartYAML processing | Raw YAML only |
| `.sql` | String content | String content |
| `.md`, `.txt` | String content | String content |
| `.json` | String content | String content |
| Others | String content | String content |

## Best Practices

1. **Use `!include`** for YAML files that should be processed by SmartYAML
2. **Use `!include_yaml`** for third-party YAML files or templates
3. **Use conditional inclusion** for feature flags and environment-specific configuration
4. **Organize files logically** in subdirectories (configs/, data/, sql/, etc.)
5. **Document required environment variables** for conditional inclusion
6. **Test all conditional paths** to ensure they work as expected
7. **Use relative paths** from the base configuration file
8. **Keep included files focused** on single responsibilities
