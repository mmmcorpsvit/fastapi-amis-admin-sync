import $RefParser from "@apidevtools/json-schema-ref-parser";
import fs from "fs";
import yaml from "js-yaml";
import { execSync } from "child_process";
import path from "path";

const SCHEMA_FILE = "schema.json";
const OUTPUT_JSON = "schema-bundled.json";
const OUTPUT_YAML = "schema-bundled.yaml";
const MODELS_OUTPUT = "models.py";

async function main() {
  try {
    console.log("🔹 Bundling JSON Schema...");

    const parser = new $RefParser();
    const schema = await parser.bundle(SCHEMA_FILE);

    // --- Save JSON ---
    fs.writeFileSync(OUTPUT_JSON, JSON.stringify(schema, null, 2));
    console.log(`✅ Bundled schema saved as ${OUTPUT_JSON}`);

    // --- Save YAML ---
    fs.writeFileSync(OUTPUT_YAML, yaml.dump(schema, { noRefs: true }));
    console.log(`✅ Bundled schema saved as ${OUTPUT_YAML}`);

    // --- Call datamodel-code-generator ---
    console.log("🔹 Running datamodel-code-generator...");
    const pythonCmd = process.platform === "win32" ? "python" : "python3";
    const cmd = `${pythonCmd} run_datamodel_codegen.py --input ${OUTPUT_JSON} --output ${MODELS_OUTPUT} --reuse-model --encoding utf-8 --target-pydantic-version 2 --output-model-type pydantic_v2.BaseModel`;
    execSync(cmd, { stdio: "inherit" });

    console.log(`✅ Models generated at ${MODELS_OUTPUT}`);
  } catch (err) {
    console.error("❌ Error:", err);
  }
}

main();
