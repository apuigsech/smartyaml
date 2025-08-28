"""
File operation scenarios - !include and file-related directives.

This module runs all scenarios in the 'file_operations' category.
Tests file inclusion and external file processing.
"""

from .test_runner import TestRunner


def test_file_operations_include_basic(env_vars):
    """Basic include directive to include external YAML file."""
    runner = TestRunner()
    runner.load_and_compare_fixture("file_operations/include_basic", env_vars)


def test_file_operations_include_if_basic(env_vars):
    """!include_if directive includes file when condition is true."""
    runner = TestRunner()
    runner.load_and_compare_fixture("file_operations/include_if_basic", env_vars)


def test_file_operations_include_yaml_basic(env_vars):
    """!include_yaml loads raw YAML without processing directives."""
    runner = TestRunner()
    runner.load_and_compare_fixture("file_operations/include_yaml_basic", env_vars)


def test_file_operations_include_if_false_condition(env_vars):
    """!include_if directive returns null when condition is false."""
    runner = TestRunner()
    runner.load_and_compare_fixture("file_operations/include_if_false_condition", env_vars)