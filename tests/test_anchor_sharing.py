"""
Tests for cross-file anchor sharing functionality in SmartYAML templates.
"""

import pytest
import tempfile
from pathlib import Path
import smartyaml


class TestAnchorSharing:
    """Test cross-file anchor sharing between templates and main documents."""

    def test_basic_anchor_sharing(self, tmp_path):
        """Test basic anchor sharing from template to main document."""
        # Create template directory
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        
        # Create template with anchor
        template_file = template_dir / "config.yaml"
        template_file.write_text("""
shared_config: &shared_config
  host: localhost
  port: 8080
  debug: true
""")
        
        # Create main document that uses template anchor
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
<<: !template(config)

service:
  <<: *shared_config
  name: my-service
""")
        
        # Load and verify
        result = smartyaml.load(main_file, template_path=template_dir)
        
        expected = {
            'shared_config': {
                'host': 'localhost',
                'port': 8080,
                'debug': True
            },
            'service': {
                'host': 'localhost',
                'port': 8080,
                'debug': True,
                'name': 'my-service'
            }
        }
        
        assert result == expected

    def test_multiple_anchors_from_template(self, tmp_path):
        """Test multiple anchors from single template."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        
        # Template with multiple anchors
        template_file = template_dir / "multi.yaml"
        template_file.write_text("""
database: &db_config
  host: db.example.com
  port: 5432

cache: &cache_config
  host: cache.example.com
  port: 6379

common: &common_config
  timeout: 30
  retries: 3
""")
        
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
<<: !template(multi)

services:
  web:
    <<: *common_config
    database:
      <<: *db_config
  worker:
    <<: *common_config
    cache:
      <<: *cache_config
""")
        
        result = smartyaml.load(main_file, template_path=template_dir)
        
        # Verify all anchors work
        assert result['services']['web']['timeout'] == 30
        assert result['services']['web']['database']['host'] == 'db.example.com'
        assert result['services']['worker']['cache']['port'] == 6379

    def test_nested_template_anchors(self, tmp_path):
        """Test anchors with nested template structures."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        
        template_file = template_dir / "nested.yaml"
        template_file.write_text("""
defaults: &defaults
  app:
    name: MyApp
    version: "1.0"
  database:
    engine: postgresql
    pool_size: 10

environment_overrides: &prod_overrides
  app:
    debug: false
    log_level: ERROR
  database:
    pool_size: 20
""")
        
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
<<: !template(nested)

development:
  <<: *defaults
  # NOTE: YAML merge doesn't do deep merging, so this replaces the entire app object
  # In practice, you'd need to use separate anchors or handle merging differently
  
staging:
  <<: *defaults  # This inherits the full structure
  
production:
  <<: *defaults
  <<: *prod_overrides  # This does merge at the top level
""")
        
        result = smartyaml.load(main_file, template_path=template_dir)
        
        # Check staging inherits full defaults structure
        assert result['staging']['app']['name'] == 'MyApp'
        assert result['staging']['app']['version'] == '1.0'
        assert result['staging']['database']['engine'] == 'postgresql'
        
        # Check production has overrides applied (top-level merge works)
        assert result['production']['app']['log_level'] == 'ERROR'
        assert result['production']['database']['pool_size'] == 20

    def test_anchor_precedence_template_vs_main(self, tmp_path):
        """Test anchor precedence when both template and main define same anchor."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        
        template_file = template_dir / "base.yaml"
        template_file.write_text("""
config: &template_config
  source: template
  value: 100
""")
        
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
<<: !template(base)

config: &main_config
  source: main
  value: 200

result_template:
  <<: *template_config

result_main:
  <<: *main_config
""")
        
        result = smartyaml.load(main_file, template_path=template_dir)
        
        # Both anchors should be available
        assert result['result_template']['source'] == 'template'
        assert result['result_main']['source'] == 'main'

    def test_multiple_templates_with_anchors(self, tmp_path):
        """Test using anchors from multiple templates."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        
        # First template
        db_template = template_dir / "database.yaml"
        db_template.write_text("""
postgres_config: &postgres
  driver: postgresql
  port: 5432
""")
        
        # Second template
        cache_template = template_dir / "cache.yaml" 
        cache_template.write_text("""
redis_config: &redis
  driver: redis
  port: 6379
""")
        
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
<<: !template(database)
<<: !template(cache)

services:
  api:
    database:
      <<: *postgres
    cache:
      <<: *redis
""")
        
        result = smartyaml.load(main_file, template_path=template_dir)
        
        assert result['services']['api']['database']['driver'] == 'postgresql'
        assert result['services']['api']['cache']['driver'] == 'redis'

    def test_anchor_with_scalar_values(self, tmp_path):
        """Test anchors with scalar values, not just mappings."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        
        template_file = template_dir / "scalars.yaml"
        template_file.write_text("""
app_name: &app_name "MyApplication"
version: &version "2.1.0"
debug_enabled: &debug true
max_connections: &max_conn 100
""")
        
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
<<: !template(scalars)

config:
  application:
    name: *app_name
    version: *version
    debug: *debug
  database:
    max_connections: *max_conn
""")
        
        result = smartyaml.load(main_file, template_path=template_dir)
        
        assert result['config']['application']['name'] == 'MyApplication'
        assert result['config']['application']['version'] == '2.1.0'
        assert result['config']['application']['debug'] is True
        assert result['config']['database']['max_connections'] == 100

    def test_anchor_sharing_with_sequence_values(self, tmp_path):
        """Test anchors with sequence/list values."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        
        template_file = template_dir / "sequences.yaml"
        template_file.write_text("""
default_middleware: &middleware
  - auth
  - cors
  - logging

admin_routes: &admin_routes
  - /admin
  - /admin/users
  - /admin/settings
""")
        
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
<<: !template(sequences)

apps:
  web:
    middleware: *middleware
    routes: 
      - /
      - /api
  admin:
    middleware: *middleware
    routes: *admin_routes
""")
        
        result = smartyaml.load(main_file, template_path=template_dir)
        
        assert result['apps']['web']['middleware'] == ['auth', 'cors', 'logging']
        assert result['apps']['admin']['routes'] == ['/admin', '/admin/users', '/admin/settings']

    def test_error_handling_missing_template(self, tmp_path):
        """Test error handling when template file doesn't exist."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
<<: !template(nonexistent)

test: value
""")
        
        # Should raise an error about missing template during normal loading
        # (Gets wrapped in ConstructorError when used in merge context)
        import yaml
        with pytest.raises((smartyaml.SmartYAMLFileNotFoundError, yaml.constructor.ConstructorError)):
            smartyaml.load(main_file, template_path=template_dir)

    def test_no_anchor_sharing_without_template_path(self, tmp_path):
        """Test that anchor sharing only works when template_path is provided."""
        # Create a document that would use anchor sharing
        main_file = tmp_path / "main.yaml"
        main_file.write_text("""
<<: !template(config)

service:
  <<: *shared_config
""")
        
        # Without template_path, should get undefined alias error
        with pytest.raises(Exception) as exc_info:
            smartyaml.load(main_file)  # No template_path provided
        
        # Should be a composer error about undefined alias
        assert "undefined alias" in str(exc_info.value).lower()

    def test_anchor_preprocessing_detection(self):
        """Test the preprocessing detection logic."""
        from smartyaml.constructors.templates import TemplatePreProcessor
        
        preprocessor = TemplatePreProcessor()
        
        # Should detect template directives
        assert preprocessor.should_preprocess_document("<<: !template(config)")
        assert preprocessor.should_preprocess_document("data: !template(config)")
        assert preprocessor.should_preprocess_document("  <<: !template(config)  ")
        
        # Should not detect non-template content
        assert not preprocessor.should_preprocess_document("config: value")
        assert not preprocessor.should_preprocess_document("<<: !import_yaml(file.yaml)")
        
        # Test template reference extraction
        content = """
<<: !template(config)
other: !template(database)
"""
        refs = preprocessor.extract_template_references(content)
        assert set(refs) == {'config', 'database'}