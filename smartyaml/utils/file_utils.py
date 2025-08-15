"""
File operations and caching utilities for SmartYAML
"""

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from ..config import get_config
from ..exceptions import ResourceLimitError, SmartYAMLFileNotFoundError


@dataclass
class CacheEntry:
    """File cache entry with content and metadata."""

    content: str
    timestamp: float
    file_mtime: float
    size: int


class FileCache:
    """Thread-safe file cache with TTL and size limits."""

    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._last_cleanup = time.time()

    def get(self, file_path: Path) -> Optional[str]:
        """Get cached file content if valid."""
        config = get_config()

        if not config.enable_file_caching:
            return None

        cache_key = str(file_path.resolve())
        entry = self._cache.get(cache_key)

        if entry is None:
            return None

        current_time = time.time()

        # Check if entry is expired
        if current_time - entry.timestamp > config.cache_ttl_seconds:
            del self._cache[cache_key]
            return None

        # Check if file has been modified
        try:
            current_mtime = file_path.stat().st_mtime
            if current_mtime != entry.file_mtime:
                del self._cache[cache_key]
                return None
        except OSError:
            # File no longer exists
            del self._cache[cache_key]
            return None

        return entry.content

    def put(self, file_path: Path, content: str) -> None:
        """Cache file content."""
        config = get_config()

        if not config.enable_file_caching:
            return

        try:
            file_stat = file_path.stat()
            cache_key = str(file_path.resolve())

            entry = CacheEntry(
                content=content,
                timestamp=time.time(),
                file_mtime=file_stat.st_mtime,
                size=len(content),
            )

            self._cache[cache_key] = entry

            # Check cache size limits and maybe cleanup
            self._enforce_size_limits()
            self._maybe_cleanup()

        except OSError:
            # Failed to get file stats, don't cache
            pass

    def _maybe_cleanup(self) -> None:
        """Perform lazy cleanup if enough time has passed since last cleanup."""
        get_config()
        current_time = time.time()

        # Only cleanup every 5 minutes to avoid overhead
        cleanup_interval = 300  # 5 minutes

        if current_time - self._last_cleanup > cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = current_time

    def _cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        config = get_config()
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if current_time - entry.timestamp > config.cache_ttl_seconds
        ]

        for key in expired_keys:
            del self._cache[key]

    def _enforce_size_limits(self) -> None:
        """Enforce cache size limits by removing oldest entries."""
        config = get_config()
        max_size_bytes = config.max_cache_size_mb * 1024 * 1024

        current_size = sum(entry.size for entry in self._cache.values())

        if current_size <= max_size_bytes:
            return

        # Sort by timestamp (oldest first)
        sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].timestamp)

        # Remove oldest entries until under limit
        for key, entry in sorted_entries:
            del self._cache[key]
            current_size -= entry.size

            if current_size <= max_size_bytes:
                break

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "entries": len(self._cache),
            "total_size_bytes": sum(entry.size for entry in self._cache.values()),
            "oldest_entry_age": int(
                time.time()
                - min(
                    (entry.timestamp for entry in self._cache.values()),
                    default=time.time(),
                )
            ),
        }


# Global file cache instance
_file_cache = FileCache()


def read_file(file_path: Path, max_size: Optional[int] = None) -> str:
    """
    Read file content safely with size limits and optional caching.

    Args:
        file_path: Path to file to read
        max_size: Maximum file size in bytes (uses config default if None)

    Returns:
        File content as string

    Raises:
        SmartYAMLFileNotFoundError: If file doesn't exist or can't be read
        ResourceLimitError: If file exceeds size limit
    """
    config = get_config()

    if max_size is None:
        max_size = config.max_file_size

    # Try cache first
    cached_content = _file_cache.get(file_path)
    if cached_content is not None:
        return cached_content

    try:
        # Check file size before reading
        file_size = file_path.stat().st_size
        if file_size > max_size:
            raise ResourceLimitError(
                f"File '{file_path}' size ({file_size} bytes) exceeds limit ({max_size} bytes)"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Cache the content
        _file_cache.put(file_path, content)

        return content

    except OSError as e:
        raise SmartYAMLFileNotFoundError(f"Cannot read file '{file_path}': {e}")


def get_file_hash(file_path: Path) -> str:
    """
    Get SHA-256 hash of file content.

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal hash string
    """
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()
    except OSError as e:
        raise SmartYAMLFileNotFoundError(
            f"Cannot read file '{file_path}' for hashing: {e}"
        )


def clear_file_cache() -> None:
    """Clear the global file cache."""
    _file_cache.clear()


def get_cache_stats() -> Dict[str, int]:
    """Get file cache statistics."""
    return _file_cache.get_stats()
