"""
Tag parsing system for SmartYAML
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Pattern

import yaml

from .parameter_processors import SmartParameterProcessor


@dataclass
class ParsedTag:
    """Represents a parsed SmartYAML tag with parameters."""

    base_tag: str
    parameters: List[str]
    original_tag: str
    syntax_type: str  # 'parentheses', 'brackets', 'simple'


class TagParser:
    """
    Centralized tag parsing system for SmartYAML.

    This class handles the complex logic of parsing various YAML tag syntaxes
    and reconstructing split tags that PyYAML breaks apart.
    """

    # Pre-compiled regex patterns for performance
    PARENTHESES_PATTERN: Pattern = re.compile(r"^(![\w_]+)\((.+)\)$")
    BRACKETS_PATTERN: Pattern = re.compile(r"^(![\w_]+)\s*\[(.+)\]$")

    def __init__(self):
        self.parameter_processor = SmartParameterProcessor()

    def parse_tag(self, tag_suffix: str, node: yaml.Node) -> Optional[ParsedTag]:
        """
        Parse a YAML tag and return structured information.

        Args:
            tag_suffix: The tag suffix from PyYAML multi-constructor
            node: The YAML node containing the tag value

        Returns:
            ParsedTag object if parsing successful, None otherwise
        """
        full_tag = tag_suffix if tag_suffix.startswith("!") else "!" + tag_suffix

        # Handle case where PyYAML splits the tag due to commas/spaces
        if self._is_split_tag(full_tag, node):
            full_tag = self._reconstruct_split_tag(full_tag, node)

        # Try parentheses syntax: !tag(params)
        if match := self.PARENTHESES_PATTERN.match(full_tag):
            base_tag, params_str = match.groups()
            parameters = self.parameter_processor.process(params_str, "comma")
            return ParsedTag(
                base_tag=base_tag,
                parameters=parameters,
                original_tag=full_tag,
                syntax_type="parentheses",
            )

        # Try bracket syntax: !tag [params]
        if match := self.BRACKETS_PATTERN.match(full_tag):
            base_tag, params_str = match.groups()
            parameters = self.parameter_processor.process(params_str, "bracket")
            return ParsedTag(
                base_tag=base_tag,
                parameters=parameters,
                original_tag=full_tag,
                syntax_type="brackets",
            )

        # Simple tag without parameters
        return ParsedTag(
            base_tag=full_tag,
            parameters=[],
            original_tag=full_tag,
            syntax_type="simple",
        )

    def _is_split_tag(self, full_tag: str, node: yaml.Node) -> bool:
        """Check if a tag was split by PyYAML."""
        return (
            "(" in full_tag
            and not full_tag.endswith(")")
            and hasattr(node, "value")
            and isinstance(node.value, str)
            and node.value.endswith(")")
        )

    def _reconstruct_split_tag(self, full_tag: str, node: yaml.Node) -> str:
        """Reconstruct a tag that was split by PyYAML."""
        tag_param_part = full_tag[full_tag.index("(") + 1 :]
        value_param_part = node.value[:-1]

        # Add appropriate separator
        separator = " " if full_tag.endswith(",") else " "
        params_str = tag_param_part + separator + value_param_part
        base_tag = full_tag[: full_tag.index("(")]

        return base_tag + "(" + params_str + ")"

    def create_scalar_node(
        self, tag: str, value: str, start_mark=None
    ) -> yaml.ScalarNode:
        """Create a YAML scalar node."""
        return yaml.ScalarNode(tag=tag, value=value, start_mark=start_mark)

    def create_sequence_node(
        self, tag: str, parameters: List[str], start_mark=None
    ) -> yaml.SequenceNode:
        """Create a YAML sequence node from parameters."""
        param_nodes = [
            yaml.ScalarNode(
                tag="tag:yaml.org,2002:str", value=param, start_mark=start_mark
            )
            for param in parameters
        ]

        return yaml.SequenceNode(tag=tag, value=param_nodes, start_mark=start_mark)
