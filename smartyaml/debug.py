"""
Debugging and error analysis utilities for SmartYAML

Provides detailed error reporting, processing traces, and diagnostic tools
for troubleshooting SmartYAML processing issues.
"""

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import SmartYAMLConfig
from .exceptions import SmartYAMLError


class ProcessingTrace:
    """Records the processing steps and timing for debugging."""

    def __init__(self):
        self.steps: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.total_time: Optional[float] = None
        self.errors: List[Dict[str, Any]] = []

    def add_step(
        self, stage: str, action: str, details: Optional[Dict[str, Any]] = None
    ):
        """Add a processing step to the trace."""
        step = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "action": action,
            "details": details or {},
        }
        self.steps.append(step)

    def add_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Add an error to the trace."""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {},
            "traceback": traceback.format_exception(
                type(error), error, error.__traceback__
            ),
        }
        self.errors.append(error_info)

    def finalize(self):
        """Finalize the trace with total processing time."""
        end_time = datetime.now()
        self.total_time = (end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for serialization."""
        return {
            "start_time": self.start_time.isoformat(),
            "total_time": self.total_time,
            "steps": self.steps,
            "errors": self.errors,
            "step_count": len(self.steps),
            "error_count": len(self.errors),
        }


class SmartYAMLDebugger:
    """Debug utility for analyzing SmartYAML processing."""

    def __init__(self, config: SmartYAMLConfig):
        self.config = config
        self.trace = ProcessingTrace()
        self.enabled = config.debug_mode

    def trace_step(self, stage: str, action: str, **kwargs):
        """Trace a processing step."""
        if self.enabled:
            self.trace.add_step(stage, action, kwargs)

    def trace_error(self, error: Exception, **context):
        """Trace an error with context."""
        if self.enabled:
            self.trace.add_error(error, context)

    def analyze_yaml_content(self, content: str) -> Dict[str, Any]:
        """Analyze YAML content for common issues."""
        issues = []

        # Check for tabs (common YAML issue)
        if "\t" in content:
            issues.append(
                {
                    "type": "tabs_detected",
                    "severity": "warning",
                    "message": "Tabs detected in YAML content. Use spaces for indentation.",
                    "lines": [
                        i + 1
                        for i, line in enumerate(content.split("\n"))
                        if "\t" in line
                    ],
                }
            )

        # Check for very long lines
        long_lines = []
        for i, line in enumerate(content.split("\n")):
            if len(line) > 200:
                long_lines.append(i + 1)

        if long_lines:
            issues.append(
                {
                    "type": "long_lines",
                    "severity": "info",
                    "message": "Very long lines detected (>200 chars)",
                    "lines": long_lines[:10],  # Limit to first 10
                }
            )

        # Check for potential directive syntax issues
        directive_lines = []
        for i, line in enumerate(content.split("\n")):
            if "!" in line and "{{" in line:
                directive_lines.append(i + 1)

        if directive_lines:
            issues.append(
                {
                    "type": "mixed_syntax",
                    "severity": "warning",
                    "message": "Lines with both directives and variables detected",
                    "lines": directive_lines[:5],
                }
            )

        return {
            "total_lines": len(content.split("\n")),
            "total_chars": len(content),
            "issues": issues,
        }

    def analyze_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze variable structure for potential issues."""
        analysis = {
            "variable_count": len(variables),
            "nested_levels": 0,
            "circular_references": [],
            "undefined_references": [],
        }

        # Check nesting depth
        def get_max_depth(obj, current_depth=0):
            if isinstance(obj, dict):
                if not obj:
                    return current_depth
                return max(get_max_depth(v, current_depth + 1) for v in obj.values())
            elif isinstance(obj, list):
                if not obj:
                    return current_depth
                return max(get_max_depth(v, current_depth + 1) for v in obj)
            else:
                return current_depth

        analysis["nested_levels"] = get_max_depth(variables)

        return analysis

    def generate_report(self, file_path: Optional[Path] = None) -> str:
        """Generate a detailed debug report."""
        self.trace.finalize()

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "file_path": str(file_path) if file_path else None,
            "config": {
                "version": self.config.version,
                "strict_variables": self.config.strict_variables,
                "validate_schema": self.config.validate_schema,
                "enable_caching": self.config.enable_caching,
                "max_recursion_depth": self.config.max_recursion_depth,
            },
            "processing_trace": self.trace.to_dict(),
        }

        return json.dumps(report_data, indent=2)

    def save_report(self, output_path: Union[str, Path]) -> None:
        """Save debug report to file."""
        output_path = Path(output_path)
        report = self.generate_report()

        output_path.write_text(report)


class ErrorAnalyzer:
    """Analyzes SmartYAML errors and provides helpful suggestions."""

    @staticmethod
    def analyze_error(error: SmartYAMLError) -> Dict[str, Any]:
        """Analyze an error and provide suggestions."""
        analysis = {
            "error_type": type(error).__name__,
            "message": str(error),
            "file_path": getattr(error, "file_path", None),
            "field_path": getattr(error, "field_path", None),
            "suggestions": [],
        }

        # Add type-specific suggestions
        if "DirectiveSyntaxError" in analysis["error_type"]:
            analysis["suggestions"].extend(
                [
                    "Check directive syntax - use array format: !env ['VAR_NAME', 'default']",
                    "Verify directive name is spelled correctly",
                    "Ensure directive arguments are properly formatted",
                ]
            )

        elif "VariableExpansionError" in analysis["error_type"]:
            analysis["suggestions"].extend(
                [
                    "Check variable name spelling and case",
                    "Ensure variable is defined in __vars section",
                    "Verify variable scope and precedence rules",
                    "Use strict_variables=False to allow undefined variables",
                ]
            )

        elif "FileNotFoundError" in analysis["error_type"]:
            analysis["suggestions"].extend(
                [
                    "Check file path is correct and file exists",
                    "Verify file permissions are readable",
                    "Ensure base_path configuration is correct",
                    "Check for typos in include/template paths",
                ]
            )

        elif "SchemaValidationError" in analysis["error_type"]:
            analysis["suggestions"].extend(
                [
                    "Check data structure matches schema requirements",
                    "Verify all required fields are present",
                    "Check data types match schema definitions",
                    "Review schema file for correctness",
                ]
            )

        elif "RecursionLimitExceededError" in analysis["error_type"]:
            analysis["suggestions"].extend(
                [
                    "Check for circular references in includes/templates",
                    "Review variable expansion for infinite loops",
                    "Increase max_recursion_depth if needed",
                    "Simplify file inclusion hierarchy",
                ]
            )

        return analysis

    @staticmethod
    def format_error_report(
        error: SmartYAMLError, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a comprehensive error report."""
        analysis = ErrorAnalyzer.analyze_error(error)

        report_lines = [
            f"SmartYAML Error: {analysis['error_type']}",
            f"Message: {analysis['message']}",
            "",
        ]

        if analysis["file_path"]:
            report_lines.append(f"File: {analysis['file_path']}")

        if analysis["field_path"]:
            report_lines.append(f"Field: {analysis['field_path']}")

        if context:
            report_lines.extend(["", "Context:", json.dumps(context, indent=2)])

        if analysis["suggestions"]:
            report_lines.extend(
                [
                    "",
                    "Suggestions:",
                    *[f"  • {suggestion}" for suggestion in analysis["suggestions"]],
                ]
            )

        return "\n".join(report_lines)
