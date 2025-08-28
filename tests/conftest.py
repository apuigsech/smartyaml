"""
Test configuration and shared fixtures for SmartYAML tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def tmp_path():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def fixtures_path():
    """Get path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def env_vars():
    """Context manager for setting environment variables during tests."""
    class EnvVarsManager:
        def __init__(self):
            self._original = {}
        
        def set(self, name: str, value: str):
            """Set an environment variable."""
            if name in os.environ:
                self._original[name] = os.environ[name]
            else:
                self._original[name] = None
            os.environ[name] = value
        
        def clear(self, name: str):
            """Clear an environment variable."""
            if name in os.environ:
                self._original[name] = os.environ[name]
                del os.environ[name]
            else:
                self._original[name] = None
        
        def restore(self):
            """Restore original environment state."""
            for name, original_value in self._original.items():
                if original_value is None:
                    if name in os.environ:
                        del os.environ[name]
                else:
                    os.environ[name] = original_value
            self._original.clear()
    
    manager = EnvVarsManager()
    yield manager
    manager.restore()


def create_test_file(path: Path, content: str) -> Path:
    """Helper function to create test files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def assert_yaml_equal(actual: Any, expected: Any, msg: str = None):
    """Assert that two YAML structures are equal."""
    if msg:
        assert actual == expected, f"{msg}: Expected {expected}, got {actual}"
    else:
        assert actual == expected, f"Expected {expected}, got {actual}"


# Dynamic test generation for scenario-based tests
def pytest_generate_tests(metafunc):
    """Generate tests dynamically from scenario index."""
    if metafunc.function.__name__ == "test_scenario" and "scenario_info" in metafunc.fixturenames:
        try:
            from .test_runner import ScenarioRunner
            
            runner = ScenarioRunner()
            scenarios = runner.get_all_scenarios()
            
            # Create test parameters
            test_ids = []
            test_params = []
            
            for scenario in scenarios:
                test_id = f"{scenario['category']}__{scenario['name']}"
                test_ids.append(test_id)
                test_params.append(scenario)
            
            if test_params:  # Only parametrize if we have scenarios
                metafunc.parametrize("scenario_info", test_params, ids=test_ids)
            
        except (ImportError, FileNotFoundError, Exception):
            # If scenario runner or index not available, skip parametrization
            pass