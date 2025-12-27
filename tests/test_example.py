"""Tests for the example FastAPI application."""
from fastapi.testclient import TestClient

import sys
from pathlib import Path

# Add examples to path
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
sys.path.insert(0, str(EXAMPLES_DIR))

from basic_example import app

client = TestClient(app)


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_returns_links(self):
        """Test root endpoint returns endpoint links."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "endpoints" in data
        assert "page" in data["endpoints"]


class TestPageEndpoints:
    """Test AMIS page endpoints."""

    def test_get_page_returns_schema(self):
        """Test /page returns valid AMIS schema."""
        response = client.get("/page")
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "page"
        assert "body" in data
        assert isinstance(data["body"], list)

    def test_get_form_returns_schema(self):
        """Test /form returns valid AMIS schema."""
        response = client.get("/form")
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "page"
        assert "body" in data

    def test_get_table_returns_schema(self):
        """Test /table returns valid AMIS schema."""
        response = client.get("/table")
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "page"
        assert "body" in data


class TestViewerEndpoint:
    """Test AMIS viewer HTML page."""

    def test_viewer_returns_html(self):
        """Test /viewer returns HTML page."""
        response = client.get("/viewer")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<!DOCTYPE html>" in response.text
        assert "AMIS" in response.text


class TestMockAPIEndpoints:
    """Test mock API endpoints."""

    def test_submit_form(self):
        """Test form submission endpoint."""
        test_data = {"username": "testuser", "email": "test@example.com"}
        response = client.post("/api/submit", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 0
        assert data["msg"] == "Success"

    def test_get_users(self):
        """Test users API endpoint."""
        response = client.get("/api/users")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == 0
        assert "data" in data
        assert "items" in data["data"]
        assert len(data["data"]["items"]) > 0


class TestAMISSchemaStructure:
    """Test AMIS schema structure compliance."""

    def test_page_has_required_fields(self):
        """Test page schema has required AMIS fields."""
        response = client.get("/page")
        data = response.json()

        # AMIS page must have type
        assert "type" in data
        assert data["type"] == "page"

        # Should have body array
        assert "body" in data
        assert isinstance(data["body"], list)

    def test_form_structure(self):
        """Test form component structure."""
        response = client.get("/page")
        data = response.json()

        form = data["body"][0]
        assert form["type"] == "form"
        assert "body" in form
        assert isinstance(form["body"], list)

    def test_crud_structure(self):
        """Test CRUD/table component structure."""
        response = client.get("/table")
        data = response.json()

        crud = data["body"][0]
        assert crud["type"] == "crud"
        assert "columns" in crud
        assert isinstance(crud["columns"], list)


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
