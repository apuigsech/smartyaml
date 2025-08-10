"""
Tests for encoding constructors
"""

import pytest
import smartyaml


class TestBase64Constructor:
    """Test !base64 directive"""
    
    def test_base64_encode(self):
        """Test base64 encoding"""
        yaml_content = """
secret: !base64(hello world)
"""
        
        result = smartyaml.load(yaml_content)
        assert result['secret'] == 'aGVsbG8gd29ybGQ='
    
    def test_base64_encode_unicode(self):
        """Test base64 encoding with unicode characters"""
        yaml_content = """
message: !base64(Hola, ¡mundo!)
"""
        
        result = smartyaml.load(yaml_content)
        # Should properly encode unicode
        assert isinstance(result['message'], str)
        assert len(result['message']) > 0


class TestBase64DecodeConstructor:
    """Test !base64_decode directive"""
    
    def test_base64_decode(self):
        """Test base64 decoding"""
        yaml_content = """
message: !base64_decode(aGVsbG8gd29ybGQ=)
"""
        
        result = smartyaml.load(yaml_content)
        assert result['message'] == 'hello world'
    
    def test_base64_decode_unicode(self):
        """Test base64 decoding with unicode"""
        yaml_content = """
message: !base64_decode(SG9sYSwgwqFtdW5kbyE=)
"""
        
        result = smartyaml.load(yaml_content)
        assert result['message'] == 'Hola, ¡mundo!'
    
    def test_base64_decode_invalid(self):
        """Test base64 decoding with invalid data"""
        yaml_content = """
message: !base64_decode(invalid_base64_data)
"""
        
        with pytest.raises(smartyaml.SmartYAMLError):
            smartyaml.load(yaml_content)


class TestBase64RoundTrip:
    """Test base64 encode/decode round trip"""
    
    def test_roundtrip(self):
        """Test encoding then decoding returns original"""
        original = "Hello, 世界! 🌍"
        
        # First encode
        yaml_content = f"""
encoded: !base64({original})
"""
        result = smartyaml.load(yaml_content)
        encoded = result['encoded']
        
        # Then decode
        yaml_content2 = f"""
decoded: !base64_decode({encoded})
"""
        result2 = smartyaml.load(yaml_content2)
        assert result2['decoded'] == original