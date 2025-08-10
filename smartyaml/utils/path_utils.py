"""
Path resolution and validation utilities for SmartYAML
"""

from pathlib import Path
from typing import Optional, Union

from ..config import get_config
from ..exceptions import InvalidPathError


def resolve_path(
    path: Union[str, Path], base_path: Path, allow_absolute: Optional[bool] = None
) -> Path:
    """
    Resolve a path relative to base_path with security checks.

    Args:
        path: Path to resolve (can be relative or absolute)
        base_path: Base directory for relative path resolution
        allow_absolute: Whether to allow absolute paths outside base_path (uses config default if None)

    Returns:
        Resolved absolute path

    Raises:
        InvalidPathError: If the path tries to access outside allowed directories
    """
    config = get_config()
    if allow_absolute is None:
        allow_absolute = config.allow_absolute_paths

    path = Path(path)

    # Normalize and resolve the path
    if path.is_absolute():
        resolved = path.resolve()
    else:
        resolved = (base_path / path).resolve()

    # Security check: ensure resolved path is within base_path or its subdirectories
    try:
        resolved.relative_to(base_path.resolve())
    except ValueError:
        # Path is outside base_path
        if not allow_absolute:
            raise InvalidPathError(
                f"Path '{path}' resolves outside the base directory: {resolved}"
            )

        # For absolute paths, perform additional security checks
        if path.is_absolute():
            if config.is_path_restricted(resolved):
                raise InvalidPathError(
                    f"Access to system path '{resolved}' is not allowed"
                )
        else:
            raise InvalidPathError(
                f"Relative path '{path}' resolves outside base directory: {resolved}"
            )

    return resolved


def is_safe_path(path: Path) -> bool:
    """
    Check if a path is safe to access.

    Args:
        path: Path to check

    Returns:
        True if the path is safe to access
    """
    config = get_config()
    return not config.is_path_restricted(path)


def normalize_path(path: Union[str, Path]) -> Path:
    """
    Normalize a path by resolving . and .. components.

    Args:
        path: Path to normalize

    Returns:
        Normalized path
    """
    return Path(path).resolve()


def get_relative_path(path: Path, base_path: Path) -> Optional[Path]:
    """
    Get relative path from base_path to path if possible.

    Args:
        path: Target path
        base_path: Base path

    Returns:
        Relative path if possible, None otherwise
    """
    try:
        return path.relative_to(base_path)
    except ValueError:
        return None
