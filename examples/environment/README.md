# Environment Variable Examples

This folder demonstrates SmartYAML's environment variable integration capabilities.

## Examples

### `basic_env.yaml`
Shows basic environment variable usage with string values and defaults.

**Features:**
- `!env` directive for string environment variables
- `!secret` directive for sensitive environment variables
- Default values when environment variables are not set

**Test with environment variables:**
```bash
export APP_NAME="MyCustomApp"
export ENVIRONMENT="production"
export DB_HOST="prod-db.example.com"
export API_KEY="prod-api-key-xyz"
```

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/environment/basic_env.yaml')
print(f"App: {data['app']['name']}")
print(f"Environment: {data['app']['environment']}")
print(f"DB Host: {data['database']['host']}")
```

### `typed_env.yaml`
Demonstrates type conversion for environment variables.

**Features:**
- `!env_int` for integer conversion
- `!env_float` for floating-point conversion
- `!env_bool` for boolean conversion
- Automatic type validation and error handling

**Test with typed environment variables:**
```bash
export PORT="3000"
export WORKERS="8"
export CPU_LIMIT="2.5"
export DEBUG="true"
export SSL_ENABLED="false"
```

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/environment/typed_env.yaml')
print(f"Port: {data['server']['port']} (type: {type(data['server']['port'])})")
print(f"CPU Limit: {data['performance']['cpu_limit']} (type: {type(data['performance']['cpu_limit'])})")
print(f"Debug: {data['features']['debug_mode']} (type: {type(data['features']['debug_mode'])})")
```

### `env_with_variables.yaml`
Shows how to combine environment variables with SmartYAML variables for complex configurations.

**Features:**
- Environment variables stored in `__vars`
- Variable expansion using environment-based values
- Complex string composition with multiple variables
- Conditional configuration based on environment

**Test with comprehensive environment:**
```bash
export APP_NAME="payment-service"
export ENVIRONMENT="staging"
export AWS_REGION="us-west-2"
export CLUSTER_NAME="staging-cluster"
export APP_VERSION="2.1.0"
export BUILD_ID="build-456"
export DB_HOST="staging-db.internal"
export LOG_LEVEL="DEBUG"
export TRACING_ENABLED="true"
```

**Run:**
```python
import smartyaml
data = smartyaml.load('examples/environment/env_with_variables.yaml')
print(f"Full Name: {data['application']['full_name']}")
print(f"S3 Bucket: {data['aws']['s3_bucket']}")
print(f"Database Name: {data['database']['name']}")
print(f"Kubernetes Namespace: {data['kubernetes']['namespace']}")
```

## Environment Variable Types

### String Variables (`!env`)
- Always return strings
- Useful for URLs, names, paths, and text configuration

### Integer Variables (`!env_int`)
- Convert environment variable to integer
- Raise error if conversion fails
- Perfect for ports, counts, timeouts

### Float Variables (`!env_float`)
- Convert environment variable to floating-point number
- Useful for ratios, percentages, decimal values

### Boolean Variables (`!env_bool`)
- Convert environment variable to boolean
- Truthy values: `true`, `yes`, `1`, `on`, `enabled` (case-insensitive)
- Falsy values: `false`, `no`, `0`, `off`, `disabled`, empty string

### Secret Variables (`!secret`)
- Same as `!env` but semantically different
- Intended for sensitive data like passwords and API keys
- May integrate with secret management systems in future versions

## Best Practices

1. **Always provide defaults** for non-critical environment variables
2. **Use appropriate types** (`!env_int`, `!env_float`, `!env_bool`) for better validation
3. **Use `!secret`** for sensitive data to improve security visibility
4. **Combine with variables** for complex configuration patterns
5. **Document required environment variables** in your application README
