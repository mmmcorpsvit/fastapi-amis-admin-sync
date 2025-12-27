"""Tests for generate_models.py script."""
import ast
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add scripts to path
import sys

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import generate_models


class TestCheckDependencies:
    """Test check_dependencies function."""

    @patch("generate_models.subprocess.run")
    def test_dependency_installed(self, mock_run):
        """Test when datamodel-code-generator is installed."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "datamodel-code-generator 0.25.0"
        mock_run.return_value = mock_result

        assert generate_models.check_dependencies() is True

    @patch("generate_models.subprocess.run")
    def test_dependency_not_installed(self, mock_run):
        """Test when datamodel-code-generator is not installed."""
        mock_run.side_effect = FileNotFoundError()

        assert generate_models.check_dependencies() is False


class TestGenerateModels:
    """Test generate_models function."""

    @patch("generate_models.subprocess.run")
    def test_successful_generation(self, mock_run, tmp_path):
        """Test successful model generation."""
        schema_path = tmp_path / "schema.json"
        output_path = tmp_path / "models.py"

        # Create dummy schema
        schema_path.write_text('{"type": "object"}')

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Create output file (simulating datamodel-codegen)
        output_path.write_text("from pydantic import BaseModel\n\nclass Schema(BaseModel):\n    pass\n")

        result = generate_models.generate_models(schema_path, output_path)
        assert result is True

    @patch("generate_models.subprocess.run")
    def test_schema_not_found(self, mock_run, tmp_path):
        """Test when schema file doesn't exist."""
        schema_path = tmp_path / "nonexistent.json"
        output_path = tmp_path / "models.py"

        result = generate_models.generate_models(schema_path, output_path)
        assert result is False

    @patch("generate_models.subprocess.run")
    def test_generation_failure(self, mock_run, tmp_path):
        """Test when datamodel-codegen fails."""
        schema_path = tmp_path / "schema.json"
        output_path = tmp_path / "models.py"
        schema_path.write_text('{"type": "object"}')

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Invalid schema"
        mock_run.return_value = mock_result

        result = generate_models.generate_models(schema_path, output_path)
        assert result is False


class TestValidateGeneratedCode:
    """Test validate_generated_code function."""

    def test_valid_python_code(self, tmp_path):
        """Test validation of valid Python code."""
        output_path = tmp_path / "models.py"
        code = """
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
"""
        output_path.write_text(code)

        assert generate_models.validate_generated_code(output_path) is True

    def test_invalid_python_syntax(self, tmp_path):
        """Test validation fails on invalid syntax."""
        output_path = tmp_path / "models.py"
        output_path.write_text("class User(BaseModel:\n    pass")  # Missing closing paren

        assert generate_models.validate_generated_code(output_path) is False


class TestAddHeaderComment:
    """Test add_header_comment function."""

    def test_adds_header(self, tmp_path):
        """Test that header comment is added to file."""
        output_path = tmp_path / "models.py"
        schema_path = tmp_path / "schema.json"

        original_content = "from pydantic import BaseModel\n"
        output_path.write_text(original_content)
        schema_path.touch()

        generate_models.add_header_comment(output_path, schema_path)

        content = output_path.read_text()
        assert '"""' in content
        assert "AUTO-GENERATED FILE" in content
        assert original_content in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
