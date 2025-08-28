# Conditional Processing Examples

This folder demonstrates SmartYAML's conditional processing capabilities using `!if` and `!switch` directives.

## Examples

### `if_conditions.yaml`
Shows how to use `!if` for simple conditional inclusion of configuration sections.

**Features:**
- Basic `!if` conditions based on environment variables
- Conditional feature flags
- Environment-specific configuration
- Nested conditional structures

**Test with environment variables:**
```bash
export DEBUG="true"
export PRODUCTION="true"
export SSL_ENABLED="true"
export ENABLE_ANALYTICS="true"
export ENABLE_MONITORING="true"
```

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/conditionals/if_conditions.yaml')
print("Included sections:")
if 'debug_config' in data['app']:
    print("- Debug configuration")
if 'ssl' in data['app']:
    print("- SSL configuration")
if 'analytics' in data['features']:
    print("- Analytics")
```

### `switch_conditions.yaml`
Demonstrates multi-way conditional logic using `!switch` for complex configuration scenarios.

**Features:**
- Database selection based on type
- Deployment platform configuration
- Tiered service configurations
- Environment-specific logging

**Test with environment variables:**
```bash
export DATABASE_TYPE="postgres"
export DEPLOYMENT_PLATFORM="kubernetes"
export SCALE_TIER="professional"
export LOG_ENVIRONMENT="production"
export MONITORING_TIER="full"
```

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/conditionals/switch_conditions.yaml')
print(f"Database: {data['database']['type']}")
print(f"Deployment: {data['deployment']['type']}")
print(f"Caching: {data['caching']['provider']}")
print(f"Log Level: {data['logging']['level']}")
```

### `nested_conditions.yaml`
Shows complex nested conditional logic for sophisticated configuration management.

**Features:**
- Nested `!if` and `!switch` combinations
- Multi-level conditional hierarchies
- Environment and feature-based configuration trees
- Complex dependency management

**Test with comprehensive environment:**
```bash
export ENVIRONMENT="production"
export PRODUCTION_FEATURES="true"
export ENABLE_AUTO_SCALING="true"
export BACKUP_STRATEGY="comprehensive"
export ENHANCED_SECURITY="true"
export NETWORK_SETUP="vpc"
export DATABASE_ENVIRONMENT="production"
export DB_PROVIDER="aws"
export DB_SIZE="large"
export HA_ENABLED="true"
export READ_REPLICA_COUNT="3"
export ENABLE_MONITORING="true"
export MONITORING_TIER="enterprise"
export ADVANCED_ALERTING="true"
export PERFORMANCE_MONITORING="true"
```

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/conditionals/nested_conditions.yaml')
print(f"Environment: {data['application']['environment_config']['tier']}")
if 'features' in data['application']['environment_config']:
    print("Production features enabled")
if 'auto_scaling' in data['application']['environment_config']['features']:
    print(f"Auto-scaling: {data['application']['environment_config']['features']['auto_scaling']['enabled']}")
```

## Conditional Directives

### `!if` Directive

**Syntax:** `!if ['ENV_VAR', value_if_true]` or `!if ['ENV_VAR'] { configuration }`

**Behavior:**
- Includes the configuration block if the environment variable is truthy
- Truthy values: `true`, `yes`, `1`, `on`, `enabled` (case-insensitive)
- If the environment variable is not set or falsy, the entire block is omitted

**Examples:**
```yaml
# Simple conditional value
debug_mode: !if ['DEBUG', true]

# Conditional configuration block
ssl_config: !if ['SSL_ENABLED']
  cert_path: "/etc/ssl/cert.pem"
  key_path: "/etc/ssl/key.pem"
```

### `!switch` Directive

**Syntax:** `!switch ['ENV_VAR'] [cases]`

**Structure:**
```yaml
field: !switch ['ENV_VAR']
  - case: 'value1'
    config: for_value1
  - case: 'value2'
    config: for_value2
  - default: 'fallback_value'
    config: for_default
```

**Behavior:**
- Matches the environment variable value against case values
- Returns the configuration for the first matching case
- Uses the `default` case if no matches are found
- If no default and no matches, the field is omitted

## Use Cases

### Feature Flags
```yaml
features:
  analytics: !if ['ENABLE_ANALYTICS']
    provider: "google-analytics"
    tracking_id: "GA-XXXXX-X"
```

### Environment-Specific Configuration
```yaml
database: !switch ['ENVIRONMENT']
  - case: 'production'
    host: "prod-db.example.com"
    pool_size: 50
  - case: 'staging'
    host: "staging-db.example.com"
    pool_size: 20
  - default: 'development'
    host: "localhost"
    pool_size: 5
```

### Progressive Feature Enablement
```yaml
monitoring: !switch ['MONITORING_TIER']
  - case: 'full'
    metrics: true
    tracing: true
    alerts: true
  - case: 'basic'
    metrics: true
    health_checks: true
  - default: 'minimal'
    health_checks: true
```

## Best Practices

1. **Use meaningful environment variable names** that clearly indicate their purpose
2. **Provide sensible defaults** in switch statements for robustness
3. **Nest conditions logically** to avoid deep nesting where possible
4. **Document required environment variables** for each conditional path
5. **Test all conditional branches** to ensure they work as expected
6. **Use `!if` for binary choices** and `!switch` for multiple options
