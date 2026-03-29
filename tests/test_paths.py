import pytest
import os
import sys
from unittest.mock import patch


class TestResourcePath:
    def test_resource_path_returns_combined_path(self):
        from utils.paths import resource_path
        
        result = resource_path("test.txt")
        assert os.path.isabs(result)
        assert result.endswith("test.txt")

    def test_resource_path_fallback_behavior(self):
        from utils.paths import resource_path
        
        result = resource_path("test.txt")
        expected_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assert expected_dir in result

    def test_resource_path_with_pyinstaller_mock(self):
        from utils.paths import resource_path
        
        with patch.object(sys, '_MEIPASS', create=True, new='/tmp/frozen_path'):
            result = resource_path("test.txt")
            assert "/tmp/frozen_path" in result
            assert result.endswith("test.txt")
