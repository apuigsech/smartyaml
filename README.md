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

# Load from string
yaml_content = """
database: !import_yaml db.yaml
  password: !env(DB_PASSWORD)
"""
data = smartyaml.load(yaml_content)

# Load with custom options
data = smartyaml.load('config.yaml',
                     base_path='/custom/path',
                     template_path='/templates',
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

## Complete Example

```yaml
# config.yaml
app:
  name: MyApplication
  version: !env(APP_VERSION, "1.0.0")
  debug: !env(DEBUG, false)

database: !import_yaml(config/database.yaml)
  password: !env(DB_PASSWORD)

cache: !template(redis)

logging: !include_yaml_if(DEBUG, config/debug_logging.yaml)

# Large SQL queries from external files
queries:
  get_users: !import(sql/users.sql)
  analytics: !import(sql/analytics.sql)

# Secrets (base64 encoded for safety)
secrets:
  api_key: !base64_decode(YWJjZGVmZ2hpams=)

# Development-only settings
dev_tools: !include_if(DEVELOPMENT, dev_tools.txt)
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
