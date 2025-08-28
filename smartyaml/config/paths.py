"""
Path Configuration

Settings related to file paths, base directories, and path resolution.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from .core import ConfigSection, ConfigurationError


class PathConfig(ConfigSection):
    """Configuration for path-related settings."""

    def __init__(
        self,
        base_path: Optional[Path] = None,
        template_path: Optional[Path] = None,
        schema_base_path: Optional[Path] = None,
        templates_dir: Optional[str] = None,
    ):
        """
        Initialize path configuration.

        Args:
            base_path: Base directory for resolving relative paths
            template_path: Directory containing template files
            schema_base_path: Base directory for schema files
            templates_dir: Templates directory (can also be set via TEMPLATES_DIR env var)
        """
        self.base_path = self._resolve_path(base_path)
        self.template_path = self._resolve_path(template_path)
        self.schema_base_path = self._resolve_path(schema_base_path)

        # Handle templates directory from parameter or environment
        templates_dir = templates_dir or os.environ.get("TEMPLATES_DIR")
        if templates_dir:
            self.template_path = self._resolve_path(Path(templates_dir))

        self.validate()

    def _resolve_path(self, path: Optional[Path]) -> Optional[Path]:
        """Resolve and normalize a path."""
        if path is None:
            return None

        if isinstance(path, str):
            path = Path(path)

        return path.resolve() if path.is_absolute() else path

    def validate(self) -> None:
        """Validate path configuration settings."""
        # Check if template_path is relative but no base_path is set
        if (
            self.template_path
            and not self.template_path.is_absolute()
            and not self.base_path
        ):
            raise ConfigurationError(
                "template_path must be absolute or base_path must be set",
                "template_path",
            )

        # Check if schema_base_path is relative but no base_path is set
        if (
            self.schema_base_path
            and not self.schema_base_path.is_absolute()
            and not self.base_path
        ):
            raise ConfigurationError(
                "schema_base_path must be absolute or base_path must be set",
                "schema_base_path",
            )

    def merge_with(self, other: "PathConfig") -> "PathConfig":
        """Merge with another path configuration."""
        return PathConfig(
            base_path=other.base_path or self.base_path,
            template_path=other.template_path or self.template_path,
            schema_base_path=other.schema_base_path or self.schema_base_path,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert path configuration to dictionary."""
        return {
            "base_path": str(self.base_path) if self.base_path else None,
            "template_path": str(self.template_path) if self.template_path else None,
            "schema_base_path": (
                str(self.schema_base_path) if self.schema_base_path else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PathConfig":
        """Create path configuration from dictionary."""
        # Convert string paths back to Path objects
        processed_data = {}
        for key, value in data.items():
            if value is not None and key.endswith("_path"):
                processed_data[key] = Path(value)
            else:
                processed_data[key] = value

        return cls(**processed_data)

    def resolve_path(self, path: Path) -> Path:
        """Resolve a path relative to the base_path if needed."""
        if path.is_absolute():
            return path

        if self.base_path:
            return (self.base_path / path).resolve()

        return path.resolve()

    def get_template_path(self, template_name: str) -> Optional[Path]:
        """Get the full path for a template file."""
        if not self.template_path:
            return None

        # Convert dot notation to path (e.g., "sub.name" -> "sub/name.yaml")
        template_file = template_name.replace(".", "/") + ".yaml"
        return self.template_path / template_file

    def get_schema_path(self, schema_name: str) -> Optional[Path]:
        """Get the full path for a schema file."""
        if not self.schema_base_path:
            return None

        return self.schema_base_path / schema_name
