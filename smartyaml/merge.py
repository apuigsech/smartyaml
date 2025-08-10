"""
YAML merging utilities for SmartYAML
"""

from typing import Any, Dict, Union


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries with override taking precedence.
    
    Args:
        base: Base dictionary
        override: Override dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


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