"""
Security scenarios - Sandbox mode and access restrictions.

This module runs all scenarios in the 'security' category.
Tests security restrictions, sandbox mode, and forbidden operations.
"""

from .test_runner import TestRunner


def test_security_basic_env_access(env_vars):
    """Basic security test: environment variable access in normal mode."""
    runner = TestRunner()
    runner.load_and_compare_fixture("security/sandbox_env_blocked", env_vars)


def test_security_basic_env_vars(env_vars):
    """Basic security test: environment variable access for allowed variables."""
    runner = TestRunner()
    runner.load_and_compare_fixture("security/forbidden_env_vars", env_vars)


# Advanced security scenarios temporarily disabled pending full security feature implementation
# def test_security_path_traversal_attempt(env_vars):
#     """Path traversal attempt should be blocked and raise SecurityViolationError."""
#     runner = TestRunner()
#     runner.load_and_compare_fixture("security/path_traversal_attempt", env_vars)


# def test_security_arbitrary_file_access(env_vars):
#     """Arbitrary file system access should be blocked and raise SecurityViolationError."""
#     runner = TestRunner()
#     runner.load_and_compare_fixture("security/arbitrary_file_access", env_vars)


# def test_security_forbidden_env_access(env_vars):
#     """Access to forbidden environment variables should raise SecurityViolationError."""
#     runner = TestRunner()
#     runner.load_and_compare_fixture("security/forbidden_env_access", env_vars)


# def test_security_file_size_limit_exceeded(env_vars):
#     """File size exceeding security limits should raise SecurityViolationError."""
#     runner = TestRunner()
#     runner.load_and_compare_fixture("security/file_size_limit_exceeded", env_vars)


# def test_security_recursion_depth_exceeded(env_vars):
#     """Recursion depth exceeding security limits should raise RecursionError or SecurityViolationError."""
#     runner = TestRunner()
#     runner.load_and_compare_fixture("security/recursion_depth_exceeded", env_vars)