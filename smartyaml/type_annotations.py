"""
Comprehensive type annotations and type checking utilities for SmartYAML
"""

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    import yaml


# Type aliases for better code readability
YAMLValue = Union[str, int, float, bool, List[Any], Dict[str, Any], None]
YAMLNode = Union["yaml.ScalarNode", "yaml.SequenceNode", "yaml.MappingNode"]
YAMLLoader = "yaml.SafeLoader"
FilePath = Union[str, Path]
ParameterDict = Dict[str, Any]
ContextDict = Dict[str, Any]
ConstructorFunction = Callable[["yaml.SafeLoader", "yaml.Node"], Any]

# Generic types
T = TypeVar("T")
NodeType = TypeVar("NodeType", bound="yaml.Node")


# Protocol definitions for better type checking
class ConstructorProtocol(Protocol):
    """Protocol for SmartYAML constructors."""

    def __call__(self, loader: YAMLLoader, node: YAMLNode) -> Any:
        """Execute the constructor with given loader and node."""
        ...


class ValidatorProtocol(Protocol):
    """Protocol for parameter validators."""

    def validate(self, params: ParameterDict, directive_name: str) -> None:
        """Validate parameters for a directive."""
        ...


class ExtractorProtocol(Protocol):
    """Protocol for parameter extractors."""

    def extract_parameters(
        self, loader: YAMLLoader, node: YAMLNode, directive_name: str
    ) -> ParameterDict:
        """Extract parameters from a YAML node."""
        ...


# Literal types for better type safety
DirectiveName = Literal[
    "!import",
    "!import_yaml",
    "!env",
    "!include_if",
    "!include_yaml_if",
    "!template",
    "!base64",
    "!base64_decode",
]

ParameterPattern = Literal[
    "single_scalar",
    "scalar_or_sequence",
    "fixed_sequence",
    "flexible_sequence",
    "mapping",
    "complex",
]

ValidationRuleType = Literal["required", "type", "custom"]

# Error type annotations
ErrorContext = Dict[str, Union[str, int, Path, None]]


# Configuration types
class ConfigProtocol(Protocol):
    """Protocol for SmartYAML configuration."""

    enable_file_caching: bool
    max_file_size: int
    cache_ttl_seconds: int
    cache_cleanup_interval: int
    max_recursion_depth: int


# Type guards for runtime type checking
def is_yaml_scalar_node(node: Any) -> bool:
    """Type guard for YAML scalar nodes."""
    return hasattr(node, "value") and isinstance(node.value, str)


def is_yaml_sequence_node(node: Any) -> bool:
    """Type guard for YAML sequence nodes."""
    return hasattr(node, "value") and isinstance(node.value, list)


def is_yaml_mapping_node(node: Any) -> bool:
    """Type guard for YAML mapping nodes."""
    return (
        hasattr(node, "value")
        and isinstance(node.value, list)
        and all(isinstance(item, tuple) and len(item) == 2 for item in node.value)
    )


# Generic result wrapper for better error handling
class Result(Generic[T]):
    """Generic result type for operations that might fail."""

    def __init__(self, value: Optional[T] = None, error: Optional[Exception] = None):
        self._value = value
        self._error = error

    @property
    def is_success(self) -> bool:
        """Check if the result represents success."""
        return self._error is None

    @property
    def is_error(self) -> bool:
        """Check if the result represents an error."""
        return self._error is not None

    @property
    def value(self) -> T:
        """Get the success value, raising if error."""
        if self._error:
            raise self._error
        return self._value  # type: ignore

    @property
    def error(self) -> Optional[Exception]:
        """Get the error, if any."""
        return self._error

    @classmethod
    def success(cls, value: T) -> "Result[T]":
        """Create a successful result."""
        return cls(value=value)

    @classmethod
    def failure(cls, error: Exception) -> "Result[T]":
        """Create a failed result."""
        return cls(error=error)


# Type-safe constructor registry interface
class TypedConstructorRegistry:
    """Type-safe wrapper for constructor registry operations."""

    def __init__(self, registry: Any):
        self._registry = registry

    def register(self, tag: DirectiveName, constructor: ConstructorProtocol) -> None:
        """Register a constructor with type checking."""
        self._registry.register(tag, constructor)

    def get_constructor(self, tag: DirectiveName) -> Optional[ConstructorProtocol]:
        """Get a constructor with proper return type."""
        return self._registry.get_constructor(tag)

    def dispatch(self, loader: YAMLLoader, tag_suffix: str, node: YAMLNode) -> Any:
        """Dispatch to constructor with type safety."""
        return self._registry.dispatch(loader, tag_suffix, node)


# Type annotations for common patterns
LoaderContextType = Dict[
    Literal[
        "base_path",
        "template_path",
        "max_file_size",
        "max_recursion_depth",
        "import_stack",
    ],
    Any,
]

ParameterSpecType = Dict[
    Literal["name", "type", "required", "default", "validator", "description"], Any
]
