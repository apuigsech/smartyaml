# SmartYAML

Extended YAML format with custom directives for imports, environment variables, conditional processing, and more. SmartYAML maintains full compatibility with standard YAML while providing powerful additional features.

## Features

SmartYAML extends standard YAML with powerful custom directives:

### Core Directives
- **!import(filename)** - Import content from text files
- **!import_yaml(filename)** - Import and merge YAML files
- **!env(VAR_NAME, default?)** - Access environment variables with optional defaults
- **!expand(text)** - Variable substitution using `{{key}}` syntax

### Template System
- **!template(template_name)** - Load external templates from template directory
- **__template** - Inline template inheritance and merging
- **__vars** - Variable definitions with inheritance support

### Conditional Processing
- **!include_if(condition, filename)** - Conditional file inclusion based on environment variables
- **!include_yaml_if(condition, filename)** - Conditional YAML inclusion

### Encoding
- **!base64(data)** - Base64 encoding of strings
- **!base64_decode(data)** - Base64 decoding of strings

### Metadata
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

# Basic loading
data = smartyaml.load("config.yaml")

# Load with template support
data = smartyaml.load("config.yaml", template_path="templates")

# Load with variables and full options
variables = {"environment": "production", "version": "2.0.0"}
data = smartyaml.load('config.yaml',
                     base_path='/custom/path',
                     template_path='/templates',
                     variables=variables,
                     max_file_size=5*1024*1024)

# Load from string content
yaml_content = """
__vars:
  app: "MyApp"
  
database: !import_yaml db.yaml
  password: !env(DB_PASSWORD)
  name: !expand "{{app}}_database"
"""
data = smartyaml.loads(yaml_content)
```

## Real-World Example: AI Agent Configuration

```yaml
# agent.yaml - Customer support agent configuration
__vars:
  agent_name: "ACME Customer Support"
  company_name: "ACME Corp"
  environment: !env(ENVIRONMENT, "development")

# Inherit from base agent template
__template:
  <<: !template(agents/customer_support)

# Agent-specific customization
config:
  name: !expand "{{agent_name}}"
  welcome_message: !expand "Hello! Welcome to {{company_name}} support."
  
# Environment-specific features
debug_tools: !include_yaml_if(DEBUG, tools/debug.yaml)
production_monitoring: !include_yaml_if(PRODUCTION, monitoring/prod.yaml)

# Load external resources
knowledge_base: !import(knowledge/company_info.txt)
faq_data: !import_yaml(data/faq.yaml)
```

```yaml
# templates/agents/customer_support.yaml - Reusable template
__vars:
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 1000
  voice_id: "default"

config:
  llm:
    model: !expand "{{model}}"
    temperature: !expand "{{temperature}}"
    max_tokens: !expand "{{max_tokens}}"
  
  voice:
    provider: "elevenlabs"
    voice_id: !expand "{{voice_id}}"
    
  conversation:
    timeout: 300
    max_turns: 50
```

**Loading:**
```python
import smartyaml

# Load with template inheritance
data = smartyaml.load("agent.yaml", template_path="templates")

# Override with production settings
prod_vars = {"environment": "production", "model": "gpt-4-turbo"}
data = smartyaml.load("agent.yaml", 
                     template_path="templates",
                     variables=prod_vars)
```

**Result:** Deep merging with proper variable precedence - agent variables override template variables.

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

### 6. Template System

#### External Templates: `!template(template_name)`

Loads templates from a centralized template directory.

```yaml
# Loads from templates/postgres.yaml
database: !template(postgres)

# Loads from templates/redis.yaml  
cache: !template(redis)
```

**Usage:** Pass `template_path` parameter to `smartyaml.load()`

#### Inline Templates: `__template`

Inherit from external templates with local customization.

```yaml
# agent.yaml
__vars:
  agent_name: "Customer Support"
  company: "ACME Corp"

__template:
  <<: !template(agents/base)

# Document-level overrides
custom_prompt: !expand "You are {{agent_name}} for {{company}}"
```

```yaml
# templates/agents/base.yaml
__vars:
  model: "gpt-4"
  temperature: 0.7

config:
  llm: !expand "{{model}}"
  temperature: !expand "{{temperature}}"
  prompt: !expand "{{custom_prompt}}"
```

**Features:**
- **Variable Inheritance**: Template variables available in main document
- **Override Support**: Document variables override template variables
- **Merge Semantics**: Uses YAML merge key (`<<:`) for composition

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

**Variable Priority** (highest to lowest):
1. Function parameters (`smartyaml.load(file, variables={...})`)
2. Document `__vars` (main file)
3. Template `__vars` (from imported templates)

**Variable Inheritance:**
Variables from imported templates are available for expansion in the main document, enabling powerful template composition patterns.

### 9. Variable System: `__vars`

Define variables for template expansion with inheritance support.

```yaml
# Basic variables
__vars:
  app_name: "MyApp"
  version: "1.0.0"
  debug: !env(DEBUG, false)

config:
  name: !expand "{{app_name}}"
  version: !expand "{{version}}"
  debug_mode: !expand "{{debug}}"
```

**Variable Sources & Precedence:**
1. **Function variables** (highest): `smartyaml.load(file, variables={...})`
2. **Document variables** (medium): `__vars` in main file
3. **Template variables** (lowest): `__vars` from imported templates

**Variable Inheritance:**
```yaml
# main.yaml
__vars:
  company: "ACME Corp"  # Overrides template variable
  
__template:
  <<: !template(base)  # Inherits variables from templates/base.yaml
  
welcome: !expand "Welcome to {{company}}!"  # Uses overridden value
```

### 10. Metadata Fields

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
  
__template:              # Template inheritance metadata
  <<: !template(base_config)
  
__build_info:            # Documentation metadata  
  date: !env(BUILD_DATE)
  
app_url: !expand "https://{{env}}.example.com"
```

**Special Metadata Fields:**
- `__vars`: Variable definitions
- `__template`: Template inheritance
- `__*`: Custom metadata (automatically removed)

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

# Template inheritance with customization
__template:
  <<: !template(apps/base_config)

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

**Loading with templates and variables:**

```python
import smartyaml

# Load with template support
data = smartyaml.load("config.yaml", template_path="templates")

# Override variables via function parameters
custom_vars = {"environment": "production", "version": "2.0.0"}
data = smartyaml.load("config.yaml", 
                     template_path="templates",
                     variables=custom_vars)

# Load string content
yaml_string = "app: !expand '{{name}}'"
data = smartyaml.loads(yaml_string, variables={"name": "MyApp"})
```

## Advanced Template Examples

### Template Inheritance Chain

```yaml
# templates/base/app.yaml - Base application template
__vars:
  default_timeout: 30
  log_level: "INFO"

__template:
  application:
    timeout: !expand "{{default_timeout}}"
    logging:
      level: !expand "{{log_level}}"
```

```yaml
# templates/environments/production.yaml - Production template
__vars:
  log_level: "WARN"
  replica_count: 3

__template:
  <<: !template(base/app)
  
  # Production-specific overrides
  application:
    replicas: !expand "{{replica_count}}"
    security:
      enabled: true
```

```yaml
# myapp.yaml - Final configuration
__vars:
  app_name: "MyService"
  default_timeout: 60  # Override base template

__template:
  <<: !template(environments/production)

# Application-specific additions
app_config:
  name: !expand "{{app_name}}"
  custom_feature: true
```

**Result:** Deep merging with proper variable precedence - app variables override template variables.

### Multi-Template Composition

```yaml
# Service configuration combining multiple templates
__vars:
  service_name: "UserAPI"
  environment: "staging"

__template:
  # Combine database, cache, and monitoring templates
  database: !template(components/postgres)
  cache: !template(components/redis)
  monitoring: !template(components/prometheus)
  
# Service-specific configuration
service:
  name: !expand "{{service_name}}"
  environment: !expand "{{environment}}"
  endpoints:
    health: "/health"
    metrics: "/metrics"
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
