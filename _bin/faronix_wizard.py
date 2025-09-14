#!/usr/bin/env python3
import json
import os
import subprocess
import sys, re, glob
from pathlib import Path
from datetime import datetime


timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
DEFAULT_CONFIG = {
    "app_label": "core",
    "view_name": "Default",
    "model": None,
    "table": None,
    "constraints": {"unique_together": [], "indexes": []},
    "fields": [],
    "tabs": [],
    "webhooks": None,
}


ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
ROOT = Path(__file__).resolve().parent
JSON_DIR = os.path.join(ROOT, "builder", "json")
os.makedirs(JSON_DIR, exist_ok=True)
sot_file = JSON_DIR / f"yofaron_scaffolded_{ts}.json"

APP_DEFAULT = "core"
VIEW_DEFAULT = "views"
PATTERN = re.compile(r"yofaron_scaffolded_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.json")

MODEL_DEFAULT = ""  # blank = no model

MODEL_TYPE_CHOICES = [
    "text",
    "slug",
    "bool",
    "int",
    "number",
    "float",
    "date",
    "datetime",
    "json",
    "file",
    "image",
]
FORM_TYPE_CHOICES = [
    "text",
    "email",
    "password",
    "number",
    "bool",
    "date",
    "datetime",
    "file",
    "image",
    "choice",
    "textarea",
]
RANK_CHOICES = ["guest", "member", "staff", "manager", "admin", "superadmin"]


def yn(q, default=True):
    d = "Y/n" if default else "y/N"
    while True:
        a = input(f"{q} [{d}]: ").strip().lower()
        if not a:
            return default
        if a in ("y", "yes"):
            return True
        if a in ("n", "no"):
            return False
        print("Please answer y or n.")


def ask(q, default=None, allow_blank=False):
    suffix = f" [{default}]" if default is not None else ""
    while True:
        a = input(f"{q}{suffix}: ").strip()
        if not a and default is not None:
            return default
        if a or allow_blank:
            return a


def choose(q, choices, default=None, allow_blank=False):
    while True:
        a = ask(f"{q} ({'/'.join(choices)})", default, allow_blank).strip()
        if allow_blank and a == "":
            return a
        if a in choices:
            return a
        print(f"Choose one of: {', '.join(choices)}")


def number_or_blank(s):
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s  # keep as string (e.g., "True" or "uuid4()")


def collect_model_fields():
    fields = []
    print("\n--- Define MODEL (DB) fields. Leave name blank to finish.")
    print(
        "Types: text, slug, bool, int, number, float, date, datetime, json, file, image"
    )
    while True:
        name = ask("Field name", allow_blank=True)
        if not name:
            break
        ftype = choose("Field type", MODEL_TYPE_CHOICES, default="text")
        opts = ask("Django opts (e.g. max_length=200, unique=True)", allow_blank=True)
        default_raw = ask("Default (blank for none)", allow_blank=True)
        default_val = number_or_blank(default_raw)
        # append default into opts if provided and not already present
        if default_raw and "default=" not in (opts or ""):
            opts = (opts + ", " if opts else "") + f"default={repr(default_val)}"
        fields.append({"name": name, "type": ftype, **({"opts": opts} if opts else {})})
    return fields


def collect_tab_fields():
    fields = []
    print("\nUI fields for this TAB (plain Form fallback). Leave name blank to finish.")
    print("Types:", ", ".join(FORM_TYPE_CHOICES))
    while True:
        name = ask("UI field name", allow_blank=True)
        if not name:
            break
        ftype = choose("UI field type", FORM_TYPE_CHOICES, default="text")
        label = ask("Label (blank = use name)", allow_blank=True)
        required = yn("Required?", True)
        f = {"name": name, "type": ftype, "required": required}
        if label:
            f["label"] = label
        if ftype == "choice":
            raw = ask("Choices (comma separated, e.g. A,B,C)", allow_blank=True)
            if raw:
                f["choices"] = [c.strip() for c in raw.split(",") if c.strip()]
        fields.append(f)
    return fields


def latest_spec() -> Path | None:
    files = [Path(p) for p in glob.glob(str(ROOT / "yofaron_scaffolded_*.json"))]
    files = [p for p in files if PATTERN.match(p.name)]
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def collect_tabs():
    tabs = []
    print("\n--- Define TABS. Leave slug blank to finish.")
    while True:
        slug = ask("Tab slug (e.g. list, details)", allow_blank=True)
        if not slug:
            break
        label = ask("Tab label", default=slug.title())
        rank = choose("Required rank", RANK_CHOICES, default="staff")
        form_tpl = ask(
            "Form template filename to generate", default=f"{slug}_form.html"
        )
        tab = {
            "slug": slug,
            "label": label,
            "required_rank": rank,
            "form_template": form_tpl,
        }

        if yn("Add UI fields for this tab?", True):
            tab["fields"] = collect_tab_fields()

        if yn("Add a table config for this tab?", True):
            comp = ask("Table component", default="DataTable.tpl")
            triggers = ask(
                "HTMX triggers",
                default=f"{slug}Created, {slug}Updated, {slug}Deleted from:body",
            )
            headers = [
                h.strip()
                for h in ask(
                    "Headers (comma separated)", default="Title,Status,Updated,Actions"
                ).split(",")
            ]
            columns = [
                c.strip()
                for c in ask(
                    "Columns (comma separated)",
                    default="title,status,updated_at,actions",
                ).split(",")
            ]
            tab["table"] = {
                "component": comp,
                "hx": {"triggers": triggers, "swap": "outerHTML"},
                "headers": headers,
                "columns": columns,
            }

        tabs.append(tab)
    return tabs


def collect_webhooks():
    if not yn("\nConfigure outbound webhooks?", False):
        return None
    base_url = (
        ask("Base URL (e.g. https://hooks.example.com)", allow_blank=True) or None
    )
    headers = {}
    if yn("Add headers?", False):
        while True:
            k = ask("Header key", allow_blank=True)
            if not k:
                break
            v = ask("Header value", allow_blank=True)
            headers[k] = v
    events = {}
    if yn("Add event routes (created/updated/deleted)?", True):
        c = ask("Route for 'created'", allow_blank=True)
        u = ask("Route for 'updated'", allow_blank=True)
        d = ask("Route for 'deleted'", allow_blank=True)
        if c:
            events["created"] = c
        if u:
            events["updated"] = u
        if d:
            events["deleted"] = d
    secret = (
        ask(
            "Shared secret for HMAC signatures (blank disables signing)",
            allow_blank=True,
        )
        or None
    )
    timeout = float(ask("Timeout seconds", default="3.0"))
    retries = int(ask("Max retries", default="3"))
    b0 = float(ask("Backoff initial seconds", default="0.25"))
    bmax = float(ask("Backoff max seconds", default="5.0"))
    jitter = float(ask("Jitter seconds", default="0.2"))
    mode = choose("Delivery mode", ["thread", "sync"], default="thread")
    verify = yn("Verify SSL?", True)
    transport = (
        ask(
            "Transport path (blank=urllib; e.g. core.views.webhook_transports:RequestsTransport)",
            allow_blank=True,
        )
        or None
    )

    return {
        "base_url": base_url,
        "headers": headers or None,
        "events": events or None,
        "secret": secret,
        "timeout_sec": timeout,
        "max_retries": retries,
        "backoff_initial_sec": b0,
        "backoff_max_sec": bmax,
        "jitter_sec": jitter,
        "async_mode": mode,
        "verify_ssl": verify,
        "transport": transport,
    }


def ensure_sot(path: Path):
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        print(f"🆕 Created {path} (empty starter). Edit it and rerun.")


def run(cmd):
    print("→", " ".join(str(c) for c in cmd))
    res = subprocess.run(cmd, cwd=ROOT)
    if res.returncode != 0:
        sys.exit(res.returncode)


def main():

    print("=== Yofaron Interactive Scaffolding Wizard ===\n")
    app_label = ask("App label", default=APP_DEFAULT)
    view_name = ask("View/Module name", default=VIEW_DEFAULT)
    sidebar_heading = ask("Sidebar group heading (e.g. Admin, Core)", default=view_name)
    view_slug = re.sub(r"\W+", "_", view_name.strip().lower())
    model = (
        ask("Model name (blank = none)", default="", allow_blank=True).strip() or None
    )
    table = ask("Explicit db_table (blank auto)", allow_blank=True).strip() or None

    constraints = {"unique_together": [], "indexes": []}
    if yn("Add DB constraints?", False):
        if yn("Add unique_together?", False):
            raw = ask("Groups e.g. [slug,owner_id];[title]", allow_blank=True)
            if raw:
                groups = []
                for grp in raw.split(";"):
                    cols = [c.strip() for c in grp.strip(" []").split(",") if c.strip()]
                    if cols:
                        groups.append(cols)
                constraints["unique_together"] = groups
        if yn("Add simple indexes?", False):
            raw = ask("Indexes e.g. [slug];[updated_at]", allow_blank=True)
            if raw:
                idxs = []
                for grp in raw.split(";"):
                    cols = [c.strip() for c in grp.strip(" []").split(",") if c.strip()]
                    if cols:
                        idxs.append({"fields": cols})
                constraints["indexes"] = idxs

    fields = collect_model_fields() if model else []
    tabs = collect_tabs()
    webhooks = collect_webhooks()

    doc = {
        "app_label": app_label,
        "view_name": view_name,
        "view_slug": view_slug,  # You can generate this too
        "sidebar_heading": sidebar_heading,
        "model": model,
        "table": table,
        "constraints": constraints,
        "fields": fields,
        "tabs": tabs,
        "webhooks": webhooks,
    }

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    sot_file = ROOT / f"yofaron_scaffolded_{ts}.json"
    sot_file.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"\n✅ Wrote {sot_file}")

    if yn("\nRun full scaffold now (index → validate → generate)?", True):
        run([sys.executable, "generate_component_index.py"])
        run([sys.executable, "yofaron_validate.py", sot_file.name])
        run([sys.executable, "yofaron_generate.py", sot_file.name])
        print("\n🎉 Scaffolding complete.")

    print("\nNext:")
    print("  - python manage.py makemigrations && python manage.py migrate")
    print("  - include generated urls in your project")
    print("  - open your module page and test HTMX CRUD")


if __name__ == "__main__":
    main()
