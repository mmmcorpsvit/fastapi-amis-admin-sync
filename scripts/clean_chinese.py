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
        
        # Fix malformed docstrings (Chinese text without proper quotes)
        if contains_chinese(line) and not in_docstring:
            # Check if this is a malformed docstring line
            if re.match(r'^\s+[\u4e00-\u9fff]', line):
                # This is Chinese text that should be in a docstring but isn't
                logger.debug(f"Removing malformed Chinese line: {line[:80]}...")
                continue
        
        # Replace Chinese in description fields
        if 'description=' in line and contains_chinese(line):
            # Extract the description value - handle both single and double quotes
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
    Remove entire docstrings that contain Chinese and fix malformed docstrings.
    
    Args:
        content: File content
    
    Returns:
        Content with Chinese docstrings removed
    """
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a class definition
        class_match = re.match(r'^class\s+(\w+)\([^)]+\):', line)
        if class_match:
            class_name = class_match.group(1)
            result.append(line)
            i += 1
            
            # Check next lines for docstring
            if i < len(lines) and lines[i].strip() == '':
                i += 1
            
            # Check if next line starts a docstring
            if i < len(lines):
                next_line = lines[i]
                # Check for malformed docstring (Chinese text without quotes)
                if contains_chinese(next_line) and '"""' not in next_line and "'''" not in next_line:
                    # Skip this malformed line
                    logger.debug(f"Removing malformed Chinese line after {class_name}: {next_line[:80]}...")
                    i += 1
                    # Skip until we find closing quotes or next class
                    while i < len(lines):
                        if '"""' in lines[i] or "'''" in lines[i] or re.match(r'^class\s+', lines[i]):
                            break
                        if contains_chinese(lines[i]):
                            i += 1
                            continue
                        break
                    continue
                
                # Check for proper docstring
                if '"""' in next_line or "'''" in next_line:
                    # This is a docstring - check if it contains Chinese
                    docstring_lines = [next_line]
                    i += 1
                    in_docstring = True
                    delimiter = '"""' if '"""' in next_line else "'''"
                    
                    # Collect docstring lines
                    while i < len(lines) and in_docstring:
                        docstring_lines.append(lines[i])
                        if delimiter in lines[i] and lines[i].count(delimiter) >= 2:
                            in_docstring = False
                        i += 1
                    
                    # Check if docstring contains Chinese
                    docstring_content = '\n'.join(docstring_lines)
                    if contains_chinese(docstring_content):
                        # Replace with generic docstring
                        result.append(f'    """')
                        result.append(f'    AMIS {class_name} component.')
                        result.append(f'    """')
                        logger.debug(f"Replaced Chinese docstring for {class_name}")
                    else:
                        # Keep original docstring
                        result.extend(docstring_lines)
                    continue
            
            continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)


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
