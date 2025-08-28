# SmartYAML

A powerful YAML processing library that extends standard YAML parsing with advanced features for templating, variable substitution, environment variable integration, conditional logic, and schema validation. SmartYAML processes input YAML files through a comprehensive pipeline to resolve all special constructs and output plain YAML data structures.

## Features

### 🔧 Core Processing Pipeline
- **6-Stage Processing**: parsing → metadata → templates → directives → variables → validation
- **Recursive Processing**: Depth-first resolution of nested structures and includes
- **Version Compatibility**: Built-in `__version` checking for future-proofing
- **Error Context**: Comprehensive error reporting with file/field location details

### 📝 Metadata System
- **`__vars`**: Variable definitions with inheritance and precedence
- **`__template`**: Powerful template inheritance and overlay system
- **`__schema`**: JSON Schema validation of final resolved YAML
- **`__version`**: Version compatibility checking
- **Auto-removal**: All `__*` metadata fields automatically removed from final output

### 🎯 Directive System
- **Environment Variables**: `!env`, `!env_int`, `!env_float`, `!env_bool`, `!secret`
- **File Operations**: `!include`, `!include_if`, `!include_yaml`, `!include_yaml_if`
- **Template Loading**: `!template`, `!template_if`
- **Data Manipulation**: `!merge`, `!concat`
- **Variable Operations**: `!var`, `!expand`
- **Conditionals**: `!if`, `!switch`

### 🔒 Security Features
- **Path Sanitization**: Directory traversal protection
- **File Size Limits**: Configurable limits (default 10MB)
- **Recursion Protection**: Prevents infinite recursion and circular imports
- **Environment Controls**: Whitelist/blacklist for environment variables
- **Sandbox Mode**: Restricts file and environment access
- **No Code Execution**: Safe YAML parsing only

## Installation

### From PyPI (Recommended)

```bash
pip install pysmartyaml
```

### From GitHub Repository

```bash
# Install latest from main branch
pip install git+https://github.com/apuigsech/smartyaml.git

# Install specific version/tag
pip install git+https://github.com/apuigsech/smartyaml.git@v1.0.0

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

# Load with variables and full configuration
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
  env: !env ['ENVIRONMENT', 'development']

__template:
  path: 'templates/base.yaml'
  overlay: true

database:
  name: !expand "{{app}}_{{env}}_db"
  host: !env ['DB_HOST', 'localhost']

features: !include_yaml_if ['ENABLE_FEATURES', 'features.yaml']
"""
data = smartyaml.loads(yaml_content, template_path="templates")
```

## Complete Example

```yaml
# config.yaml - Comprehensive SmartYAML demonstration
__version: "1.0.0"

# Variables with environment integration
__vars:
  app_name: "MyApplication"
  environment: !env ['ENVIRONMENT', 'development']
  version: !env ['APP_VERSION', '1.0.0']
  debug_mode: !env ['DEBUG', false]

# Template inheritance
__template:
  use: 'apps.base_config'  # Loads from templates/apps/base_config.yaml
  overlay: true           # Merge template with current content

# JSON Schema validation
__schema:
  type: object
  properties:
    app:
      type: object
      required: [name, version]
    database:
      type: object
      required: [host, name]
  required: [app, database]

# Application configuration with variable operations
app:
  name: !var "app_name"                                      # Direct string variable
  full_title: !expand "{{app_name}} v{{version}}"            # String templating
  environment: !var "environment"                            # Direct string variable
  debug: !var "debug_mode"                                   # Direct boolean variable
  api_url: !expand "https://api-{{environment}}.example.com" # String templating

# Database with conditional configuration
database: !merge
  - !include_yaml 'config/database_base.yaml'
  - host: !env ['DB_HOST', 'localhost']
    name: !expand "{{app_name}}_{{environment}}"         # String templating for name
    password: !env ['DB_PASSWORD']

# Environment-specific features
logging: !include_yaml_if ['DEBUG', 'config/debug_logging.yaml']
monitoring: !include_yaml_if ['PRODUCTION', 'config/monitoring.yaml']

# External content inclusion
documentation: !include 'docs/api_guide.md'
queries:
  users: !include 'sql/select_users.sql'

# Conditional service configuration
services: !switch ['DEPLOYMENT_TYPE']
  - case: 'kubernetes'
    deployment: !include_yaml 'k8s/deployment.yaml'
  - case: 'docker'
    deployment: !include_yaml 'docker/compose.yaml'
  - default: 'standalone'
    deployment: !include_yaml 'config/standalone.yaml'
```

## Metadata Fields Reference

SmartYAML recognizes only specific metadata fields that have special processing behavior. All other fields starting with `__` are **custom metadata** and are ignored.

### Recognized Metadata Fields
- **`__version`**: Version compatibility checking
- **`__vars`**: Variable definitions (available for substitution)
- **`__template`**: Template inheritance and overlay configuration
- **`__schema`**: JSON Schema validation rules

### Custom Metadata Fields
Any other field starting with `__` (like `__author`, `__created`, `__description`) is **custom metadata** and will be removed from the final output.

**Example:**
```yaml
# Recognized metadata - these work as expected
__vars:
  app_name: "MyApp"
__version: "1.0.0"

# Custom metadata - these are ignored
__author: "John Doe"
__created: "2024-01-01"

app:
  name: "{{app_name}}"
```

### `__version`
Version compatibility checking to ensure YAML files work with library version.

```yaml
__version: "1.0.0"  # Requires SmartYAML v1.0.0+
```

### `__vars`
Variable definitions with inheritance support. Variables can contain directives.

```yaml
__vars:
  app_name: "MyApp"
  environment: !env ['ENVIRONMENT', 'development']
  db_host: !env ['DB_HOST', 'localhost']
  connection_string: !expand "postgresql://{{db_host}}/{{app_name}}"

# Usage with expansion
database_url: !expand "{{connection_string}}_{{environment}}"
```

**Variable Precedence (highest to lowest):**
1. Function parameters: `smartyaml.load(file, variables={...})`
2. Document `__vars`: In the main YAML file
3. Template `__vars`: From inherited templates

### `__template`
Template inheritance and overlay system.

```yaml
__template:
  path: 'templates/base.yaml'     # Direct file path
  use: 'apps.microservice'        # Template name (loads from template_path)
  overlay: true                   # true=merge, false=replace (default: true)
```

**Template Inheritance Chain:**
```yaml
# templates/base.yaml
__vars:
  timeout: 30
  log_level: "INFO"

config:
  timeout: !expand "{{timeout}}"
  logging:
    level: !expand "{{log_level}}"
```

```yaml
# service.yaml
__vars:
  service_name: "UserAPI"
  timeout: 60  # Overrides template value

__template:
  use: 'base'

# Service-specific additions
service:
  name: !expand "{{service_name}}"
  # Inherits config.timeout=60, config.logging.level="INFO"
```

### `__schema`
JSON Schema validation of the final resolved YAML.

```yaml
__schema:
  type: object
  properties:
    app:
      type: object
      properties:
        name:
          type: string
        version:
          type: string
          pattern: "^\\d+\\.\\d+\\.\\d+$"
      required: [name, version]
    database:
      type: object
      properties:
        host: {type: string}
        port: {type: integer, minimum: 1, maximum: 65535}
      required: [host, port]
  required: [app, database]

# Schema composition with directives
__schema: !merge
  - !include_yaml 'schemas/common.yaml'
  - !include_yaml 'schemas/app_specific.yaml'
```

## Directives Reference

### Environment Variables

#### `!env ['VAR_NAME', 'default']`
Access environment variables as strings with optional defaults. Environment variables are always returned as strings.

```yaml
database_host: !env ['DB_HOST', 'localhost']
port: !env ['PORT', '8080']          # Returns string '8080'
debug_mode: !env ['DEBUG', 'false']  # Returns string 'false'
```

#### `!env_int ['VAR_NAME', default_int]`
Access environment variables and convert to integers.

```yaml
port: !env_int ['PORT', 8080]              # Returns integer 8080
max_connections: !env_int ['MAX_CONN', 100]  # Returns integer 100
workers: !env_int ['WORKERS', 4]            # Returns integer 4
```

#### `!env_float ['VAR_NAME', default_float]`
Access environment variables and convert to floats.

```yaml
timeout: !env_float ['TIMEOUT', 30.5]       # Returns float 30.5
cpu_limit: !env_float ['CPU_LIMIT', 1.0]    # Returns float 1.0
memory_ratio: !env_float ['MEM_RATIO', 0.8] # Returns float 0.8
```

#### `!env_bool ['VAR_NAME', default_bool]`
Access environment variables and convert to booleans. Accepts: `true`/`false`, `yes`/`no`, `1`/`0` (case-insensitive).

```yaml
debug_mode: !env_bool ['DEBUG', false]      # Returns boolean false
ssl_enabled: !env_bool ['SSL_ENABLE', true] # Returns boolean true
auto_deploy: !env_bool ['AUTO_DEPLOY', false] # Returns boolean false
```

#### `!secret ['SECRET_NAME', 'default']`
Same as `!env` - returns strings (future versions will support secure secret stores).

```yaml
api_key: !secret ['API_KEY', 'dev_key_123']
jwt_secret: !secret ['JWT_SECRET', 'fallback_secret']
```

### File Operations

#### `!include 'filename'`
Include file content as string (supports both text and YAML files).

```yaml
# Text files loaded as strings
sql_query: !include 'queries/users.sql'
html_template: !include 'templates/email.html'

# YAML files processed through full SmartYAML pipeline
config: !include 'config/database.yaml'
```

#### `!include_if ['CONDITION', 'filename']`
Conditional file inclusion based on environment variable.

```yaml
debug_config: !include_if ['DEBUG_MODE', 'debug.yaml']
prod_settings: !include_if ['PRODUCTION', 'prod_overrides.yaml']
```

**Truthy values:** `true`, `1`, `yes`, `on`, `enabled` (case-insensitive)

#### `!include_yaml 'filename'`
Include raw YAML content without processing SmartYAML directives.

```yaml
# Loads YAML but doesn't process any !directives within it
external_config: !include_yaml 'third_party/config.yaml'
```

#### `!include_yaml_if ['CONDITION', 'filename']`
Conditional raw YAML inclusion.

```yaml
legacy_config: !include_yaml_if ['USE_LEGACY', 'legacy/config.yaml']
```

### Template System

#### `!template 'template_name'`
Load templates from template directory using dot notation.

```yaml
# Loads templates/database/postgres.yaml
database: !template 'database.postgres'

# Loads templates/services/api.yaml
api_service: !template 'services.api'
```

#### `!template_if ['CONDITION', 'template_name']`
Conditional template loading.

```yaml
cache: !template_if ['ENABLE_CACHE', 'components.redis']
monitoring: !template_if ['PRODUCTION', 'observability.prometheus']
```

### Data Operations

#### `!merge [item1, item2, ...]`
Deep merge multiple data structures (objects/arrays).

```yaml
# Merge multiple configuration sources
database_config: !merge
  - !include_yaml 'config/db_base.yaml'
  - !include_yaml 'config/db_env_overrides.yaml'
  - host: !env ['DB_HOST', 'localhost']
    pool_size: !env ['DB_POOL_SIZE', 10]

# Merge template with local overrides
service_config: !merge
  - !template 'services.base'
  - name: 'user-service'
    replicas: 3
```

#### `!concat [item1, item2, ...]`
Concatenate arrays/lists.

```yaml
# Combine multiple lists
all_endpoints: !concat
  - !include_yaml 'api/public_endpoints.yaml'
  - !include_yaml 'api/admin_endpoints.yaml'
  - ['/health', '/metrics']  # Additional endpoints

# Dynamic list building
middleware: !concat
  - ['cors', 'logging']
  - !include_yaml_if ['DEVELOPMENT', 'middleware/dev.yaml']
  - !include_yaml_if ['PRODUCTION', 'middleware/prod.yaml']
```

### Variable Operations

#### `!var 'variable_name'`
Direct variable resolution with original type preservation. Unlike `!expand`, this returns the variable value in its original data type.

```yaml
__vars:
  service_name: "user-api"        # string
  port: 8080                      # integer
  ssl_enabled: true               # boolean
  timeout: 30.5                   # float
  nullable_setting: null          # null

# Direct variable access (preserves original types)
app:
  name: !var "service_name"       # Returns string: "user-api"
  port: !var "port"               # Returns integer: 8080
  ssl: !var "ssl_enabled"         # Returns boolean: true
  timeout: !var "timeout"         # Returns float: 30.5
  setting: !var "nullable_setting" # Returns null

# Supports default values with pipe syntax
database:
  host: !var "db_host|localhost"         # String default
  port: !var "db_port|5432"              # Integer default
  ssl: !var "db_ssl|true"                # Boolean default

# Supports nested variable access with dot notation
config:
  db_host: !var "database.host"
  first_service: !var "services.0.name"
```

#### `!expand 'text with {{variables}}'`
String expansion with variable substitution. Always returns strings with template processing.

```yaml
__vars:
  service_name: "user-api"
  environment: !env ['ENVIRONMENT', 'dev']
  version: !env ['VERSION', '1.0.0']
  port: 8080                      # integer

# String template expansion (always returns strings)
app_title: !expand "{{service_name}} v{{version}}"     # Returns: "user-api v1.0.0"
api_endpoint: !expand "https://{{service_name}}-{{environment}}.example.com"
connection_string: !expand "postgresql://{{db_host}}/{{service_name}}_{{environment}}"
port_string: !expand "{{port}}"                        # Returns: "8080" (string)

# Complex template processing
container_name: !expand "{{service_name}}-{{environment}}-{{version}}"
log_path: !expand "/var/log/{{service_name}}/{{environment}}.log"
```

**Key Differences:**
- **`!var "port"`** → `8080` (integer preserved)
- **`!expand "{{port}}"`** → `"8080"` (string result)
- **`!var`** is for direct variable access with type preservation
- **`!expand`** is for string templating with variable substitution

### Conditionals

#### `!if ['ENV_VAR', value]`
Conditional field inclusion.

```yaml
# Include field only if DEBUG is truthy
debug_panel: !if ['DEBUG', {'enabled': true, 'level': 'verbose'}]

# Conditional with complex value
development_tools: !if ['DEVELOPMENT']
  webpack_dev_server: true
  hot_reload: true
  source_maps: true
```

#### `!switch ['ENV_VAR', cases]`
Multi-way conditional based on environment variable value.

```yaml
database: !switch ['DATABASE_TYPE']
  - case: 'postgres'
    driver: 'postgresql+psycopg2'
    port: 5432
    pool_size: 20
  - case: 'mysql'
    driver: 'mysql+pymysql'
    port: 3306
    pool_size: 15
  - case: 'sqlite'
    driver: 'sqlite'
    file: 'app.db'
  - default: 'postgres'
    driver: 'postgresql+psycopg2'
    port: 5432

# Service configuration based on deployment type
deployment: !switch ['DEPLOYMENT']
  - case: 'kubernetes'
    type: 'k8s'
    config: !include_yaml 'k8s/deployment.yaml'
  - case: 'docker'
    type: 'container'
    config: !include_yaml 'docker/compose.yaml'
  - default: 'standalone'
    type: 'process'
    config: !include_yaml 'config/standalone.yaml'
```

## Advanced Examples

### Multi-Service Configuration

```yaml
# services.yaml - Configure multiple services with shared templates
__vars:
  company: "ACME Corp"
  environment: !env ['ENVIRONMENT', 'development']
  version: !env ['VERSION', '1.0.0']

__template:
  use: 'infrastructure.base'

# API Gateway
gateway: !merge
  - !template 'services.api_gateway'
  - name: !expand "{{company}}-gateway"
    version: !expand "{{version}}"
    config:
      upstream_services: !concat
        - !include_yaml 'services/core_services.yaml'
        - !include_yaml_if ['ENABLE_ANALYTICS', 'services/analytics.yaml']

# User Service
user_service: !merge
  - !template 'services.microservice'
  - name: 'user-service'
    database: !switch ['USER_DB_TYPE']
      - case: 'postgres'
        config: !template 'databases.postgres'
      - case: 'mongodb'
        config: !template 'databases.mongodb'
      - default: 'sqlite'
        config: !template 'databases.sqlite'

# Environment-specific overrides
overrides: !include_yaml_if ['PRODUCTION', 'config/production_overrides.yaml']
```

### Configuration with Schema Validation

```yaml
# app_config.yaml - Production application configuration
__version: "1.0.0"

__vars:
  app_name: "ProductionApp"
  environment: "production"
  replica_count: !env ['REPLICAS', 3]

__schema:
  type: object
  properties:
    application:
      type: object
      properties:
        name: {type: string, minLength: 1}
        replicas: {type: integer, minimum: 1, maximum: 100}
        database:
          type: object
          properties:
            host: {type: string}
            port: {type: integer, minimum: 1, maximum: 65535}
            ssl: {type: boolean}
          required: [host, port]
      required: [name, replicas, database]
  required: [application]

application:
  name: !var "app_name"                                    # String variable
  replicas: !var "replica_count"                          # Integer variable (preserves type for schema validation)
  database:
    host: !env ['DB_HOST']  # Required - will fail validation if not set
    port: !env_int ['DB_PORT', 5432]                       # Integer from environment
    ssl: !env_bool ['DB_SSL', true]                        # Boolean from environment
    connection_string: !expand "postgresql://{{database.host}}:{{database.port}}/{{app_name}}"
```

## Configuration API

SmartYAML provides a fluent configuration API:

```python
import smartyaml
from smartyaml.config import SmartYAMLConfigBuilder

# Basic configuration
config = SmartYAMLConfigBuilder().build()

# Development preset
config = SmartYAMLConfigBuilder().development_mode().build()

# Production preset
config = SmartYAMLConfigBuilder().production_mode().build()

# Custom configuration
config = (SmartYAMLConfigBuilder()
          .with_template_path("./templates")
          .with_max_file_size(50 * 1024 * 1024)  # 50MB
          .with_security_options(sandbox_mode=True)
          .with_allowed_env_vars(['APP_*', 'DB_*'])
          .build())

# Use with load functions
data = smartyaml.load("config.yaml", config=config)
```

## Error Handling

SmartYAML provides comprehensive error reporting:

```python
import smartyaml
from smartyaml import (
    SmartYAMLError, VersionMismatchError, FileNotFoundError,
    DirectiveSyntaxError, VariableNotFoundError, SchemaValidationError
)

try:
    data = smartyaml.load("config.yaml")
except VersionMismatchError as e:
    print(f"Version incompatible: {e}")
except FileNotFoundError as e:
    print(f"Missing file: {e}")
except DirectiveSyntaxError as e:
    print(f"Invalid directive syntax: {e}")
except SchemaValidationError as e:
    print(f"Schema validation failed: {e}")
except SmartYAMLError as e:
    print(f"SmartYAML error: {e}")
```

All errors include:
- **File context**: Which file caused the error
- **Field context**: Which field/path in the YAML
- **Operation context**: What operation was being performed
- **Detailed messages**: Clear explanation of the issue

## Security Considerations

SmartYAML implements multiple security layers:

### Safe Defaults
- **File size limits**: 10MB default (configurable)
- **Recursion limits**: 20 levels max (configurable)
- **Path validation**: Prevents directory traversal
- **No code execution**: Only safe YAML parsing

### Environment Variable Controls
```python
# Whitelist specific variables
config = SmartYAMLConfigBuilder().with_allowed_env_vars([
    'APP_NAME', 'DB_HOST', 'API_*'
]).build()

# Blacklist sensitive variables
config = SmartYAMLConfigBuilder().with_forbidden_env_vars([
    'SECRET_KEY', 'PRIVATE_KEY', '*_PASSWORD'
]).build()
```

### Sandbox Mode
```python
# Restricts file access and environment variables
config = SmartYAMLConfigBuilder().with_security_options(
    sandbox_mode=True,
    strict_security=True
).build()
```

## Development

### Testing
```bash
python -m pytest                    # Run all tests (230+)
python -m pytest --cov=smartyaml    # Run with coverage
python -m pytest -v                 # Verbose output
```

### Code Quality
```bash
black smartyaml/          # Format code
isort smartyaml/          # Sort imports
flake8 smartyaml/         # Lint code
mypy smartyaml/           # Type check
```

### Building
```bash
python -m build          # Build packages
pip install -e ".[dev]"  # Development install
```

## Requirements

- **Python**: 3.9+ (3.7+ for basic usage)
- **Dependencies**: PyYAML 5.1+, minimal external dependencies
- **Optional**: jsonschema for schema validation

## Compatibility

SmartYAML files are valid YAML files. Standard YAML parsers will treat custom directives as regular tagged values, making the format backward-compatible.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

---

**SmartYAML**: Making YAML configurations smarter, more powerful, and easier to maintain.
