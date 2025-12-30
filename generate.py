import json
import jsonref
import yaml
from pathlib import Path
import subprocess

SCHEMA_FILE = Path("schema.json")
OUTPUT_DIR = Path("schemas")
OUTPUT_DIR.mkdir(exist_ok=True)
MODELS_FILE = Path("models.py")

# --- Завантаження та розгортання схеми ---
with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
    base_schema = json.load(f)

# Використовуємо jsonref для автоматичного вирішення $ref
schema = jsonref.replace_refs(base_schema, base_uri=f"file://{SCHEMA_FILE.resolve()}")

# --- Збереження повної bundled JSON ---
bundled_json_file = OUTPUT_DIR / "schema-bundled.json"
with open(bundled_json_file, "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2)
print(f"✅ Bundled JSON saved: {bundled_json_file}")

# --- Конвертація в YAML ---
bundled_yaml_file = OUTPUT_DIR / "schema-bundled.yaml"
with open(bundled_yaml_file, "w", encoding="utf-8") as f:
    yaml.safe_dump(schema, f, sort_keys=False)
print(f"✅ Bundled YAML saved: {bundled_yaml_file}")

# --- Розбивка $defs / $components ---
defs = schema.get("$defs") or schema.get("definitions")
if defs:
    defs_dir = OUTPUT_DIR / "defs"
    defs_dir.mkdir(exist_ok=True)
    for name, content in defs.items():
        file_json = defs_dir / f"{name}.json"
        file_yaml = defs_dir / f"{name}.yaml"
        with open(file_json, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)
        with open(file_yaml, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f, sort_keys=False)
    print(f"✅ Split $defs into {len(defs)} files")

# --- Виклик datamodel-code-generator ---
cmd = [
    "datamodel-codegen",
    "--input", str(bundled_json_file),
    "--output", str(MODELS_FILE),
    "--reuse-model"
]

print("🔹 Running datamodel-code-generator...")
subprocess.run(cmd, check=True)
print(f"✅ Models generated at {MODELS_FILE}")
