import subprocess
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))


from yofaron_config import (
    JSON_DIR,
    OUTPUT_DIR,
    TPL_PY_DIR,
    VIEW_PATH,
    TPL_HTML_DIR,
    URLS_PATH,
    FORM_PATH,
)

ROOT = Path(__file__).resolve().parent 
TEMPLATE_PATH = ROOT / "templates"
TEMPLATE_PARTIALS_PATH = TEMPLATE_PATH / "partials"

TPL_HTML_DIR = ROOT / "builder" / "tpl" / "tpl_html"
TPL_PY_DIR = ROOT / "builder" / "tpl" / "tpl_py"

APP="core"
VIEW_PATH = ROOT / APP / "views"
URLS_PATH = ROOT / APP / "urls"
FORM_PATH = ROOT / APP / "forms"
MODEL_PATH = ROOT / APP / "models"



# 1. Create a minimal HomePanel spec using DEFAULT_CONFIG as base

spec = {
    "app_label": "core",
    "view_name": "HomePanel",
    "sidebar_heading": "Home",
    "model": None,
    "table": None,
    "constraints": {"unique_together": [], "indexes": []},
    "fields": [],
    "tabs": [
        {
            "slug": "main",
            "label": "Home",
            "form_template": "main_form.html",
            "hx_get": "/core/home/",
            "hx_target": ".main-content",
            "hx_trigger": "load",
            "hx_swap": "innerHTML",
            "hx_push_url": "false",
        }
    ],
}
spec_path = JSON_DIR / "homepanel_test.json"
spec_path.parent.mkdir(parents=True, exist_ok=True)
spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")

# 2. Run the generator
subprocess.run(
    [".venv/bin/python", "builder/yofaron_generator.py", str(spec_path)], check=True
)

# 3. Check output files using config paths
expected_files = [

    TEMPLATE_PARTIALS_PATH / "homepanel_partial.html",
    TEMPLATE_PARTIALS_PATH / "homepanel_content.html",  
    TEMPLATE_PARTIALS_PATH / "homepanel_nav.html",
    TEMPLATE_PARTIALS_PATH / "homepanel_sidebar.html",
    FORM_PATH / "main_form.py",
    VIEW_PATH / "homepanel.py",
    URLS_PATH / "homepanel_urls.py",
]
for f in expected_files:
    if not f.exists():
        print(f"❌ Missing: {f}")
    else:
        print(f"✅ Found: {f}")

print("Test complete.")
