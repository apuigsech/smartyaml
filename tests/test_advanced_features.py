"""
Advanced feature tests using enhanced testing utilities
"""

import pytest
from pathlib import Path
import smartyaml
from smartyaml.testing_utils import (
    SmartYAMLTestCase, ConstructorTestHelper, ErrorTestHelper,
    PerformanceTestHelper
)
from smartyaml.exceptions import ConstructorError, SmartYAMLFileNotFoundError


class TestAdvancedConstructorFeatures(SmartYAMLTestCase):
    """Test advanced constructor features with enhanced testing utilities."""
    
    def test_complex_nested_imports(self):
        """Test deeply nested imports with proper cleanup."""
        temp_dir = self.create_temp_dir()
        
        # Create nested structure with absolute paths
        level3_file = temp_dir / "level3.yaml"
        level3_file.write_text("value: deep_nested_value")
        
        level2_file = temp_dir / "level2.yaml"
        level2_file.write_text(f"nested: !import_yaml {level3_file}")
        
        level1_file = temp_dir / "level1.yaml"
        level1_file.write_text(f"data: !import_yaml {level2_file}")
        
        main_file = self.create_temp_yaml_file(f"""
root: !import_yaml {level1_file}
""")
        
        result = smartyaml.load(main_file)
        self.assert_yaml_equal(result['root']['data']['nested']['value'], 'deep_nested_value')
    
    def test_environment_variable_combinations(self):
        """Test complex environment variable scenarios."""
        # Test with temporary environment variables
        self.set_env_var('TEST_VAR1', 'value1')
        self.set_env_var('TEST_VAR2', 'value2')
        
        yaml_content = """
config:
  var1: !env(TEST_VAR1)
  var2: !env(TEST_VAR2, default_value)
  var3: !env(TEST_VAR_MISSING, fallback)
"""
        yaml_file = self.create_temp_yaml_file(yaml_content)
        result = smartyaml.load(yaml_file)
        
        self.assert_contains_key(result, 'config')
        config = result['config']
        
        self.assert_contains_key(config, 'var1', 'value1')
        self.assert_contains_key(config, 'var2', 'value2')
        self.assert_contains_key(config, 'var3', 'fallback')
    
    def test_conditional_inclusion_with_env_context(self):
        """Test conditional inclusion with environment context manager."""
        content_file = self.create_temp_file("conditional content", suffix='.txt')
        
        yaml_content = f"""
result: !include_if(ENABLE_FEATURE, {content_file})
"""
        yaml_file = self.create_temp_yaml_file(yaml_content)
        
        # Test with feature enabled
        with self.temp_env_var('ENABLE_FEATURE', 'true'):
            result = smartyaml.load(yaml_file)
            assert result['result'] == 'conditional content'
        
        # Test with feature disabled
        with self.temp_env_var('ENABLE_FEATURE', 'false'):
            result = smartyaml.load(yaml_file)
            assert result['result'] is None
    
    def test_error_handling_with_context(self):
        """Test enhanced error handling with context information."""
        yaml_content = """
invalid: !import(nonexistent_file.txt)
"""
        yaml_file = self.create_temp_yaml_file(yaml_content)
        
        with pytest.raises(SmartYAMLFileNotFoundError) as exc_info:
            smartyaml.load(yaml_file)
        
        error = exc_info.value
        ErrorTestHelper.assert_error_contains(error, 'nonexistent_file.txt')
        ErrorTestHelper.assert_error_type(error, SmartYAMLFileNotFoundError)
    
    def test_performance_benchmarks(self):
        """Test performance with the enhanced testing utilities."""
        # Create a moderately complex YAML structure
        temp_dir = self.create_temp_dir()
        
        # Create multiple files
        for i in range(5):
            file_path = temp_dir / f"data_{i}.yaml"
            file_path.write_text(f"item_{i}: value_{i}")
        
        yaml_content = f"""
data:
  file0: !import_yaml {temp_dir}/data_0.yaml
  file1: !import_yaml {temp_dir}/data_1.yaml
  file2: !import_yaml {temp_dir}/data_2.yaml
  file3: !import_yaml {temp_dir}/data_3.yaml
  file4: !import_yaml {temp_dir}/data_4.yaml
"""
        yaml_file = self.create_temp_yaml_file(yaml_content)
        
        # Assert that loading completes within reasonable time
        result = PerformanceTestHelper.assert_performance_threshold(
            smartyaml.load, 1.0, yaml_file  # 1 second max
        )
        
        # Verify the result structure
        assert 'data' in result
        assert len(result['data']) == 5
        
        for i in range(5):
            key = f'file{i}'
            assert key in result['data']
            assert f'item_{i}' in result['data'][key]


class TestConstructorTestHelpers:
    """Test the constructor testing helper utilities."""
    
    def test_mock_loader_creation(self):
        """Test mock loader creation."""
        base_path = Path('/test/path')
        loader = ConstructorTestHelper.create_mock_loader(
            base_path=base_path,
            max_file_size=2048
        )
        
        assert loader.base_path == base_path
        assert loader.max_file_size == 2048
        assert hasattr(loader, 'construct_scalar')
        assert hasattr(loader, 'import_stack')
    
    def test_mock_node_creation(self):
        """Test mock node creation utilities."""
        # Test scalar node
        scalar_node = ConstructorTestHelper.create_scalar_node("test_value")
        assert scalar_node.value == "test_value"
        assert scalar_node.tag == "tag:yaml.org,2002:str"
        
        # Test sequence node
        sequence_node = ConstructorTestHelper.create_sequence_node(["a", "b", "c"])
        assert len(sequence_node.value) == 3
        assert sequence_node.tag == "tag:yaml.org,2002:seq"


class TestErrorTestHelpers:
    """Test error testing helper utilities."""
    
    def test_error_assertion_helpers(self):
        """Test error assertion utilities."""
        # Test basic error checking
        error = ValueError("test error message")
        ErrorTestHelper.assert_error_contains(error, "test error")
        ErrorTestHelper.assert_error_type(error, ValueError)
        
        # Test constructor error checking
        constructor_error = ConstructorError('!test', 'param', 'test message')
        ErrorTestHelper.assert_constructor_error(constructor_error, '!test', 'param')


class TestPerformanceHelpers:
    """Test performance testing utilities."""
    
    def test_execution_time_measurement(self):
        """Test execution time measurement."""
        import time
        
        def slow_function():
            time.sleep(0.1)  # 100ms
            return "result"
        
        result, execution_time = PerformanceTestHelper.measure_execution_time(slow_function)
        
        assert result == "result"
        assert 0.09 <= execution_time <= 0.5  # Allow variance for CI environments
    
    def test_performance_threshold_assertion(self):
        """Test performance threshold assertions."""
        def fast_function():
            return "fast"
        
        def slow_function():
            import time
            time.sleep(0.2)
            return "slow"
        
        # Test passing threshold
        result = PerformanceTestHelper.assert_performance_threshold(fast_function, 0.1)
        assert result == "fast"
        
        # Test failing threshold
        with pytest.raises(AssertionError, match="exceeded performance threshold"):
            PerformanceTestHelper.assert_performance_threshold(slow_function, 0.1)


class TestTypeAnnotationCompatibility:
    """Test compatibility with type annotations."""
    
    def test_import_type_annotations(self):
        """Test that type annotations can be imported."""
        from smartyaml.type_annotations import (
            YAMLValue, YAMLNode, ParameterDict, ContextDict
        )
        
        # Basic type checking
        yaml_value: YAMLValue = "test"
        param_dict: ParameterDict = {"key": "value"}
        context_dict: ContextDict = {"context": "info"}
        
        assert isinstance(yaml_value, str)
        assert isinstance(param_dict, dict)
        assert isinstance(context_dict, dict)
    
    def test_result_wrapper(self):
        """Test the Result wrapper for better error handling."""
        from smartyaml.type_annotations import Result
        
        # Test successful result
        success_result = Result.success("test_value")
        assert success_result.is_success
        assert not success_result.is_error
        assert success_result.value == "test_value"
        
        # Test failed result
        error = ValueError("test error")
        error_result = Result.failure(error)
        assert not error_result.is_success
        assert error_result.is_error
        assert error_result.error == error
        
        # Test error when accessing value on failed result
        with pytest.raises(ValueError):
            _ = error_result.value