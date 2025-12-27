"""
Basic example demonstrating AMIS schema usage with FastAPI.

This example shows how to:
1. Import generated AMIS models
2. Build type-safe AMIS page configurations
3. Serve them via FastAPI endpoints
4. Get full IDE autocomplete support

Run with: uvicorn examples.basic_example:app --reload
Then visit: http://localhost:8000/page
"""
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="FastAPI-AMIS-Admin Example",
    description="Example demonstrating AMIS schema integration",
    version="0.1.0",
)


@app.get("/")
def root():
    """Root endpoint with links to examples."""
    return {
        "message": "FastAPI-AMIS-Admin Example",
        "endpoints": {
            "page": "/page",
            "form": "/form",
            "table": "/table",
            "amis_viewer": "/viewer",
        },
    }


@app.get("/page")
def get_page() -> Dict[str, Any]:
    """
    Example AMIS page with a form.

    Note: Once models are generated, you can import and use them like:
        from fastapi_amis_admin.amis.generated_models import Schema

    For now, we use plain dicts to ensure the example works before generation.
    """
    page = {
        "type": "page",
        "title": "User Registration Form",
        "body": [
            {
                "type": "form",
                "api": "/api/submit",
                "title": "Create New User",
                "body": [
                    {
                        "type": "input-text",
                        "name": "username",
                        "label": "Username",
                        "required": True,
                        "placeholder": "Enter your username",
                    },
                    {
                        "type": "input-email",
                        "name": "email",
                        "label": "Email",
                        "required": True,
                        "placeholder": "user@example.com",
                    },
                    {
                        "type": "input-password",
                        "name": "password",
                        "label": "Password",
                        "required": True,
                    },
                    {
                        "type": "select",
                        "name": "role",
                        "label": "Role",
                        "options": [
                            {"label": "Admin", "value": "admin"},
                            {"label": "User", "value": "user"},
                            {"label": "Guest", "value": "guest"},
                        ],
                    },
                ],
            }
        ],
    }
    return page


@app.get("/form")
def get_form() -> Dict[str, Any]:
    """Example AMIS form with various input types."""
    return {
        "type": "page",
        "title": "Advanced Form Example",
        "body": [
            {
                "type": "form",
                "title": "User Profile",
                "body": [
                    {
                        "type": "input-text",
                        "name": "name",
                        "label": "Full Name",
                        "required": True,
                    },
                    {
                        "type": "input-number",
                        "name": "age",
                        "label": "Age",
                        "min": 0,
                        "max": 120,
                    },
                    {
                        "type": "input-date",
                        "name": "birthdate",
                        "label": "Birth Date",
                        "format": "YYYY-MM-DD",
                    },
                    {
                        "type": "switch",
                        "name": "active",
                        "label": "Active",
                        "option": "Enable user account",
                    },
                    {
                        "type": "textarea",
                        "name": "bio",
                        "label": "Biography",
                        "maxLength": 500,
                    },
                ],
            }
        ],
    }


@app.get("/table")
def get_table() -> Dict[str, Any]:
    """Example AMIS table (CRUD) component."""
    return {
        "type": "page",
        "title": "User Management",
        "body": [
            {
                "type": "crud",
                "api": "/api/users",
                "columns": [
                    {"name": "id", "label": "ID", "type": "text"},
                    {"name": "username", "label": "Username", "type": "text"},
                    {"name": "email", "label": "Email", "type": "text"},
                    {
                        "name": "role",
                        "label": "Role",
                        "type": "mapping",
                        "map": {
                            "admin": "<span class='label label-success'>Admin</span>",
                            "user": "<span class='label label-info'>User</span>",
                            "guest": "<span class='label label-default'>Guest</span>",
                        },
                    },
                    {"name": "created_at", "label": "Created", "type": "date"},
                ],
                "bulkActions": [],
            }
        ],
    }


@app.get("/viewer", response_class=HTMLResponse)
def get_viewer():
    """
    HTML page with AMIS viewer to visualize the schema.
    Visit this page to see the forms/tables rendered.
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AMIS Viewer</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/amis@latest/sdk/sdk.css" />
        <style>
            body { margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #333; }
            .nav { margin-bottom: 20px; }
            .nav button { margin-right: 10px; padding: 8px 16px; cursor: pointer; }
        </style>
        <script src="https://cdn.jsdelivr.net/npm/amis@latest/sdk/sdk.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>FastAPI-AMIS-Admin Viewer</h1>
            <div class="nav">
                <button onclick="loadPage('page')">User Form</button>
                <button onclick="loadPage('form')">Advanced Form</button>
                <button onclick="loadPage('table')">User Table</button>
            </div>
            <div id="root"></div>
        </div>
        
        <script>
            const amis = amisRequire('amis/embed');
            let amisInstance = null;

            async function loadPage(endpoint) {
                try {
                    const response = await fetch(`/${endpoint}`);
                    const schema = await response.json();
                    
                    if (amisInstance) {
                        amisInstance.updateProps({ schema });
                    } else {
                        amisInstance = amis.embed('#root', schema);
                    }
                } catch (error) {
                    console.error('Error loading page:', error);
                }
            }

            // Load default page on startup
            loadPage('page');
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# Mock API endpoints for demonstration
@app.post("/api/submit")
def submit_form(data: Dict[str, Any]):
    """Mock form submission endpoint."""
    return {"status": 0, "msg": "Success", "data": data}


@app.get("/api/users")
def get_users():
    """Mock users API for table example."""
    return {
        "status": 0,
        "msg": "Success",
        "data": {
            "items": [
                {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "role": "admin",
                    "created_at": "2024-01-15T10:30:00Z",
                },
                {
                    "id": 2,
                    "username": "john_doe",
                    "email": "john@example.com",
                    "role": "user",
                    "created_at": "2024-02-20T14:15:00Z",
                },
                {
                    "id": 3,
                    "username": "guest_user",
                    "email": "guest@example.com",
                    "role": "guest",
                    "created_at": "2024-03-10T09:00:00Z",
                },
            ],
            "total": 3,
        },
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("Starting FastAPI-AMIS-Admin Example Server")
    print("=" * 60)
    print("\nEndpoints:")
    print("  - API Root: http://localhost:8000/")
    print("  - User Form: http://localhost:8000/page")
    print("  - Advanced Form: http://localhost:8000/form")
    print("  - User Table: http://localhost:8000/table")
    print("  - AMIS Viewer: http://localhost:8000/viewer  👈 View rendered UI here!")
    print("\n" + "=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
