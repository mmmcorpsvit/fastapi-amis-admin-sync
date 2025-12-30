#!/usr/bin/env python3
"""
Fix duplicate enum values in generated models.

The generator sometimes creates duplicate enum members with the same value
but different names (e.g., action and action_1 both = 'action').
This script removes the duplicates.
"""
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GENERATED_MODELS = Path(__file__).parent.parent / "fastapi_amis_admin" / "amis" / "auto_generated_models.py"


def fix_enum_duplicates(content: str) -> tuple[str, int]:
    """
    Fix duplicate enum values by removing the _1, _2, etc. variants.
    
    Returns:
        (fixed_content, count_of_fixes)
    """
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    fixes = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is an enum class definition
        enum_match = re.match(r'^class\s+(\w+)\(Enum\):', line)
        if enum_match:
            enum_name = enum_match.group(1)
            enum_start = i
            enum_lines = [line]
            i += 1
            
            # Collect all enum members
            enum_members = {}
            member_lines = []
            
            # Read until next class or end of enum
            while i < len(lines):
                current_line = lines[i]
                
                # Check if we've reached the next class or end of enum
                if re.match(r'^class\s+', current_line) or current_line.strip() == '':
                    # End of enum
                    break
                
                # Check for enum member
                member_match = re.match(r'^\s+(\w+)\s*=\s*[\'"]?([^\'"\n]+)[\'"]?', current_line)
                if member_match:
                    member_name = member_match.group(1)
                    member_value = member_match.group(2).strip('\'"')
                    
                    # Check if this value already exists
                    if member_value in enum_members.values():
                        # This is a duplicate - check if it's a _1, _2 variant
                        if re.match(r'.+_\d+$', member_name):
                            # Skip this duplicate member
                            logger.info(f"Removing duplicate enum member: {enum_name}.{member_name} = '{member_value}'")
                            fixes += 1
                            i += 1
                            continue
                        else:
                            # The original might be the _1 variant, check
                            original_name = None
                            for orig_name, orig_value in enum_members.items():
                                if orig_value == member_value and re.match(r'.+_\d+$', orig_name):
                                    original_name = orig_name
                                    break
                            
                            if original_name:
                                # Replace the _1 variant with the non-variant
                                logger.info(f"Replacing {enum_name}.{original_name} with {enum_name}.{member_name}")
                                # Remove the _1 variant from our dict
                                enum_members = {k: v for k, v in enum_members.items() if k != original_name}
                                member_lines = [ml for ml in member_lines if not ml[0].startswith(original_name)]
                    
                    enum_members[member_name] = member_value
                    member_lines.append((member_name, current_line))
                
                enum_lines.append(current_line)
                i += 1
            
            # Rebuild enum without duplicates
            fixed_lines.append(enum_lines[0])  # Class definition
            seen_values = set()
            for member_name, member_line in member_lines:
                member_value = enum_members.get(member_name)
                # Skip if it's a _1 variant and value already exists
                if re.match(r'.+_\d+$', member_name) and member_value in seen_values:
                    continue
                fixed_lines.append(member_line)
                if member_value:
                    seen_values.add(member_value)
            
            # Add blank line after enum
            if i < len(lines) and lines[i].strip() == '':
                fixed_lines.append('')
                i += 1
            
            continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines), fixes


def main() -> int:
    """Main function."""
    logger.info("=" * 60)
    logger.info("Fix Enum Duplicates")
    logger.info("=" * 60)
    
    if not GENERATED_MODELS.exists():
        logger.error(f"File not found: {GENERATED_MODELS}")
        return 1
    
    logger.info(f"Reading {GENERATED_MODELS}")
    with open(GENERATED_MODELS, "r", encoding="utf-8") as f:
        content = f.read()
    
    logger.info("Fixing duplicate enum values...")
    fixed_content, fixes = fix_enum_duplicates(content)
    
    if fixes > 0:
        logger.info(f"Fixed {fixes} duplicate enum members")
        with open(GENERATED_MODELS, "w", encoding="utf-8") as f:
            f.write(fixed_content)
        logger.info(f"✅ Fixed enum duplicates in {GENERATED_MODELS}")
    else:
        logger.info("No duplicate enum values found")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

