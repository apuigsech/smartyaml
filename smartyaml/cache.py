"""
Caching system for SmartYAML processing

Provides intelligent caching for file contents, processed templates,
compiled schemas, and variable expansions to improve performance.
"""

import hashlib
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class CacheEntry:
    """Single cache entry with metadata."""

    def __init__(self, key: str, value: Any, ttl: Optional[float] = None):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 1
        self.last_access = self.created_at

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self):
        """Mark this entry as recently accessed."""
        self.last_access = time.time()
        self.access_count += 1


class SmartYAMLCache:
    """Thread-safe LRU cache with TTL support for SmartYAML processing."""

    def __init__(self, max_size: int = 100, default_ttl: Optional[float] = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl  # 1 hour default
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0}

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._stats["expired"] += 1
                self._stats["misses"] += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._stats["hits"] += 1

            return entry.value

    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put a value in cache."""
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl

            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]

            # Add new entry
            entry = CacheEntry(key, value, ttl)
            self._cache[key] = entry

            # Check size limit and evict if necessary
            while len(self._cache) > self.max_size:
                # Remove least recently used
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1

    def invalidate(self, key: str) -> bool:
        """Remove a specific key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                self._stats["expired"] += 1

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self._stats["evictions"],
                "expired": self._stats["expired"],
            }


class FileContentCache:
    """Specialized cache for file contents with modification time checking."""

    def __init__(self, cache: SmartYAMLCache):
        self.cache = cache

    def get_file_content(self, file_path: Path) -> Optional[str]:
        """Get file content from cache, checking modification time."""
        if not file_path.exists():
            return None

        # Create cache key including modification time
        stat = file_path.stat()
        cache_key = f"file:{file_path}:{stat.st_mtime}:{stat.st_size}"

        return self.cache.get(cache_key)

    def put_file_content(self, file_path: Path, content: str) -> None:
        """Cache file content with modification time."""
        if not file_path.exists():
            return

        stat = file_path.stat()
        cache_key = f"file:{file_path}:{stat.st_mtime}:{stat.st_size}"

        # Cache for longer since files change less frequently
        self.cache.put(cache_key, content, ttl=7200)  # 2 hours


class ProcessedDataCache:
    """Cache for processed YAML data with dependency tracking."""

    def __init__(self, cache: SmartYAMLCache):
        self.cache = cache

    def get_processed_data(
        self, content_hash: str, config_hash: str, dependencies: Tuple[str, ...]
    ) -> Optional[Any]:
        """Get processed data from cache."""
        cache_key = f"processed:{content_hash}:{config_hash}:{hash(dependencies)}"
        return self.cache.get(cache_key)

    def put_processed_data(
        self,
        content_hash: str,
        config_hash: str,
        dependencies: Tuple[str, ...],
        data: Any,
    ) -> None:
        """Cache processed data."""
        cache_key = f"processed:{content_hash}:{config_hash}:{hash(dependencies)}"
        self.cache.put(cache_key, data, ttl=1800)  # 30 minutes

    def compute_content_hash(self, content: str) -> str:
        """Compute hash of content for cache key."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def compute_config_hash(self, config) -> str:
        """Compute hash of configuration for cache key."""
        # Create a deterministic representation of config
        config_repr = {
            "strict_variables": config.strict_variables,
            "validate_schema": config.validate_schema,
            "remove_metadata": config.remove_metadata,
            "template_path": (
                str(config.template_path) if config.template_path else None
            ),
            "variables": sorted(config.variables.items()) if config.variables else [],
        }

        config_str = str(sorted(config_repr.items()))
        return hashlib.sha256(config_str.encode("utf-8")).hexdigest()[:16]


class CacheManager:
    """Central cache manager for SmartYAML processing."""

    def __init__(self, config):
        if not config.enable_caching:
            self.cache = None
            self.file_cache = None
            self.processed_cache = None
        else:
            self.cache = SmartYAMLCache(
                max_size=config.cache_size, default_ttl=3600  # 1 hour default
            )
            self.file_cache = FileContentCache(self.cache)
            self.processed_cache = ProcessedDataCache(self.cache)

    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.cache is not None

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics."""
        if not self.cache:
            return None
        return self.cache.get_stats()

    def clear_all(self) -> None:
        """Clear all caches."""
        if self.cache:
            self.cache.clear()

    def cleanup_expired(self) -> int:
        """Clean up expired entries."""
        if not self.cache:
            return 0
        return self.cache.cleanup_expired()
