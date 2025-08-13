"""
Content reading utilities for SmartYAML loading pipeline.
"""

from pathlib import Path
from typing import Tuple, Union


class ContentReader:
    """
    Handles reading YAML content from various sources.

    This class centralizes content reading logic that was previously
    scattered across load() and loads() functions.
    """

    def read_from_stream(
        self, stream: Union[str, Path], base_path: Path = None
    ) -> Tuple[str, Path]:
        """
        Read content from a stream (file path or string content).

        Args:
            stream: Either a file path or string content
            base_path: Base directory for resolving relative paths

        Returns:
            Tuple of (content, resolved_base_path)
        """
        # Check if stream is explicitly a Path object or a string that represents an existing file
        if isinstance(stream, Path):
            return self._read_from_file(stream, base_path)
        elif isinstance(stream, str):
            # Only treat as file path if it looks like a reasonable path and exists
            # This avoids treating long YAML content as a file path
            if len(stream) < 1000 and not stream.startswith(("\n", " ", "\t")):
                try:
                    path = Path(stream)
                    if path.exists():
                        return self._read_from_file(path, base_path)
                except (OSError, ValueError):
                    # Not a valid path, treat as string content
                    pass
            return self._read_from_string(stream, base_path)
        else:
            return self._read_from_string(str(stream), base_path)

    def _read_from_file(
        self, file_path: Path, base_path: Path = None
    ) -> Tuple[str, Path]:
        """Read content from a file."""
        resolved_path = file_path.resolve()

        with open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Use file's parent directory as base_path if not provided
        resolved_base_path = base_path.resolve() if base_path else resolved_path.parent

        return content, resolved_base_path

    def _read_from_string(
        self, content: str, base_path: Path = None
    ) -> Tuple[str, Path]:
        """Read content from a string."""
        resolved_base_path = base_path.resolve() if base_path else Path.cwd()
        return content, resolved_base_path
