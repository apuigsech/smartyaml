"""
Tests for nested template scenarios and variable inheritance across imports.

These tests cover complex use cases where:
1. Templates import other templates (__template with !import_yaml)
2. Variables need to be inherited across file boundaries
3. Template processing and variable expansion interact
4. Merge operators (<<:) work with imported templates
"""

import pytest
import yaml
import smartyaml


class TestNestedTemplates:
    """Test nested template scenarios where templates import other templates."""
    
    def test_basic_nested_template_import(self, tmp_path):
        """Test basic case: template imports another template"""
        # Create base template (similar to test_template_2.yaml)
        base_template = tmp_path / "base.yaml"
        base_template.write_text("""
__template:
  field_a: "a"
  field_b: "b"
  field_c: "c"
  field_d: "d"
  field_e:
    field_e_1: "e_1"
    field_e_2: "e_2"
""")
        
        # Create importing template (similar to test_template_1.yaml basic case)
        importing_template = tmp_path / "importing.yaml"
        importing_template.write_text(f"""
__template:
  <<: !import_yaml(base.yaml)
""")
        
        # Load and test
        result = smartyaml.load(importing_template)
        
        # Should get the merged result from base template
        expected = {
            "field_a": "a",
            "field_b": "b", 
            "field_c": "c",
            "field_d": "d",
            "field_e": {
                "field_e_1": "e_1",
                "field_e_2": "e_2"
            }
        }
        assert result == expected
    
    def test_nested_template_with_overrides(self, tmp_path):
        """Test nested templates with field overrides"""
        # Create base template
        base_template = tmp_path / "base.yaml"
        base_template.write_text("""
__template:
  field_a: "original_a"
  field_b: "original_b"
  nested:
    sub_a: "original_sub_a"
    sub_b: "original_sub_b"
""")
        
        # Create importing template with overrides
        importing_template = tmp_path / "importing.yaml"
        importing_template.write_text(f"""
__template:
  <<: !import_yaml(base.yaml)
  field_a: "overridden_a"  # Override scalar
  nested:
    sub_a: "overridden_sub_a"  # Override nested field
    sub_c: "new_sub_c"  # Add new field
  
# Document-level overrides
field_b: "document_override_b"
new_field: "document_new"
""")
        
        result = smartyaml.load(importing_template)
        
        expected = {
            "field_a": "overridden_a",  # Template override
            "field_b": "document_override_b",  # Document override wins  
            "nested": {
                "sub_a": "overridden_sub_a",  # Template override
                "sub_c": "new_sub_c"           # Added in template
                # Note: sub_b is NOT preserved because YAML merge within __template
                # follows standard YAML semantics (shallow merge), not deep merge.
                # Deep merge only happens between __template and document level.
            },
            "new_field": "document_new"  # Document addition
        }
        assert result == expected
    
    def test_three_level_nested_templates(self, tmp_path):
        """Test three levels of template nesting: main -> mid -> base"""
        # Create deepest template
        base_template = tmp_path / "base.yaml"
        base_template.write_text("""
__template:
  level: "base"
  base_field: "from_base"
  shared_field: "base_value"
""")
        
        # Create middle template
        mid_template = tmp_path / "mid.yaml"
        mid_template.write_text(f"""
__template:
  <<: !import_yaml(base.yaml)
  level: "middle"
  mid_field: "from_mid"
  shared_field: "mid_value"  # Override base
""")
        
        # Create top-level template
        main_template = tmp_path / "main.yaml"
        main_template.write_text(f"""
__template:
  <<: !import_yaml(mid.yaml)
  level: "main"
  main_field: "from_main"

# Document overrides
shared_field: "document_value"
""")
        
        result = smartyaml.load(main_template)
        
        expected = {
            "level": "main",                    # Top template wins
            "base_field": "from_base",          # Inherited from base
            "mid_field": "from_mid",            # Inherited from mid
            "main_field": "from_main",          # From main template
            "shared_field": "document_value"    # Document override wins all
        }
        assert result == expected


class TestVariableInheritance:
    """Test variable inheritance across template imports."""
    
    def test_vars_in_main_file_used_in_template(self, tmp_path):
        """Test that variables from main file are available in templates"""
        # Create template that uses variables
        template_file = tmp_path / "template.yaml"
        template_file.write_text("""__template:
  message: !expand "Hello {{name}}!"
  count: !expand "Count: {{count}}"
""")
        
        # Create main file with variables (avoid f-string to prevent escaping issues)
        main_file = tmp_path / "main.yaml"
        main_content = '''__vars:
  name: "World"
  count: "42"

__template:
  <<: !import_yaml(template.yaml)

# Add additional field
extra: !expand "Extra: {{name}}"
'''
        main_file.write_text(main_content)
        
        result = smartyaml.load(main_file)
        
        expected = {
            "message": "Hello World!",
            "count": "Count: 42",
            "extra": "Extra: World"
        }
        assert result == expected
    
    def test_vars_inheritance_chain(self, tmp_path):
        """Test variable inheritance through multiple levels"""
        # Base template with its own vars
        base_template = tmp_path / "base.yaml"
        base_template.write_text("""__vars:
  base_var: "from_base"
  shared_var: "base_shared"

__template:
  base_message: !expand "Base: {{base_var}}"
  shared_message: !expand "Shared: {{shared_var}}"
""")
        
        # Middle template with overriding vars
        mid_template = tmp_path / "mid.yaml"
        mid_content = '''__vars:
  mid_var: "from_mid"
  shared_var: "mid_shared"

__template:
  <<: !import_yaml(base.yaml)
  mid_message: !expand "Mid: {{mid_var}}"
  shared_override: !expand "Shared now: {{shared_var}}"
'''
        mid_template.write_text(mid_content)
        
        # Main file with its own vars
        main_file = tmp_path / "main.yaml"
        main_content = '''__vars:
  main_var: "from_main"
  shared_var: "main_shared"

__template:
  <<: !import_yaml(mid.yaml)

main_message: !expand "Main: {{main_var}}"
final_shared: !expand "Final shared: {{shared_var}}"
'''
        main_file.write_text(main_content)
        
        result = smartyaml.load(main_file)
        
        expected = {
            "base_message": "Base: from_base",        # Base var
            "mid_message": "Mid: from_mid",           # Mid var
            "shared_message": "Shared: base_shared", # Uses base file's variable (correct behavior)
            "shared_override": "Shared now: mid_shared", # Uses mid file's variable (correct behavior) 
            "main_message": "Main: from_main",        # Main var
            "final_shared": "Final shared: main_shared" # Main file uses its own vars
        }
        assert result == expected
    
    def test_template_vars_vs_document_vars(self, tmp_path):
        """Test precedence of vars defined in templates vs document"""
        # Template with variables
        template_file = tmp_path / "template.yaml" 
        template_file.write_text("""__vars:
  template_var: "from_template"
  conflict_var: "template_value"

__template:
  template_field: !expand "Template: {{template_var}}"
  conflict_field: !expand "Conflict: {{conflict_var}}"
""")
        
        # Main file with conflicting variables
        main_file = tmp_path / "main.yaml"
        main_content = '''__vars:
  main_var: "from_main"
  conflict_var: "main_value"

__template:
  <<: !import_yaml(template.yaml)

main_field: !expand "Main: {{main_var}}"
resolved_conflict: !expand "Final: {{conflict_var}}"
'''
        main_file.write_text(main_content)
        
        result = smartyaml.load(main_file)
        
        expected = {
            "template_field": "Template: from_template", # Template var
            "conflict_field": "Conflict: template_value",    # Template uses its own variables
            "main_field": "Main: from_main",             # Main var
            "resolved_conflict": "Final: main_value"     # Main override
        }
        assert result == expected


class TestComplexScenarios:
    """Test complex real-world scenarios combining templates and variables."""
    
    def test_configuration_inheritance_pattern(self, tmp_path):
        """Test a real-world config inheritance pattern"""
        # Base config
        base_config = tmp_path / "base_config.yaml"
        base_config.write_text("""
__vars:
  app_name: "MyApp"
  version: "1.0.0"

__template:
  application:
    name: !expand "{{app_name}}"
    version: !expand "{{version}}"
  
  database:
    host: "localhost"
    port: 5432
    timeout: 30
    
  logging:
    level: "INFO"
    format: "standard"
""")
        
        # Environment-specific config
        prod_config = tmp_path / "prod_config.yaml"
        prod_content = '''__vars:
  app_name: "MyApp-Production"
  db_host: "prod-db.example.com"
  
__template:
  <<: !import_yaml(base_config.yaml)
  
  # Production-specific overrides in template
  database:
    host: !expand "{{db_host}}"
    timeout: 60
    ssl: true
    
  logging:
    level: "WARN"

# Document-level additions
monitoring:
  enabled: true
  endpoint: !expand "/metrics/{{app_name}}"

deployment:
  environment: "production"
  replicas: 3
'''
        prod_config.write_text(prod_content)
        
        result = smartyaml.load(prod_config)
        
        expected = {
            "application": {
                "name": "MyApp",  # Uses base template's own variables
                "version": "1.0.0"
            },
            "database": {
                "host": "prod-db.example.com",
                "timeout": 60,
                "ssl": True
                # Note: port is not preserved due to YAML merge semantics within templates
            },
            "logging": {
                "level": "WARN"
                # Note: format is not preserved due to YAML merge semantics within templates
            },
            "monitoring": {
                "enabled": True,
                "endpoint": "/metrics/MyApp-Production"  # Uses prod template's variables
            },
            "deployment": {
                "environment": "production",
                "replicas": 3
            }
        }
        assert result == expected
    
    def test_current_failing_scenario(self, tmp_path):
        """Test the currently failing scenario from the user's example"""
        # Recreate test_template_2.yaml
        template_2 = tmp_path / "test_template_2.yaml"
        template_2.write_text("""
__template:
  field_a: "a"
  field_b: "b"
  field_c: "c"
  field_d: "d"
  field_e:
    field_e_1: "e_1"
    field_e_2: "e_2"
""")
        
        # Recreate test_template_1.yaml
        template_1 = tmp_path / "test_template_1.yaml"
        template_1_content = '''__vars:
  var_3: "old 3"

__template:
  <<: !import_yaml(test_template_2.yaml)

field_f:
  field_f_2: !expand "{{var_2}}"
  field_f_3: !expand "{{var_3}}"
'''
        template_1.write_text(template_1_content)
        
        # Recreate test_main.yaml
        main_file = tmp_path / "test_main.yaml"
        main_content = '''__vars:
  var_1: "1"
  var_2: "2" 
  var_3: "3"

__template:
  <<: !import_yaml(test_template_1.yaml)

field_e:
  field_e_1: "new e_1"
field_f:
  field_f_1: !expand "{{var_1}}"
'''
        main_file.write_text(main_content)
        
        # This should work when variable inheritance is fixed
        result = smartyaml.load(main_file)
        
        expected = {
            "field_a": "a", "field_b": "b", "field_c": "c", "field_d": "d",
            "field_e": {
                "field_e_1": "new e_1",  # Document override
                "field_e_2": "e_2"       # From imported template
            },
            "field_f": {
                "field_f_1": "1",        # From main vars
                "field_f_2": "2",        # From main vars (inherited)
                "field_f_3": "old 3"     # From template_1 vars (templates use their own variables)
            }
        }
        assert result == expected


class TestErrorCases:
    """Test error cases and edge conditions."""
    
    def test_missing_template_file_error(self, tmp_path):
        """Test error when imported template file doesn't exist"""
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(nonexistent.yaml)
""")
        
        with pytest.raises((smartyaml.SmartYAMLError, smartyaml.SmartYAMLFileNotFoundError, yaml.constructor.ConstructorError)):
            smartyaml.load(main_file)
    
    def test_circular_import_detection(self, tmp_path):
        """Test that circular template imports are detected"""
        # Create circular imports: a -> b -> a
        template_a = tmp_path / "a.yaml"
        template_a.write_text("""__template:
  <<: !import_yaml(b.yaml)
  field_a: "from_a"
""")
        
        template_b = tmp_path / "b.yaml"
        template_b.write_text("""__template:
  <<: !import_yaml(a.yaml)
  field_b: "from_b"  
""")
        
        with pytest.raises((smartyaml.SmartYAMLError, yaml.constructor.ConstructorError)):
            smartyaml.load(template_a)
    
    def test_undefined_variable_in_imported_template(self, tmp_path):
        """Test error when imported template references undefined variable"""
        template_file = tmp_path / "template.yaml"
        template_file.write_text("""__template:
  message: !expand "Hello {{undefined_var}}!"
""")
        
        main_file = tmp_path / "main.yaml"
        main_content = '''__vars:
  defined_var: "value"

__template:
  <<: !import_yaml(template.yaml)
'''
        main_file.write_text(main_content)
        
        with pytest.raises(Exception) as exc_info:
            smartyaml.load(main_file)
        
        # Should get a clear error about the missing variable
        error_msg = str(exc_info.value)
        assert "undefined_var" in error_msg
        # The actual error message format may vary
        assert ("Variable expansion failed" in error_msg or 
                "not found in substitution context" in error_msg)