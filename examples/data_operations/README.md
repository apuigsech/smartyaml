# Data Operations Examples

This folder demonstrates SmartYAML's data manipulation capabilities using `!merge`, `!concat`, and `!expand` directives.

## Examples

### `merge_example.yaml`
Shows how to merge multiple data structures using the `!merge` directive.

**Features:**
- Basic object merging
- Merging with file inclusion
- Conditional merging with environment switches
- Complex nested merging
- Template merging with overrides

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/data_operations/merge_example.yaml')
print("Basic merge result:", data['basic_merge'])
print("API config host:", data['api_config']['host'])
print("Service config replicas:", data['service_config']['replicas'])
```

**Test with environment variables:**
```bash
export ENVIRONMENT="production"
export ENABLE_METRICS="true"
export DEPLOYMENT_TYPE="kubernetes"
export REPLICAS="5"
```

### `concat_example.yaml`
Demonstrates array concatenation using the `!concat` directive.

**Features:**
- Basic array concatenation
- Conditional array building
- Middleware stack construction
- API endpoint aggregation
- Service dependency management

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/data_operations/concat_example.yaml')
print("Basic concat:", data['basic_concat'])
print("Middleware stack:", data['middleware_stack'])
print("Number of API endpoints:", len(data['api_endpoints']))
```

**Test with environment variables:**
```bash
export ENVIRONMENT="production"
export ENABLE_AUTH="true"
export ADMIN_FEATURES="true"
export ENABLE_ANALYTICS="true"
export SSL_ENABLED="true"
```

### `expand_example.yaml`
Shows string interpolation and variable expansion using the `!expand` directive.

**Features:**
- Basic variable substitution
- URL and connection string construction
- Resource naming patterns
- Complex nested expansion
- Environment-specific string building

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/data_operations/expand_example.yaml')
print("Application name:", data['application']['name'])
print("API URL:", data['application']['api_url'])
print("Database URL:", data['database']['postgres_url'])
print("S3 bucket:", data['aws_resources']['data_bucket'])
```

**Test with environment variables:**
```bash
export ENVIRONMENT="staging"
export AWS_REGION="us-west-2"
export DB_HOST="staging-db.internal"
export DB_PORT="5432"
```

## Data Operation Directives

### `!merge` Directive

Combines multiple objects or arrays into a single structure.

**Syntax:**
```yaml
result: !merge
  - object1
  - object2
  - object3
```

**Behavior:**
- **Objects**: Deep merge with right-hand precedence (later objects override earlier ones)
- **Arrays**: Concatenation of all arrays
- **Conflicts**: Later values override earlier values for the same key
- **Nested**: Recursive merging for nested objects

**Examples:**
```yaml
# Basic object merge
config: !merge
  - host: "localhost"
    port: 8080
  - port: 3000  # Overrides port to 3000
    ssl: true

# Merge with file inclusion
full_config: !merge
  - !include 'base_config.yaml'
  - !include 'environment_overrides.yaml'
  - debug: true  # Additional override
```

### `!concat` Directive

Combines multiple arrays into a single array.

**Syntax:**
```yaml
result: !concat
  - [item1, item2]
  - [item3, item4]
  - [item5]
```

**Behavior:**
- **Preserves order**: Items appear in the order they are concatenated
- **Flattens arrays**: Nested arrays are flattened one level
- **Mixed types**: Can concatenate arrays of different types
- **Conditional**: Works with conditional directives

**Examples:**
```yaml
# Basic array concatenation
all_items: !concat
  - ["apple", "banana"]
  - ["cherry", "date"]
  # Result: ["apple", "banana", "cherry", "date"]

# Conditional concatenation
middleware: !concat
  - ["cors", "helmet"]  # Always included
  - !if ['DEBUG', ["logger", "dev-tools"]]  # Conditional
  - ["router"]  # Always last
```

### `!expand` Directive

Performs string interpolation using variables.

**Syntax:**
```yaml
result: !expand "Template string with {{variable}} substitution"
```

**Features:**
- **Variable substitution**: `{{variable_name}}` syntax
- **Nested variables**: Access nested object properties with dot notation
- **Default values**: `{{variable|default_value}}` (if supported)
- **Environment integration**: Works with environment variables in `__vars`

**Examples:**
```yaml
__vars:
  app_name: "myapp"
  environment: "production"
  version: "1.0.0"

# Basic expansion
service_name: !expand "{{app_name}}-{{environment}}"
# Result: "myapp-production"

# URL construction
api_url: !expand "https://api.{{environment}}.example.com/{{app_name}}/v1"
# Result: "https://api.production.example.com/myapp/v1"

# Complex naming
container_name: !expand "{{app_name}}-{{environment}}-v{{version}}"
# Result: "myapp-production-v1.0.0"
```

## Common Patterns

### Configuration Composition
```yaml
# Combine base config with environment overrides
final_config: !merge
  - !include 'config/base.yaml'
  - !include 'config/{{environment}}.yaml'
  - runtime_overrides: !env ['RUNTIME_CONFIG', '{}']
```

### Middleware Stack Building
```yaml
# Build middleware stack with conditional components
middleware: !concat
  - ["cors", "helmet"]  # Security (always first)
  - !if ['AUTH_ENABLED', ["auth", "session"]]
  - !if ['DEBUG', ["logger", "dev-tools"]]
  - !switch ['ENVIRONMENT']
    - case: 'production'
      ["rate-limiter", "ddos-protection"]
    - case: 'development'
      ["hot-reload", "error-handler"]
  - ["body-parser", "router"]  # Core (always last)
```

### Resource Naming
```yaml
__vars:
  app: "user-service"
  env: "staging"
  region: "us-west-2"

resources:
  s3_bucket: !expand "{{app}}-{{env}}-data-{{region}}"
  db_name: !expand "{{app}}_{{env}}_db"
  lambda_function: !expand "{{app}}-{{env}}-api"
  log_group: !expand "/aws/lambda/{{app}}-{{env}}"
```

### API Endpoint Aggregation
```yaml
all_endpoints: !concat
  - !include 'api/public_endpoints.yaml'
  - !include 'api/user_endpoints.yaml'
  - !if ['ADMIN_ENABLED', !include 'api/admin_endpoints.yaml']
  - !if ['ANALYTICS', !include 'api/analytics_endpoints.yaml']
```

## Best Practices

### For `!merge`
1. **Order matters**: Place more specific configurations after general ones
2. **Use with includes**: Merge base configurations with environment-specific overrides
3. **Validate types**: Ensure you're merging compatible data types
4. **Document precedence**: Make it clear which values override others

### For `!concat`
1. **Maintain order**: Be intentional about the sequence of array elements
2. **Group logically**: Keep related items together in the concatenation
3. **Use conditionals**: Build arrays dynamically based on feature flags
4. **Consider performance**: Large arrays may impact processing time

### For `!expand`
1. **Define variables early**: Ensure all variables are available in `__vars`
2. **Use meaningful names**: Choose descriptive variable names
3. **Validate expansions**: Ensure all variable references are valid
4. **Escape when needed**: Be careful with special characters in templates
5. **Document variables**: Clearly document required variables and their formats

## Error Handling

Common issues and solutions:

### Type Conflicts in Merge
```yaml
# This will cause an error - can't merge string with object
bad_merge: !merge
  - "string value"
  - {key: "object value"}

# Solution: Ensure compatible types
good_merge: !merge
  - {value: "string value"}
  - {key: "object value"}
```

### Missing Variables in Expand
```yaml
# This will fail if 'missing_var' is not defined
bad_expand: !expand "{{missing_var}}"

# Solution: Define variable or provide default
__vars:
  missing_var: "default_value"
```

### Non-Array Concatenation
```yaml
# This will cause an error - can't concatenate non-arrays
bad_concat: !concat
  - "not an array"
  - ["array", "items"]

# Solution: Ensure all items are arrays
good_concat: !concat
  - ["converted", "to", "array"]
  - ["array", "items"]
```
