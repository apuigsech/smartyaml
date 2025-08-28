"""
Fixture-based testing platform for SmartYAML.

This module provides a simple framework for testing SmartYAML functionality
using YAML fixture files instead of hardcoded test cases.

Convention:
- Each test fixture is in its own directory under tests/fixtures/
- main.yaml: Input file to be processed by SmartYAML
- output.yaml: Expected result after processing
- config.yaml: (Optional) Environment variables and configuration
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import pytest
import smartyaml
from .conftest import assert_yaml_equal


class FixtureConfig:
    """Configuration for a test fixture."""
    
    def __init__(self, fixture_path: Path):
        self.fixture_path = fixture_path
        self.config_path = fixture_path / "config.yaml"
        self.config = {}
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
    
    @property
    def env_vars(self) -> Dict[str, str]:
        """Get environment variables for this fixture."""
        return self.config.get('env_vars', {})
    
    @property
    def smartyaml_config(self) -> Dict[str, Any]:
        """Get SmartYAML configuration for this fixture."""
        return self.config.get('smartyaml_config', {})
    
    @property
    def description(self) -> str:
        """Get fixture description."""
        return self.config.get('description', '')
    
    @property
    def expected_error(self) -> Optional[str]:
        """Get expected error type for error fixtures."""
        return self.config.get('expected_error')


class TestRunner:
    """Main class for running YAML test fixtures."""
    
    def __init__(self, fixtures_root: Path = None):
        if fixtures_root is None:
            fixtures_root = Path(__file__).parent / "fixtures"
        self.fixtures_root = fixtures_root
        self.index_path = fixtures_root / "index.yaml"
    
    def load_fixture_index(self) -> Dict[str, List[Dict]]:
        """Load the fixture index file."""
        if not self.index_path.exists():
            return {"fixtures": {}}
        
        with open(self.index_path, 'r') as f:
            return yaml.safe_load(f) or {"fixtures": {}}
    
    def get_all_fixtures(self) -> List[Dict[str, str]]:
        """Get all test fixtures from the index."""
        index = self.load_fixture_index()
        all_fixtures = []
        
        for category, fixtures in index.get("fixtures", {}).items():
            for fixture in fixtures:
                fixture_info = {
                    "category": category,
                    "name": fixture["name"],
                    "path": fixture["path"],
                    "description": fixture.get("description", ""),
                    "full_path": self.fixtures_root / fixture["path"]
                }
                all_fixtures.append(fixture_info)
        
        return all_fixtures
    
    def run_fixture(self, fixture_path: Path, env_setup=None) -> bool:
        """
        Run a single test fixture.
        
        Args:
            fixture_path: Path to test fixture directory
            env_setup: Optional environment setup fixture
            
        Returns:
            True if test passes, False otherwise
        """
        main_yaml = fixture_path / "main.yaml"
        output_yaml = fixture_path / "output.yaml"
        
        if not main_yaml.exists():
            raise FileNotFoundError(f"main.yaml not found in {fixture_path}")
        
        # Load fixture configuration
        config = FixtureConfig(fixture_path)
        
        # Set up environment variables
        if env_setup:
            for key, value in config.env_vars.items():
                env_setup.set(key, value)
        
        # Check if this is an error fixture
        if config.expected_error:
            # This fixture expects an error
            try:
                if config.smartyaml_config:
                    smartyaml_config = smartyaml.SmartYAMLConfig(**config.smartyaml_config)
                    result = smartyaml.load(main_yaml, config=smartyaml_config)
                else:
                    result = smartyaml.load(main_yaml)
                
                # If we get here, the expected error didn't occur
                raise AssertionError(
                    f"Scenario {fixture_path.name} expected {config.expected_error} but no error occurred"
                )
            except Exception as e:
                # Check if the error type matches expected
                expected_error_name = config.expected_error
                actual_error_name = type(e).__name__
                
                if expected_error_name in actual_error_name or actual_error_name == expected_error_name:
                    return True  # Expected error occurred
                else:
                    raise AssertionError(
                        f"Scenario {fixture_path.name} expected {expected_error_name} but got {actual_error_name}: {str(e)}"
                    ) from e
        else:
            # Normal fixture with expected output
            if not output_yaml.exists():
                raise FileNotFoundError(f"output.yaml not found in {fixture_path} (required for non-error fixtures)")
            
            # Load expected output
            with open(output_yaml, 'r') as f:
                expected = yaml.safe_load(f)
            
            # Process main.yaml with SmartYAML
            if config.smartyaml_config:
                smartyaml_config = smartyaml.SmartYAMLConfig(**config.smartyaml_config)
                result = smartyaml.load(main_yaml, config=smartyaml_config)
            else:
                result = smartyaml.load(main_yaml)
            
            # Compare results
            try:
                assert_yaml_equal(result, expected)
                return True
            except AssertionError as e:
                # Re-raise with fixture context
                raise AssertionError(
                    f"Scenario {fixture_path.name} failed:\n{str(e)}"
                ) from e
    
    def load_and_compare_fixture(self, fixture_path: str, env_setup=None) -> bool:
        """
        Helper function for manual testing.
        
        Args:
            fixture_path: Relative path from fixtures root (e.g., "conditionals/switch_basic")
            env_setup: Optional environment setup fixture
            
        Returns:
            True if test passes
        """
        full_path = self.fixtures_root / fixture_path
        return self.run_fixture(full_path, env_setup)


def generate_fixture_tests():
    """
    Generate pytest test functions from fixture index.
    
    This function is called by conftest.py to dynamically create tests.
    """
    runner = TestRunner()
    fixtures = runner.get_all_fixtures()
    
    test_functions = []
    
    for fixture in fixtures:
        def create_test_function(fixture_info):
            def test_fixture(env_vars):
                """Generated test function for fixture."""
                runner = TestRunner()
                runner.run_fixture(Path(fixture_info["full_path"]), env_vars)
            
            # Set test metadata
            test_fixture.__name__ = f"test_fixture_{fixture_info['category']}_{fixture_info['name']}"
            test_fixture.__doc__ = fixture_info['description'] or f"Test fixture {fixture_info['name']}"
            
            return test_fixture
        
        test_functions.append(create_test_function(fixture))
    
    return test_functions


# Convenience functions for direct usage
def run_fixture_test(fixture_path: str, env_setup=None) -> bool:
    """
    Run a single fixture test by path.
    
    Args:
        fixture_path: Relative path from fixtures root
        env_setup: Optional environment setup fixture
    
    Returns:
        True if test passes
    """
    runner = TestRunner()
    return runner.load_and_compare_fixture(fixture_path, env_setup)


def list_all_fixtures() -> List[str]:
    """List all available fixtures."""
    runner = TestRunner()
    fixtures = runner.get_all_fixtures()
    return [f"{s['category']}/{s['name']}: {s['description']}" for s in fixtures]