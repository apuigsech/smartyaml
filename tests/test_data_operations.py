"""
Data operation scenarios - !merge and !concat directives.

This module runs all scenarios in the 'data_operations' category.
Tests data manipulation and combination directives.
"""

from .test_runner import TestRunner


def test_data_operations_merge_simple(env_vars):
    """Simple merge directive combining two dictionaries."""
    runner = TestRunner()
    runner.load_and_compare_fixture("data_operations/merge_simple", env_vars)


def test_data_operations_concat_arrays(env_vars):
    """Concat directive combining multiple arrays into one."""
    runner = TestRunner()
    runner.load_and_compare_fixture("data_operations/concat_arrays", env_vars)