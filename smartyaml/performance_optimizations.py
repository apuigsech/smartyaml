"""
Performance optimizations for SmartYAML
"""

import os
import re
from functools import lru_cache
from typing import Dict, Optional, Pattern, Set


class OptimizedPatterns:
    """Pre-compiled regex patterns and optimized string operations."""

    # Pre-compile all regex patterns used across the system
    ENV_VAR_PATTERN: Pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
    FILENAME_PATTERN: Pattern = re.compile(r'^[^<>:"|?*\x00-\x1f]+$')
    TEMPLATE_NAME_PATTERN: Pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")

    # YAML parsing patterns
    TEMPLATE_DIRECTIVE_PATTERN: Pattern = re.compile(
        r"^\s*__template\s*:", re.MULTILINE
    )
    VARS_SECTION_PATTERN: Pattern = re.compile(
        r"^__vars:\s*\n((?:[ ]{2}.*\n)*)", re.MULTILINE
    )

    # Template processing patterns
    TEMPLATE_REFERENCE_PATTERN: Pattern = re.compile(
        r"!template\s*\([^)]+\)|<<:\s*!template\s*\([^)]+\)"
    )
    TEMPLATE_NAME_EXTRACT_PATTERN: Pattern = re.compile(
        r"!template\s*\(\s*([^)]+)\s*\)"
    )

    # Common string operations
    SAFE_PATH_CHARS: Set[str] = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./\\"
    )

    @staticmethod
    def is_valid_env_var_name(name: str) -> bool:
        """Optimized environment variable name validation."""
        return bool(OptimizedPatterns.ENV_VAR_PATTERN.match(name))

    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """Optimized filename validation."""
        return bool(OptimizedPatterns.FILENAME_PATTERN.match(filename))

    @staticmethod
    def has_template_directive(yaml_content: str) -> bool:
        """Optimized check for __template directive in YAML content."""
        return bool(OptimizedPatterns.TEMPLATE_DIRECTIVE_PATTERN.search(yaml_content))

    @staticmethod
    def extract_vars_section(yaml_content: str) -> Optional[str]:
        """Optimized extraction of __vars section from YAML content."""
        match = OptimizedPatterns.VARS_SECTION_PATTERN.search(yaml_content)
        if match:
            return "__vars:\n" + match.group(1)
        return None

    @staticmethod
    def has_template_references(content: str) -> bool:
        """Optimized check for !template directive references in content."""
        return bool(OptimizedPatterns.TEMPLATE_REFERENCE_PATTERN.search(content))

    @staticmethod
    def extract_template_names(content: str) -> list:
        """Optimized extraction of template names from !template directives."""
        matches = OptimizedPatterns.TEMPLATE_NAME_EXTRACT_PATTERN.findall(content)
        return [match.strip() for match in matches]


class CachedOperations:
    """Cached expensive operations."""

    @staticmethod
    def resolve_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
        """Environment variable resolution (caching disabled for testing compatibility)."""
        return os.environ.get(var_name, default)

    @staticmethod
    @lru_cache(maxsize=128)
    def normalize_path_string(path_str: str) -> str:
        """Cached path normalization."""
        # Use more efficient string operations
        normalized = path_str.replace("\\", "/")

        # Handle multiple consecutive slashes
        while "//" in normalized:
            normalized = normalized.replace("//", "/")

        return normalized

    @staticmethod
    @lru_cache(maxsize=64)
    def get_file_extension(filename: str) -> str:
        """Cached file extension extraction."""
        return filename.split(".")[-1].lower() if "." in filename else ""


class StringOptimizations:
    """Optimized string processing utilities."""

    @staticmethod
    def join_with_separator(parts: list, separator: str = ", ") -> str:
        """Memory-efficient string joining with pre-allocation."""
        if not parts:
            return ""
        if len(parts) == 1:
            return str(parts[0])

        # Use join which is more efficient than concatenation
        return separator.join(str(part) for part in parts)

    @staticmethod
    def build_context_message(
        parts: Dict[str, str], prefix: str = "", suffix: str = ""
    ) -> str:
        """Optimized context message building."""
        if not parts:
            return ""

        # Filter non-empty parts efficiently
        valid_parts = [f"{k}={v}" for k, v in parts.items() if v]

        if not valid_parts:
            return ""

        # Build message efficiently
        content = StringOptimizations.join_with_separator(valid_parts)
        return f"{prefix}{content}{suffix}"


class LazyImports:
    """Lazy import system to reduce startup time."""

    _imported_modules: Dict[str, object] = {}

    @classmethod
    def get_yaml(cls):
        """Lazy import of yaml module."""
        if "yaml" not in cls._imported_modules:
            import yaml

            cls._imported_modules["yaml"] = yaml
        return cls._imported_modules["yaml"]

    @classmethod
    def get_pathlib(cls):
        """Lazy import of pathlib module."""
        if "pathlib" not in cls._imported_modules:
            from pathlib import Path

            cls._imported_modules["pathlib"] = Path
        return cls._imported_modules["pathlib"]

    @classmethod
    def get_base64(cls):
        """Lazy import of base64 module."""
        if "base64" not in cls._imported_modules:
            import base64

            cls._imported_modules["base64"] = base64
        return cls._imported_modules["base64"]


class MemoryOptimizations:
    """Memory usage optimizations."""

    @staticmethod
    def efficient_dict_merge(base_dict: dict, update_dict: dict) -> dict:
        """Memory-efficient dictionary merge."""
        if not update_dict:
            return base_dict.copy()
        if not base_dict:
            return update_dict.copy()

        # Use dict comprehension for efficiency
        result = {**base_dict}
        result.update(update_dict)
        return result

    @staticmethod
    def compact_string_list(strings: list) -> list:
        """Remove empty strings and duplicates efficiently."""
        seen = set()
        result = []
        for s in strings:
            if s and s not in seen:
                seen.add(s)
                result.append(s)
        return result


# Global instances for reuse
optimized_patterns = OptimizedPatterns()
cached_operations = CachedOperations()
string_optimizations = StringOptimizations()
lazy_imports = LazyImports()
memory_optimizations = MemoryOptimizations()
