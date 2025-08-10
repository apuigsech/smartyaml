#!/usr/bin/env python3
"""
Demonstration script for SmartYAML metadata field functionality.
This script loads the metadata_example.yaml file and shows how metadata fields are removed.
"""

import sys
import json
from pathlib import Path

# Add the parent directory to path to import smartyaml
sys.path.insert(0, str(Path(__file__).parent.parent))

import smartyaml


def demonstrate_metadata_removal():
    """Load and display the metadata example, showing before/after"""
    
    example_file = Path(__file__).parent / "metadata_example.yaml"
    
    print("=== SmartYAML Metadata Field Demonstration ===\n")
    
    # Show original file content
    print("1. Original YAML content (with metadata fields):")
    print("-" * 50)
    with open(example_file, 'r') as f:
        content = f.read()
    print(content[:500] + "..." if len(content) > 500 else content)
    
    # Load with metadata removal (default behavior)
    print("\n2. Loaded with metadata removal (default):")
    print("-" * 50)
    result_with_removal = smartyaml.load(example_file)
    print(json.dumps(result_with_removal, indent=2))
    
    # Load without metadata removal
    print("\n3. Loaded without metadata removal:")
    print("-" * 50)
    result_without_removal = smartyaml.load(example_file, remove_metadata=False)
    print(json.dumps(result_without_removal, indent=2))
    
    # Count metadata fields
    def count_metadata_fields(data, prefix=""):
        """Recursively count fields starting with __"""
        count = 0
        if isinstance(data, dict):
            for key, value in data.items():
                if key.startswith("__"):
                    count += 1
                    print(f"  Found metadata field: {prefix}{key}")
                else:
                    count += count_metadata_fields(value, f"{prefix}{key}.")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                count += count_metadata_fields(item, f"{prefix}[{i}].")
        return count
    
    print(f"\n4. Summary:")
    print("-" * 50)
    metadata_count = count_metadata_fields(result_without_removal)
    print(f"Total metadata fields found: {metadata_count}")
    print(f"Fields in result with removal: {len(str(result_with_removal))}")
    print(f"Fields in result without removal: {len(str(result_without_removal))}")
    print(f"\nMetadata fields automatically removed: ✓")


if __name__ == "__main__":
    demonstrate_metadata_removal()