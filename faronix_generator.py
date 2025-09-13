# yofaron_generate.py
import ast, json, re, os, sys, glob
from pathlib import Path
import shutil
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import subprocess
from datetime import datetime


# Ensure parent directory is in sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from yofaron_config import (
    ROOT,
    PROJECT_ROOT,
    CONFIG_DIR,
    JSON_DIR,
    TPL_HTML_DIR,
    TPL_PY_DIR,
    DEFAULT_SOT,
    ROLE_RANK,
    MODEL_TYPE_MAP,
    DEFAULT_CONFIG,
    REGISTRY,
    OUTPUT_DIR,
    VIEW_PATH,
    URLS_PATH,
    FORM_PATH,
    MODEL_PATH,
    BASE_DIR,
    TEMPLATE_PARTIALS_PATH,
)


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


env = Environment(
    loader=FileSystemLoader(
        [str(TPL_PY_DIR), str(TPL_HTML_DIR), str(ROOT), str(PROJECT_ROOT), "."]
    ),
    trim_blocks=True,
    lstrip_blocks=True,
)

env.globals["MODEL_TYPE_MAP"] = MODEL_TYPE_MAP
env.globals["JSON_DIR"] = JSON_DIR
env.globals["TPL_PY_DIR"] = TPL_PY_DIR
env.globals["TPL_HTML_DIR"] = TPL_HTML_DIR
env.globals["MODEL_PATH"] = MODEL_PATH
env.globals["DEFAULT_CONFIG"] = DEFAULT_CONFIG

print(
    "DEBUG PATHS: ROOT =",
    ROOT,
    "\n PROJECT_ROOT=",
    PROJECT_ROOT,
    "\n CONFIG_DIR  =",
    CONFIG_DIR,
    "\n JSON_DIR    =",
    JSON_DIR,
    "\n TPL_HTML_DIR     =",
    TPL_HTML_DIR,
    "\n TPL_PY_DIR     =",
    TPL_PY_DIR,
    "\n OUTPUT_DIR  =",
    "\n OUTPUT_DIR  =",
    OUTPUT_DIR,
    "\n VIEW_PATH   =",
    VIEW_PATH,
    "\n URLS_PATH   =",
    URLS_PATH,
    "\n FORM_PATH   =",
    FORM_PATH,
    "\n MODEL_PATH  =",
    MODEL_PATH,
    "\n BASE_DIR    =",
    BASE_DIR,
    "\n TEMPLATE_PATH_HTML =",
)


def _utcnow_iso():
    return datetime.utcnow().isoformat() + "Z"


def _strip_jsonc(s: str) -> str:
    # remove // line comments
    s = re.sub(r"//.*?$", "", s, flags=re.MULTILINE)
    # remove /* ... */ block comments
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    return s


def camel(s: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", str(s))
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


env.filters["camel"] = camel


def pyrepr(v):
    return repr(v)


env.filters["pyrepr"] = pyrepr


def rank_from_role(role):
    return ROLE_RANK.get(role, 1000)


def run(cmd):
    print("→", " ".join(str(c) for c in cmd))
    res = subprocess.run(cmd, cwd=ROOT)
    if res.returncode != 0:
        sys.exit(res.returncode)


################


def read_json_any(path: Path) -> dict:
    """
    Read .json or .jsonc, strip comments if needed, and parse.
    """
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonc":
        raw = _strip_jsonc(raw)
    return json.loads(raw)


def _safe_read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


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


def normalize_field_types(ctx: dict) -> None:
    """Normalize top-level model fields (semantic -> Django types)."""
    for f in ctx.get("fields", []):
        t = f.get("type")
        if t in MODEL_TYPE_MAP:
            f["type"] = MODEL_TYPE_MAP[t]


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


def ensure_sot(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        print(f"🆕 Created {path} (empty starter). Edit it and rerun.")


def load_ctx(json_path: Path) -> dict:
    if not json_path.exists():
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        print(f"🆕 Created {json_path} (empty starter). Edit it and rerun.")
        # Auto-fill missing app_label
        # if "app_label" not in ctx:
        #     ctx["app_label"] = ctx.get("view_name", "core").lower()

    ctx = read_json_any(json_path)  # <-- JSONC-aware

    # --- Run component index generator and load index ---
    subprocess.run([sys.executable, "builder/generate_component_index.py"], check=True)
    index_path = Path("builder/component_index.json")
    component_index = None
    if index_path.exists():
        with index_path.open() as f:
            index_data = json.load(f)
            # Flatten all components into a single list
            all_components = []
            for comps in index_data.get("components", {}).values():
                all_components.extend(comps)
            component_index = all_components

    # Auto-fill missing app_label
    if "app_label" not in ctx or ctx["app_label"] is None:
        ctx["app_label"] = ctx.get("view_name", "core").lower()

    for tab in ctx.get("tabs", []):
        # Clear/empty tab parameters for robustness
        tab.setdefault("params", {})
        tab.setdefault("hx_params", "")
        # Always set required_rank to 100 (superadmin)
        tab["required_rank"] = 100
        # Auto-pick form_template if missing or empty
        if "form_template" not in tab or not tab["form_template"]:
            tpl_name = component_index[0] if component_index else "FormTemplate"
            if not tpl_name.endswith(".tpl.html"):
                tpl_name = f"{tpl_name}.tpl.html"
            tab["form_template"] = tpl_name
    ctx["role_ranks"] = ROLE_RANK
    ctx["allowed_tabs"] = [t["slug"] for t in ctx.get("tabs", []) if t.get("slug")]
    normalize_field_types(ctx)
    return ctx


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


def save_registry(reg: dict) -> None:
    reg["generated_at"] = _utcnow_iso()
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    print(f"📘 Registry updated → {REGISTRY}")


def write_in_service_file(spec_paths: list[Path]):
    registry_path = ROOT / "builder" / "_in_service.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "scaffolded": [str(p) for p in spec_paths],
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    registry_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"📘 Wrote source-of-truth registry → {registry_path}")


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
    # Auto-fill missing app_label in context
    if "app_label" not in context and "view_name" in context:
        context["app_label"] = context["view_name"].lower()
    # Always provide a default user object with rank 100
    if "user" not in context:
        context["user"] = {"rank": 100}
    # If context is a tab context, auto-fill form_template
    if "tab" in context and "form_template" not in context["tab"]:
        context["tab"]["form_template"] = "FormTemplate.tpl.html"
    try:
        tpl = env.get_template(template_name)
    except TemplateNotFound:
        if optional:
            print(f"ℹ️  Skipped (template not found): {template_name}")
            return
        raise
    out = tpl.render(**context)
    # Debug output for view file generation
    if output_path.match(str(VIEW_PATH / "*.py")):
        print(f"[DEBUG] Rendering {output_path}")
        print(f"[DEBUG] Context: {json.dumps(context, default=str, indent=2)}")
        print(f"[DEBUG] Output:\n{out[:500]}{'...' if len(out) > 500 else ''}")
    write_if_changed(output_path, out)


def render_project_urls_autogen(reg: dict):
    active_specs = _build_active_specs_for_urls(reg)
    ctx = {"active_specs": active_specs}
    out = CONFIG_DIR / "urls_autogen.py"
    render_to_file("urls_autogen.tpl.py", ctx, out)
    print(f"✅ Wrote project URL includes → {out}")


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
        specs.append(
            {
                "view_name": view_name,
                "view_slug": view_slug,
                "app_label": data.get("app_label", "core"),
            }
        )
    # keep stable order (by slug)
    specs.sort(key=lambda x: x["view_slug"])
    return specs


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

    for tab in ctx.get("tabs", []):
        tab_ctx = {"tab": tab, "view": ctx}
        # Use form from tab if present, else inject dummy
        if "form" in tab:
            tab_ctx["form"] = tab["form"]
        else:

            class DummyField:
                def __init__(self):
                    self.id_for_label = "dummy_field"
                    self.label = "Dummy Field"
                    self.errors = None

                def __str__(self):
                    return "<input type='text' name='dummy_field' />"

            class DummyForm:
                non_field_errors = None

                def __iter__(self):
                    return iter([DummyField()])

            tab_ctx["form"] = DummyForm()
        render_to_file(
            "panels/FormTemplate.tpl.html",
            tab_ctx,
            TEMPLATE_PARTIALS_PATH / tab["form_template"],
        )
        render_to_file(
            "form_class.tpl.py", tab_ctx, FORM_PATH / f"{tab['slug']}_form.py"
        )
        # Build link dictionary for sidebar
        url = tab.get("hx_get", "")
        item = {
            "hx-get": tab.get("hx_get", url),
            "hx-target": tab.get("hx_target", ".main-content"),
            "hx-headers": tab.get("hx_headers", json.dumps({"X-Tab": tab["slug"]})),
            "hx-trigger": tab.get("hx_trigger", "click"),
            "hx-params": tab.get("hx_params", "none"),
            "hx-swap": tab.get("hx_swap", "innerHTML"),
            "hx-push-url": tab.get("hx_push_url", "false"),
            "required_rank": tab.get("required_rank", 0),
        }
        items = [item]
    fragment = {"heading": heading, "items": items}

    path.write_text(json.dumps(fragment, indent=2), encoding="utf-8")
    print(f"📌 Sidebar fragment written: {path}")


def write_public_sidebar(source_dir="sidemenu_bar", output_file="static/sidebar.json"):
    from collections import defaultdict

    source_path = Path(source_dir)
    sidebar_data = defaultdict(list)

    # Combine all sidemenu_bar/*.json fragments
    for json_file in sorted(source_path.glob("*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"⚠️ Skipping {json_file.name} due to parse error: {e}")
                continue

        if "sidebar" in data:
            for section in data["sidebar"]:
                heading = section.get("heading", "Misc")
                sidebar_data[heading].extend(section.get("items", []))
        else:
            heading = data.get("heading", "Misc")
            sidebar_data[heading].extend(data.get("items", []))

    # Compose unified sidebar list
    full_sidebar = [
        {"heading": heading, "items": items} for heading, items in sidebar_data.items()
    ]

    # Count total clickable items
    total_links = sum(len(section["items"]) for section in full_sidebar)

    # Set "tabbed" to False if only one link across all sections
    is_tabbed = total_links > 1

    combined = {
        "sidebar": full_sidebar,
        "tabbed": is_tabbed,
    }

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

    print(
        f"📦 Sidebar JSON compiled → {out_path} ({'Tabbed' if is_tabbed else 'Single link mode'})"
    )


# ---------- main
def generate_all(json_path: Path):
    # Also render to builder/templates/tpl_py and tpl_html for test coverage

    ctx = load_ctx(json_path)
    # Always set view_slug in context
    import re  # Ensure re is available in local scope for patch logic

    if "view_slug" not in ctx:
        ctx["view_slug"] = re.sub(r"\W+", "_", ctx.get("view_name", "view").lower())
    errs = validate_ctx(ctx)
    if errs:
        raise SystemExit("❌ Validation failed:\n- " + "\n- ".join(errs))
    view_slug = ctx["view_slug"]

    # Ensure partials directory exists
    partials_dir = Path("templates/partials")
    partials_dir.mkdir(parents=True, exist_ok=True)
    # Views + shell templates
    render_to_file("view_template.tpl.py", ctx, VIEW_PATH / f"{view_slug}.py")
    render_to_file(
        "view_template.tpl.py",
        ctx,
        TEMPLATE_PARTIALS_PATH / f"{view_slug}_partial.html",
    )
    nav_filename = f"{view_slug}_nav_{ts}.html"
    render_to_file("panels/TabNav.tpl.html", ctx, TEMPLATE_PARTIALS_PATH / nav_filename)
    render_to_file(
        "panels/TabNav.tpl.html", ctx, TEMPLATE_PARTIALS_PATH / f"{view_slug}_nav.html"
    )
    # Only append a single route line, no duplicate imports or app_name
    url_file = URLS_PATH / f"{ctx['view_slug']}_urls.py"
    route_line = f'    path("{ctx["view_slug"]}/", {ctx["view_slug"]}, name="{ctx["view_slug"]}"),\n'
    import_line = f'from core.views.{ctx["view_slug"]} import {ctx["view_slug"]}\n'
    # If file exists, preserve only the import/app_name block and unique route lines
    if url_file.exists():
        lines = url_file.read_text(encoding="utf-8").splitlines()
        header = []
        routes = set()
        in_routes = False
        for line in lines:
            if line.strip().startswith("urlpatterns += ["):
                in_routes = True
                continue
            if in_routes:
                if line.strip() == "]":
                    in_routes = False
                continue
            # Remove previous import for this view_slug
            if line.strip().startswith("from core.views.") and ctx["view_slug"] in line:
                continue
            header.append(line)
        # Only keep unique route lines
        routes.add(route_line)
        url_file.write_text(
            "\n".join(header)
            + "\n"
            + import_line
            + "\nurlpatterns += [\n"
            + "".join(routes)
            + "]\n",
            encoding="utf-8",
        )
    else:
        url_file.write_text(
            "# --- Only add new routes, do not overwrite existing ---\n"
            "from django.urls import path\n" + import_line + "\n"
            f"app_name = \"{ctx['app_label']}\"\n\n"
            "urlpatterns += [\n" + route_line + "]\n",
            encoding="utf-8",
        )
    render_to_file(
        "urls_template.tpl.py",
        ctx,
        TEMPLATE_PARTIALS_PATH / f"{view_slug}_sidebar.html",
    )
    # Render main content partial for htmx
    partial_ctx = ctx.copy()
    partial_ctx["is_partial"] = True
    partial_filename = f"{view_slug}_partial_{ts}.html"
    render_to_file(
        "view_content_partial.tpl.html",
        ctx,
        TEMPLATE_PARTIALS_PATH / f"{view_slug}_partial.html",
    )

    # ✅ First, merge sidemenu_bar/*.json → static/sidebar.json
    write_public_sidebar(source_dir="sidemenu_bar", output_file="static/sidebar.json")

    # ✅ Then load and inject it into your template render
    with open("static/sidebar.json", "r", encoding="utf-8") as f:
        sidebar_json = json.load(f)
    sidebar_filename = f"{view_slug}_sidebar_{ts}.html"
    render_to_file(
        "panels/SideMenu.tpl.html",
        {"sidebar": sidebar_json},
        TEMPLATE_PARTIALS_PATH / f"{view_slug}_sidebar.html",
    )

    # Per-tab forms + partial templates
    for tab in ctx.get("tabs", []):
        tab_ctx = {"tab": tab, "view": ctx}
        # Inject a robust dummy form object if not present
        if "form" not in tab_ctx:

            class DummyField:
                def __init__(self):
                    self.id_for_label = "dummy_field"
                    self.label = "Dummy Field"
                    self.errors = None

                def __str__(self):
                    return "<input type='text' name='dummy_field' />"

            class DummyForm:
                non_field_errors = None

                def __iter__(self):
                    return iter([DummyField()])

            tab_ctx["form"] = DummyForm()
        form_filename = f"{tab['slug']}_form_{ts}.html"
        render_to_file(
            "panels/FormTemplate.tpl.html",
            tab_ctx,
            TEMPLATE_PARTIALS_PATH / form_filename,
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
            TEMPLATE_PARTIALS_PATH / f"{view_slug}_form.html",
            optional=True,
        )

        render_to_file(
            "tables/TableWrapper.tpl.html",
            partials_dir / tab["form_template"],
            TEMPLATE_PARTIALS_PATH / f"{view_slug}_table.html",
            optional=True,
        )
        render_to_file(
            "seed.tpl.py",
            ctx,
            OUTPUT_DIR / "management/commands" / f"seed_{ctx['model'].lower()}.py",
        )


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
