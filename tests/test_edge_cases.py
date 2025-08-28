"""
Edge case scenarios - Unusual but valid configurations.

This module runs all scenarios in the 'edge_cases' category.
Tests edge cases, boundary conditions, and unusual but valid YAML configurations.
"""

from .test_runner import TestRunner


def test_edge_cases_only_metadata(env_vars):
    """Edge case: YAML with only metadata fields should result in empty output."""
    runner = TestRunner()
    runner.load_and_compare_fixture("edge_cases/only_metadata", env_vars)


def test_edge_cases_undefined_variables(env_vars):
    """Edge case: undefined variables should remain as literal strings."""
    runner = TestRunner()
    runner.load_and_compare_fixture("edge_cases/undefined_variables", env_vars)


def test_edge_cases_deeply_nested_vars(env_vars):
    """Edge case: deeply nested variable access (6+ levels deep)."""
    runner = TestRunner()
    runner.load_and_compare_fixture("edge_cases/deeply_nested_vars", env_vars)