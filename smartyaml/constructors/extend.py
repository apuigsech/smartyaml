"""
Extend constructor for SmartYAML.

Allows extending/concatenating arrays from templates instead of replacing them.
"""

from typing import Any, Dict

from ..constants import EXTEND_MARKER_KEY
from ..exceptions import ConstructorError
from .base import BaseConstructor


class ExtendConstructor(BaseConstructor):
    """
    Constructor for !extend directive.

    Marks arrays for extension/concatenation during template merging instead
    of complete replacement. This enables template inheritance patterns where
    document arrays are appended to template arrays rather than replacing them.

    Usage:
        tests: !extend
          - id: "new_test_1"
            name: "New Test 1"
          - id: "new_test_2"
            name: "New Test 2"

    Result: template_tests + document_tests (concatenated)
    """

    def __init__(self):
        super().__init__("!extend")

    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract array data from YAML node."""
        try:
            # Construct the sequence (array) from the node
            array_data = loader.construct_sequence(node)
            return {"array_data": array_data}
        except Exception as e:
            # Convert YAML errors to ConstructorError with helpful message
            raise ConstructorError(
                directive_name=self.directive_name,
                message=f"{self.directive_name} directive requires a list/array. "
                f"Example: 'items: !extend\\n  - item1\\n  - item2'",
                location=None,
            ) from e

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate that the content is a list/array."""
        array_data = params.get("array_data")

        if not isinstance(array_data, list):
            raise ConstructorError(
                f"{self.directive_name} directive requires a list/array, "
                f"got {type(array_data).__name__}"
            )

    def execute(self, loader, params: Dict[str, Any]) -> Any:
        """Mark the array data for extension during template merging."""
        array_data = params["array_data"]

        # Return marked structure for template merge processor
        return {EXTEND_MARKER_KEY: True, "data": array_data}


# Create instance for registration
extend_constructor = ExtendConstructor()
