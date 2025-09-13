# builder/generate_component_index.py
import subprocess
from pathlib import Path
import os, json, glob, re, ast, sys
import shutil
import time


from yofaron_config import (
    ROOT,
    PROJECT_ROOT,
    CONFIG_DIR,
    JSON_DIR,
    TPL_PY_DIR,
    TPL_HTML_DIR,
    DEFAULT_SOT,
    REGISTRY,
)

INDEX_PATH = ROOT / "component_index.json"


component_index: dict[str, list[str]] = {}

# Index HTML templates
for tpl_file in TPL_HTML_DIR.rglob("*.tpl.html"):
    try:
        category = tpl_file.relative_to(TPL_HTML_DIR).parts[0]
    except ValueError:
        continue
    component = tpl_file.stem
    component_index.setdefault(f"html/{category}", []).append(component)

# Index Python templates
for tpl_file in TPL_PY_DIR.rglob("*.tpl.py"):
    try:
        category = tpl_file.relative_to(TPL_PY_DIR).parts[0]
    except ValueError:
        continue
    component = tpl_file.stem
    component_index.setdefault(f"py/{category}", []).append(component)

# deterministic ordering
for components in component_index.values():
    components.sort(key=str.lower)

payload = {
    "generated_at": int(time.time()),
    "root": str(TPL_HTML_DIR),
    "categories": sorted(component_index.keys()),
    "components": component_index,
}

INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
INDEX_PATH.write_text(json.dumps(payload, indent=2))
print(f"✅ component_index.json generated at {INDEX_PATH}")
