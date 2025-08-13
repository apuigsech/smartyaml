"""
Variable expansion constructor for SmartYAML
"""

from typing import Any, Dict

import yaml

from ..exceptions import ConstructorError
from ..processing import (
    ParameterExtractor,
    ParameterPattern,
    ParameterSpec,
    ParameterValidator,
)
from ..utils.variable_substitution import VariableSubstitutionEngine
from .base import BaseConstructor


class ExpandConstructor(BaseConstructor):
    """
    Constructor for !expand directive.
    Performs variable substitution on strings using {{key}} syntax.

    Usage:
        message: !expand "Hello {{name}}, welcome to {{app}}!"

    Variables come from:
    1. Variables passed to load() function
    2. __vars metadata field (overlaid by function variables)
    """

    # Type specifications for automatic type conversion
    TYPE_SPECS = {"content": str}

    def __init__(self):
        # Create parameter specification
        content_spec = ParameterSpec(
            name="content",
            param_type=str,
            required=True,
            description="The string content to expand with variables",
        )

        # Create parameter extractor for single scalar pattern
        extractor = ParameterExtractor(
            pattern=ParameterPattern.SINGLE_SCALAR, specs=[content_spec]
        )

        # Create parameter validator
        validator = ParameterValidator.create_standard_validator(
            required_params=["content"], type_specs={"content": str}
        )

        super().__init__(
            directive_name="!expand",
            parameter_extractor=extractor,
            parameter_validator=validator,
        )

    def extract_parameters(
        self, loader: yaml.SafeLoader, node: yaml.Node
    ) -> Dict[str, Any]:
        """
        Extract parameters from the YAML node.

        Args:
            loader: YAML loader instance
            node: YAML node containing the content to expand

        Returns:
            Dictionary with 'content' parameter
        """
        if isinstance(node, yaml.ScalarNode):
            content = loader.construct_scalar(node)
            return {"content": content}
        else:
            raise ConstructorError(
                directive_name="!expand",
                message="!expand directive requires a string value",
                location=getattr(node, "start_mark", None),
            )

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """
        Validate extracted parameters.

        Args:
            params: Dictionary of parameters to validate

        Raises:
            ConstructorError: If parameters are invalid
        """
        if "content" not in params:
            raise ConstructorError(
                directive_name="!expand",
                message="!expand directive requires content parameter",
            )

        content = params["content"]
        if not isinstance(content, str):
            raise ConstructorError(
                directive_name="!expand",
                message="!expand directive requires a string value",
            )

    def execute(self, loader: yaml.SafeLoader, params: Dict[str, Any]) -> Any:
        """
        Execute the variable expansion.

        Args:
            loader: YAML loader instance
            params: Dictionary of validated parameters

        Returns:
            String with variables expanded or deferred expansion marker

        Raises:
            ConstructorError: If expansion fails
        """
        content = params["content"]

        # Check if the loader has expansion variables available
        if hasattr(loader, "expansion_variables") and loader.expansion_variables:
            try:
                # Try immediate expansion if variables are available
                engine = VariableSubstitutionEngine(loader.expansion_variables)

                # Only expand if all required variables are available
                required_vars = engine.extract_variable_names(content)
                missing_vars = [
                    var
                    for var in required_vars
                    if var not in loader.expansion_variables
                ]

                if not missing_vars:
                    # All variables available, expand immediately
                    return engine.substitute_string(content)
                # If some variables are missing, fall through to deferred expansion
            except Exception:
                # If immediate expansion fails, fall through to deferred expansion
                pass

        # Defer expansion to post-processing to handle __vars metadata
        return {"__smartyaml_expand_deferred": content}


# Convenience function to create the constructor
def expand_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> Any:
    """
    Convenience function for the !expand constructor.

    Args:
        loader: YAML loader instance
        node: YAML node containing the directive

    Returns:
        Result from ExpandConstructor
    """
    constructor = ExpandConstructor()
    return constructor(loader, node)
