"""
Conditional inclusion constructors for SmartYAML
"""

import yaml
from pathlib import Path
from typing import Any, Dict
from .base import ConditionalConstructor
from ..utils.file_utils import read_file
from ..utils.validation_utils import validate_constructor_args
from ..utils.loader_utils import create_loader_context
from ..exceptions import SmartYAMLError


class IncludeIfConstructor(ConditionalConstructor):
    """
    Constructor for !include_if [condition, filename] directive.
    Includes text file only if condition (environment variable) is truthy.
    """
    
    def __init__(self):
        super().__init__('!include_if')
    
    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract condition and filename from YAML node."""
        if isinstance(node, yaml.SequenceNode):
            sequence = loader.construct_sequence(node)
            validate_constructor_args(sequence, 2, self.directive_name)
            condition, filename = sequence
        else:
            raise SmartYAMLError(f"{self.directive_name} expects a sequence: [condition, filename]")
        
        return {'condition': condition, 'filename': filename}
    
    def execute(self, loader, params: Dict[str, Any]) -> Any:
        """Include file content if condition is met."""
        # Check condition first
        if not self.should_include(params['condition']):
            return None
        
        # Load file content
        file_path = params['resolved_file_path']
        loader_context = self.get_loader_context(loader)
        return read_file(file_path, loader_context['max_file_size'])


class IncludeYamlIfConstructor(ConditionalConstructor):
    """
    Constructor for !include_yaml_if [condition, filename] directive.
    Includes YAML file only if condition (environment variable) is truthy.
    """
    
    def __init__(self):
        super().__init__('!include_yaml_if')
    
    def extract_parameters(self, loader, node) -> Dict[str, Any]:
        """Extract condition and filename from YAML node."""
        if isinstance(node, yaml.SequenceNode):
            sequence = loader.construct_sequence(node)
            validate_constructor_args(sequence, 2, self.directive_name)
            condition, filename = sequence
        else:
            raise SmartYAMLError(f"{self.directive_name} expects a sequence: [condition, filename]")
        
        return {'condition': condition, 'filename': filename}
    
    def execute(self, loader, params: Dict[str, Any]) -> Any:
        """Include YAML data if condition is met."""
        # Check condition first
        if not self.should_include(params['condition']):
            return None
        
        # Load and parse YAML file
        file_path = params['resolved_file_path']
        loader_context = self.get_loader_context(loader)
        
        yaml_content = read_file(file_path, loader_context['max_file_size'])
        
        # Create a new loader with recursion tracking
        # Lazy import to avoid circular dependencies
        from ..loader import SmartYAMLLoader
        new_import_stack = loader_context['import_stack'].copy()
        new_import_stack.add(file_path)
        
        ConfiguredLoader = create_loader_context(
            SmartYAMLLoader, 
            loader_context['base_path'], 
            loader_context['template_path'], 
            new_import_stack,
            loader_context['max_file_size'], 
            loader_context['max_recursion_depth']
        )
        
        return yaml.load(yaml_content, Loader=ConfiguredLoader)


# Create instances for registration
include_if_constructor = IncludeIfConstructor()
include_yaml_if_constructor = IncludeYamlIfConstructor()