#!/usr/bin/env python3
"""
Debug script to examine the BadgeObject definition.
"""

import json
from pathlib import Path

def main():
    schema_path = Path("schema/schema_simplified.json")

    print("Loading schema...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    # Find BadgeObject definition
    badge_object = schema['definitions'].get('BadgeObject', {})
    print('BadgeObject found:', bool(badge_object))

    if badge_object:
        print('BadgeObject keys:', list(badge_object.keys()))
        if 'properties' in badge_object:
            properties = badge_object['properties']
            for prop_name, prop_def in properties.items():
                print(f"\n{prop_name} property:")
                print(json.dumps(prop_def, indent=2))

if __name__ == "__main__":
    main()
