# SmartYAML

Extended YAML format with custom directives for imports, environment variables, conditional processing, and more. SmartYAML maintains full compatibility with standard YAML while providing powerful additional features.

## Features

SmartYAML extends standard YAML with powerful custom directives:

- **!import(filename)** - Import content from text files
- **!import_yaml(filename)** - Import and merge YAML files
- **!env(VAR_NAME, default?)** - Access environment variables with optional defaults
- **!include_if(condition, filename)** - Conditional file inclusion based on environment variables
- **!include_yaml_if(condition, filename)** - Conditional YAML inclusion
- **!template(template_name)** - Template processing from centralized template directory
- **!base64(data)** - Base64 encoding of strings
- **!base64_decode(data)** - Base64 decoding of strings
- **!expand(text)** - Variable substitution using `{{key}}` syntax
- **Metadata fields** - `__field` prefixed fields for annotations (automatically removed)

## Installation

### From PyPI

```bash
pip install smartyaml
```

### From GitHub Repository

```bash
# Install latest from main branch
pip install git+https://github.com/apuigsech/smartyaml.git

# Install specific version/tag
pip install git+https://github.com/apuigsech/smartyaml.git@v0.1.0

# Clone and install for development
git clone https://github.com/apuigsech/smartyaml.git
cd smartyaml
pip install -e ".[dev]"
```

## Quick Start

```python
import smartyaml

# Load a SmartYAML file
data = smartyaml.load("config.yaml")

# Load from string with variables
yaml_content = """
__vars:
  app: "MyApp"
  
database: !import_yaml db.yaml
  password: !env(DB_PASSWORD)
  name: !expand "{{app}}_database"
"""
data = smartyaml.load(yaml_content)

# Load with custom options and variables
variables = {"environment": "production", "version": "2.0.0"}
data = smartyaml.load('config.yaml',
                     base_path='/custom/path',
                     template_path='/templates',
                     variables=variables,
                     max_file_size=5*1024*1024)
```

## Directive Reference

### 1. Text File Import: `!import(filename)`

Loads the entire content of a file as a string.

```yaml
# config.yaml
html_template: !import(template.html)
sql_query: !import(queries/select_users.sql)
```

### 2. YAML Import with Merge: `!import_yaml(filename)`

Loads YAML content from a file with optional local overrides.

```yaml
# Simple import
database: !import_yaml(database.yaml)

# Import with local overrides
database: !import_yaml(database.yaml)
  password: production_pass  # Overrides imported password
```

### 3. Environment Variables: `!env(VAR_NAME, default?)`

Reads values from environment variables with optional defaults.

```yaml
database_url: !env(DATABASE_URL, "postgresql://localhost/myapp")
debug_mode: !env(DEBUG, false)
port: !env(PORT, 8080)
```

### 4. Conditional Text Import: `!include_if(condition, filename)`

Includes a text file only if an environment variable condition is truthy.

```yaml
debug_config: !include_if(DEBUG_MODE, debug_settings.txt)
development_notes: !include_if(DEV_ENV, notes.md)
```

**Truthy values:** `1`, `true`, `yes`, `on`, `enabled` (case-insensitive)

### 5. Conditional YAML Import: `!include_yaml_if(condition, filename)`

Includes a YAML file only if an environment variable condition is truthy.

```yaml
debug: !include_yaml_if(DEBUG, debug.yaml)
database: !include_yaml_if(PRODUCTION, prod_db.yaml)
```

### 6. Template Import: `!template(template_name)`

Loads templates from a centralized template directory.

```yaml
# Loads from $SMARTYAML_TMPL/postgres.yaml
database: !template(postgres)

# Loads from $SMARTYAML_TMPL/redis.yaml
cache: !template(redis)
```

**Requires:** `SMARTYAML_TMPL` environment variable set to template directory

### 7. Base64 Encoding/Decoding

Encode strings to base64 or decode base64 strings.

```yaml
# Encoding
secret: !base64(my_secret_password)  # -> bXlfc2VjcmV0X3Bhc3N3b3Jk

# Decoding
password: !base64_decode(bXlfc2VjcmV0X3Bhc3N3b3Jk)  # -> my_secret_password
```

### 8. Variable Substitution: `!expand(text)`

Replaces `{{key}}` patterns with variable values from function parameters or `__vars` metadata.

```yaml
# Using __vars metadata
__vars:
  app_name: "MyApp"
  version: "1.0.0"
  environment: "production"

title: !expand "{{app_name}} v{{version}}"
api_url: !expand "https://api-{{environment}}.example.com"
```

```python
# Using function variables (override __vars)
variables = {"app_name": "CustomApp", "version": "2.0.0"}
data = smartyaml.load("config.yaml", variables=variables)
```

**Variable Priority:**
1. Function parameters (highest priority)
2. `__vars` metadata fields

### 9. Metadata Fields

Fields prefixed with `__` are automatically removed from the final result and serve as documentation/configuration.

```yaml
# Input
__version: "1.2.3"        # Removed
__build_date: 2024-01-15  # Removed
app_name: "MyApp"         # Kept

# Result: {"app_name": "MyApp"}
```

Metadata fields can contain SmartYAML directives:

```yaml
__vars:                   # Special metadata for variables
  env: !env(ENVIRONMENT, "dev")
  
__build_info:            # Documentation metadata  
  date: !env(BUILD_DATE)
  
app_url: !expand "https://{{env}}.example.com"
```

## Complete Example

```yaml
# config.yaml - Comprehensive SmartYAML demonstration

# Variables and metadata for configuration
__vars:
  app_name: "MyApplication"
  environment: !env(ENVIRONMENT, "development")
  version: !env(APP_VERSION, "1.0.0")
  
__build_info:  # Documentation metadata (removed from final result)
  date: !env(BUILD_DATE)
  commit: !env(GIT_COMMIT, "unknown")

# Application configuration with variable expansion
app:
  name: !expand "{{app_name}}"
  full_title: !expand "{{app_name}} v{{version}}"
  environment: !expand "{{environment}}"
  debug: !env(DEBUG, false)
  api_url: !expand "https://api-{{environment}}.example.com"

# Database configuration using variables and imports
database: !import_yaml(config/database.yaml)
  password: !env(DB_PASSWORD)
  connection_string: !expand "postgresql://localhost/{{app_name}}_{{environment}}"

# Template-based configuration
cache: !template(redis)

# Conditional configuration based on environment
logging: !include_yaml_if(DEBUG, config/debug_logging.yaml)

# Large SQL queries from external files
queries:
  get_users: !import(sql/users.sql)
  analytics: !import(sql/analytics.sql)

# Secrets with encoding
secrets:
  api_key: !base64_decode(YWJjZGVmZ2hpams=)
  jwt_secret: !expand "{{app_name}}_secret_{{environment}}"

# Development-only settings
dev_tools: !include_if(DEVELOPMENT, dev_tools.txt)

# Service configuration with variable expansion
services:
  api:
    name: !expand "{{app_name}}-api"
    image: !expand "{{app_name}}:{{version}}"
    url: !expand "https://{{app_name}}-{{environment}}.example.com"
```

**Loading with custom variables:**

```python
import smartyaml

# Load with default __vars
data = smartyaml.load("config.yaml")

# Override variables via function parameters
custom_vars = {"environment": "production", "version": "2.0.0"}
data = smartyaml.load("config.yaml", variables=custom_vars)
```

## Security Features

- **File Size Limits**: Default 10MB limit per file, configurable
- **Recursion Protection**: Default 10-level deep import limit
- **Path Security**: Directory traversal protection
- **Cycle Detection**: Prevents circular import chains
- **No Code Execution**: Safe YAML parsing only
- **Template Path Validation**: Prevents access to system directories

## Error Handling

SmartYAML provides specific exceptions with detailed context:

- `SmartYAMLError` - Base exception
- `SmartYAMLFileNotFoundError` - Referenced file not found
- `InvalidPathError` - Invalid or unsafe path access
- `EnvironmentVariableError` - Environment variable issues
- `TemplatePathError` - Template path configuration issues
- `Base64Error` - Base64 encoding/decoding failures
- `ResourceLimitError` - File size or resource limits exceeded
- `RecursionLimitError` - Import recursion or circular imports
- `ConstructorError` - Invalid arguments or constructor state

## Development

### Testing

```bash
python -m pytest
python -m pytest --cov=smartyaml
```

### Code Quality

```bash
black smartyaml/
isort smartyaml/
flake8 smartyaml/
mypy smartyaml/
```

### Building

```bash
python -m build
```

## Compatibility

- **Python**: 3.7+
- **YAML**: Full YAML 1.2 compatibility
- **Dependencies**: PyYAML 5.1+

SmartYAML files are valid YAML files - standard YAML parsers will treat custom directives as regular tagged values, making the format backward-compatible.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.
