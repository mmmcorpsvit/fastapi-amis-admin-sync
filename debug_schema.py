#!/usr/bin/env python3
"""Debug script to examine the TplSchema and badge field structure."""

import json
import sys
from pathlib import Path

def main():
    schema_path = Path("schema/schema_simplified.json")

    print("Loading schema...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    # Find TplSchema definition
    tpl_schema = schema['definitions'].get('TplSchema', {})
    print(f"TplSchema found: {bool(tpl_schema)}")

    if tpl_schema:
        print(f"TplSchema keys: {list(tpl_schema.keys())}")

        if 'allOf' in tpl_schema:
            print(f"Number of allOf items: {len(tpl_schema['allOf'])}")

            # Look at the second item (index 1) which contains properties
            if len(tpl_schema['allOf']) > 1:
                properties_item = tpl_schema['allOf'][1]
                print(f"Second allOf item keys: {list(properties_item.keys())}")

                if 'properties' in properties_item:
                    badge_prop = properties_item['properties'].get('badge')
                    if badge_prop:
                        print(f"\nBadge property structure:")
                        print(json.dumps(badge_prop, indent=2))

                        # Check for any nested text properties
                        if isinstance(badge_prop, dict) and 'properties' in badge_prop:
                            text_prop = badge_prop['properties'].get('text')
                            if text_prop:
                                print(f"\nText property structure:")
                                print(json.dumps(text_prop, indent=2))
                    else:
                        print("No badge property found in TplSchema properties")
                else:
                    print("No properties found in second allOf item")
        else:
            print("No allOf found in TplSchema")
    else:
        print("TplSchema not found!")

        # List available definitions
        definitions = schema.get('definitions', {})
        print(f"Available definitions: {len(definitions)}")
        tpl_related = [k for k in definitions.keys() if 'tpl' in k.lower()]
        print(f"TPL-related definitions: {tpl_related}")

if __name__ == "__main__":
    main()
