"""
Variable merging utilities for SmartYAML loading pipeline.
"""

from typing import Any, Dict, Optional


class VariableMerger:
    """
    Handles variable merging and precedence logic.

    This class centralizes the complex variable precedence logic that was
    previously duplicated between load() and loads() functions.
    """

    def merge_variables(
        self,
        function_variables: Optional[Dict[str, Any]],
        accumulated_variables: Dict[str, Any],
        document_vars: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Merge variables from different sources with proper precedence.

        Precedence order (highest to lowest):
        1. Function variables (passed as parameters)
        2. Document __vars (from YAML metadata)
        3. Accumulated variables (from imported templates)

        Args:
            function_variables: Variables passed to load/loads functions
            accumulated_variables: Variables accumulated during loading
            document_vars: Variables from document __vars metadata

        Returns:
            Merged variables dictionary with proper precedence
        """
        # Start with accumulated vars as base (lowest precedence)
        merged_vars = {}

        if accumulated_variables and isinstance(accumulated_variables, dict):
            merged_vars.update(accumulated_variables)

        # Add document variables (medium precedence)
        if document_vars and isinstance(document_vars, dict):
            merged_vars.update(document_vars)

        # Add function variables (highest precedence)
        if function_variables and isinstance(function_variables, dict):
            merged_vars.update(function_variables)

        return merged_vars

    def process_accumulated_variables(
        self, loader_instance, result: Any, function_variables: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process and merge all accumulated variables from various sources.

        Args:
            loader_instance: The YAML loader instance
            result: Parsed YAML result (may contain __vars)
            function_variables: Variables passed to load/loads functions

        Returns:
            Final merged variables dictionary
        """
        # Get variables accumulated during loading
        accumulated_variables = {}
        if loader_instance and hasattr(loader_instance, "accumulated_vars"):
            accumulated_variables = loader_instance.accumulated_vars or {}

        # Extract variables from root result using shared utility
        from ..utils.variable_substitution import extract_vars_metadata

        document_vars = extract_vars_metadata(result)

        # Merge with proper precedence
        return self.merge_variables(
            function_variables=function_variables,
            accumulated_variables=accumulated_variables,
            document_vars=document_vars,
        )

    def expand_variables_recursively(
        self, variables: Dict[str, Any], max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Expand variables that reference each other recursively.

        This handles cases where variables contain references to other variables.
        Uses change tracking to optimize performance by detecting convergence.

        Args:
            variables: Dictionary of variables to expand
            max_iterations: Maximum expansion iterations to prevent infinite loops

        Returns:
            Fully expanded variables dictionary
        """

        expanded_vars = variables.copy()

        # Import the expansion processing function
        from .. import process_deferred_expansions

        # Track which variables have changed to optimize iterations
        changed_keys = set(variables.keys()) if variables else set()

        for i in range(max_iterations):
            if not changed_keys:
                # No variables changed in previous iteration, we're done
                break

            # Only process variables that might have changed
            old_values = {k: expanded_vars.get(k) for k in changed_keys}

            # Process any deferred expansions in the variables themselves
            new_expanded = process_deferred_expansions(expanded_vars, expanded_vars)

            # Track which variables actually changed in this iteration
            new_changed_keys = set()
            for key in changed_keys:
                if key in new_expanded and new_expanded.get(key) != old_values.get(key):
                    new_changed_keys.add(key)

            # Also check for any new variables that were added
            for key in new_expanded:
                if key not in expanded_vars or expanded_vars.get(
                    key
                ) != new_expanded.get(key):
                    new_changed_keys.add(key)

            # If no changes, we're done
            if not new_changed_keys:
                break

            expanded_vars = new_expanded
            changed_keys = new_changed_keys

        return expanded_vars
