#!/usr/bin/env python3
"""
Generate Pydantic models from AMIS schema.json using datamodel-code-generator.

This script reads the schema.json file and generates type-safe Pydantic v2 models
with full IDE autocomplete support for all ~120 AMIS components.
"""
import ast
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "schema_simplified.json"
DEFAULT_OUTPUT_PATH = (
    Path(__file__).parent.parent
    / "fastapi_amis_admin"
    / "amis"
    / "auto_generated_models.py"
)


def check_dependencies() -> bool:
    """
    Check if datamodel-code-generator is installed.

    Returns:
        bool: True if installed, False otherwise.
    """
    try:
        result = subprocess.run(
            ["datamodel-codegen", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            logger.info(f"datamodel-code-generator version: {result.stdout.strip()}")
            return True
        return False
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("datamodel-code-generator not found. Install with:")
        logger.error("  pip install 'datamodel-code-generator[http]'")
        return False


def generate_models(schema_path: Path, output_path: Path) -> bool:
    """
    Generate Pydantic models using datamodel-code-generator.

    Args:
        schema_path: Path to input schema.json.
        output_path: Path to output Python file.

    Returns:
        bool: True if generation successful, False otherwise.
    """
    logger.info(f"Generating models from {schema_path}")
    logger.info(f"Output will be written to {output_path}")

    # Ensure input exists
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return False

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build datamodel-codegen command
    # Using minimal options to avoid recursion errors with complex schema
    cmd = [
        "datamodel-codegen",
        "--input",
        str(schema_path),
        "--output",
        str(output_path),
        "--input-file-type",
        "jsonschema",
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--snake-case-field",
        "--disable-timestamp",
        "--encoding",
        "utf-8",
        "--collapse-root-models",  # Helps with complex schemas
        "--use-default",  # Use default values from schema
        "--use-schema-description",  # Keep descriptions
    ]

    logger.info(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            logger.error("Model generation failed!")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False

        if result.stdout:
            logger.info(f"Generator output: {result.stdout}")
        if result.stderr:
            logger.warning(f"Generator warnings: {result.stderr}")

        logger.info("✅ Model generation completed")
        return True

    except subprocess.TimeoutExpired:
        logger.error("Model generation timed out after 60 seconds")
        return False
    except Exception as e:
        logger.error(f"Error running datamodel-codegen: {e}")
        return False


def add_header_comment(output_path: Path, schema_path: Path) -> None:
    """
    Add a header comment to the generated file with metadata.

    Args:
        output_path: Path to the generated Python file.
        schema_path: Path to the source schema file.
    """
    logger.info("Adding header comment to generated file")

    header = f'''"""
Generated Pydantic models for AMIS components.

AUTO-GENERATED FILE - DO NOT EDIT MANUALLY!

This file was automatically generated from the AMIS JSON Schema.
To regenerate, run: python scripts/generate_models.py

Generation info:
- Generated at: {datetime.now().isoformat()}
- Source schema: {schema_path.name}
- Generator: datamodel-code-generator

For more information about AMIS, visit: https://github.com/baidu/amis
"""

'''

    # Read existing content
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Write header + content
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(content)

    logger.info("Header comment added")


def validate_generated_code(output_path: Path) -> bool:
    """
    Validate that the generated Python file has valid syntax.

    Args:
        output_path: Path to the generated Python file.

    Returns:
        bool: True if valid, False otherwise.
    """
    logger.info(f"Validating generated code syntax at {output_path}")

    try:
        with open(output_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Parse the code to check syntax
        ast.parse(code)

        # Count lines and classes for info
        lines = code.count("\n") + 1
        classes = code.count("class ")

        logger.info(f"✅ Syntax validation passed")
        logger.info(f"   Lines: {lines:,}")
        logger.info(f"   Classes: {classes:,}")

        return True

    except SyntaxError as e:
        logger.error(f"Syntax error in generated code: {e}")
        return False
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


def main(
    schema_path: Optional[Path] = None, output_path: Optional[Path] = None
) -> int:
    """
    Main function to generate and validate Pydantic models.

    Args:
        schema_path: Optional custom schema path.
        output_path: Optional custom output path.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    if schema_path is None:
        schema_path = DEFAULT_SCHEMA_PATH
    if output_path is None:
        output_path = DEFAULT_OUTPUT_PATH

    logger.info("=" * 60)
    logger.info("AMIS Pydantic Model Generator")
    logger.info("=" * 60)

    try:
        # Check dependencies
        if not check_dependencies():
            return 1

        # Generate models
        if not generate_models(schema_path, output_path):
            return 1

        # Add header comment
        add_header_comment(output_path, schema_path)

        # Validate generated code
        if not validate_generated_code(output_path):
            return 1

        # Optional: Fix union types
        try:
            import fix_union_types
            logger.info("Attempting to fix union types...")
            if fix_union_types.fix_file_regex(output_path):
                logger.info("✅ Union types fixed")
                # Re-validate after fixing
                if not validate_generated_code(output_path):
                    logger.warning("⚠️  Validation failed after fixing union types")
        except ImportError:
            logger.debug("fix_union_types not available, skipping")
        except Exception as e:
            logger.warning(f"Could not fix union types: {e}")
        
        # Optional: Fix enum duplicates
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            import fix_enum_duplicates
            logger.info("Attempting to fix enum duplicates...")
            # Read file, fix, and write back
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            fixed_content, fixes = fix_enum_duplicates.fix_enum_duplicates(content)
            if fixes > 0:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
                logger.info(f"✅ Fixed {fixes} enum duplicates")
                # Re-validate after fixing
                if not validate_generated_code(output_path):
                    logger.warning("⚠️  Validation failed after fixing enum duplicates")
            else:
                logger.info("✅ No enum duplicates found")
        except ImportError:
            logger.debug("fix_enum_duplicates not available, skipping")
        except Exception as e:
            logger.warning(f"Could not fix enum duplicates: {e}")

        logger.info("=" * 60)
        logger.info("✅ Models generated and validated successfully!")
        logger.info(f"Location: {output_path.absolute()}")
        logger.info("=" * 60)
        return 0

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
