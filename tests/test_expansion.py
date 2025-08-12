"""
Tests for variable expansion functionality
"""

import pytest
from pathlib import Path
import smartyaml


class TestExpandConstructor:
    """Test !expand directive functionality"""
    
    def test_basic_expansion(self):
        """Test basic variable expansion with !expand directive"""
        yaml_content = 'message: !expand "Hello {{name}}!"'
        variables = {"name": "World"}
        
        result = smartyaml.loads(yaml_content, variables=variables)
        assert result == {"message": "Hello World!"}
    
    def test_multiple_variables(self):
        """Test expansion with multiple variables"""
        yaml_content = 'greeting: !expand "{{greeting}} {{name}}, welcome to {{app}}!"'
        variables = {
            "greeting": "Hello",
            "name": "Alice",
            "app": "SmartYAML"
        }
        
        result = smartyaml.loads(yaml_content, variables=variables)
        assert result == {"greeting": "Hello Alice, welcome to SmartYAML!"}
    
    def test_no_variables_no_expansion(self):
        """Test that strings without variables pass through unchanged"""
        yaml_content = 'message: !expand "Just a regular string"'
        
        result = smartyaml.loads(yaml_content)
        assert result == {"message": "Just a regular string"}
    
    def test_missing_variable_error(self):
        """Test error when required variable is missing"""
        yaml_content = 'message: !expand "Hello {{missing}}!"'
        
        with pytest.raises(Exception) as excinfo:
            smartyaml.loads(yaml_content)
        
        # Test for enhanced error message with debugging info
        error_msg = str(excinfo.value)
        assert "Variable expansion failed" in error_msg
        assert "Variables found in content: ['missing']" in error_msg
        assert "No variables provided to SmartYAML" in error_msg
    
    def test_escaped_braces(self):
        """Test escaping literal braces"""
        yaml_content = r'message: !expand "Use \\{{this}} for literal braces, but {{name}} expands"'
        variables = {"name": "Alice"}
        
        result = smartyaml.loads(yaml_content, variables=variables)
        assert result == {"message": "Use {{this}} for literal braces, but Alice expands"}


class TestVariableMetadata:
    """Test __vars metadata field integration"""
    
    def test_vars_metadata_basic(self):
        """Test basic __vars metadata usage"""
        yaml_content = """
__vars:
  name: "Alice"
  app: "TestApp"

greeting: !expand "Hello {{name}}, welcome to {{app}}!"
"""
        result = smartyaml.loads(yaml_content)
        assert result == {"greeting": "Hello Alice, welcome to TestApp!"}
    
    def test_vars_metadata_override(self):
        """Test function variables override __vars metadata"""
        yaml_content = """
__vars:
  name: "Alice"
  app: "DefaultApp"

greeting: !expand "Hello {{name}}, welcome to {{app}}!"
"""
        variables = {"app": "OverrideApp"}
        
        result = smartyaml.loads(yaml_content, variables=variables)
        assert result == {"greeting": "Hello Alice, welcome to OverrideApp!"}
    
    def test_vars_metadata_nested(self):
        """Test __vars with nested structures"""
        yaml_content = """
__vars:
  user: "Alice"
  
config:
  database:
    name: !expand "{{user}}_db"
  app:
    title: !expand "{{user}}'s Application"
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "config": {
                "database": {
                    "name": "Alice_db"
                },
                "app": {
                    "title": "Alice's Application"
                }
            }
        }
        assert result == expected
    
    def test_vars_metadata_removed(self):
        """Test that __vars is removed from final result"""
        yaml_content = """
__vars:
  name: "Alice"

greeting: !expand "Hello {{name}}!"
regular_field: "value"
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "greeting": "Hello Alice!",
            "regular_field": "value"
        }
        assert result == expected
        assert "__vars" not in result
    
    def test_vars_metadata_preserved_when_disabled(self):
        """Test __vars is preserved when metadata removal is disabled"""
        yaml_content = """
__vars:
  name: "Alice"

greeting: !expand "Hello {{name}}!"
"""
        result = smartyaml.loads(yaml_content, remove_metadata=False)
        
        expected = {
            "__vars": {"name": "Alice"},
            "greeting": "Hello Alice!"
        }
        assert result == expected


class TestVariableTypes:
    """Test different variable value types"""
    
    def test_string_variables(self):
        """Test string variable substitution"""
        yaml_content = 'value: !expand "{{text}}"'
        variables = {"text": "Hello World"}
        
        result = smartyaml.loads(yaml_content, variables=variables)
        assert result == {"value": "Hello World"}
    
    def test_numeric_variables(self):
        """Test numeric variables converted to strings"""
        yaml_content = 'port: !expand "Port {{port}} is active"'
        variables = {"port": 8080}
        
        result = smartyaml.loads(yaml_content, variables=variables)
        assert result == {"port": "Port 8080 is active"}
    
    def test_boolean_variables(self):
        """Test boolean variables converted to strings"""
        yaml_content = 'status: !expand "Debug mode: {{debug}}"'
        variables = {"debug": True}
        
        result = smartyaml.loads(yaml_content, variables=variables)
        assert result == {"status": "Debug mode: True"}


class TestVariableSubstitutionEngine:
    """Test the VariableSubstitutionEngine directly"""
    
    def test_engine_basic_substitution(self):
        """Test engine basic functionality"""
        from smartyaml.utils.variable_substitution import VariableSubstitutionEngine
        
        engine = VariableSubstitutionEngine({"name": "Alice", "age": 30})
        
        result = engine.substitute_string("Hello {{name}}, you are {{age}} years old")
        assert result == "Hello Alice, you are 30 years old"
    
    def test_engine_has_variables(self):
        """Test engine variable detection"""
        from smartyaml.utils.variable_substitution import VariableSubstitutionEngine
        
        engine = VariableSubstitutionEngine()
        
        assert engine.has_variables("Hello {{name}}")
        assert engine.has_variables("{{var1}} and {{var2}}")
        assert not engine.has_variables("Hello world")
        assert not engine.has_variables("No variables here")
    
    def test_engine_extract_variable_names(self):
        """Test engine variable name extraction"""
        from smartyaml.utils.variable_substitution import VariableSubstitutionEngine
        
        engine = VariableSubstitutionEngine()
        
        names = engine.extract_variable_names("Hello {{name}}, welcome to {{app}}!")
        assert set(names) == {"name", "app"}
        
        names = engine.extract_variable_names("No variables here")
        assert names == []
    
    def test_engine_recursive_substitution(self):
        """Test engine recursive data structure substitution"""
        from smartyaml.utils.variable_substitution import VariableSubstitutionEngine
        
        engine = VariableSubstitutionEngine({"name": "Alice", "port": 8080})
        
        data = {
            "user": "{{name}}",
            "config": {
                "port": "{{port}}",
                "host": "localhost"
            },
            "list": ["{{name}}", "admin"]
        }
        
        result = engine.substitute_recursive(data)
        
        expected = {
            "user": "Alice",
            "config": {
                "port": "8080",
                "host": "localhost"
            },
            "list": ["Alice", "admin"]
        }
        assert result == expected
    
    def test_engine_merge_variables(self):
        """Test engine variable merging"""
        from smartyaml.utils.variable_substitution import VariableSubstitutionEngine
        
        engine = VariableSubstitutionEngine()
        
        base_vars = {"name": "Alice", "app": "BaseApp"}
        override_vars = {"app": "OverrideApp", "version": "1.0"}
        
        merged = engine.merge_variables(base_vars, override_vars)
        
        expected = {"name": "Alice", "app": "OverrideApp", "version": "1.0"}
        assert merged == expected
    
    def test_extract_vars_metadata_function(self):
        """Test extract_vars_metadata utility function"""
        from smartyaml.utils.variable_substitution import extract_vars_metadata
        
        data = {
            "__vars": {"name": "Alice", "age": 30},
            "other": "data"
        }
        
        vars_meta = extract_vars_metadata(data)
        assert vars_meta == {"name": "Alice", "age": 30}
        
        # Test with no __vars
        data_no_vars = {"other": "data"}
        vars_meta = extract_vars_metadata(data_no_vars)
        assert vars_meta == {}


class TestIntegrationScenarios:
    """Test complex integration scenarios"""
    
    def test_mixed_expansion_and_metadata(self):
        """Test mixing regular YAML with expansion and metadata"""
        yaml_content = """
__version: "1.0.0"
__vars:
  env: "production"
  db_host: "prod-db.example.com"

application:
  name: "MyApp"
  environment: !expand "{{env}}"
  database:
    host: !expand "{{db_host}}"
    name: !expand "myapp_{{env}}"
    
features:
  - name: "auth"
    enabled: true
  - name: "cache"
    enabled: !expand "{{env}}"
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "application": {
                "name": "MyApp",
                "environment": "production",
                "database": {
                    "host": "prod-db.example.com",
                    "name": "myapp_production"
                }
            },
            "features": [
                {"name": "auth", "enabled": True},
                {"name": "cache", "enabled": "production"}
            ]
        }
        assert result == expected
        
        # Ensure metadata fields are removed
        assert "__version" not in result
        assert "__vars" not in result
    
    def test_file_loading_with_variables(self, tmp_path):
        """Test loading from file with variables"""
        yaml_file = tmp_path / "config.yaml"
        yaml_content = """
__vars:
  service_name: "test-service"

service:
  name: !expand "{{service_name}}"
  port: 8080
  endpoint: !expand "/api/{{service_name}}/v1"
"""
        yaml_file.write_text(yaml_content)
        
        # Load from file with additional variables
        variables = {"version": "v2"}
        result = smartyaml.load(yaml_file, variables=variables)
        
        expected = {
            "service": {
                "name": "test-service",
                "port": 8080,
                "endpoint": "/api/test-service/v1"
            }
        }
        assert result == expected
    
    def test_no_expansion_without_directive(self):
        """Test that {{}} patterns are not expanded without !expand directive"""
        yaml_content = """
message: "Hello {{name}}, this should not expand"
expanded: !expand "Hello {{name}}, this should expand"

__vars:
  name: "Alice"
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            "message": "Hello {{name}}, this should not expand",
            "expanded": "Hello Alice, this should expand"
        }
        assert result == expected