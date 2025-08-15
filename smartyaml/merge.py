"""
YAML merging utilities for SmartYAML
"""

from typing import Any, Dict


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries with override taking precedence.

    This is the shared implementation used throughout SmartYAML for consistent
    deep merging behavior. It uses copy.deepcopy to avoid modifying original data.

    Args:
        base: Base dictionary
        override: Override dictionary (takes precedence)

    Returns:
        Merged dictionary
    """
    import copy

    # Start with a deep copy of base to avoid modifying original
    result = copy.deepcopy(base)

    # Recursively merge override into result
    _merge_dict_recursive(result, override)

    return result


def _merge_dict_recursive(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    Recursively merge source dictionary into target dictionary.

    This is an internal helper function that modifies the target dictionary in place.

    Args:
        target: Target dictionary to merge into (modified in place)
        source: Source dictionary to merge from
    """
    import copy

    for key, value in source.items():
        if key in target:
            # Key exists in both - need to merge
            if isinstance(target[key], dict) and isinstance(value, dict):
                # Both are dicts - recursive merge
                _merge_dict_recursive(target[key], value)
            else:
                # Different types or scalars - source wins (override)
                target[key] = copy.deepcopy(value)
        else:
            # Key only in source - add to target
            target[key] = copy.deepcopy(value)


def merge_yaml_data(imported_data: Any, local_data: Dict[str, Any]) -> Any:
    """
    Merge imported YAML data with local overrides.

    Args:
        imported_data: Data from imported YAML file
        local_data: Local overrides from the same YAML node

    Returns:
        Merged data with local overrides taking precedence
    """
    if not local_data:
        return imported_data

    if isinstance(imported_data, dict):
        return deep_merge(imported_data, local_data)
    else:
        # If imported data is not a dict, local overrides replace it entirely
        return local_data if local_data else imported_data
