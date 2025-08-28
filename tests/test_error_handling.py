"""
Error handling scenarios - Exception testing and error cases.

This module runs all scenarios in the 'error_handling' category.
Tests that appropriate exceptions are raised for invalid inputs and missing files.
"""

from .test_runner import TestRunner


def test_error_handling_env_invalid_int(env_vars):
    """Error case: !env_int with invalid integer value should raise DirectiveProcessingError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/env_invalid_int", env_vars)


def test_error_handling_env_invalid_float(env_vars):
    """Error case: !env_float with invalid float value should raise DirectiveProcessingError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/env_invalid_float", env_vars)


def test_error_handling_env_invalid_bool(env_vars):
    """Error case: !env_bool with invalid boolean value should raise DirectiveProcessingError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/env_invalid_bool", env_vars)


def test_error_handling_switch_missing_args(env_vars):
    """Error case: !switch with missing arguments should raise DirectiveSyntaxError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/switch_missing_args", env_vars)


def test_error_handling_include_file_not_found(env_vars):
    """Error case: !include with nonexistent file should raise FileNotFoundError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/include_file_not_found", env_vars)


def test_error_handling_template_file_not_found(env_vars):
    """Error case: __template with nonexistent file should raise FileNotFoundError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/template_file_not_found", env_vars)


def test_error_handling_circular_reference(env_vars):
    """Circular variable references should raise CircularReferenceError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/circular_reference", env_vars)


def test_error_handling_invalid_yaml_syntax(env_vars):
    """Invalid YAML syntax should raise YAMLError or ParserError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/invalid_yaml_syntax", env_vars)


# Advanced error scenarios temporarily disabled pending adjustment to match actual SmartYAML behavior
def test_error_handling_merge_type_conflict(env_vars):
    """Merging incompatible types should raise DirectiveProcessingError or TypeError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/merge_type_conflict", env_vars)


def test_error_handling_concat_type_mismatch(env_vars):
    """Concatenating incompatible types should raise DirectiveProcessingError or TypeError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/concat_type_mismatch", env_vars)


def test_error_handling_invalid_directive_syntax(env_vars):
    """Invalid directive syntax should raise DirectiveSyntaxError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/invalid_directive_syntax", env_vars)


def test_error_handling_template_variable_conflict(env_vars):
    """Template variable conflicts should raise VariableConflictError (if strict mode) or resolve with main file precedence."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/template_variable_conflict", env_vars)


def test_error_handling_unknown_directive(env_vars):
    """Unknown directives should raise UnknownDirectiveError or ConstructorError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("error_handling/unknown_directive", env_vars)
