"""Tests for download_schema.py script."""
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

# Add scripts to path
import sys

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import download_schema


class TestGetLatestReleaseInfo:
    """Test get_latest_release_info function."""

    @patch("download_schema.requests.get")
    def test_success(self, mock_get):
        """Test successful API call."""
        mock_response = Mock()
        mock_response.json.return_value = {"tag_name": "v6.13.0", "assets": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = download_schema.get_latest_release_info()

        assert result["tag_name"] == "v6.13.0"
        mock_get.assert_called_once()

    @patch("download_schema.requests.get")
    def test_retry_on_failure(self, mock_get):
        """Test retry logic on network failure."""
        mock_get.side_effect = [
            requests.RequestException("Network error"),
            requests.RequestException("Network error"),
            Mock(json=lambda: {"tag_name": "v6.13.0"}),
        ]

        # Should succeed on third attempt
        result = download_schema.get_latest_release_info()
        assert result["tag_name"] == "v6.13.0"


class TestFindSchemaAsset:
    """Test find_schema_asset function."""

    def test_finds_schema_json(self):
        """Test finding schema.json in assets."""
        release_info = {
            "assets": [
                {"name": "amis.js", "browser_download_url": "https://example.com/amis.js"},
                {"name": "schema.json", "browser_download_url": "https://example.com/schema.json"},
            ]
        }

        url = download_schema.find_schema_asset(release_info)
        assert url == "https://example.com/schema.json"

    def test_returns_none_when_not_found(self):
        """Test returns None when schema.json not in assets."""
        release_info = {"assets": [{"name": "amis.js", "browser_download_url": "https://example.com/amis.js"}]}

        url = download_schema.find_schema_asset(release_info)
        assert url is None


class TestValidateSchema:
    """Test validate_schema function."""

    def test_valid_json_schema(self, tmp_path):
        """Test validation of valid JSON schema."""
        schema_path = tmp_path / "schema.json"
        schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        with open(schema_path, "w") as f:
            json.dump(schema_data, f)

        assert download_schema.validate_schema(schema_path) is True

    def test_invalid_json(self, tmp_path):
        """Test validation fails on invalid JSON."""
        schema_path = tmp_path / "schema.json"

        with open(schema_path, "w") as f:
            f.write("{ invalid json }")

        assert download_schema.validate_schema(schema_path) is False

    def test_not_json_object(self, tmp_path):
        """Test validation fails when not a JSON object."""
        schema_path = tmp_path / "schema.json"

        with open(schema_path, "w") as f:
            json.dump([], f)  # Array instead of object

        assert download_schema.validate_schema(schema_path) is False


class TestDownloadFile:
    """Test download_file function."""

    @patch("download_schema.requests.get")
    def test_successful_download(self, mock_get, tmp_path):
        """Test successful file download."""
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b"test data"])
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        output_path = tmp_path / "test.json"
        download_schema.download_file("https://example.com/file", output_path)

        assert output_path.exists()
        assert output_path.read_bytes() == b"test data"

    @patch("download_schema.requests.get")
    def test_creates_parent_directory(self, mock_get, tmp_path):
        """Test that parent directories are created."""
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b"data"])
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        output_path = tmp_path / "subdir" / "nested" / "file.json"
        download_schema.download_file("https://example.com/file", output_path)

        assert output_path.exists()
        assert output_path.parent.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
