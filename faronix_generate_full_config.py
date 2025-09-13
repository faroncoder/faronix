from pathlib import Path
import json
import time

# === PART 1: Generate config ===

BASE = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE / "builder" / "yofaron_config.py"

paths = {
    "ROOT": BASE,
    "PROJECT_ROOT": BASE.parent,
    "BUILDER_DIR": BASE / "builder",
    "CONFIG_DIR": BASE / "config",
    "JSON_DIR": BASE / "builder/json",
    "TPL_PY_DIR": BASE / "builder/tpl/tpl_py",
    "TPL_HTML_DIR": BASE / "builder/tpl/tpl_html",
    "OUTPUT_DIR": BASE / "core",
    "VIEW_PATH": BASE / "core/views",
    "FORM_PATH": BASE / "core/forms",
    "MODEL_PATH": BASE / "core/models",
    "URLS_PATH": BASE / "core/urls",
    "UTILS_PATH": BASE / "core/utils",
    "TEMPLATE_PATH": BASE / "templates",
    "TEMPLATE_PARTIALS_PATH": BASE / "templates/partials",
    "REGISTRY": BASE / "builder/_in_service.json",
    "DEFAULT_SOT": BASE / "builder/json/yofaron_scaffolded.json",
}

role_rank = {
    "guest": 0,
    "member": 20,
    "staff": 40,
    "manager": 60,
    "admin": 80,
    "superadmin": 100,
}

model_type_map = {
    "text": "CharField",
    "slug": "SlugField",
    "bool": "BooleanField",
    "boolean": "BooleanField",
    "int": "IntegerField",
    "number": "IntegerField",
    "float": "FloatField",
    "date": "DateField",
    "datetime": "DateTimeField",
    "json": "JSONField",
    "file": "FileField",
    "image": "ImageField",
}

def write_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("# Auto-generated config\n")
        f.write("from pathlib import Path\n\n")
        for k, v in paths.items():
            f.write(f"{k} = Path({repr(str(v))})\n")
        f.write("\nROLE_RANK = " + json.dumps(role_rank, indent=2))
        f.write("\n\nMODEL_TYPE_MAP = " + json.dumps(model_type_map, indent=2))
        f.write("""

DEFAULT_CONFIG = {
    "app_label": "core",
    "view_name": "Default",
    "model": None,
    "table": None,
    "constraints": {"unique_together": [], "indexes": []},
    "fields": [],
    "tabs": [
        {
            "slug": "main",
            "label": "Main",
            "form_template": "main_form.html",
            "hx_get": "/core/main/",
            "hx_target": ".main-content",
            "hx_trigger": "load",
            "hx_swap": "innerHTML",
            "hx_push_url": "false"
        }
    ]
}
""")
    print(f"✅ Config constants written to {CONFIG_FILE}")

# === PART 2: Generate component index ===

INDEX_PATH = BASE / "builder" / "component_index.json"

def build_component_index():
    html_dir = paths["TPL_HTML_DIR"]
    py_dir = paths["TPL_PY_DIR"]
    index = {}

    # HTML templates
    for tpl_file in html_dir.rglob("*.tpl.html"):
        try:
            category = tpl_file.relative_to(html_dir).parts[0]
        except ValueError:
            continue
        component = tpl_file.stem
        index.setdefault(f"html/{category}", []).append(component)

    # PY templates
    for tpl_file in py_dir.rglob("*.tpl.py"):
        try:
            category = tpl_file.relative_to(py_dir).parts[0]
        except ValueError:
            continue
        component = tpl_file.stem
        index.setdefault(f"py/{category}", []).append(component)

    for val in index.values():
        val.sort(key=str.lower)

    payload = {
        "generated_at": int(time.time()),
        "root": str(html_dir),
        "categories": sorted(index.keys()),
        "components": index,
    }

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(payload, indent=2))
    print(f"✅ component_index.json written to {INDEX_PATH}")

# === MAIN ===

if __name__ == "__main__":
    write_config()
    build_component_index()
