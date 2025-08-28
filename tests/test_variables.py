"""
Variable expansion scenarios - __vars metadata and {{variable}} syntax.

This module runs all scenarios in the 'variables' category.
Tests variable definition, expansion, and template processing.
"""

from .test_runner import TestRunner


def test_variables_basic_expansion(env_vars):
    """Basic variable expansion using __vars and {{variable}} syntax."""
    runner = TestRunner()
    runner.load_and_compare_fixture("variables/basic_expansion", env_vars)


def test_variables_expand_basic(env_vars):
    """Basic !expand directive functionality."""
    runner = TestRunner()
    runner.load_and_compare_fixture("variables/expand_basic", env_vars)


def test_variables_expand_in_directive_args(env_vars):
    """!expand directive working within other directive arguments."""
    runner = TestRunner()
    runner.load_and_compare_fixture("variables/expand_in_directive_args", env_vars)


def test_variables_expand_missing_vars(env_vars):
    """!expand directive handling missing variables gracefully."""
    runner = TestRunner()
    runner.load_and_compare_fixture("variables/expand_missing_vars", env_vars)


def test_variables_expand_nested_vars(env_vars):
    """!expand directive with nested variable references."""
    runner = TestRunner()
    runner.load_and_compare_fixture("variables/expand_nested_vars", env_vars)


def test_variables_expand_with_defaults(env_vars):
    """!expand directive with default values for missing variables."""
    runner = TestRunner()
    runner.load_and_compare_fixture("variables/expand_with_defaults", env_vars)


def test_variables_var_basic(env_vars):
    """Basic !var directive functionality with type preservation."""
    runner = TestRunner()
    runner.load_and_compare_fixture("variables/var_basic", env_vars)


def test_variables_var_with_defaults(env_vars):
    """!var directive with default values using pipe syntax."""
    runner = TestRunner()
    runner.load_and_compare_fixture("variables/var_with_defaults", env_vars)


def test_variables_var_nested_access(env_vars):
    """!var directive with nested variable access using dot notation."""
    runner = TestRunner()
    runner.load_and_compare_fixture("variables/var_nested_access", env_vars)