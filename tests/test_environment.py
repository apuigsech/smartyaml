"""
Tests for environment variable constructor
"""

import os
import pytest
import smartyaml


class TestEnvConstructor:
    """Test !env directive"""
    
    def test_env_with_existing_var(self, monkeypatch):
        """Test reading existing environment variable"""
        monkeypatch.setenv("TEST_VAR", "test_value")
        
        yaml_content = """
database_url: !env(TEST_VAR)
"""
        
        result = smartyaml.load(yaml_content)
        assert result['database_url'] == 'test_value'
    
    def test_env_with_default(self, monkeypatch):
        """Test environment variable with default value"""
        # Ensure the var doesn't exist
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        
        yaml_content = """
database_url: !env(NONEXISTENT_VAR, localhost)
"""
        
        result = smartyaml.load(yaml_content)
        assert result['database_url'] == 'localhost'
    
    def test_env_missing_no_default(self, monkeypatch):
        """Test missing environment variable without default raises error"""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        
        yaml_content = """
database_url: !env(MISSING_VAR)
"""
        
        with pytest.raises(smartyaml.SmartYAMLError):
            smartyaml.load(yaml_content)
    
    def test_env_override_existing(self, monkeypatch):
        """Test that existing env var overrides default"""
        monkeypatch.setenv("EXISTING_VAR", "env_value")
        
        yaml_content = """
database_url: !env(EXISTING_VAR, default_value)
"""
        
        result = smartyaml.load(yaml_content)
        assert result['database_url'] == 'env_value'