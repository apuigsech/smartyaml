"""
Stage 1: YAML Parsing and Version Checking

Initial parsing of YAML with custom constructors for SmartYAML directives
and version compatibility checking.
"""

import re
from typing import Any, Dict

import yaml
from yaml import SafeLoader

from ..config import SmartYAMLConfig
from ..exceptions import DirectiveSyntaxError, SmartYAMLError, VersionMismatchError


def _construct_directive(loader, node):
    """Construct directive data for later processing."""
    directive_name = node.tag[1:]  # Remove '!' prefix

    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        value = loader.construct_mapping(node)
    else:
        raise DirectiveSyntaxError(
            f"!{directive_name}",
            "scalar, sequence, or mapping",
            type(node).__name__,
        )

    return {
        "__directive__": directive_name,
        "__value__": value,
        "__line__": getattr(node, "start_mark", None),
    }


class SmartYAMLLoader(SafeLoader):
    """Custom YAML loader that handles SmartYAML directives with array syntax."""

    def __init__(self, stream, config: SmartYAMLConfig):
        super().__init__(stream)
        self.config = config


# Register constructors for all SmartYAML directives at module level
directives = [
    "env",
    "env_int",
    "env_float",
    "env_bool",
    "secret",
    "include",
    "include_if",
    "include_yaml",
    "include_yaml_if",
    "template",
    "template_if",
    "merge",
    "concat",
    "expand",
    "var",
    "if",
    "switch",
]

for directive in directives:
    SmartYAMLLoader.add_constructor(f"!{directive}", _construct_directive)


class YAMLParser:
    """Stage 1: Parse YAML and check version compatibility."""

    def __init__(self, config: SmartYAMLConfig):
        self.config = config

    def parse(self, yaml_content: str, context) -> Dict[str, Any]:
        """Parse YAML content and check version compatibility."""
        try:
            # Parse YAML with custom loader
            def create_loader(stream):
                return SmartYAMLLoader(stream, self.config)

            data = yaml.load(yaml_content, Loader=create_loader)

            if data is None:
                return {}

            if not isinstance(data, dict):
                raise SmartYAMLError("Root YAML element must be an object/dictionary")

            # Check version compatibility
            self._check_version_compatibility(data, context)

            return data

        except yaml.YAMLError as e:
            raise SmartYAMLError(
                f"Invalid YAML syntax: {e}", str(context.file_path)
            ) from e

    def _check_version_compatibility(self, data: Dict[str, Any], context) -> None:
        """Check if the __version field is compatible with current library version."""
        if "__version" not in data:
            return  # No version specified, assume compatible

        required_version = data["__version"]
        if not isinstance(required_version, str):
            raise SmartYAMLError(
                "__version must be a string", str(context.file_path), "__version"
            )

        # Simple semantic version comparison (major.minor.patch)
        current_version = self.config.version

        if not self._is_version_compatible(required_version, current_version):
            raise VersionMismatchError(
                required_version, current_version, str(context.file_path)
            )

    def _is_version_compatible(self, required: str, current: str) -> bool:
        """Check if current version is compatible with required version."""
        # Parse semantic versions
        required_parts = self._parse_semantic_version(required)
        current_parts = self._parse_semantic_version(current)

        if not required_parts or not current_parts:
            return True  # If parsing fails, assume compatible

        # Major version must match, minor and patch can be higher in current
        req_major, req_minor, req_patch = required_parts
        curr_major, curr_minor, curr_patch = current_parts

        if curr_major != req_major:
            return curr_major > req_major

        if curr_minor != req_minor:
            return curr_minor >= req_minor

        return curr_patch >= req_patch

    def _parse_semantic_version(self, version: str) -> tuple:
        """Parse a semantic version string into (major, minor, patch) tuple."""
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-.*)?(?:\+.*)?$"
        match = re.match(pattern, version)

        if not match:
            return None

        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
