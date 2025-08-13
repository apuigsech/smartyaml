"""
Constants used throughout SmartYAML.

This module centralizes all magic strings and constants to improve maintainability.
"""

# Template and metadata field names
TEMPLATE_KEY = "__template"
VARS_KEY = "__vars"
DEFERRED_EXPANSION_KEY = "__smartyaml_expand_deferred"
EXTEND_MARKER_KEY = "__smartyaml_extend_marker"

# YAML tags and directives
TAG_PREFIX = "!"
MERGE_KEY = "<<"

# Common directive names
DIRECTIVE_IMPORT = "!import"
DIRECTIVE_IMPORT_YAML = "!import_yaml"
DIRECTIVE_EXPAND = "!expand"
DIRECTIVE_ENV = "!env"
DIRECTIVE_TEMPLATE = "!template"
DIRECTIVE_IF_ENV = "!if_env"
DIRECTIVE_BASE64 = "!base64"
DIRECTIVE_EXTEND = "!extend"

# Default limits and settings
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_MAX_RECURSION_DEPTH = 10
DEFAULT_CACHE_SIZE = 128

# File extensions and patterns
YAML_EXTENSIONS = {".yaml", ".yml"}
TEMPLATE_EXTENSIONS = {".html", ".txt", ".md", ".xml", ".json"}

# Environment variable patterns
ENV_VAR_PATTERN = r"^[A-Za-z_][A-Za-z0-9_-]*$"
VARIABLE_PATTERN = r"\{\{([^}]+)\}\}"

# Error message templates
ERROR_FILE_NOT_FOUND = "File not found: {file_path}. Please check the file path and ensure the file exists."
ERROR_CIRCULAR_IMPORT = "Circular import detected: {file_path}"
ERROR_VARIABLE_NOT_FOUND = "Variable '{var_name}' not found in substitution context"
ERROR_INVALID_DIRECTIVE = "Invalid directive: {directive_name}"
