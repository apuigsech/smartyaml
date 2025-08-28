"""
Conditional directive scenarios - Switch and If directives.

This module runs all scenarios in the 'conditionals' category.
Tests various switch directive formats and conditional logic.
"""

from .test_runner import TestRunner


def test_conditionals_switch_basic(env_vars):
    """Basic switch directive with environment variable (flattened format)."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/switch_basic", env_vars)


def test_conditionals_switch_with_default(env_vars):
    """Switch directive with default case fallback (flattened format)."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/switch_with_default", env_vars)


def test_conditionals_switch_array_format(env_vars):
    """Switch directive using array format to test compatibility."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/switch_array_format", env_vars)


def test_conditionals_switch_single_value(env_vars):
    """Switch directive returning single value when only one key-value pair remains."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/switch_single_value", env_vars)


def test_conditionals_switch_no_match(env_vars):
    """Switch directive with no matching case and no default (returns null)."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/switch_no_match", env_vars)


def test_conditionals_if_basic(env_vars):
    """Basic !if directive with environment variable conditions."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/if_basic", env_vars)


def test_conditionals_if_complex_value(env_vars):
    """!if directive with complex nested value structure."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/if_complex_value", env_vars)


def test_conditionals_if_nested(env_vars):
    """!if directive with nested conditional logic."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/if_nested", env_vars)


def test_conditionals_if_array_format(env_vars):
    """!if directive using array format to test backward compatibility."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/if_array_format", env_vars)


def test_conditionals_if_flattened_format(env_vars):
    """!if directive using flattened format (recommended syntax)."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/if_flattened_format", env_vars)


def test_conditionals_if_with_else(env_vars):
    """!if directive with else clause using flattened format."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/if_with_else", env_vars)


def test_conditionals_if_array_with_else(env_vars):
    """!if directive with else clause using array format."""
    runner = TestRunner()
    runner.load_and_compare_fixture("conditionals/if_array_with_else", env_vars)