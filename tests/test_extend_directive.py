"""
Tests for the !extend directive functionality.
"""

import pytest

import smartyaml
from smartyaml.exceptions import ConstructorError


class TestExtendDirective:
    """Test cases for !extend directive array concatenation."""

    def test_basic_array_extension(self, tmp_path):
        """Test basic array extension functionality."""
        # Base template
        template_file = tmp_path / "base.yaml"
        template_file.write_text("""
base_list:
  - item1
  - item2
""")

        # Document with extend
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(base.yaml)

base_list: !extend
  - item3
  - item4
""")

        result = smartyaml.load(main_file)
        
        expected = {
            "base_list": ["item1", "item2", "item3", "item4"]
        }
        assert result == expected

    def test_extend_with_template_inheritance(self, tmp_path):
        """Test !extend with __template inheritance."""
        # Base template with array
        template_file = tmp_path / "base_template.yaml" 
        template_file.write_text("""
tests:
  - id: "base_test_1"
    name: "Base Test 1"
  - id: "base_test_2" 
    name: "Base Test 2"
    
config:
  timeout: 30
""")

        # Main document extending the array
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(base_template.yaml)

tests: !extend
  - id: "custom_test_1"
    name: "Custom Test 1"
  - id: "custom_test_2"
    name: "Custom Test 2"
""")

        result = smartyaml.load(main_file)
        
        # Should have 4 tests total: 2 base + 2 custom
        assert len(result["tests"]) == 4
        assert result["tests"][0]["id"] == "base_test_1"
        assert result["tests"][1]["id"] == "base_test_2"
        assert result["tests"][2]["id"] == "custom_test_1"
        assert result["tests"][3]["id"] == "custom_test_2"
        
        # Config should be merged normally
        assert result["config"]["timeout"] == 30

    def test_extend_complex_objects(self, tmp_path):
        """Test extending arrays of complex objects."""
        template_file = tmp_path / "template.yaml"
        template_file.write_text("""
evaluations:
  - criteria: "metric_x"
    weight: 1.0
    thresholds:
      min: 0.8
      max: 1.0
  - criteria: "metric_y"
    weight: 0.5
""")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(template.yaml)

evaluations: !extend
  - criteria: "metric_z"
    weight: 0.9
    description: "Extended metric"
    thresholds:
      min: 0.7
""")

        result = smartyaml.load(main_file)
        
        assert len(result["evaluations"]) == 3
        
        # First two should be from template
        assert result["evaluations"][0]["criteria"] == "metric_x"
        assert result["evaluations"][1]["criteria"] == "metric_y"
        
        # Third should be the extended one
        custom_eval = result["evaluations"][2]
        assert custom_eval["criteria"] == "metric_z"
        assert custom_eval["weight"] == 0.9
        assert custom_eval["thresholds"]["min"] == 0.7

    def test_extend_with_variables(self, tmp_path):
        """Test !extend with variable expansion."""
        template_file = tmp_path / "base.yaml"
        template_file.write_text("""
__vars:
  base_name: "ItemA"
  
items:
  - name: !expand "{{base_name}} 1"
    type: "base"
""")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__vars:
  custom_name: "ItemB"

__template:
  <<: !import_yaml(base.yaml)

items: !extend
  - name: !expand "{{custom_name}} A"
    type: "custom"
  - name: !expand "{{base_name}} Extended"  
    type: "extended"
""")

        result = smartyaml.load(main_file)
        
        assert len(result["items"]) == 3
        assert result["items"][0]["name"] == "ItemA 1"
        assert result["items"][1]["name"] == "ItemB A"
        assert result["items"][2]["name"] == "ItemA Extended"

    def test_extend_empty_base_array(self, tmp_path):
        """Test extending when base array is empty."""
        template_file = tmp_path / "empty_base.yaml"
        template_file.write_text("""
empty_list: []
config: 
  setting: "value"
""")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(empty_base.yaml)

empty_list: !extend
  - "data_x1"
  - "data_x2"
""")

        result = smartyaml.load(main_file)
        
        assert result["empty_list"] == ["data_x1", "data_x2"]
        assert result["config"]["setting"] == "value"

    def test_extend_no_base_array(self, tmp_path):
        """Test extending when base doesn't have the array."""
        template_file = tmp_path / "no_array.yaml"
        template_file.write_text("""
config:
  timeout: 60
""")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(no_array.yaml)

new_list: !extend
  - "data_1"
  - "data_2"
""")

        result = smartyaml.load(main_file)
        
        # Should create new array
        assert result["new_list"] == ["data_1", "data_2"]
        assert result["config"]["timeout"] == 60

    def test_extend_type_mismatch_fallback(self, tmp_path):
        """Test fallback when extending non-array with array."""
        template_file = tmp_path / "mismatch.yaml"
        template_file.write_text("""
field: "not_an_array"
""")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(mismatch.yaml)

field: !extend
  - "data_1"
  - "data_2"
""")

        result = smartyaml.load(main_file)
        
        # Should fallback to replacement
        assert result["field"] == ["data_1", "data_2"]

    def test_extend_with_non_array_error(self):
        """Test that !extend with non-array raises error."""
        yaml_content = """
items: !extend "not_an_array"
"""
        
        with pytest.raises(ConstructorError) as exc_info:
            smartyaml.loads(yaml_content)
        
        assert "requires a list/array" in str(exc_info.value)

    def test_extend_empty_array(self):
        """Test extending with empty array."""
        yaml_content = """
items: 
  - "data_1"
  - "data_2"

extended: !extend []
"""
        
        result = smartyaml.loads(yaml_content)
        
        # Empty extend should result in empty array since no base
        assert result["extended"] == []
        assert result["items"] == ["data_1", "data_2"]

    def test_nested_extend_support(self, tmp_path):
        """Test !extend in nested structures."""
        template_file = tmp_path / "nested.yaml"
        template_file.write_text("""
section1:
  items:
    - "base1"
    - "base2"
section2:
  config: "value"
""")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(nested.yaml)

section1:
  items: !extend
    - "data_c1"
    - "data_c2"
""")

        result = smartyaml.load(main_file)
        
        expected_items = ["base1", "base2", "data_c1", "data_c2"]
        assert result["section1"]["items"] == expected_items
        assert result["section2"]["config"] == "value"

    def test_multiple_extends_in_document(self, tmp_path):
        """Test multiple !extend directives in same document."""
        template_file = tmp_path / "multi_arrays.yaml"
        template_file.write_text("""
list1:
  - "base1_1"
list2:
  - "base2_1" 
list3:
  - "base3_1"
""")

        main_file = tmp_path / "main.yaml"  
        main_file.write_text("""
__template:
  <<: !import_yaml(multi_arrays.yaml)

list1: !extend
  - "ext1_1"

list2: !extend
  - "ext2_1"
  - "ext2_2"

# list3 without extend - should be replaced
list3:
  - "rep3_1"
""")

        result = smartyaml.load(main_file)
        
        assert result["list1"] == ["base1_1", "ext1_1"]
        assert result["list2"] == ["base2_1", "ext2_1", "ext2_2"] 
        assert result["list3"] == ["rep3_1"]  # Replaced, not extended

    def test_template_array_extension_scenario(self, tmp_path):
        """Test template array extension with multiple item types."""
        # Base template
        base_template = tmp_path / "template_base.yaml"
        base_template.write_text("""
tests:
  - id: "type_a_001"
    name: "Generic Type A Test 1"
    type: "type_a"
  - id: "type_a_002" 
    name: "Generic Type A Test 2"
    type: "type_a"
  - id: "type_a_003"
    name: "Generic Type A Test 3"
    type: "type_a"

config:
  timeout: 300
  language: "xx"
""", encoding='utf-8')

        # Extended configuration
        extended_file = tmp_path / "extended_config.yaml"
        extended_file.write_text("""
__vars:
  entity_name: "EntityX"

__template:
  <<: !import_yaml(template_base.yaml)

tests: !extend
  - id: "type_b_001"
    name: "Generic Type B Test 1"
    type: "type_b"
  - id: "type_b_002"
    name: "Generic Type B Test 2" 
    type: "type_b"
  - id: "type_b_003"
    name: "Generic Type B Test 3"
    type: "type_b"
""", encoding='utf-8')

        result = smartyaml.load(extended_file)
        
        # Should have 6 tests total: 3 type_a + 3 type_b
        assert len(result["tests"]) == 6
        
        # First three should be from base template (type_a)
        type_a_tests = [t for t in result["tests"] if t["type"] == "type_a"]
        assert len(type_a_tests) == 3
        
        # Last three should be type_b  
        type_b_tests = [t for t in result["tests"] if t["type"] == "type_b"]
        assert len(type_b_tests) == 3
        
        # Verify order: base tests first, then extended
        assert result["tests"][0]["id"] == "type_a_001"
        assert result["tests"][3]["id"] == "type_b_001"
        
        # Config should be inherited normally
        assert result["config"]["timeout"] == 300


class TestExtendEdgeCases:
    """Test edge cases and error conditions for !extend."""

    def test_extend_with_null_base(self, tmp_path):
        """Test extending when base field is null."""
        template_file = tmp_path / "null_base.yaml"
        template_file.write_text("""
field: null
""")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(null_base.yaml)

field: !extend
  - "data_1"
""")

        result = smartyaml.load(main_file)
        
        # Should create new array
        assert result["field"] == ["data_1"]

    def test_extend_preserves_order(self, tmp_path):
        """Test that extend preserves item order."""
        template_file = tmp_path / "ordered.yaml"
        template_file.write_text("""
items:
  - "A"
  - "B" 
  - "C"
""")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(ordered.yaml)

items: !extend
  - "D"
  - "E"
  - "F"
""")

        result = smartyaml.load(main_file)
        
        assert result["items"] == ["A", "B", "C", "D", "E", "F"]