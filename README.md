# FastAPI-AMIS-Admin

> High-performance FastAPI admin framework with automated AMIS schema integration

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-purple.svg)](https://docs.pydantic.dev/)
[![AMIS](https://img.shields.io/badge/AMIS-latest-orange.svg)](https://github.com/baidu/amis)

## Overview

FastAPI-AMIS-Admin provides **type-safe Pydantic models** for all [Baidu AMIS](https://github.com/baidu/amis) components (~120 widgets), automatically generated from the official AMIS JSON Schema. This enables:

- ✅ **Full IDE Autocomplete** for all AMIS fields and properties
- ✅ **Runtime Validation** with Pydantic v2
- ✅ **Automated Updates** via GitHub Actions
- ✅ **Type Safety** with Python 3.12+ type hints

## Features

- 🔄 **Automated Schema Updates**: Weekly GitHub Action downloads latest AMIS schema and regenerates models
- 🎯 **Type-Safe Models**: **452 auto-generated Pydantic models** covering all AMIS components
- 🛠️ **Developer-Friendly**: Full IDE support with autocomplete and type checking
- 📦 **Idempotent Workflow**: Download → Simplify → Generate → Validate pipeline
- 🚀 **FastAPI Integration**: Ready-to-use examples with forms, tables, and CRUD
- ✨ **Schema Preprocessing**: Intelligent simplification handles circular references and deep nesting

> **✅ Success!** We solved the RecursionError by preprocessing the AMIS schema. Now enjoy **452 fully type-safe Pydantic models** with complete IDE autocomplete!

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/yourusername/fastapi-amis-admin-sync.git
cd fastapi-amis-admin-sync

# Install dependencies with uv
uv sync

# Generate AMIS models (downloads schema, simplifies, generates)
uv run update-amis-models
# Or: uv run python update_models.py
```

### Basic Usage

```python
from fastapi import FastAPI
from fastapi_amis_admin.amis.generated_models import Page, Form, InputText, InputEmail

app = FastAPI()

@app.get("/page")
def get_page():
    # Option 1: Using manual Pydantic models (type-safe)
    page = Page(
        type="page",
        title="User Form",
        body=[
            Form(
                type="form",
                body=[
                    InputText(type="input-text", name="username", label="Username"),
                    InputEmail(type="input-email", name="email", label="Email"),
                ]
            )
        ]
    )
    return page.model_dump(by_alias=True, exclude_none=True)

    # Option 2: Using plain dicts (works for all components)
    # return {
    #     "type": "page",
    #     "title": "User Form",
    #     "body": [
    #         {
    #             "type": "form",
    #             "body": [
    #                 {"name": "username", "type": "input-text", "label": "Username"},
    #                 {"name": "email", "type": "input-email", "label": "Email"}
    #             ]
    #         }
    #     ]
    # }
```

### Run Example

```bash
# Start example server with uv
uv run python examples/basic_example.py

# Open in browser
# http://localhost:8000/viewer  - Interactive AMIS viewer
# http://localhost:8000/page     - JSON schema endpoint
```

## Project Structure

```
fastapi-amis-admin-sync/
├── .github/
│   └── workflows/
│       └── update-amis-schema.yml   # Automated schema updates
├── fastapi_amis_admin/
│   ├── __init__.py
│   └── amis/
│       ├── __init__.py
│       └── generated_models.py      # Generated Pydantic models (5000+ lines)
├── scripts/
│   ├── download_schema.py           # Download latest AMIS schema
│   └── generate_models.py           # Generate Pydantic models
├── schema/
│   └── schema.json                  # AMIS JSON Schema
├── examples/
│   └── basic_example.py             # FastAPI example with AMIS
├── tests/
│   ├── test_download_schema.py
│   ├── test_generate_models.py
│   └── test_generated_models.py
├── update_models.py                 # Orchestration script
├── requirements.txt
└── README.md
```

## Workflow

### Manual Update

```bash
# Run complete workflow: download + simplify + generate + validate
uv run update-amis-models

# Or run individual steps:
uv run python scripts/download_schema.py      # Download schema
uv run python scripts/simplify_schema.py      # Preprocess schema  
uv run python scripts/generate_models.py      # Generate models
```

### Automated Updates (GitHub Actions)

The workflow runs:
- **Weekly** on Sundays at midnight UTC
- **Manually** via workflow dispatch

When changes are detected, it automatically:
1. Downloads latest AMIS schema from GitHub releases
2. Regenerates Pydantic models
3. Creates a Pull Request for review

## Scripts

### Download Schema

```bash
python scripts/download_schema.py
```

Downloads the latest `schema.json` from [baidu/amis releases](https://github.com/baidu/amis/releases/latest) to `schema/schema.json`.

**Features:**
- GitHub API integration with retry logic
- JSON validation
- Error handling for network failures

### Generate Models

```bash
python scripts/generate_models.py
```

Generates Pydantic v2 models from `schema.json` using [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator).

**Configuration:**
- Base class: `pydantic.BaseModel`
- Field naming: `snake_case` (converts from camelCase)
- Timestamp: Disabled
- Validation: Full JSON Schema constraints

## Development

### Requirements

- Python 3.12+
- Dependencies in `requirements.txt`

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=fastapi_amis_admin --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Type checking
mypy fastapi_amis_admin/

# Lint
ruff check .
```

## Examples

### Form Example

```python
from fastapi_amis_admin.amis.generated_models import Schema

schema = Schema(
    type="page",
    title="Registration",
    body=[
        {
            "type": "form",
            "api": "/submit",
            "body": [
                {"type": "input-text", "name": "username", "label": "Username", "required": True},
                {"type": "input-email", "name": "email", "label": "Email", "required": True},
                {"type": "input-password", "name": "password", "label": "Password", "required": True},
            ]
        }
    ]
)
```

### Table/CRUD Example

See `examples/basic_example.py` for a complete working example with:
- User registration form
- Advanced form with various input types  
- CRUD table with user management
- Interactive AMIS viewer

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Baidu AMIS](https://github.com/baidu/amis) - Low-code framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) - Model generation tool

## Related Projects

- [fastapi-amis-admin](https://github.com/amisadmin/fastapi-amis-admin) - Original FastAPI-AMIS-Admin framework
- [AMIS Editor](https://aisuda.github.io/amis-editor-demo/) - Visual AMIS schema editor

## Support

- 📖 [Documentation](https://github.com/yourusername/fastapi-amis-admin-sync/wiki)
- 🐛 [Issue Tracker](https://github.com/yourusername/fastapi-amis-admin-sync/issues)
- 💬 [Discussions](https://github.com/yourusername/fastapi-amis-admin-sync/discussions)

---

**Note**: This project focuses on providing automated, type-safe AMIS schema integration. For a full-featured admin framework with CRUD, authentication, and more, see the [original fastapi-amis-admin](https://github.com/amisadmin/fastapi-amis-admin) project.
