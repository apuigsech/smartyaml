# SmartYAML Examples

This directory contains comprehensive examples demonstrating all features of SmartYAML, from basic usage to advanced real-world configurations.

## Getting Started

To run these examples, you'll need to install SmartYAML:

```bash
pip install pysmartyaml
```

Then you can load any example:

```python
import smartyaml

# Basic example
data = smartyaml.load('examples/basic/simple_config.yaml')
print(data)

# Example with templates
data = smartyaml.load('examples/templates/base_template.yaml',
                     template_path='examples/templates')
print(data)
```

## Example Categories

### 📁 [basic/](basic/)
Fundamental SmartYAML concepts and simple usage patterns.

**What you'll learn:**
- Basic YAML processing without special features
- Variable definition and substitution with `__vars` and `!expand`
- JSON Schema validation with `__schema`
- Version compatibility with `__version`

**Examples:**
- `simple_config.yaml` - Plain YAML configuration
- `variables_example.yaml` - Variable substitution basics
- `schema_validation.yaml` - Schema validation example

### 📁 [environment/](environment/)
Environment variable integration for dynamic configuration.

**What you'll learn:**
- String environment variables with `!env`
- Typed environment variables (`!env_int`, `!env_float`, `!env_bool`)
- Secret handling with `!secret`
- Combining environment variables with SmartYAML variables

**Examples:**
- `basic_env.yaml` - Basic environment variable usage
- `typed_env.yaml` - Type conversion examples
- `env_with_variables.yaml` - Complex environment integration

### 📁 [conditionals/](conditionals/)
Dynamic configuration based on conditions and environment.

**What you'll learn:**
- Simple conditions with `!if`
- Multi-way branching with `!switch`
- Nested conditional logic
- Feature flags and environment-specific configuration

**Examples:**
- `if_conditions.yaml` - Basic conditional inclusion
- `switch_conditions.yaml` - Multi-way conditional logic
- `nested_conditions.yaml` - Complex nested conditions

### 📁 [file_operations/](file_operations/)
File inclusion and external content integration.

**What you'll learn:**
- File inclusion with `!include`
- Conditional file inclusion with `!include_if`
- Raw YAML inclusion with `!include_yaml`
- Mixed content types (SQL, Markdown, JSON)

**Examples:**
- `basic_include.yaml` - Basic file inclusion
- `conditional_include.yaml` - Conditional file loading
- Supporting files in `configs/`, `data/`, and `sql/` directories

### 📁 [templates/](templates/)
Template inheritance and reusable configuration patterns.

**What you'll learn:**
- Template inheritance with `__template`
- Template loading with `!template`
- Overlay vs. replacement modes
- Building reusable configuration libraries

**Examples:**
- `base_template.yaml` - Template inheritance
- `template_use_example.yaml` - Template loading with dot notation
- Template library in `base/`, `services/`, and `databases/` directories

### 📁 [data_operations/](data_operations/)
Data manipulation and transformation directives.

**What you'll learn:**
- Object merging with `!merge`
- Array concatenation with `!concat`
- String interpolation with `!expand`
- Complex data composition patterns

**Examples:**
- `merge_example.yaml` - Object and array merging
- `concat_example.yaml` - Array concatenation patterns
- `expand_example.yaml` - String interpolation and templating

### 📁 [integration/](integration/)
Real-world configuration examples combining multiple features.

**What you'll learn:**
- Complete microservice configuration
- Production-ready configuration patterns
- Multi-feature integration
- Best practices for complex configurations

**Examples:**
- `microservice_config.yaml` - Complete microservice setup

### 📁 [advanced/](advanced/)
Advanced patterns and enterprise-level configuration management.

**What you'll learn:**
- Multi-environment configuration strategies
- Large-scale configuration management
- Performance optimization techniques
- Enterprise deployment patterns

**Examples:**
- `multi_environment.yaml` - Cross-environment configuration

## Quick Start Examples

### Basic Variable Substitution
```yaml
__vars:
  app_name: "my-app"
  version: "1.0.0"

application:
  name: !expand "{{app_name}}"
  full_title: !expand "{{app_name}} v{{version}}"
```

### Environment-Based Configuration
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

### Template Inheritance
```yaml
__template:
  use: 'services.microservice'
  overlay: true

service:
  name: "my-service"
  port: 3000
```

### Conditional Features
```yaml
features:
  analytics: !if ['ENABLE_ANALYTICS']
    provider: "google-analytics"
    tracking_id: "GA-XXXXX-X"

  monitoring: !if ['PRODUCTION']
    enabled: true
    detailed_metrics: true
```

## Testing Examples

Many examples can be tested with different environment variables:

```bash
# Test environment-based configuration
export ENVIRONMENT="production"
export DATABASE_TYPE="postgres"
export ENABLE_ANALYTICS="true"

python -c "
import smartyaml
data = smartyaml.load('examples/conditionals/switch_conditions.yaml')
print(f'Database: {data[\"database\"][\"type\"]}')
print(f'Environment: {data[\"logging\"][\"level\"]}')
"
```

## Common Patterns

### Configuration Composition
```yaml
final_config: !merge
  - !include 'config/base.yaml'
  - !include 'config/{{environment}}.yaml'
  - runtime_overrides: !env ['RUNTIME_CONFIG', '{}']
```

### Dynamic Resource Naming
```yaml
__vars:
  app: "user-service"
  env: !env ['ENVIRONMENT', 'dev']

resources:
  s3_bucket: !expand "{{app}}-{{env}}-data"
  db_name: !expand "{{app}}_{{env}}_db"
  lambda_function: !expand "{{app}}-{{env}}-api"
```

### Feature Flag Management
```yaml
features: !merge
  - # Always enabled
    logging: true
    health_checks: true

  - # Conditionally enabled
    analytics: !if ['ENABLE_ANALYTICS', true]
    monitoring: !if ['PRODUCTION', true]
    debug_tools: !if ['DEVELOPMENT', true]
```

## Best Practices Demonstrated

1. **Organize by concerns**: Group related examples in focused directories
2. **Use meaningful variable names**: Clear, descriptive variable naming
3. **Provide defaults**: Always include sensible default values
4. **Document environment variables**: Clear documentation of required variables
5. **Validate with schemas**: Use JSON Schema for critical configurations
6. **Test all paths**: Ensure all conditional branches work correctly
7. **Keep templates focused**: Single-responsibility templates
8. **Use consistent naming**: Follow naming conventions across configurations

## Error Handling Examples

See individual example READMEs for common error scenarios and solutions:

- Type conflicts in merge operations
- Missing variables in expand operations
- Invalid environment variable types
- Circular dependencies in includes
- Schema validation failures

## Performance Considerations

- Use caching for repeated file processing
- Minimize deep nesting in conditionals
- Optimize template inheritance chains
- Consider file sizes for large configurations
- Profile complex configurations for bottlenecks

## Contributing

When adding new examples:

1. Follow the existing directory structure
2. Include comprehensive README documentation
3. Provide multiple test scenarios with environment variables
4. Add error handling examples
5. Include performance notes where relevant
6. Test examples with different SmartYAML configurations

---

**Need Help?**

- Check the [main SmartYAML documentation](../README.md)
- Review the [architecture document](../ARCHITECTURE.md)
- Look at the [test cases](../tests/) for additional examples
- Open an issue for specific use case questions
