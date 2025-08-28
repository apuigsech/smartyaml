# Schema Composition Examples

This folder demonstrates various ways to compose and load JSON Schema definitions using SmartYAML's `__schema` metadata field with external files.

## Overview

SmartYAML allows you to build complex schema validation by:
- Loading complete schemas from external files
- Composing schemas by merging multiple schema files  
- Conditionally loading schemas based on environment variables
- Using complex logic with switch statements for schema selection

## Examples

### Example 1: Simple Single Schema File (`1_simple_schema.yaml`)

The most basic approach - loading a complete schema from one external file.

```yaml
__schema: !include_yaml 'schemas/simple_app_schema.yaml'
```

**Features:**
- Single schema file import
- Complete schema definition in external file
- Simple and clean approach for basic validation needs

**Run:**
```bash
python cli.py examples/schema_examples/1_simple_schema.yaml
```

### Example 2: Composed Schema (`2_composed_schema.yaml`)

Building a complex schema by merging multiple schema files for modular schema management.

```yaml
__schema: !merge
  - !include_yaml 'schemas/base_schema.yaml'
  - properties: !merge
      - !include_yaml 'schemas/app_properties.yaml'
      - !include_yaml 'schemas/database_properties.yaml'
      - !include_yaml 'schemas/monitoring_properties.yaml'
  - !include_yaml 'schemas/required_fields.yaml'
```

**Features:**
- Modular schema files for different concerns
- Reusable schema components
- Complex property composition
- Centralized required field management

**Run:**
```bash
python cli.py examples/schema_examples/2_composed_schema.yaml
```

### Example 3: Environment-Based Schema (`3_environment_schema.yaml`)

Loading different schema constraints based on environment using conditional directives.

```yaml
__schema: !merge
  - !include_yaml 'schemas/core_schema.yaml'
  - !include_yaml_if ['DEVELOPMENT', 'schemas/development_constraints.yaml']
  - !include_yaml_if ['PRODUCTION', 'schemas/production_constraints.yaml']
```

**Features:**
- Core schema with environment-specific overlays
- Conditional schema loading based on environment variables
- Different validation rules for development vs production
- Security constraints enforced in production

**Run with environment variables:**
```bash
# Development mode
ENVIRONMENT=development python cli.py examples/schema_examples/3_environment_schema.yaml

# Production mode  
ENVIRONMENT=production PRODUCTION=true python cli.py examples/schema_examples/3_environment_schema.yaml
```

### Example 4: Advanced Schema with Switch (`4_advanced_schema.yaml`)

Complex schema selection based on deployment type using switch logic.

```yaml
__schema: !merge
  - !include_yaml 'schemas/core_schema.yaml'
  - !switch ['DEPLOYMENT_TYPE']
    - case: 'microservice'
      schema: !include_yaml 'schemas/microservice_schema.yaml'
    - case: 'monolith' 
      schema: !include_yaml 'schemas/monolith_schema.yaml'
    - case: 'serverless'
      schema: !include_yaml 'schemas/serverless_schema.yaml'
```

**Features:**
- Multi-way schema selection
- Deployment-type specific validation
- Complex validation rules for different architectures
- Comprehensive schema coverage

**Run with different deployment types:**
```bash
# Microservice deployment
DEPLOYMENT_TYPE=microservice python cli.py examples/schema_examples/4_advanced_schema.yaml

# Monolithic deployment
DEPLOYMENT_TYPE=monolith python cli.py examples/schema_examples/4_advanced_schema.yaml

# Serverless deployment  
DEPLOYMENT_TYPE=serverless python cli.py examples/schema_examples/4_advanced_schema.yaml
```

## Schema Files Structure

```
schemas/
├── simple_app_schema.yaml      # Complete schema for basic app
├── base_schema.yaml            # JSON Schema base structure
├── core_schema.yaml            # Common validation rules
├── app_properties.yaml         # Application-specific properties
├── database_properties.yaml    # Database validation rules
├── monitoring_properties.yaml  # Monitoring/observability rules  
├── required_fields.yaml        # Required field specifications
├── development_constraints.yaml # Development environment rules
├── production_constraints.yaml  # Production environment rules
├── microservice_schema.yaml    # Microservice deployment rules
├── monolith_schema.yaml        # Monolithic deployment rules
└── serverless_schema.yaml      # Serverless deployment rules
```

## Key Benefits

### 1. **Modularity**
Break complex schemas into focused, reusable components:
- Application properties
- Database constraints  
- Environment-specific rules
- Deployment-type validation

### 2. **Reusability**
Share schema components across multiple configurations:
- Common base schemas
- Standard property definitions
- Environment constraint sets

### 3. **Maintainability** 
Easier to maintain and update schemas:
- Single source of truth for each concern
- Clear separation of validation logic
- Version control friendly

### 4. **Flexibility**
Adapt validation based on runtime conditions:
- Environment-specific constraints
- Deployment-type specific rules
- Feature flag driven validation

### 5. **Composition**
Build complex schemas from simple parts:
- Merge multiple schema files
- Override specific constraints
- Add environment-specific requirements

## Best Practices

1. **Start Simple**: Begin with single schema files, then compose as needed
2. **Organize by Concern**: Group related validation rules in separate files
3. **Use Descriptive Names**: Make schema file purposes clear from names
4. **Environment Separation**: Keep environment-specific rules in separate files
5. **Version Schemas**: Consider versioning schema files for compatibility
6. **Test Thoroughly**: Validate configurations against schemas in different environments
7. **Document Rules**: Include comments in schema files explaining complex rules

## Common Patterns

### Base + Overlay Pattern
```yaml
__schema: !merge
  - !include_yaml 'schemas/base.yaml'
  - !include_yaml 'schemas/environment_overlay.yaml'
```

### Conditional Loading Pattern  
```yaml
__schema: !merge
  - !include_yaml 'schemas/core.yaml'
  - !include_yaml_if ['FEATURE_ENABLED', 'schemas/feature.yaml']
```

### Switch Selection Pattern
```yaml
__schema: !switch ['DEPLOYMENT_TYPE']
  - case: 'k8s': !include_yaml 'schemas/kubernetes.yaml'
  - case: 'docker': !include_yaml 'schemas/docker.yaml' 
  - default: !include_yaml 'schemas/standalone.yaml'
```

### Property Composition Pattern
```yaml
__schema:
  type: object
  properties: !merge
    - !include_yaml 'schemas/app_props.yaml'
    - !include_yaml 'schemas/db_props.yaml'
  required: !concat
    - !include_yaml 'schemas/core_required.yaml'  
    - !include_yaml 'schemas/env_required.yaml'
```

This approach provides powerful, flexible schema validation that adapts to your application's needs while maintaining clean, modular schema definitions.