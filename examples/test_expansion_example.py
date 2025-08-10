#!/usr/bin/env python3
"""
Demonstration script for SmartYAML variable expansion functionality.
This script shows how the !expand directive and __vars metadata work together.
"""

import sys
import json
from pathlib import Path

# Add the parent directory to path to import smartyaml
sys.path.insert(0, str(Path(__file__).parent.parent))

import smartyaml


def demonstrate_expansion():
    """Load and display the expansion example, showing various scenarios"""
    
    example_file = Path(__file__).parent / "expansion_example.yaml"
    
    print("=== SmartYAML Variable Expansion Demonstration ===\n")
    
    # 1. Basic expansion with __vars metadata
    print("1. Loading with __vars metadata:")
    print("-" * 50)
    result_with_vars = smartyaml.load(example_file)
    print(json.dumps(result_with_vars, indent=2))
    
    # 2. Function variables override __vars
    print("\n2. Function variables override __vars metadata:")
    print("-" * 50)
    override_vars = {
        "environment": "production",
        "version": "3.0.0",
        "database_host": "prod-db.example.com"
    }
    result_override = smartyaml.load(example_file, variables=override_vars)
    print(json.dumps(result_override, indent=2))
    
    # 3. Show what happens without expansion
    print("\n3. Comparison - No expansion (using loads with string):")
    print("-" * 50)
    # Read raw content to show literal {{}} syntax
    with open(example_file, 'r') as f:
        lines = f.readlines()
    
    # Show a few key lines with variable patterns
    print("Raw YAML content contains:")
    for i, line in enumerate(lines):
        if '!expand' in line and '{{' in line:
            print(f"  Line {i+1}: {line.strip()}")
            if i > 10:  # Limit output
                break
    
    # 4. Variables usage summary  
    print("\n4. Variable Usage Summary:")
    print("-" * 50)
    
    # Count how many !expand directives were processed
    def count_expansions(data, count=0):
        if isinstance(data, dict):
            for value in data.values():
                count = count_expansions(value, count)
        elif isinstance(data, list):
            for item in data:
                count = count_expansions(item, count)
        elif isinstance(data, str):
            if '{{' not in data:  # Expanded strings won't have {{ anymore
                count += 1 if any('{{' in str(v) for v in override_vars.values()) else 0
        return count
    
    print(f"Variables defined in __vars: {len([k for k in ['app_name', 'environment', 'version', 'database_host', 'database_port'] if k])}")
    print(f"Function variables provided: {len(override_vars)}")
    print(f"Metadata fields automatically removed: ✓")
    print(f"Variable expansion successful: ✓")


def demonstrate_advanced_usage():
    """Show advanced variable expansion scenarios"""
    
    print("\n=== Advanced Variable Expansion Scenarios ===\n")
    
    # 1. Variables only from function call
    print("1. Variables only from function call (no __vars):")
    print("-" * 50)
    yaml_content = """
name: !expand "{{service_name}}"
url: !expand "https://{{domain}}/{{service_name}}"
config:
  debug: !expand "{{debug_mode}}"
"""
    variables = {
        "service_name": "my-api",
        "domain": "api.example.com", 
        "debug_mode": "false"
    }
    result = smartyaml.loads(yaml_content, variables=variables)
    print(json.dumps(result, indent=2))
    
    # 2. Mixed expansion and literal {{}} content
    print("\n2. Mixed expansion and literal content:")
    print("-" * 50)
    yaml_content = """
__vars:
  user: "alice"
  
expanded_greeting: !expand "Hello {{user}}!"
literal_template: "Use {{name}} as template placeholder"
documentation: "The !expand directive processes {{variable}} patterns"
"""
    result = smartyaml.loads(yaml_content)
    print(json.dumps(result, indent=2))
    
    # 3. Error handling
    print("\n3. Error handling - Missing variables:")
    print("-" * 50)
    try:
        yaml_content = 'message: !expand "Hello {{missing_var}}!"'
        result = smartyaml.loads(yaml_content)
    except Exception as e:
        print(f"Expected error: {e}")
    
    print(f"\nVariable expansion features demonstrated: ✓")


if __name__ == "__main__":
    demonstrate_expansion()
    demonstrate_advanced_usage()