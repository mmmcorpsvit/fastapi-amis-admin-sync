#!/usr/bin/env python3
"""
Download the latest AMIS schema.json from GitHub releases.

This script fetches the latest release from baidu/amis repository
and downloads the schema.json file to the schema/ directory.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Constants
GITHUB_API_URL = "https://api.github.com/repos/baidu/amis/releases/latest"
SCHEMA_ASSET_NAME = "schema.json"
DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / "schema" / "schema.json"
TIMEOUT = 30  # seconds
MAX_RETRIES = 3


def get_latest_release_info() -> dict:
    """
    Fetch the latest release information from GitHub API.

    Returns:
        dict: Release information including tag_name, assets, etc.

    Raises:
        requests.RequestException: If the API request fails.
    """
    logger.info(f"Fetching latest release info from {GITHUB_API_URL}")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "fastapi-amis-admin-schema-downloader",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(GITHUB_API_URL, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Latest release: {data.get('tag_name', 'unknown')}")
            return data
        except requests.RequestException as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"Attempt {attempt} failed: {e}. Retrying...")
            else:
                logger.error(f"Failed to fetch release info after {MAX_RETRIES} attempts")
                raise


def find_schema_asset(release_info: dict) -> Optional[str]:
    """
    Find the schema.json download URL from release assets.

    Args:
        release_info: Release information from GitHub API.

    Returns:
        str: Download URL for schema.json, or None if not found.
    """
    assets = release_info.get("assets", [])
    logger.info(f"Searching for '{SCHEMA_ASSET_NAME}' in {len(assets)} assets")

    for asset in assets:
        if asset.get("name") == SCHEMA_ASSET_NAME:
            url = asset.get("browser_download_url")
            logger.info(f"Found schema.json: {url}")
            return url

    logger.warning(f"'{SCHEMA_ASSET_NAME}' not found in release assets")
    return None


def download_file(url: str, output_path: Path) -> None:
    """
    Download a file from URL and save to output_path.

    Args:
        url: URL to download from.
        output_path: Path to save the downloaded file.

    Raises:
        requests.RequestException: If download fails.
    """
    logger.info(f"Downloading from {url}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=TIMEOUT, stream=True)
            response.raise_for_status()

            # Create parent directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = output_path.stat().st_size
            logger.info(f"Downloaded {file_size:,} bytes to {output_path}")
            return
        except requests.RequestException as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"Download attempt {attempt} failed: {e}. Retrying...")
            else:
                logger.error(f"Download failed after {MAX_RETRIES} attempts")
                raise


def validate_schema(schema_path: Path) -> bool:
    """
    Validate that the downloaded file is valid JSON and contains expected structure.

    Args:
        schema_path: Path to the schema file.

    Returns:
        bool: True if valid, False otherwise.
    """
    logger.info(f"Validating schema at {schema_path}")

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # Basic validation: check if it's a dict and has some expected properties
        if not isinstance(schema, dict):
            logger.error("Schema is not a JSON object")
            return False

        # Check for common JSON Schema properties
        has_schema_props = any(
            key in schema
            for key in ["$schema", "definitions", "properties", "type", "$defs"]
        )

        if not has_schema_props:
            logger.warning(
                "Schema doesn't contain typical JSON Schema properties, but may still be valid"
            )

        logger.info(f"Schema validation successful. Root keys: {list(schema.keys())}")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


def main(output_path: Optional[Path] = None) -> int:
    """
    Main function to download and validate schema.

    Args:
        output_path: Optional custom output path. Defaults to schema/schema.json.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    if output_path is None:
        output_path = DEFAULT_OUTPUT_PATH

    logger.info("=" * 60)
    logger.info("AMIS Schema Downloader")
    logger.info("=" * 60)

    try:
        # Get latest release info
        release_info = get_latest_release_info()

        # Find schema.json asset
        schema_url = find_schema_asset(release_info)
        if not schema_url:
            logger.error("Could not find schema.json in latest release")
            return 1

        # Download schema
        download_file(schema_url, output_path)

        # Validate downloaded schema
        if not validate_schema(output_path):
            logger.error("Schema validation failed")
            return 1

        logger.info("=" * 60)
        logger.info("✅ Schema downloaded and validated successfully!")
        logger.info(f"Location: {output_path.absolute()}")
        logger.info("=" * 60)
        return 0

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
