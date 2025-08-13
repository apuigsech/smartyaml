"""
Tests for the !extend directive functionality.
"""

import pytest
import tempfile
from pathlib import Path

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
  - criteria: "accuracy"
    weight: 1.0
    thresholds:
      min: 0.8
      max: 1.0
  - criteria: "speed"
    weight: 0.5
""")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__template:
  <<: !import_yaml(template.yaml)

evaluations: !extend
  - criteria: "custom_metric"
    weight: 0.9
    description: "Company-specific evaluation"
    thresholds:
      min: 0.7
""")

        result = smartyaml.load(main_file)
        
        assert len(result["evaluations"]) == 3
        
        # First two should be from template
        assert result["evaluations"][0]["criteria"] == "accuracy"
        assert result["evaluations"][1]["criteria"] == "speed"
        
        # Third should be the extended one
        custom_eval = result["evaluations"][2]
        assert custom_eval["criteria"] == "custom_metric"
        assert custom_eval["weight"] == 0.9
        assert custom_eval["thresholds"]["min"] == 0.7

    def test_extend_with_variables(self, tmp_path):
        """Test !extend with variable expansion."""
        template_file = tmp_path / "base.yaml"
        template_file.write_text("""
__vars:
  base_name: "BaseItem"
  
items:
  - name: !expand "{{base_name}} 1"
    type: "base"
""")

        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
__vars:
  custom_name: "CustomItem"

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
        assert result["items"][0]["name"] == "BaseItem 1"
        assert result["items"][1]["name"] == "CustomItem A"
        assert result["items"][2]["name"] == "BaseItem Extended"

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
  - "new_item_1"
  - "new_item_2"
""")

        result = smartyaml.load(main_file)
        
        assert result["empty_list"] == ["new_item_1", "new_item_2"]
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
  - "item1"
  - "item2"
""")

        result = smartyaml.load(main_file)
        
        # Should create new array
        assert result["new_list"] == ["item1", "item2"]
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
  - "item1"
  - "item2"
""")

        result = smartyaml.load(main_file)
        
        # Should fallback to replacement
        assert result["field"] == ["item1", "item2"]

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
  - "existing1"
  - "existing2"

extended: !extend []
"""
        
        result = smartyaml.loads(yaml_content)
        
        # Empty extend should result in empty array since no base
        assert result["extended"] == []
        assert result["items"] == ["existing1", "existing2"]

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
    - "extended1"
    - "extended2"
""")

        result = smartyaml.load(main_file)
        
        expected_items = ["base1", "base2", "extended1", "extended2"]
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
  - "extend1_1"

list2: !extend
  - "extend2_1"
  - "extend2_2"

# list3 without extend - should be replaced
list3:
  - "replace3_1"
""")

        result = smartyaml.load(main_file)
        
        assert result["list1"] == ["base1_1", "extend1_1"]
        assert result["list2"] == ["base2_1", "extend2_1", "extend2_2"] 
        assert result["list3"] == ["replace3_1"]  # Replaced, not extended

    def test_maxcolchon_use_case(self, tmp_path):
        """Test the specific MaxColchon use case that motivated this feature."""
        # Base customer support template
        base_template = tmp_path / "customer_support.yaml"
        base_template.write_text("""
tests:
  - id: "offtopic-crypto"
    name: "Off-topic: cryptocurrency"
    type: "offtopic"
  - id: "offtopic-football" 
    name: "Off-topic: football trivia"
    type: "offtopic"
  - id: "offtopic-recovery"
    name: "Follow-up after off-topic"
    type: "offtopic"

config:
  timeout: 300
  language: "en"
""")

        # MaxColchon specific agent
        agent_file = tmp_path / "maxcolchon_agent.yaml"
        agent_file.write_text("""
__vars:
  company_name: "MaxColchon"

__template:
  <<: !import_yaml(customer_support.yaml)

tests: !extend
  - id: "specific-product-info-sojamax"
    name: "Specific Product Information - Colchón Sojamax"
    type: "product_specific"
  - id: "concrete-recommendation-hot-sleeper"
    name: "Concrete Product Recommendation - Hot Sleeper" 
    type: "product_specific"
  - id: "vague-request-better-sleep"
    name: "Vague Request - Better Sleep"
    type: "product_specific"
""")

        result = smartyaml.load(agent_file)
        
        # Should have 6 tests total: 3 offtopic + 3 MaxColchon specific
        assert len(result["tests"]) == 6
        
        # First three should be from base template (offtopic)
        offtopic_tests = [t for t in result["tests"] if t["type"] == "offtopic"]
        assert len(offtopic_tests) == 3
        
        # Last three should be MaxColchon specific  
        product_tests = [t for t in result["tests"] if t["type"] == "product_specific"]
        assert len(product_tests) == 3
        
        # Verify order: base tests first, then extended
        assert result["tests"][0]["id"] == "offtopic-crypto"
        assert result["tests"][3]["id"] == "specific-product-info-sojamax"
        
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
  - "item1"
""")

        result = smartyaml.load(main_file)
        
        # Should create new array
        assert result["field"] == ["item1"]

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