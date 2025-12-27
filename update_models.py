#!/usr/bin/env python3
"""
Complete workflow orchestration: simplify schema, then generate models.

This script runs:
1. Download latest AMIS schema from GitHub
2. Simplify schema to avoid recursion issues
3. Generate Pydantic models from simplified schema
4. Validate everything

Usage:
    python update_models.py
"""
import logging
import sys
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import download_schema
import translate_schema
import simplify_schema
import generate_models
import clean_chinese

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """
    Run the complete model update workflow.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    logger.info("=" * 70)
    logger.info("AMIS Model Update Workflow")
    logger.info("=" * 70)

    try:
        # Step 1: Download schema
        logger.info("\n📥 Step 1: Downloading latest AMIS schema...")
        logger.info("-" * 70)
        exit_code = download_schema.main()
        if exit_code != 0:
            logger.error("❌ Schema download failed!")
            return exit_code

        # Step 2: Translate Chinese to English
        logger.info("\n🌐 Step 2: Translating Chinese descriptions to English...")
        logger.info("-" * 70)
        exit_code = translate_schema.main()
        if exit_code != 0:
            logger.error("❌ Schema translation failed!")
            return exit_code

        # Step 3: Simplify schema
        logger.info("\n🔧 Step 3: Simplifying schema...")
        logger.info("-" * 70)
        exit_code = simplify_schema.main()
        if exit_code != 0:
            logger.error("❌ Schema simplification failed!")
            return exit_code

        # Step 4: Generate models
        logger.info("\n🔨 Step 4: Generating Pydantic models...")
        logger.info("-" * 70)
        exit_code = generate_models.main()
        if exit_code != 0:
            logger.error("❌ Model generation failed!")
            return exit_code

        # Step 5: Clean remaining Chinese
        logger.info("\n🧹 Step 5: Removing any remaining Chinese text...")
        logger.info("-" * 70)
        exit_code = clean_chinese.main()
        if exit_code != 0:
            logger.error("❌ Chinese cleanup failed!")
            return exit_code

        # Success!
        logger.info("\n" + "=" * 70)
        logger.info("✅ AMIS models updated successfully!")
        logger.info("=" * 70)
        logger.info("\nGenerated files:")
        logger.info("  - schema/schema.json (original, 34k lines)")
        logger.info("  - schema/schema_simplified.json (preprocessed)")
        logger.info("  - fastapi_amis_admin/amis/auto_generated_models.py (452 models!)")
        logger.info("\nNext steps:")
        logger.info("  1. Review generated models in auto_generated_models.py")
        logger.info("  2. Run tests to ensure compatibility")
        logger.info("  3. Try the example: python examples/basic_example.py")
        logger.info("=" * 70)
        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
