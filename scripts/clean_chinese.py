#!/usr/bin/env python3
"""
Post-process generated models to remove any remaining Chinese characters.

This script reads the auto_generated_models.py file and removes/replaces
any remaining Chinese text with generic English placeholders.
"""
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS_PATH = Path(__file__).parent.parent / "fastapi_amis_admin" / "amis" / "auto_generated_models.py"


def contains_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def remove_chinese_from_docstrings(content: str) -> str:
    """
    Remove Chinese from Python docstrings and descriptions.
    
    Args:
        content: File content
    
    Returns:
        Content with Chinese removed/replaced
    """
    lines = content.split('\n')
    result = []
    in_docstring = False
    docstring_delimiter = None
    
    for line in lines:
        # Detect docstring start/end
        if '"""' in line or "'''" in line:
            delimiter = '"""' if '"""' in line else "'''"
            if not in_docstring:
                in_docstring = True
                docstring_delimiter = delimiter
            elif docstring_delimiter == delimiter:
                in_docstring = False
                docstring_delimiter = None
        
        # Remove Chinese from docstrings
        if in_docstring and contains_chinese(line):
            # Remove lines with Chinese in docstrings
            logger.debug(f"Removing Chinese docstring line: {line[:80]}...")
            continue
        
        # Replace Chinese in description fields
        if 'description=' in line and contains_chinese(line):
            # Extract the description value
            match = re.search(r"description=['\"]([^'\"]+)['\"]", line)
            if match:
                chinese_desc = match.group(1)
                # Replace with generic description
                english_desc = "Component property"
                line = line.replace(chinese_desc, english_desc)
                logger.debug(f"Replaced Chinese description: {chinese_desc[:50]}... -> {english_desc}")
        
        result.append(line)
    
    return '\n'.join(result)


def remove_chinese_docstring_classes(content: str) -> str:
    """
    Remove entire docstrings that contain Chinese.
    
    Args:
        content: File content
    
    Returns:
        Content with Chinese docstrings removed
    """
    # Pattern to match class docstrings
    pattern = r'(class \w+\([^)]+\):\s*""")\s*([^"]+)(""")'
    
    def replace_docstring(match):
        class_def = match.group(1)
        docstring_content = match.group(2)
        end_quotes = match.group(3)
        
        # If docstring contains Chinese, replace it with a generic one
        if contains_chinese(docstring_content):
            logger.debug(f"Removing Chinese from class docstring: {docstring_content[:50]}...")
            # Extract class name
            class_match = re.search(r'class (\w+)', class_def)
            class_name = class_match.group(1) if class_match else "Component"
            return f'{class_def}\n    AMIS {class_name} component.\n    {end_quotes}'
        
        return match.group(0)
    
    return re.sub(pattern, replace_docstring, content, flags=re.MULTILINE | re.DOTALL)


def main():
    """Main function to clean generated models."""
    logger.info("=" * 60)
    logger.info("Post-processing: Remove Chinese from Generated Models")
    logger.info("=" * 60)
    
    # Read file
    logger.info(f"Reading {MODELS_PATH}")
    with open(MODELS_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Count Chinese before
    chinese_before = len(re.findall(r'[\u4e00-\u9fff]', content))
    logger.info(f"Chinese characters before: {chinese_before}")
    
    # Remove Chinese from class docstrings
    content = remove_chinese_docstring_classes(content)
    
    # Remove Chinese from inline docstrings and descriptions
    content = remove_chinese_from_docstrings(content)
    
    # Count Chinese after
    chinese_after = len(re.findall(r'[\u4e00-\u9fff]', content))
    
    # Write back
    logger.info(f"Writing cleaned content to {MODELS_PATH}")
    with open(MODELS_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info("=" * 60)
    logger.info(f"✅ Post-processing complete!")
    logger.info(f"Chinese characters removed: {chinese_before - chinese_after}")
    logger.info(f"Remaining Chinese characters: {chinese_after}")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
