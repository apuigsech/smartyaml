"""
Tests for inline template functionality (__template directive).
"""

import os
import tempfile
from pathlib import Path

import pytest

import smartyaml
from smartyaml.exceptions import ConstructorError


class TestInlineTemplate:
    """Test cases for __template directive functionality."""
    
    def test_basic_inline_template(self):
        """Test basic __template functionality with simple merge."""
        yaml_content = """
__template:
  field_1: "1"
  field_2: "2"
  field_3:
    field_3_1: "3_1"
    field_3_2: "3_2"

field_4: "4"
field_3:
  field_3_2: "new 3_2"
"""
        
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "field_1": "1",
            "field_2": "2", 
            "field_3": {
                "field_3_1": "3_1",
                "field_3_2": "new 3_2"  # Override from document
            },
            "field_4": "4"
        }
        
        assert result == expected
    
    def test_template_with_smartyaml_directives(self):
        """Test __template containing SmartYAML directives."""
        yaml_content = """
__vars:
  env: "test"
  port: 8080

__template:
  environment: !expand "{{env}}"
  server:
    port: !expand "{{port}}"
    host: "localhost"
  features:
    - logging
    - metrics

# Override specific fields
server:
  host: "0.0.0.0"
  ssl: true
features:
  - logging
  - metrics
  - security
"""
        
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "environment": "test",
            "server": {
                "port": "8080",     # Note: expansion converts to string
                "host": "0.0.0.0",  # Override
                "ssl": True         # New field
            },
            "features": ["logging", "metrics", "security"]  # Complete override
        }
        
        assert result == expected
    
    def test_template_with_import_yaml(self):
        """Test __template with !import_yaml directive."""
        # Create temporary file with base config in the current directory
        temp_filename = "test_base_config.yaml"
        temp_file_path = Path(temp_filename)
        
        try:
            # Write config to local file
            with open(temp_file_path, 'w') as f:
                f.write("""
database:
  host: "localhost"
  port: 5432
cache:
  redis_host: "localhost"
  redis_port: 6379
""")
            
            yaml_content = f"""
__template:
  base_config: !import_yaml "{temp_filename}"
  app_name: "TestApp"
  
# Override database host
base_config:
  database:
    host: "prod-db.example.com"
"""
            
            result = smartyaml.loads(yaml_content)
            
            assert result["app_name"] == "TestApp"
            assert result["base_config"]["database"]["host"] == "prod-db.example.com"
            assert result["base_config"]["database"]["port"] == 5432
            assert result["base_config"]["cache"]["redis_host"] == "localhost"
            
        finally:
            # Clean up
            if temp_file_path.exists():
                temp_file_path.unlink()
    
    def test_nested_template_inheritance(self):
        """Test multiple levels of template inheritance."""
        yaml_content = """
__template:
  level_1:
    field_a: "a1"
    field_b: "b1"
    nested:
      deep_field_1: "deep1"
      deep_field_2: "deep2"
  level_2:
    field_x: "x1"

level_1:
  field_b: "b_override"
  nested:
    deep_field_2: "deep2_override"
    deep_field_3: "deep3_new"
  field_c: "c_new"
"""
        
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "level_1": {
                "field_a": "a1",                      # From template
                "field_b": "b_override",              # Override
                "field_c": "c_new",                   # New field
                "nested": {
                    "deep_field_1": "deep1",          # From template
                    "deep_field_2": "deep2_override", # Override
                    "deep_field_3": "deep3_new"       # New field
                }
            },
            "level_2": {
                "field_x": "x1"                      # From template
            }
        }
        
        assert result == expected
    
    def test_template_with_arrays(self):
        """Test template behavior with arrays (complete replacement)."""
        yaml_content = """
__template:
  services:
    - web
    - db
  ports:
    - 80
    - 443
  config:
    features:
      - feature1
      - feature2

# Override arrays (complete replacement)
services:
  - web
  - api
  - cache
config:
  features:
    - feature1
    - feature3
    - feature4
"""
        
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "services": ["web", "api", "cache"],                 # Complete override
            "ports": [80, 443],                                  # From template
            "config": {
                "features": ["feature1", "feature3", "feature4"]  # Complete override
            }
        }
        
        assert result == expected
    
    def test_template_with_variables(self):
        """Test __template with variable expansion."""
        yaml_content = """
__vars:
  app_name: "MyApp"
  version: "1.0.0"
  environment: "production"

__template:
  metadata:
    name: !expand "{{app_name}}"
    version: !expand "{{version}}"
    environment: !expand "{{environment}}"
  defaults:
    timeout: 30
    retries: 3

# Override specific values
metadata:
  environment: "staging"
defaults:
  timeout: 60
"""
        
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "metadata": {
                "name": "MyApp",
                "version": "1.0.0",
                "environment": "staging"  # Override
            },
            "defaults": {
                "timeout": 60,           # Override
                "retries": 3            # From template
            }
        }
        
        assert result == expected
    
    def test_empty_template(self):
        """Test behavior with empty __template."""
        yaml_content = """
__template: {}

field_1: "value1"
field_2: "value2"
"""
        
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "field_1": "value1",
            "field_2": "value2"
        }
        
        assert result == expected
    
    def test_template_only_document(self):
        """Test document with only __template (no overrides)."""
        yaml_content = """
__template:
  database:
    host: "localhost"
    port: 5432
  cache:
    enabled: true
"""
        
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "cache": {
                "enabled": True
            }
        }
        
        assert result == expected
    
    def test_null_template_error(self):
        """Test error handling for null __template."""
        yaml_content = """
__template: null
field_1: "value1"
"""
        
        with pytest.raises(ConstructorError) as exc_info:
            smartyaml.loads(yaml_content)
        
        error = str(exc_info.value)
        assert "__template cannot be null" in error
    
    def test_invalid_template_type_error(self):
        """Test error handling for invalid __template type."""
        yaml_content = """
__template: "this should be an object"
field_1: "value1"
"""
        
        with pytest.raises(ConstructorError) as exc_info:
            smartyaml.loads(yaml_content)
        
        error = str(exc_info.value)
        assert "__template must be a YAML mapping/object" in error
        assert "got str" in error
    
    def test_template_with_metadata_removal(self):
        """Test __template with metadata field removal."""
        yaml_content = """
__template:
  app:
    name: "TestApp"
    __internal: "should be removed"
  __debug: true

production:
  enabled: true
"""
        
        # Test with remove_metadata=True (default)
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "app": {
                "name": "TestApp"
                # __internal removed
            },
            "production": {
                "enabled": True
            }
            # __debug removed
        }
        
        assert result == expected
        assert "__internal" not in result.get("app", {})
        assert "__debug" not in result
    
    def test_template_preserve_metadata(self):
        """Test __template with metadata preservation."""
        yaml_content = """
__template:
  app:
    name: "TestApp"
    __internal: "should be kept"
  __debug: true

production:
  enabled: true
"""
        
        # Test with remove_metadata=False
        result = smartyaml.load(yaml_content, remove_metadata=False)
        
        expected = {
            "app": {
                "name": "TestApp",
                "__internal": "should be kept"
            },
            "production": {
                "enabled": True
            },
            "__debug": True
        }
        
        assert result == expected
    
    def test_complex_template_scenario(self):
        """Test a complex real-world scenario."""
        # Create a base config file in current directory
        base_config_filename = "test_base_defaults.yaml"
        base_config_path = Path(base_config_filename)
        
        try:
            # Write base config to local file (without defaults wrapper for flat merge)
            with open(base_config_path, 'w') as f:
                f.write("""
timeout: 30
retries: 3
log_level: "INFO"
""")
        
            yaml_content = f"""
__vars:
  env: "production"
  db_host: "prod-db.example.com"
  api_version: "v2"

__template:
  environment: !expand "{{{{env}}}}"
  base: !import_yaml "{base_config_filename}"
  database:
    host: !expand "{{{{db_host}}}}"
    port: 5432
    ssl: true
  api:
    version: !expand "{{{{api_version}}}}"
    endpoints:
      - "/health"
      - "/metrics"
  features:
    caching: true
    monitoring: true

# Environment-specific overrides
base:
  timeout: 60        # Production needs longer timeout
  log_level: "WARN"  # Less verbose in production

api:
  endpoints:         # Complete override
    - "/health"
    - "/metrics"
    - "/admin"
  
features:
  caching: true
  monitoring: true
  analytics: true    # Additional feature
"""
            
            result = smartyaml.loads(yaml_content)
            
            # Verify the complex merge worked correctly
            assert result["environment"] == "production"
            assert result["base"]["timeout"] == 60  # Override
            assert result["base"]["retries"] == 3   # From included file
            assert result["base"]["log_level"] == "WARN"  # Override
            
            assert result["database"]["host"] == "prod-db.example.com"
            assert result["database"]["port"] == 5432
            assert result["database"]["ssl"] is True
            
            assert result["api"]["version"] == "v2"
            assert len(result["api"]["endpoints"]) == 3  # Complete override
            assert "/admin" in result["api"]["endpoints"]
            
            assert result["features"]["analytics"] is True  # New feature
            assert result["features"]["caching"] is True    # From template
            
        finally:
            # Clean up
            if base_config_path.exists():
                base_config_path.unlink()


class TestInlineTemplateEdgeCases:
    """Test edge cases and error conditions for inline templates."""
    
    def test_no_template_directive(self):
        """Test normal YAML without __template works unchanged."""
        yaml_content = """
regular_field: "value"
nested:
  field: 42
list:
  - item1
  - item2
"""
        
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "regular_field": "value",
            "nested": {"field": 42},
            "list": ["item1", "item2"]
        }
        
        assert result == expected
    
    def test_template_with_scalar_root(self):
        """Test behavior when document root is not a mapping."""
        # This should not trigger template processing
        yaml_content = "just a string"
        result = smartyaml.loads(yaml_content)
        assert result == "just a string"
        
        yaml_content = "42"
        result = smartyaml.loads(yaml_content)
        assert result == 42
        
        yaml_content = """
- item1
- item2
"""
        result = smartyaml.loads(yaml_content)
        assert result == ["item1", "item2"]