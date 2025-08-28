"""
Stage 3: Template Processing

Loads and merges template files according to __template metadata configuration.
Supports both path-based and use-based template loading with overlay modes.
"""

import copy
from pathlib import Path
from typing import Any, Dict

from ..config import SmartYAMLConfig
from ..exceptions import FileNotFoundError, RecursionLimitExceededError, SmartYAMLError
from ..utils.merge import DeepMerger, MergeStrategy


class TemplateProcessor:
    """Stage 3: Load and merge templates."""

    def __init__(self, config: SmartYAMLConfig):
        self.config = config

    def process(self, data: Dict[str, Any], context) -> Dict[str, Any]:
        """Process template loading and merging."""
        template_config = context.metadata.get("__template")
        if not template_config:
            return data

        # Load template data
        template_data = self._load_template(template_config, context)

        # Merge template with current data
        overlay_mode = template_config.get("overlay", True)

        if overlay_mode:
            # Overlay mode: merge template with current (current overrides template)
            merged_data = copy.deepcopy(template_data)
            self._deep_merge(merged_data, data)
            return merged_data
        else:
            # Replace mode: current data completely replaces template
            return data

    def _load_template(
        self, template_config: Dict[str, Any], context
    ) -> Dict[str, Any]:
        """Load template file according to configuration."""
        template_path = self._resolve_template_path(template_config, context)

        # Check sandbox mode restrictions
        if self.config.security.sandbox_mode:
            from ..exceptions import SecurityViolationError

            raise SecurityViolationError(
                "Template inheritance blocked in sandbox mode",
                str(context.file_path),
                "sandbox_template_access",
            )

        # Validate overlay type if specified
        overlay = template_config.get("overlay")
        if overlay is not None and not isinstance(overlay, bool):
            from ..exceptions import DirectiveSyntaxError

            raise DirectiveSyntaxError(
                "__template.overlay must be a boolean",
                str(context.file_path),
                "__template.overlay",
            )

        # Check for circular references
        if template_path in context.loaded_files:
            raise RecursionLimitExceededError(
                context.config.max_recursion_depth,
                "template loading",
                str(context.file_path),
                str(template_path),
            )

        context.loaded_files.add(template_path)

        try:
            # Read template file
            if not template_path.exists():
                raise FileNotFoundError(
                    str(template_path), str(context.base_path), "template"
                )

            template_content = template_path.read_text()

            # Process template through stages 1-4 (skip variable expansion)
            from .processor import SmartYAMLProcessor

            processor = SmartYAMLProcessor(self.config)

            # Create new context for template processing
            template_context = type(context)(self.config, template_path)
            template_context.recursion_depth = context.recursion_depth
            template_context.loaded_files = context.loaded_files.copy()
            # Store main context variables to preserve precedence during template processing
            template_context._main_variables = copy.deepcopy(context.variables)

            # Process template through stages 1-4 only (not variable expansion)
            template_data = self._process_template_stages(
                processor, template_content, template_context
            )

            # Merge template variables into current context (template has lower precedence)
            if template_context.variables:
                # Template variables have lower precedence than local variables
                # Start with template variables, then overlay main file variables
                merged_vars = copy.deepcopy(template_context.variables)
                # Remove any variables that were passed from main to avoid double-merge
                for key in context.variables:
                    if (
                        key in merged_vars
                        and merged_vars[key] == context.variables[key]
                    ):
                        # This variable came from main context, keep main's value
                        merged_vars[key] = context.variables[key]
                # Add any new variables from main that weren't in template
                self._deep_merge(merged_vars, context.variables)
                context.variables = merged_vars

            return template_data

        finally:
            context.loaded_files.discard(template_path)

    def _process_template_stages(
        self, processor, template_content: str, template_context
    ) -> Dict[str, Any]:
        """Process template through stages 1-4 only (skip variable expansion)."""
        template_context.check_recursion("template processing")

        try:
            # Stage 1: Initial Parsing & Version Check
            template_context.check_timeout()
            data = processor.parser.parse(template_content, template_context)
            template_context.track_stage("parsing")

            # Stage 2: Metadata Resolution
            template_context.check_timeout()
            data = processor.metadata_processor.process(data, template_context)
            template_context.track_stage("metadata")

            # Stage 3: Template Processing (recursive templates)
            template_context.check_timeout()
            data = processor.template_processor.process(data, template_context)
            template_context.track_stage("templates")

            # Stage 4: Directive Resolution
            template_context.check_timeout()
            data = processor.directive_processor.process(data, template_context)
            template_context.track_stage("directives")

            # Skip Stage 5: Variable Expansion - we'll do this at the main level

            return data

        except Exception as e:
            template_context.decrease_recursion()
            raise e

    def _resolve_template_path(self, template_config: Dict[str, Any], context) -> Path:
        """Resolve template file path from configuration."""
        path = template_config.get("path")
        use = template_config.get("use")

        if path:
            # Direct path reference - validate path type
            if not isinstance(path, str):
                from ..exceptions import DirectiveSyntaxError

                raise DirectiveSyntaxError(
                    "__template.path must be a string",
                    str(context.file_path),
                    "__template.path",
                )
            template_path = Path(path)
            if not template_path.is_absolute():
                template_path = context.base_path / template_path
            return template_path.resolve()

        elif use:
            # Use-based reference (requires template_path configuration)
            if not self.config.template_path:
                raise SmartYAMLError(
                    "template_path must be configured to use 'use' references",
                    str(context.file_path),
                    "__template.use",
                )

            # Convert dot notation to path (e.g., "sub.name" -> "sub/name.yaml")
            use_path = use.replace(".", "/") + ".yaml"
            template_path = self.config.template_path / use_path
            return template_path.resolve()

        else:
            from ..exceptions import DirectiveSyntaxError

            raise DirectiveSyntaxError(
                "__template must specify either 'path' or 'use'",
                str(context.file_path),
                "__template",
            )

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source dict into target dict using unified merger."""
        merger = DeepMerger(
            list_strategy=MergeStrategy.REPLACE,
            conflict_strategy=MergeStrategy.REPLACE,  # Templates allow overrides
        )
        merger.merge(target, source)
