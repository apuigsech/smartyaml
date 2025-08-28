"""
Metadata processing scenarios - __vars, __version, __schema fields.

This module runs all scenarios in the 'metadata' category.
Tests metadata field processing, variable definitions, and field stripping.
"""

from .test_runner import TestRunner


def test_metadata_metadata_stripped(env_vars):
    """Metadata fields (__*) should be stripped from output and variables processed."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/metadata_stripped", env_vars)


def test_metadata_vars_nested(env_vars):
    """Nested variable access using dot notation (obj.property.subproperty)."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/vars_nested", env_vars)


def test_metadata_version_compatibility_match(env_vars):
    """__version matches current library version - should process without error."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/version_compatibility_match", env_vars)


def test_metadata_version_compatibility_mismatch(env_vars):
    """__version higher than library version should raise VersionMismatchError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/version_compatibility_mismatch", env_vars)


def test_metadata_version_missing(env_vars):
    """Missing __version should assume compatibility and process normally."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/version_missing", env_vars)


def test_metadata_version_invalid_format(env_vars):
    """Invalid __version format should raise VersionMismatchError or DirectiveSyntaxError."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/version_invalid_format", env_vars)


def test_metadata_schema_validation_success(env_vars):
    """Successful schema validation - data matches JSON Schema requirements."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/schema_validation_success", env_vars)


def test_metadata_schema_validation_success_complex(env_vars):
    """Schema validation success with required fields - metadata field should be stripped and data should pass validation."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/schema_validation_failure", env_vars)


def test_metadata_schema_with_include(env_vars):
    """__schema using !include directive to load external JSON Schema file."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/schema_with_include", env_vars)


def test_metadata_schema_missing(env_vars):
    """Missing __schema should skip validation gracefully and process normally."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/schema_missing", env_vars)


def test_metadata_schema_complex_types(env_vars):
    """Complex schema validation with arrays, nested objects, enums, patterns, and required fields."""
    runner = TestRunner()
    runner.load_and_compare_fixture("metadata/schema_complex_types", env_vars)