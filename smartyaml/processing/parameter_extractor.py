"""
Standardized parameter extraction system for SmartYAML constructors
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml

from ..exceptions import ConstructorError
from ..utils import validate_constructor_args


class ParameterPattern(Enum):
    """Defines the expected parameter pattern for a constructor."""

    SINGLE_SCALAR = "single_scalar"  # !tag(value)
    SCALAR_OR_SEQUENCE = "scalar_or_sequence"  # !tag(value) or !tag(value1, value2)
    FIXED_SEQUENCE = "fixed_sequence"  # !tag(value1, value2) - exact count required
    FLEXIBLE_SEQUENCE = (
        "flexible_sequence"  # !tag(value1, ..., valueN) - variable count
    )
    MAPPING = "mapping"  # !tag {key: value}
    COMPLEX = "complex"  # Custom logic required


@dataclass
class ParameterSpec:
    """Specification for a single parameter in a constructor."""

    name: str
    param_type: type = str
    required: bool = True
    default: Any = None
    validator: Optional[callable] = None
    description: str = ""


class ParameterExtractor:
    """
    Standardized parameter extraction system for SmartYAML constructors.

    This class provides a unified way to extract and validate parameters
    from YAML nodes, reducing code duplication and inconsistencies.
    """

    def __init__(self, pattern: ParameterPattern, specs: List[ParameterSpec]):
        """
        Initialize the parameter extractor.

        Args:
            pattern: The expected parameter pattern
            specs: List of parameter specifications
        """
        self.pattern = pattern
        self.specs = {spec.name: spec for spec in specs}
        self.ordered_specs = specs

    def extract_parameters(
        self, loader: yaml.SafeLoader, node: yaml.Node, directive_name: str
    ) -> Dict[str, Any]:
        """
        Extract parameters from a YAML node according to the configured pattern.

        Args:
            loader: The YAML loader instance
            node: The YAML node containing the parameters
            directive_name: The name of the directive for error messages

        Returns:
            Dictionary of extracted parameters

        Raises:
            ConstructorError: If parameter extraction fails
        """
        try:
            if self.pattern == ParameterPattern.SINGLE_SCALAR:
                return self._extract_single_scalar(loader, node)
            elif self.pattern == ParameterPattern.SCALAR_OR_SEQUENCE:
                return self._extract_scalar_or_sequence(loader, node)
            elif self.pattern == ParameterPattern.FIXED_SEQUENCE:
                return self._extract_fixed_sequence(loader, node, directive_name)
            elif self.pattern == ParameterPattern.FLEXIBLE_SEQUENCE:
                return self._extract_flexible_sequence(loader, node)
            elif self.pattern == ParameterPattern.MAPPING:
                return self._extract_mapping(loader, node)
            else:
                raise ConstructorError(
                    directive_name,
                    None,
                    "Complex parameter pattern requires custom extraction",
                    getattr(node, "start_mark", None),
                )
        except Exception as e:
            if isinstance(e, ConstructorError):
                raise
            raise ConstructorError(
                directive_name,
                None,
                f"Parameter extraction failed - {str(e)}",
                getattr(node, "start_mark", None),
            ) from e

    def _extract_single_scalar(
        self, loader: yaml.SafeLoader, node: yaml.Node
    ) -> Dict[str, Any]:
        """Extract a single scalar parameter."""
        if len(self.ordered_specs) != 1:
            raise ValueError(
                "SINGLE_SCALAR pattern requires exactly one parameter spec"
            )

        spec = self.ordered_specs[0]

        # Handle sequence nodes that should be treated as single parameters
        if hasattr(node, "value") and isinstance(node.value, list):
            # Special case for nodes like !base64(Hello, world!) where comma is part of data
            params = [loader.construct_scalar(param_node) for param_node in node.value]
            if spec.name in ["data", "content", "text"]:  # Data-like parameters
                value = ", ".join(params)
            else:  # Other single parameters shouldn't have commas
                value = "".join(params)
        else:
            value = loader.construct_scalar(node)

        return {spec.name: value}

    def _extract_scalar_or_sequence(
        self, loader: yaml.SafeLoader, node: yaml.Node
    ) -> Dict[str, Any]:
        """Extract parameters that can be either scalar or sequence."""
        if isinstance(node, yaml.ScalarNode):
            if len(self.ordered_specs) < 1:
                raise ValueError(
                    "SCALAR_OR_SEQUENCE pattern requires at least one parameter spec"
                )

            spec = self.ordered_specs[0]
            value = loader.construct_scalar(node)
            result = {spec.name: value}

            # Add defaults for remaining optional parameters
            for spec in self.ordered_specs[1:]:
                if not spec.required:
                    result[spec.name] = spec.default

            return result

        elif isinstance(node, yaml.SequenceNode):
            sequence = loader.construct_sequence(node)
            result = {}

            for i, spec in enumerate(self.ordered_specs):
                if i < len(sequence):
                    result[spec.name] = sequence[i]
                elif spec.required:
                    raise ConstructorError(
                        None,
                        spec.name,
                        "Required parameter missing from sequence",
                        getattr(node, "start_mark", None),
                    )
                else:
                    result[spec.name] = spec.default

            return result
        else:
            raise ConstructorError(
                None,
                None,
                f"Expected scalar or sequence node, got {type(node).__name__}",
                getattr(node, "start_mark", None),
            )

    def _extract_fixed_sequence(
        self, loader: yaml.SafeLoader, node: yaml.Node, directive_name: str
    ) -> Dict[str, Any]:
        """Extract a fixed-length sequence of parameters."""
        if not isinstance(node, yaml.SequenceNode):
            raise ConstructorError(
                None,
                None,
                f"{directive_name} expects a sequence",
                getattr(node, "start_mark", None),
            )

        sequence = loader.construct_sequence(node)
        required_count = len([spec for spec in self.ordered_specs if spec.required])

        validate_constructor_args(sequence, required_count, directive_name)

        result = {}
        for i, spec in enumerate(self.ordered_specs):
            if i < len(sequence):
                result[spec.name] = sequence[i]
            elif spec.required:
                raise ConstructorError(
                    None,
                    None,
                    f"{directive_name}: Required parameter '{spec.name}' missing",
                    getattr(node, "start_mark", None),
                )
            else:
                result[spec.name] = spec.default

        return result

    def _extract_flexible_sequence(
        self, loader: yaml.SafeLoader, node: yaml.Node
    ) -> Dict[str, Any]:
        """Extract a flexible-length sequence of parameters."""
        if not isinstance(node, yaml.SequenceNode):
            raise ConstructorError(
                None,
                None,
                "Expected sequence node for flexible sequence",
                getattr(node, "start_mark", None),
            )

        sequence = loader.construct_sequence(node)
        result = {}

        # Handle named parameters first
        for i, spec in enumerate(self.ordered_specs):
            if i < len(sequence):
                result[spec.name] = sequence[i]
            elif spec.required:
                raise ConstructorError(
                    None,
                    None,
                    f"Required parameter '{spec.name}' missing from sequence",
                    getattr(node, "start_mark", None),
                )
            else:
                result[spec.name] = spec.default

        # Handle any extra parameters as a list
        if len(sequence) > len(self.ordered_specs):
            result["extra_params"] = sequence[len(self.ordered_specs) :]

        return result

    def _extract_mapping(
        self, loader: yaml.SafeLoader, node: yaml.Node
    ) -> Dict[str, Any]:
        """Extract parameters from a mapping node."""
        if not isinstance(node, yaml.MappingNode):
            raise ConstructorError(
                None, None, "Expected mapping node", getattr(node, "start_mark", None)
            )

        mapping = loader.construct_mapping(node)
        result = {}

        for spec in self.ordered_specs:
            if spec.name in mapping:
                result[spec.name] = mapping[spec.name]
            elif spec.required:
                raise ConstructorError(
                    None,
                    None,
                    f"Required parameter '{spec.name}' missing from mapping",
                    getattr(node, "start_mark", None),
                )
            else:
                result[spec.name] = spec.default

        return result

    def validate_parameters(self, params: Dict[str, Any], directive_name: str) -> None:
        """
        Validate extracted parameters according to their specifications.

        Args:
            params: The extracted parameters
            directive_name: The name of the directive for error messages

        Raises:
            ConstructorError: If validation fails
        """
        for name, spec in self.specs.items():
            if name not in params:
                continue

            value = params[name]

            # Type validation
            if value is not None and not isinstance(value, spec.param_type):
                try:
                    # Attempt type conversion
                    params[name] = spec.param_type(value)
                except (ValueError, TypeError):
                    raise ConstructorError(
                        None,
                        None,
                        f"{directive_name}: Parameter '{name}' must be {spec.param_type.__name__}, "
                        f"got {type(value).__name__}",
                        None,
                    )

            # Custom validation
            if spec.validator and value is not None:
                try:
                    spec.validator(value)
                except Exception as e:
                    raise ConstructorError(
                        None,
                        None,
                        f"{directive_name}: Parameter '{name}' validation failed - {str(e)}",
                        None,
                    ) from e
