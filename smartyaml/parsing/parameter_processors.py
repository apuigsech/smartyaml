"""
Parameter processing classes for SmartYAML tag parsing
"""

import re
from abc import ABC, abstractmethod
from typing import List


class BaseParameterProcessor(ABC):
    """Base class for parameter processors."""

    @abstractmethod
    def process(self, raw_params: str) -> List[str]:
        """Process raw parameter string into a list of parameters."""


class ScalarParameterProcessor(BaseParameterProcessor):
    """Processor for single scalar parameters."""

    def process(self, raw_params: str) -> List[str]:
        """Return single parameter as-is after cleaning."""
        if not raw_params.strip():
            return []
        return [raw_params.strip().strip("\"'")]


class CommaParameterProcessor(BaseParameterProcessor):
    """Processor for comma-separated parameters."""

    def process(self, raw_params: str) -> List[str]:
        """Split parameters by comma and clean each one."""
        if not raw_params.strip():
            return []

        parameters = [
            param.strip().strip("\"'")
            for param in raw_params.split(",")
            if param.strip()
        ]

        return parameters


class BracketParameterProcessor(BaseParameterProcessor):
    """Processor for bracket-enclosed parameters."""

    BRACKET_PATTERN = re.compile(r"^\s*\[(.+)\]\s*$")

    def process(self, raw_params: str) -> List[str]:
        """Extract parameters from bracket notation."""
        if not raw_params.strip():
            return []

        # Check if wrapped in brackets
        match = self.BRACKET_PATTERN.match(raw_params)
        if match:
            inner_content = match.group(1)
            # Process inner content as comma-separated
            return CommaParameterProcessor().process(inner_content)

        # If not in brackets, treat as single parameter
        return [raw_params.strip().strip("\"'")]


class SmartParameterProcessor:
    """
    Smart parameter processor that automatically detects the appropriate processing strategy.
    """

    def __init__(self):
        self.processors = {
            "scalar": ScalarParameterProcessor(),
            "comma": CommaParameterProcessor(),
            "bracket": BracketParameterProcessor(),
        }

    def process(self, raw_params: str, syntax_type: str = "auto") -> List[str]:
        """
        Process parameters using the appropriate processor.

        Args:
            raw_params: Raw parameter string
            syntax_type: Type of syntax ('auto', 'scalar', 'comma', 'bracket')

        Returns:
            List of processed parameters
        """
        if syntax_type == "auto":
            syntax_type = self._detect_syntax_type(raw_params)

        processor = self.processors.get(syntax_type, self.processors["comma"])
        return processor.process(raw_params)

    def _detect_syntax_type(self, raw_params: str) -> str:
        """Detect the most appropriate syntax type for the given parameters."""
        if not raw_params.strip():
            return "scalar"

        # Check for bracket notation
        if raw_params.strip().startswith("[") and raw_params.strip().endswith("]"):
            return "bracket"

        # Check for comma separation
        if "," in raw_params:
            return "comma"

        # Default to scalar
        return "scalar"
