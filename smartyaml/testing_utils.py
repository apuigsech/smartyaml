"""
Testing utilities and fixtures for SmartYAML
"""

from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pytest

if TYPE_CHECKING:
    pass


class SmartYAMLTestCase:
    """Base test case class with common testing utilities."""

    def setup_method(self) -> None:
        """Set up test environment before each test method."""
        self.temp_files: List[Path] = []
        self.original_env: Dict[str, Optional[str]] = {}

    def teardown_method(self) -> None:
        """Clean up test environment after each test method."""
        # Clean up temporary files
        for file_path in self.temp_files:
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    import shutil

                    shutil.rmtree(file_path)

        # Restore original environment variables
        for var_name, original_value in self.original_env.items():
            if original_value is None:
                os.environ.pop(var_name, None)
            else:
                os.environ[var_name] = original_value

        self.original_env.clear()

    def create_temp_file(
        self, content: str, suffix: str = ".txt", prefix: str = "test_"
    ) -> Path:
        """
        Create a temporary file with given content.

        Args:
            content: File content
            suffix: File suffix
            prefix: File prefix

        Returns:
            Path to the created file
        """
        temp_file = Path(tempfile.mktemp(suffix=suffix, prefix=prefix))
        temp_file.write_text(content, encoding="utf-8")
        self.temp_files.append(temp_file)
        return temp_file

    def create_temp_yaml_file(self, yaml_content: str) -> Path:
        """
        Create a temporary YAML file.

        Args:
            yaml_content: YAML content string

        Returns:
            Path to the created YAML file
        """
        return self.create_temp_file(yaml_content, suffix=".yaml", prefix="test_")

    def create_temp_dir(self, prefix: str = "test_dir_") -> Path:
        """
        Create a temporary directory.

        Args:
            prefix: Directory name prefix

        Returns:
            Path to the created directory
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self.temp_files.append(temp_dir)
        return temp_dir

    def set_env_var(self, name: str, value: str) -> None:
        """
        Set an environment variable, saving original value for cleanup.

        Args:
            name: Environment variable name
            value: Environment variable value
        """
        if name not in self.original_env:
            self.original_env[name] = os.environ.get(name)
        os.environ[name] = value

    def unset_env_var(self, name: str) -> None:
        """
        Unset an environment variable, saving original value for cleanup.

        Args:
            name: Environment variable name
        """
        if name not in self.original_env:
            self.original_env[name] = os.environ.get(name)
        os.environ.pop(name, None)

    @contextmanager
    def temp_env_var(self, name: str, value: str):
        """
        Context manager for temporarily setting an environment variable.

        Args:
            name: Environment variable name
            value: Environment variable value
        """
        original_value = os.environ.get(name)
        try:
            os.environ[name] = value
            yield
        finally:
            if original_value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = original_value

    def assert_yaml_equal(self, actual: Any, expected: Any) -> None:
        """
        Assert that two YAML values are equal, with better error messages.

        Args:
            actual: Actual YAML value
            expected: Expected YAML value
        """
        assert (
            actual == expected
        ), f"YAML values not equal:\nActual: {actual}\nExpected: {expected}"

    def assert_contains_key(
        self, data: Dict[str, Any], key: str, expected_value: Any = None
    ) -> None:
        """
        Assert that a dictionary contains a specific key and optionally check its value.

        Args:
            data: Dictionary to check
            key: Key to look for
            expected_value: Expected value (optional)
        """
        assert key in data, f"Key '{key}' not found in data: {list(data.keys())}"

        if expected_value is not None:
            actual_value = data[key]
            assert (
                actual_value == expected_value
            ), f"Value for key '{key}' incorrect:\nActual: {actual_value}\nExpected: {expected_value}"


class ConstructorTestHelper:
    """Helper class for testing SmartYAML constructors."""

    @staticmethod
    def create_mock_loader(
        base_path: Optional[Path] = None,
        template_path: Optional[Path] = None,
        max_file_size: int = 1024 * 1024,
        max_recursion_depth: int = 10,
    ) -> Any:
        """
        Create a mock YAML loader for testing.

        Args:
            base_path: Base path for file resolution
            template_path: Template path for template resolution
            max_file_size: Maximum file size limit
            max_recursion_depth: Maximum recursion depth

        Returns:
            Mock loader object
        """
        from unittest.mock import Mock

        loader = Mock()
        loader.base_path = base_path or Path.cwd()
        loader.template_path = template_path
        loader.max_file_size = max_file_size
        loader.max_recursion_depth = max_recursion_depth
        loader.import_stack = set()

        # Mock common loader methods
        loader.construct_scalar.return_value = "test_value"
        loader.construct_sequence.return_value = ["test", "values"]
        loader.construct_mapping.return_value = {"test": "mapping"}

        return loader

    @staticmethod
    def create_mock_node(
        tag: str = "!test", value: Any = "test_value", start_mark: Optional[Any] = None
    ) -> Any:
        """
        Create a mock YAML node for testing.

        Args:
            tag: YAML tag
            value: Node value
            start_mark: Start mark for position information

        Returns:
            Mock YAML node
        """
        from unittest.mock import Mock

        node = Mock()
        node.tag = tag
        node.value = value
        node.start_mark = start_mark

        return node

    @staticmethod
    def create_scalar_node(value: str, tag: str = "tag:yaml.org,2002:str") -> Any:
        """Create a mock scalar YAML node."""
        return ConstructorTestHelper.create_mock_node(tag=tag, value=value)

    @staticmethod
    def create_sequence_node(
        values: List[str], tag: str = "tag:yaml.org,2002:seq"
    ) -> Any:
        """Create a mock sequence YAML node."""

        # Create scalar nodes for each value
        value_nodes = [ConstructorTestHelper.create_scalar_node(v) for v in values]
        return ConstructorTestHelper.create_mock_node(tag=tag, value=value_nodes)


class ErrorTestHelper:
    """Helper class for testing error handling."""

    @staticmethod
    def assert_error_contains(error: Exception, expected_substring: str) -> None:
        """
        Assert that an error message contains a specific substring.

        Args:
            error: Exception to check
            expected_substring: Expected substring in error message
        """
        error_message = str(error)
        assert (
            expected_substring in error_message
        ), f"Error message does not contain '{expected_substring}':\nActual: {error_message}"

    @staticmethod
    def assert_error_type(error: Exception, expected_type: type) -> None:
        """
        Assert that an error is of the expected type.

        Args:
            error: Exception to check
            expected_type: Expected exception type
        """
        assert isinstance(
            error, expected_type
        ), f"Error type incorrect:\nActual: {type(error).__name__}\nExpected: {expected_type.__name__}"

    @staticmethod
    def assert_constructor_error(
        error: Exception, directive_name: str, parameter_name: Optional[str] = None
    ) -> None:
        """
        Assert that a ConstructorError has the expected context.

        Args:
            error: Exception to check
            directive_name: Expected directive name
            parameter_name: Expected parameter name (optional)
        """
        from .exceptions import ConstructorError

        ErrorTestHelper.assert_error_type(error, ConstructorError)

        if hasattr(error, "directive_name"):
            assert (
                error.directive_name == directive_name
            ), f"Directive name incorrect: {error.directive_name} != {directive_name}"

        if parameter_name and hasattr(error, "parameter_name"):
            assert (
                error.parameter_name == parameter_name
            ), f"Parameter name incorrect: {error.parameter_name} != {parameter_name}"


# Pytest fixtures
@pytest.fixture
def temp_dir():
    """Pytest fixture for temporary directory."""
    temp_path = Path(tempfile.mkdtemp(prefix="smartyaml_test_"))
    yield temp_path
    # Cleanup
    import shutil

    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def mock_loader():
    """Pytest fixture for mock YAML loader."""
    return ConstructorTestHelper.create_mock_loader()


@pytest.fixture
def test_env_vars():
    """Pytest fixture for managing test environment variables."""
    original_vars = {}

    def set_var(name: str, value: str):
        if name not in original_vars:
            original_vars[name] = os.environ.get(name)
        os.environ[name] = value

    def unset_var(name: str):
        if name not in original_vars:
            original_vars[name] = os.environ.get(name)
        os.environ.pop(name, None)

    yield set_var, unset_var

    # Cleanup
    for name, original_value in original_vars.items():
        if original_value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = original_value


# Performance testing utilities
class PerformanceTestHelper:
    """Helper class for performance testing."""

    @staticmethod
    def measure_execution_time(func: callable, *args, **kwargs) -> tuple[Any, float]:
        """
        Measure execution time of a function.

        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Tuple of (result, execution_time_seconds)
        """
        import time

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time

    @staticmethod
    def assert_performance_threshold(
        func: callable, max_seconds: float, *args, **kwargs
    ) -> Any:
        """
        Assert that a function executes within a time threshold.

        Args:
            func: Function to test
            max_seconds: Maximum allowed execution time
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        result, execution_time = PerformanceTestHelper.measure_execution_time(
            func, *args, **kwargs
        )

        assert (
            execution_time <= max_seconds
        ), f"Function exceeded performance threshold: {execution_time:.4f}s > {max_seconds}s"

        return result
