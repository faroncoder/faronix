#!/usr/bin/env python3
import subprocess
import shutil
import os
import re
import sys
import json
import time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Add builder path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Configuration
from yofaron_config import (
    ROOT,
    PROJECT_ROOT,
    CONFIG_DIR,
    JSON_DIR,
    BUILDER_DIR,
    DEFAULT_SOT,
    REGISTRY,
    OUTPUT_DIR,
    VIEW_PATH,
    URLS_PATH,
    TEMPLATE_PATH,
    FORM_PATH,
    MODEL_PATH,
    BASE_DIR,
    TPL_PY_DIR,
    TPL_HTML_DIR,
    UTILS_PATH,
    ERROR_PY_COPY_FILE,
    ERRORS_PY_SRC_FILE,
    HANDLER_UTILS_SRC_DIR,
    MODULE_DIRS,
    SRC_HANDLER_BASE,
    HANDLER_BASE,
    DEFAULT_CONFIG,
    MODEL_TYPE_MAP,
    URL_CONFIG_DIR,
    LOAD_CONFIG_URLS,
)

TEMPLATES_DIR = TEMPLATE_PATH  # clarify usage if needed elsewhere
DEFAULT_CONFIG = DEFAULT_CONFIG
MODEL_TYPE_MAP = MODEL_TYPE_MAP
MODULE_DIRS = MODULE_DIRS


env = Environment(
    loader=FileSystemLoader(
        [str(TPL_PY_DIR), str(TPL_HTML_DIR), str(ROOT), str(PROJECT_ROOT), "."]
    ),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.globals["BUILDER_DIR"] = BUILDER_DIR
env.globals["DEFAULT_CONFIG"] = DEFAULT_CONFIG
env.globals["MODEL_TYPE_MAP"] = MODEL_TYPE_MAP
env.globals["DEFAULT_CONFIG"] = DEFAULT_CONFIG
env.globals["MODULE_DIRS"] = MODULE_DIRS
# ─────────────────────────────────────────────────────────────
# 🛠️ Utility
# ─────────────────────────────────────────────────────────────


def run(cmd):
    """Run a subprocess command."""
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, check=True)
        else:
            result = subprocess.run(cmd, check=True)
        print(f"✅ Ran: {cmd}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        sys.exit(e.returncode)


# ─────────────────────────────────────────────────────────────
# 🔧 Core Setup Functions
# ─────────────────────────────────────────────────────────────


def create_requirements_txt():
    reqs = """django
djangorestframework
django-htmx
django-crispy-forms
crispy-bootstrap5
"""
    Path("requirements.txt").write_text(reqs)
    print("📦 Created requirements.txt")
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("📥 Installed packages from requirements.txt")

    run(["django-admin", "startproject", "config", "."])
    run(["django-admin", "startapp", "core"])

    BASECOPY = Path(".", "builder", "_filecopy", "handler_base")
    PATHBASE = Path(".", "templates")
    if BASECOPY.exists():
        shutil.copytree(BASECOPY, PATHBASE, dirs_exist_ok=True)
        print(f"📥 Copied handler_base → {PATHBASE}")
    CORECOPY = Path(".", "builder", "_filecopy", "handler_core")
    PATHCORE = Path(".", "core")
    if CORECOPY.exists():
        shutil.copytree(CORECOPY, PATHCORE, dirs_exist_ok=True)
        print(f"📥 Copied handler_core → {PATHCORE}")
    settings_path = CONFIG_DIR / "settings.py"
    if not settings_path.exists():
        print("⚠️ No settings.py found.")
        return

    else:

        with settings_path.open("r") as f:

            lines = settings_path.read_text().splitlines()
            new_lines, in_middleware = [], False

            for line in lines:
                if "WSGI_APPLICATION" in line:
                    line = line.replace("WSGI_APPLICATION", "ASGI_APPLICATION").replace(
                        "wsgi", "asgi"
                    )
                    continue
                if line.strip().startswith('"DIRS": [') or line.strip().startswith(
                    "'DIRS': ["
                ):
                    new_lines.append(
                        "        'DIRS': [BASE_DIR / 'templates', BASE_DIR / 'builder/snippets/static'],"
                    )
                    continue

                # Patch STATICFILES_DIRS for two locations
                if line.strip().startswith("STATICFILES_DIRS ="):
                    new_lines.append(
                        "STATICFILES_DIRS = [BASE_DIR / 'static', BASE_DIR / 'builder/snippets/static']"
                    )
                    continue

                if "context_processors" in line and "[" in line:
                    new_lines.extend(
                        [
                            line,
                            "                'core.utils.context_processors.global_vars',",
                            "                'core.utils.context_processors.debug_to_browser',",
                        ]
                    )
                    continue

                # INSTALLED_APPS block
                stripped = line.strip()
                if stripped.startswith("INSTALLED_APPS") and (
                    "[" in stripped or "(" in stripped
                ):
                    inside_installed_apps = True
                    core_already_present = False
                    new_lines.append(line)
                    continue

                if "inside_installed_apps" in locals() and inside_installed_apps:
                    if "'core'" in stripped or '"core"' in stripped:
                        core_already_present = True

                    # Detect closing bracket of INSTALLED_APPS
                    if (
                        stripped.startswith("]")
                        or stripped.startswith(")")
                        or stripped.endswith("],")
                        or stripped.endswith("),")
                    ):
                        if not core_already_present:
                            new_lines.append("    'core',")
                        inside_installed_apps = False

                    new_lines.append(line)
                    continue

                # MIDDLEWARE block
                if line.strip().startswith("MIDDLEWARE") and (
                    "[" in line or "(" in line
                ):
                    in_middleware = True
                    new_lines.append(line)
                    continue

                if in_middleware:
                    # Track if HtmxMiddleware already exists
                    if "django_htmx.middleware.HtmxMiddleware" in line:
                        pass

                    # Inject HtmxMiddleware AFTER AuthenticationMiddleware
                    if (
                        "AuthenticationMiddleware" in line
                        and "django_htmx.middleware.HtmxMiddleware" not in line
                    ):
                        new_lines.append(line)
                        if not any(
                            "django_htmx.middleware.HtmxMiddleware" in l for l in lines
                        ):
                            new_lines.append(
                                "    'django_htmx.middleware.HtmxMiddleware',"
                            )
                        continue

                    # Close block
                    if line.strip().startswith(("]", ")")):
                        in_middleware = False

                new_lines.append(line)

        # Static + Media block
        new_lines.append(
            """
if DEBUG:
    STATIC_ROOT = BASE_DIR / "staticfiles"
    MEDIA_ROOT = BASE_DIR / "media"
    STATICFILES_DIRS = [BASE_DIR / "static"]
else:
    STATIC_ROOT = '/static'
    MEDIA_ROOT = '/media'

MEDIA_URL = '/media/'
        """
        )

        settings_path = CONFIG_DIR / "settings.py"
        settings_path.write_text("\n".join(new_lines) + "\n")
        print("⚙️ Patched settings.py")

    homepanel_json = JSON_DIR / "homepanel.json"
    homepanel_spec = {
        "view_name": "HomePanel",
        "sidebar_heading": "Home",
        "tabs": [
            {
                "slug": "main",
                "label": "Home",
                "hx_get": "/core/home/",
                "hx_target": ".main-content",
                "hx_trigger": "load",
                "hx_swap": "innerHTML",
                "hx_push_url": "false",
            }
        ],
        "model": None,
    }
    template_file = Path(".", "templates", "partials", "homepanel_partial.html")
    template_file.parent.mkdir(parents=True, exist_ok=True)

    content = """
{% block content %}
<div class="container py-4">
  <h1 class="mb-4">Welcome to HomePanel</h1>
  <p>This is your default HomePanel page, ready to be customized.</p>
</div>
{% endblock %}
"""
    template_file.write_text(content, encoding="utf-8")
    print(f"📄 Created HomePanel page → {template_file}")

    JSON_DIR.mkdir(parents=True, exist_ok=True)
    homepanel_json.write_text(json.dumps(homepanel_spec, indent=2), encoding="utf-8")
    print(f"📝 Created HomePanel spec: {homepanel_json}")
    return homepanel_json


def main():
    os.chdir(str(PROJECT_ROOT))
    with open(".conda", "w") as f:
        f.write(f"{PROJECT_ROOT.name}\n")

    create_requirements_txt()

    print("🎉 Django scaffold complete.")


if __name__ == "__main__":
    main()
