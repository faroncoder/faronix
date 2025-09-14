# yofaron_generate.py
import ast, json, re, os, sys, glob
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import subprocess
from datetime import datetime

from pathlib import Path

ROOT = Path(__file__).resolve().parent  # /home/faron/yofaron/builder
PROJECT_ROOT = ROOT.parent  # /home/faron/yofaron
CONFIG_DIR = PROJECT_ROOT / "config"  # /home/faron/yofaron/config
JSON_DIR = PROJECT_ROOT / "builder" / "json"  # /home/faron/yofaron/builder/json
TPL_DIR = PROJECT_ROOT / "builder" / "tpl"  # /home/faron/yofaron/builder/tpl
DEFAULT_SOT = JSON_DIR / "yofaron_scaffolded.json"
REGISTRY = PROJECT_ROOT / "builder" / "_in_service.json"
ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


sot_file = (JSON_DIR.glob("yofaron_scaffolded_*.json*"),)  # handles .json and .jsonc
files = sorted(
    JSON_DIR.glob("yofaron_scaffolded_*.json*"),  # handles .json and .jsonc
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)


PY = sys.executable
PATTERN = re.compile(r"yofaron_scaffolded_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.json")
SCAFFOLDED_REGEX = PATTERN


ROLE_RANK = {
    "guest": 0,
    "member": 20,
    "staff": 40,
    "manager": 60,
    "admin": 80,
    "superadmin": 100,
}

# ROOT = Path(__file__).resolve().parent
# PROJECT_ROOT = ROOT.parent     # adjust if your project root differs
# JSON_DIR = ROOT / "json"       # or ROOT / "builder" / "json"
# TPL_DIR = ROOT / "tpl"


# PROJECT_ROOT  = ROOT
# TEMPLATE_DIR  = PROJECT_ROOT / "templates"                # scaffolding .tpl.*
OUTPUT_DIR = Path("core")
VIEW_PATH = OUTPUT_DIR / "views"
URLS_PATH = OUTPUT_DIR / "urls"
TEMPLATE_PATH = OUTPUT_DIR / "templates"
FORM_PATH = OUTPUT_DIR / "forms"
MODEL_PATH = OUTPUT_DIR / "models"
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH_HTML = BASE_DIR / "templates" / "base" / "sidemenu" / "partials"
# DEFAULT_SOT = JSON_DIR / "yofaron_scaffolded.json"
# REGISTRY = ROOT / "builder" / "_in_service.json"
# sot_file = JSON_DIR / f"yofaron_scaffolded_*.json"
# sot = sot_file if sot_file else DEFAULT_SOT
# CONFIG_DIR = ROOT.parent / "config"   # adjust if your project structure differs


env = Environment(
    loader=FileSystemLoader(
        [
            str(TPL_DIR),
        ]
    ),
    trim_blocks=True,
    lstrip_blocks=True,
)

print(
    "DEBUG PATHS:",
    "\n ROOT        =",
    ROOT,
    "\n PROJECT_ROOT=",
    PROJECT_ROOT,
    "\n CONFIG_DIR  =",
    CONFIG_DIR,
    "\n JSON_DIR    =",
    JSON_DIR,
    "\n TPL_DIR     =",
    TPL_DIR,
)


def _build_active_specs_for_urls(reg: dict) -> list[dict]:
    specs = []
    for e in reg.get("specs", []):
        if not e.get("active", True):
            continue
        p = Path(e["path"])
        try:
            data = read_json_any(
                p
            )  # if you use the jsonc-aware loader; else json.loads(p.read_text())
        except Exception:
            continue
        view_name = data.get("view_name") or p.stem
        view_slug = data.get("view_slug") or re.sub(r"\W+", "_", view_name.lower())
        app_label = data.get("app_label") or "core"
        specs.append(
            {
                "view_name": view_name,
                "view_slug": view_slug,
                "app_label": app_label,
            }
        )
    # keep stable order (by slug)
    specs.sort(key=lambda x: x["view_slug"])
    return specs


def render_project_urls_autogen(reg: dict):
    active_specs = _build_active_specs_for_urls(reg)
    ctx = {"active_specs": active_specs}
    out = CONFIG_DIR / "urls_autogen.py"
    render_to_file("urls_autogen.tpl.py", ctx, out)
    print(f"✅ Wrote project URL includes → {out}")


def _strip_jsonc(s: str) -> str:
    # remove // line comments
    s = re.sub(r"//.*?$", "", s, flags=re.MULTILINE)
    # remove /* ... */ block comments
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    return s


def read_json_any(path: Path) -> dict:
    """
    Read .json or .jsonc, strip comments if needed, and parse.
    """
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonc":
        raw = _strip_jsonc(raw)
    return json.loads(raw)


# ---------- helpers / filters
def camel(s: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", str(s))
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def pyrepr(v):
    return repr(v)


env.filters["camel"] = camel
env.filters["pyrepr"] = pyrepr

FORM_TYPE_MAP = {
    "text": "CharField",
    "email": "EmailField",
    "password": "CharField",
    "number": "IntegerField",
    "bool": "BooleanField",
    "boolean": "BooleanField",
    "date": "DateField",
    "datetime": "DateTimeField",
    "file": "FileField",
    "image": "ImageField",
    "choice": "ChoiceField",
    "textarea": "CharField",
}

env.globals["FORM_TYPE_MAP"] = FORM_TYPE_MAP


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
    "image": "ImageField",
}

# ---------- defaults
DEFAULT_CONFIG = {
    "app_label": "core",
    "view_name": "Default",
    "model": None,
    "table": None,
    "constraints": {"unique_together": [], "indexes": []},
    "fields": [],
    "tabs": [],
}


# --- helpers ---
def _utcnow_iso() -> str:
    from datetime import datetime

    return datetime.utcnow().isoformat() + "Z"


def _safe_read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _is_layout_spec(p: Path) -> bool:
    data = _safe_read_json(p)
    return bool(data) and data.get("kind") == "layout"


def _view_slug_from_spec(p: Path) -> str | None:
    data = _safe_read_json(p)
    if not data:
        return None
    if vs := data.get("view_slug"):
        return vs
    if vn := data.get("view_name"):
        return re.sub(r"\W+", "_", vn.strip().lower())
    return None


def write_if_changed(path: Path, content: str) -> None:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"✅ Generated: {path}")
    else:
        print(f"⏭  Unchanged: {path}")


def render_to_file(
    template_name: str, context: dict, output_path: Path, *, optional: bool = False
) -> None:
    try:
        tpl = env.get_template(template_name)
    except TemplateNotFound:
        if optional:
            print(f"ℹ️  Skipped (template not found): {template_name}")
            return
        raise
    out = tpl.render(**context)
    write_if_changed(output_path, out)


def rank_from_role(role):
    return ROLE_RANK.get(role, 1000)


def ensure_sot(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        print(f"🆕 Created {path} (empty starter). Edit it and rerun.")


def normalize_field_types(ctx: dict) -> None:
    """Normalize top-level model fields (semantic -> Django types)."""
    for f in ctx.get("fields", []):
        t = f.get("type")
        if t in MODEL_TYPE_MAP:
            f["type"] = MODEL_TYPE_MAP[t]


def load_ctx(json_path: Path) -> dict:
    if not json_path.exists():
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        print(f"🆕 Created {json_path} (empty starter). Edit it and rerun.")
    ctx = read_json_any(json_path)  # <-- JSONC-aware

    # normalize ranks on tabs, etc...
    for tab in ctx.get("tabs", []):
        rr = tab.get("required_rank")
        if isinstance(rr, str):
            tab["required_rank"] = rank_from_role(rr)
    ctx["role_ranks"] = ROLE_RANK
    ctx["allowed_tabs"] = [t["slug"] for t in ctx.get("tabs", []) if t.get("slug")]
    normalize_field_types(ctx)
    return ctx


def validate_ctx(ctx: dict) -> list[str]:
    errs = []
    for k in ("app_label", "view_name", "tabs"):
        if k not in ctx:
            errs.append(f"missing key: {k}")

    slugs = []
    for t in ctx.get("tabs", []):
        if "slug" not in t:
            errs.append("tab missing slug")
            continue
        if t["slug"] in slugs:
            errs.append(f"duplicate tab slug: {t['slug']}")
        slugs.append(t["slug"])
        if "form_template" not in t:
            errs.append(f"tab {t['slug']} missing form_template")

    if ctx.get("model") and not isinstance(ctx.get("fields"), list):
        errs.append("model declared but 'fields' is not a list")
    return errs


def latest_spec() -> Path | None:
    if not JSON_DIR.exists():
        return None
    # pick newest timestamped spec; include .jsonc if you use it
    files = sorted(
        [
            p
            for p in JSON_DIR.glob("yofaron_scaffolded_*.json*")
            if p.name != "_in_service.json"
        ],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if files:
        return files[0]
    # optional fallback
    return DEFAULT_SOT if DEFAULT_SOT.exists() else None


def run(cmd):
    print("→", " ".join(str(c) for c in cmd))
    res = subprocess.run(cmd, cwd=ROOT)
    if res.returncode != 0:
        sys.exit(res.returncode)


# ---------- main
def generate_all(json_path: Path):
    ctx = load_ctx(json_path)
    errs = validate_ctx(ctx)
    if errs:
        raise SystemExit("❌ Validation failed:\n- " + "\n- ".join(errs))
    view_slug = ctx["view_name"].lower()

    # Ensure partials directory exists
    partials_dir = BASE_DIR / "templates" / "partials"
    partials_dir.mkdir(parents=True, exist_ok=True)
    # Create a subdirectory for this view_slug/element
    element_dir = partials_dir / view_slug
    element_dir.mkdir(parents=True, exist_ok=True)
    TEMPLATE_PATH_HTML.mkdir(parents=True, exist_ok=True)
    # Views + shell templates
    render_to_file("view_template.tpl.py", ctx, VIEW_PATH / f"{view_slug}.py")
    render_to_file(
        "panels/TabNav.tpl.html", ctx, TEMPLATE_PATH_HTML / f"{view_slug}_nav.html"
    )
    render_to_file(
        "urls_template.tpl.py", ctx, URLS_PATH / f"{ctx['view_slug']}_urls.py"
    )
    # Render main content partial for htmx
    partial_ctx = ctx.copy()
    partial_ctx["is_partial"] = True
    render_to_file(
        "view_content_partial.tpl.html",
        partial_ctx,
        TEMPLATE_PATH_HTML / f"{view_slug}_partial.html",
    )
    # ✅ First, merge sidemenu_bar/*.json → static/sidebar.json
    write_public_sidebar(source_dir="sidemenu_bar", output_file="static/sidebar.json")

    # ✅ Then load and inject it into your template render
    with open("static/sidebar.json", "r", encoding="utf-8") as f:
        sidebar_json = json.load(f)
        render_to_file(
            "panels/SideMenu.tpl.html",
            {"sidebar": sidebar_json},
            TEMPLATE_PATH_HTML / f"{view_slug}_sidebar.html",
        )

    # Per-tab forms + partial templates
    for tab in ctx.get("tabs", []):
        tab_ctx = {"tab": tab, "view": ctx}
        render_to_file(
            "panel/FormTemplate.tpl.html",
            tab_ctx,
            TEMPLATE_PATH_HTML / tab["form_template"],
        )
        render_to_file(
            "form_class.tpl.py", tab_ctx, FORM_PATH / f"{tab['slug']}_form.py"
        )

    # Optional DB/CRUD scaffolds
    if ctx.get("model"):
        # Model + repo/webhooks + HX helper
        render_to_file(
            "model_class.tpl.py", ctx, MODEL_PATH / f"{ctx['model'].lower()}.py"
        )
        render_to_file(
            "repo.tpl.py",
            ctx,
            VIEW_PATH / "repo.py",
        )
        # use secure version if you created it; else keep basic
        # render_to_file("webhook_wrapper_secure.tpl.py", ctx, VIEW_PATH / "webhook_wrapper.py", optional=True)
        render_to_file(
            "webhook_wrapper.tpl.py",
            ctx,
            VIEW_PATH / "webhook_wrapper.py",
            optional=True,
        )
        render_to_file(
            "hx_helpers.tpl.py", ctx, VIEW_PATH / "hx_helpers.py", optional=True
        )

        # Base CRUD (optional if you haven’t added templates yet)
        render_to_file(
            "views_base.tpl.py", ctx, VIEW_PATH / f"{view_slug}_base.py", optional=True
        )
        render_to_file(
            "urls_base.tpl.py",
            ctx,
            URLS_PATH / f"{view_slug}_urls_base.py",
            optional=True,
        )

        # HTML wrappers that include your runtime /tpl components
        render_to_file(
            "modals/FormModal.tpl.html",
            ctx,
            TEMPLATE_PATH_HTML / f"{view_slug}_form.html",
            optional=True,
        )

        render_to_file(
            "tables/TableWrapper.tpl.html",
            ctx,
            TEMPLATE_PATH_HTML / f"{view_slug}_table.html",
            optional=True,
        )
        render_to_file(
            "seed.tpl.py",
            ctx,
            OUTPUT_DIR / "management/commands" / f"seed_{ctx['model'].lower()}.py",
        )


# def latest_spec(DEFAULT_SOT) -> Path | None:
#     files = [Path(p) for p in glob.glob(str(ROOT / "yofaron_scaffolded_*.json"))]
#     files = [p for p in files if PATTERN.match(p.name)]
#     if not files:
#         return DEFAULT_SOT
#     files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
#     return files[0]


def write_sidebar_fragment(ctx: dict):
    """Write a sidebar JSON fragment for this view/tabs into sidemenu_bar/."""
    sidemenu_dir = ROOT / "sidemenu_bar"
    sidemenu_dir.mkdir(parents=True, exist_ok=True)

    heading = ctx.get("sidebar_heading")
    if not heading:
        print("⚠️  No 'sidebar_heading' found in context. Skipping sidebar fragment.")
        return

    view_slug = ctx.get("view_slug", re.sub(r"\W+", "_", ctx["view_name"].lower()))
    path = sidemenu_dir / f"{view_slug}_menu.json"

    tabs = ctx.get("tabs", [])
    if len(tabs) == 1:
        tab = tabs[0]
        url = tab.get("url") or f"/{view_slug}/{tab['slug']}/"
        fragment = {
            "content_id": tab.get("content_id", "main-content"),
            "hx_get": tab.get("hx_get", url),
            "hx_trigger": tab.get("hx_trigger", "load"),
            "hx_target": tab.get("hx_target", ".main-content"),
            "hx_swap": tab.get("hx_swap", "innerHTML"),
            "hx_push_url": tab.get("hx_push_url", "false"),
            "title": tab.get("label", tab["slug"]),
        }
    else:
        items = []
        for tab in tabs:
            url = tab.get("url") or f"/{view_slug}/{tab['slug']}/"
            items.append(
                {
                    "title": tab.get("label", tab["slug"]),
                    "id": tab["slug"],
                    "icon": tab.get("icon", "fas fa-bars"),
                    "data-nav-group": tab.get("nav_group", "account"),
                    "data-tab": tab["slug"],
                    "hx-get": tab.get("hx_get", url),
                    "hx-target": tab.get("hx_target", ".main-content"),
                    "hx-headers": tab.get(
                        "hx_headers", json.dumps({"X-Tab": tab["slug"]})
                    ),
                    "hx-trigger": tab.get("hx_trigger", "click"),
                    "hx-params": tab.get("hx_params", "none"),
                    "hx-swap": tab.get("hx_swap", "innerHTML"),
                    "hx-push-url": tab.get("hx_push_url", "false"),
                    "required_rank": tab.get("required_rank", 0),
                }
            )
        fragment = {"heading": heading, "items": items}

    path.write_text(json.dumps(fragment, indent=2), encoding="utf-8")
    print(f"📌 Sidebar fragment written: {path}")


def write_public_sidebar(source_dir="sidemenu_bar", output_file="static/sidebar.json"):
    from collections import defaultdict

    source_path = Path(source_dir)
    sidebar_data = defaultdict(list)

    for json_file in sorted(source_path.glob("*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "sidebar" in data:
            for section in data["sidebar"]:
                heading = section.get("heading", "Misc")
                sidebar_data[heading].extend(section.get("items", []))
        else:
            heading = data.get("heading", "Misc")
            sidebar_data[heading].extend(data.get("items", []))

    combined = {
        "sidebar": [
            {"heading": heading, "items": items}
            for heading, items in sidebar_data.items()
        ]
    }

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

    print(f"📦 Sidebar JSON compiled → {out_path}")


def write_in_service_file(spec_paths: list[Path]):
    registry_path = ROOT / "builder" / "_in_service.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "scaffolded": [str(p) for p in spec_paths],
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    registry_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"📘 Wrote source-of-truth registry → {registry_path}")


def _utcnow_iso():
    return datetime.utcnow().isoformat() + "Z"


def save_registry(reg: dict) -> None:
    """
    Save the in-service registry to builder/_in_service.json.
    Ensures parent directory exists and injects a fresh timestamp.
    """
    reg["generated_at"] = _utcnow_iso()
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    print(f"📘 Registry updated → {REGISTRY}")


def _utcnow_iso():
    return datetime.utcnow().isoformat() + "Z"


def save_registry(reg: dict) -> None:
    reg["generated_at"] = _utcnow_iso()
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    print(f"📘 Registry updated → {REGISTRY}")


def load_registry() -> dict:
    """
    Load builder/_in_service.json or return a fresh skeleton.
    Schema:
      {
        "generated_at": "...Z",
        "layout": "builder/json/yofaron_layout_base.json" | null,
        "specs": [
          {"path": ".../yofaron_scaffolded_*.json", "view_slug": "admin", "mtime": 1757641909, "active": true}
        ]
      }
    """
    if REGISTRY.exists():
        data = _safe_read_json(REGISTRY)
        if isinstance(data, dict):
            # ensure keys exist
            data.setdefault("generated_at", _utcnow_iso())
            data.setdefault("layout", None)
            data.setdefault("specs", [])
            return data
        print("⚠️  _in_service.json malformed; starting fresh.")
    return {"generated_at": _utcnow_iso(), "layout": None, "specs": []}


def discover_specs() -> tuple[list[Path], list[Path]]:
    if not JSON_DIR.exists():
        return ([], [])
    files = [
        p for p in JSON_DIR.glob("*.json*") if p.name != "_in_service.json"
    ]  # *.json and *.jsonc
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    layouts, modules = [], []
    for p in files:
        try:
            data = read_json_any(p)
        except Exception:
            continue
        if data.get("kind") == "layout":
            layouts.append(p)
        else:
            modules.append(p)
    return (layouts, modules)


def sync_registry(
    auto_pick_latest_layout: bool = True, prune_missing: bool = False
) -> dict:
    reg = load_registry()
    layouts, modules = discover_specs()

    # existing layout path in registry
    current_layout = Path(reg.get("layout")) if reg.get("layout") else None

    if auto_pick_latest_layout and layouts:
        # sort layouts by modified time (newest first)
        latest_layout = sorted(layouts, key=lambda p: p.stat().st_mtime, reverse=True)[
            0
        ]
        if not current_layout or current_layout.resolve() != latest_layout.resolve():
            reg["layout"] = str(latest_layout)
            print(f"🎯 Updated layout in registry → {latest_layout.name}")
        else:
            print(f"⏭ Layout unchanged → {current_layout.name}")

    save_registry(reg)
    render_project_urls_autogen(reg)

    return reg


def main():
    args = sys.argv[1:]
    spec = None
    no_index = "--no-index" in args
    no_validate = "--no-validate" in args
    dry = "--dry-run" in args

    if "--spec" in args:
        i = args.index("--spec")
        try:
            spec = Path(args[i + 1])
        except Exception:
            print("❌ --spec requires a filename")
            sys.exit(2)
    else:
        spec = latest_spec()
        if not spec:
            print("❌ No yofaron_scaffolded_*.json found. Run the wizard first.")
            sys.exit(2)

    print(f"📄 Using spec: {spec}")

    if not no_index:
        run([PY, "generate_component_index.py"])

    if not no_validate:
        # 🔑 now always call yofaron_validator.py
        run([PY, "yofaron_validator.py", spec.name])

    if dry:
        print("ℹ️ Dry-run: skipping generation.")
        return

    run([PY, "yofaron_generate.py", spec.name])
    print("🎉 yofaron scaffolding complete")


if __name__ == "__main__":
    cli_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if cli_path and not cli_path.is_absolute():
        cli_path = JSON_DIR / cli_path

    sot = cli_path if cli_path else latest_spec()
    if not sot:
        print(
            "❌ No spec file found in builder/json/. Run the wizard or place a yofaron_scaffolded_*.json here."
        )
        sys.exit(1)

    print(f"📄 Using spec: {sot}")
    generate_all(sot)
