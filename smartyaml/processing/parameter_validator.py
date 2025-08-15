"""
Parameter validation system for SmartYAML constructors
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..exceptions import ErrorFactory


class ValidationRule(ABC):
    """Base class for parameter validation rules."""

    @abstractmethod
    def validate(self, params: Dict[str, Any], directive_name: str) -> None:
        """
        Validate parameters according to the rule.

        Args:
            params: The parameters to validate
            directive_name: The name of the directive for error messages

        Raises:
            ConstructorError: If validation fails
        """


class RequiredParameterRule(ValidationRule):
    """Validates that required parameters are present and not None."""

    def __init__(self, required_params: List[str]):
        self.required_params = required_params

    def validate(self, params: Dict[str, Any], directive_name: str) -> None:
        for param_name in self.required_params:
            if param_name not in params or params[param_name] is None:
                raise ErrorFactory.parameter_required(directive_name, param_name)


class TypeValidationRule(ValidationRule):
    """Validates parameter types."""

    def __init__(self, type_specs: Dict[str, type]):
        self.type_specs = type_specs

    def validate(self, params: Dict[str, Any], directive_name: str) -> None:
        for param_name, expected_type in self.type_specs.items():
            if param_name in params and params[param_name] is not None:
                value = params[param_name]
                if not isinstance(value, expected_type):
                    raise ErrorFactory.parameter_type_mismatch(
                        directive_name, param_name, expected_type, type(value)
                    )


class CustomValidationRule(ValidationRule):
    """Validates parameters using custom validation functions."""

    def __init__(self, validators: Dict[str, callable]):
        self.validators = validators

    def validate(self, params: Dict[str, Any], directive_name: str) -> None:
        for param_name, validator in self.validators.items():
            if param_name in params and params[param_name] is not None:
                try:
                    validator(params[param_name])
                except Exception as e:
                    raise ErrorFactory.parameter_validation_failed(
                        directive_name, param_name, str(e)
                    ) from e


class ParameterValidator:
    """
    Unified parameter validation system for SmartYAML constructors.

    This class provides a pipeline of validation rules that can be
    applied to extracted parameters in a consistent manner.
    """

    def __init__(self, rules: List[ValidationRule] = None):
        """
        Initialize the parameter validator.

        Args:
            rules: List of validation rules to apply
        """
        self.rules = rules or []

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule to the pipeline."""
        self.rules.append(rule)

    def validate(self, params: Dict[str, Any], directive_name: str) -> None:
        """
        Validate parameters using all configured rules.

        Args:
            params: The parameters to validate
            directive_name: The name of the directive for error messages

        Raises:
            ConstructorError: If any validation rule fails
        """
        for rule in self.rules:
            rule.validate(params, directive_name)

    @classmethod
    def create_standard_validator(
        cls,
        required_params: List[str] = None,
        type_specs: Dict[str, type] = None,
        custom_validators: Dict[str, callable] = None,
    ) -> "ParameterValidator":
        """
        Create a validator with standard validation rules.

        Args:
            required_params: List of required parameter names
            type_specs: Dictionary mapping parameter names to expected types
            custom_validators: Dictionary mapping parameter names to validation functions

        Returns:
            Configured ParameterValidator instance
        """
        validator = cls()

        if required_params:
            validator.add_rule(RequiredParameterRule(required_params))

        if type_specs:
            validator.add_rule(TypeValidationRule(type_specs))

        if custom_validators:
            validator.add_rule(CustomValidationRule(custom_validators))

        return validator
