"""
Template scenarios - __template metadata and inheritance.

This module runs all scenarios in the 'templates' category.
Tests template inheritance, overlay mode, and variable integration.
"""

from .test_runner import TestRunner


def test_templates_template_inheritance(env_vars):
    """Basic template inheritance with overlay mode."""
    runner = TestRunner()
    runner.load_and_compare_fixture("templates/template_inheritance", env_vars)


def test_templates_template_overlay_mode(env_vars):
    """Template overlay mode behavior - main content overlays on top of template."""
    runner = TestRunner()
    runner.load_and_compare_fixture("templates/template_overlay_mode", env_vars)


def test_templates_template_with_variables(env_vars):
    """Template inheritance with variables - main variables override template variables."""
    runner = TestRunner()
    runner.load_and_compare_fixture("templates/template_with_variables", env_vars)


def test_templates_template_use_basic(env_vars):
    """Basic template usage with use: format - loads from templates directory."""
    runner = TestRunner()
    runner.load_and_compare_fixture("templates/template_use_basic", env_vars)


def test_templates_template_use_nested(env_vars):
    """Nested template usage with use: format - loads from nested templates directory structure."""
    runner = TestRunner()
    runner.load_and_compare_fixture("templates/template_use_nested", env_vars)


def test_templates_template_use_overlay(env_vars):
    """Template with overlay mode using use: format - merges template content with main content."""
    runner = TestRunner()
    runner.load_and_compare_fixture("templates/template_use_overlay", env_vars)


def test_templates_template_use_with_vars(env_vars):
    """Template with variable inheritance using use: format - main file variables override template variables."""
    runner = TestRunner()
    runner.load_and_compare_fixture("templates/template_use_with_vars", env_vars)


def test_templates_template_nested_inheritance(env_vars):
    """Nested template inheritance - template that loads a template that loads another template (3-level inheritance chain)."""
    runner = TestRunner()
    runner.load_and_compare_fixture("templates/template_nested_inheritance", env_vars)