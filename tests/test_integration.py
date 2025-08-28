"""
Integration scenarios - Multiple directive combinations.

This module runs all scenarios in the 'integration' category.
Tests complex scenarios combining multiple SmartYAML features.
"""

from .test_runner import TestRunner


def test_integration_switch_env_merge(env_vars):
    """Integration test combining switch, env, merge, concat, if, and expand directives."""
    runner = TestRunner()
    runner.load_and_compare_fixture("integration/switch_env_merge", env_vars)