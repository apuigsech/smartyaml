"""
Tests for metadata field removal functionality
"""

import pytest
from pathlib import Path
import smartyaml


class TestMetadataFieldRemoval:
    """Test metadata field removal with __ prefix"""
    
    def test_simple_metadata_removal(self):
        """Test basic metadata removal from dictionary"""
        yaml_content = """
app_name: "MyApp"
__version: "1.0.0"
__build_date: "2024-01-01"
port: 8080
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            'app_name': 'MyApp',
            'port': 8080
        }
        assert result == expected
    
    def test_nested_metadata_removal(self):
        """Test metadata removal from nested structures"""
        yaml_content = """
app:
  name: "MyApp"
  __internal_id: "app-123"
  database:
    host: "localhost"
    __connection_pool: 10
    __debug_enabled: true
__global_config: "removed"
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            'app': {
                'name': 'MyApp',
                'database': {
                    'host': 'localhost'
                }
            }
        }
        assert result == expected
    
    def test_metadata_in_lists(self):
        """Test metadata removal from objects within lists"""
        yaml_content = """
servers:
  - name: "server1"
    host: "192.168.1.1"
    __maintenance_notes: "Updated last week"
  - name: "server2"
    host: "192.168.1.2"
    __maintenance_notes: "Needs restart"
__server_count: 2
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            'servers': [
                {'name': 'server1', 'host': '192.168.1.1'},
                {'name': 'server2', 'host': '192.168.1.2'}
            ]
        }
        assert result == expected
    
    def test_metadata_with_smartyaml_directives(self, tmp_path):
        """Test that metadata fields can contain SmartYAML directives"""
        # Create a test file for import
        version_file = tmp_path / "version.txt"
        version_file.write_text("1.2.3")
        
        yaml_file = tmp_path / "test.yaml"
        yaml_content = f"""
app_name: "TestApp"
__version: !import(version.txt)
__debug_mode: !env(DEBUG, false)
port: 3000
"""
        yaml_file.write_text(yaml_content)
        
        # The metadata fields should be processed but then removed
        result = smartyaml.load(yaml_file)
        
        expected = {
            'app_name': 'TestApp',
            'port': 3000
        }
        assert result == expected
    
    def test_disable_metadata_removal(self):
        """Test that metadata removal can be disabled"""
        yaml_content = """
app_name: "MyApp"
__version: "1.0.0"
__build_date: "2024-01-01"
"""
        result = smartyaml.loads(yaml_content, remove_metadata=False)
        
        expected = {
            'app_name': 'MyApp',
            '__version': '1.0.0',
            '__build_date': '2024-01-01'
        }
        assert result == expected
    
    def test_metadata_only_document(self):
        """Test document with only metadata fields"""
        yaml_content = """
__version: "1.0.0"
__build_date: "2024-01-01"
__author: "Developer"
"""
        result = smartyaml.loads(yaml_content)
        
        # Should result in empty dict
        assert result == {}
    
    def test_no_metadata_fields(self):
        """Test document without metadata fields works normally"""
        yaml_content = """
app_name: "MyApp"
version: "1.0.0"
database:
  host: "localhost"
  port: 5432
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            'app_name': 'MyApp',
            'version': '1.0.0',
            'database': {
                'host': 'localhost',
                'port': 5432
            }
        }
        assert result == expected
    
    def test_empty_structures(self):
        """Test metadata removal with empty structures"""
        yaml_content = """
empty_dict: {}
empty_list: []
__metadata: "removed"
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            'empty_dict': {},
            'empty_list': []
        }
        assert result == expected
    
    def test_mixed_list_types(self):
        """Test metadata removal with mixed list content types"""
        yaml_content = """
mixed_list:
  - "string_item"
  - 42
  - nested:
      key: "value"
      __hidden: "metadata"
  - __this_dict_removed: true
    visible: "kept"
__root_metadata: "removed"
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            'mixed_list': [
                'string_item',
                42,
                {
                    'nested': {
                        'key': 'value'
                    }
                },
                {
                    'visible': 'kept'
                }
            ]
        }
        assert result == expected
    
    def test_underscore_variations(self):
        """Test that only double underscore prefix is removed"""
        yaml_content = """
regular_field: "kept"
_single_underscore: "kept"
__double_underscore: "removed"
___triple_underscore: "removed"
field__with_double: "kept"
__: "removed"  # edge case: just double underscore
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            'regular_field': 'kept',
            '_single_underscore': 'kept',
            'field__with_double': 'kept'
        }
        assert result == expected
    
    def test_primitive_types_unchanged(self):
        """Test that primitive types are not affected"""
        yaml_content = """
string_value: "test"
int_value: 42
float_value: 3.14
bool_value: true
null_value: null
__removed: "metadata"
"""
        result = smartyaml.loads(yaml_content)
        
        expected = {
            'string_value': 'test',
            'int_value': 42,
            'float_value': 3.14,
            'bool_value': True,
            'null_value': None
        }
        assert result == expected

    def test_metadata_removal_preserves_functionality(self):
        """Test that metadata removal doesn't affect normal functionality"""
        yaml_content = 'app_name: "MyWebApp"\nport: 8080\n__debug_info: "should be removed"'
        result = smartyaml.loads(yaml_content)
        
        expected = {
            'app_name': 'MyWebApp',
            'port': 8080
        }
        assert result == expected


class TestMetadataRemovalFunction:
    """Test the remove_metadata_fields function directly"""
    
    def test_direct_function_call(self):
        """Test calling remove_metadata_fields directly"""
        data = {
            'keep': 'this',
            '__remove': 'this',
            'nested': {
                'keep': 'this too',
                '__remove': 'this too'
            }
        }
        
        result = smartyaml.remove_metadata_fields(data)
        
        expected = {
            'keep': 'this',
            'nested': {
                'keep': 'this too'
            }
        }
        assert result == expected
    
    def test_function_with_various_types(self):
        """Test function handles various Python data types"""
        data = {
            'string': 'value',
            'integer': 42,
            'float_val': 3.14,
            'boolean': True,
            'none_val': None,
            'list_val': [1, 2, {'__hidden': 'removed', 'visible': 'kept'}],
            '__metadata': 'removed'
        }
        
        result = smartyaml.remove_metadata_fields(data)
        
        expected = {
            'string': 'value',
            'integer': 42,
            'float_val': 3.14,
            'boolean': True,
            'none_val': None,
            'list_val': [1, 2, {'visible': 'kept'}]
        }
        assert result == expected