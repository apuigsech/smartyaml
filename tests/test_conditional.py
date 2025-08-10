"""
Tests for conditional inclusion constructors
"""

import os
import pytest
import smartyaml


class TestIncludeIfConstructor:
    """Test !include_if directive"""
    
    def test_include_if_true(self, tmp_path, monkeypatch):
        """Test conditional inclusion when condition is true"""
        monkeypatch.setenv("DEBUG", "1")
        
        # Create files
        debug_file = tmp_path / "debug.txt"
        debug_file.write_text("Debug content")
        
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
content: !include_if(DEBUG, debug.txt)
""")
        
        result = smartyaml.load(yaml_file)
        assert result['content'] == 'Debug content'
    
    def test_include_if_false(self, tmp_path, monkeypatch):
        """Test conditional inclusion when condition is false"""
        monkeypatch.setenv("DEBUG", "0")
        
        # Create files
        debug_file = tmp_path / "debug.txt"
        debug_file.write_text("Debug content")
        
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
content: !include_if(DEBUG, debug.txt)
""")
        
        result = smartyaml.load(yaml_file)
        assert result['content'] is None
    
    def test_include_if_missing_env(self, tmp_path, monkeypatch):
        """Test conditional inclusion when env var doesn't exist"""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        
        # Create files
        debug_file = tmp_path / "debug.txt"
        debug_file.write_text("Debug content")
        
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
content: !include_if(MISSING_VAR, debug.txt)
""")
        
        result = smartyaml.load(yaml_file)
        assert result['content'] is None


class TestIncludeYAMLIfConstructor:
    """Test !include_yaml_if directive"""
    
    def test_include_yaml_if_true(self, tmp_path, monkeypatch):
        """Test conditional YAML inclusion when condition is true"""
        monkeypatch.setenv("ENABLE_FEATURE", "true")
        
        # Create files
        feature_file = tmp_path / "feature.yaml"
        feature_file.write_text("""
enabled: true
settings:
  level: advanced
""")
        
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
feature: !include_yaml_if(ENABLE_FEATURE, feature.yaml)
""")
        
        result = smartyaml.load(yaml_file)
        assert result['feature']['enabled'] is True
        assert result['feature']['settings']['level'] == 'advanced'
    
    def test_include_yaml_if_false(self, tmp_path, monkeypatch):
        """Test conditional YAML inclusion when condition is false"""
        monkeypatch.setenv("ENABLE_FEATURE", "false")
        
        # Create files
        feature_file = tmp_path / "feature.yaml"
        feature_file.write_text("""
enabled: true
""")
        
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
feature: !include_yaml_if(ENABLE_FEATURE, feature.yaml)
""")
        
        result = smartyaml.load(yaml_file)
        assert result['feature'] is None