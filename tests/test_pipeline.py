"""
Pipeline processing scenarios - Processing order and stage coordination.

This module runs all scenarios in the 'pipeline' category.
Tests the order and coordination of processing stages in SmartYAML.
"""

from .test_runner import TestRunner


def test_pipeline_processing_order(env_vars):
    """Pipeline processing order: template loading -> variable resolution -> directive processing."""
    runner = TestRunner()
    runner.load_and_compare_fixture("pipeline/processing_order", env_vars)