# Auto-generated config
from pathlib import Path

ROOT = Path('/home/faron/app_pwa')
PROJECT_ROOT = Path('/home/faron')
BUILDER_DIR = Path('/home/faron/app_pwa/builder')
CONFIG_DIR = Path('/home/faron/app_pwa/config')
JSON_DIR = Path('/home/faron/app_pwa/builder/json')
TPL_PY_DIR = Path('/home/faron/app_pwa/builder/tpl/tpl_py')
TPL_HTML_DIR = Path('/home/faron/app_pwa/builder/tpl/tpl_html')
OUTPUT_DIR = Path('/home/faron/app_pwa/core')
VIEW_PATH = Path('/home/faron/app_pwa/core/views')
FORM_PATH = Path('/home/faron/app_pwa/core/forms')
MODEL_PATH = Path('/home/faron/app_pwa/core/models')
URLS_PATH = Path('/home/faron/app_pwa/core/urls')
UTILS_PATH = Path('/home/faron/app_pwa/core/utils')
TEMPLATE_PATH = Path('/home/faron/app_pwa/templates')
TEMPLATE_PARTIALS_PATH = Path('/home/faron/app_pwa/templates/partials')
REGISTRY = Path('/home/faron/app_pwa/builder/_in_service.json')
DEFAULT_SOT = Path('/home/faron/app_pwa/builder/json/yofaron_scaffolded.json')

ROLE_RANK = {
  "guest": 0,
  "member": 20,
  "staff": 40,
  "manager": 60,
  "admin": 80,
  "superadmin": 100
}

MODEL_TYPE_MAP = {
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
  "image": "ImageField"
}

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
