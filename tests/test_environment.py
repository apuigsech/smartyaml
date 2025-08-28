"""
Environment variable scenarios - !env, !env_int, !env_bool, !env_float directives.

This module runs all scenarios in the 'environment' category.
Tests environment variable access and type conversion.
"""

from .test_runner import TestRunner


def test_environment_env_basic(env_vars):
    """Basic environment variable usage with !env directive."""
    runner = TestRunner()
    runner.load_and_compare_fixture("environment/env_basic", env_vars)


def test_environment_env_typed(env_vars):
    """Typed environment variables (!env_int, !env_bool, !env_float)."""
    runner = TestRunner()
    runner.load_and_compare_fixture("environment/env_typed", env_vars)