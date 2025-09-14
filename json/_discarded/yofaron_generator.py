# yofaron_generate.py
# This is the core scaffolding engine for views, forms, HTML, RBAC, and HTMX

import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Default RBAC role tiers
ROLE_RANK = {
    "guest": 0,
    "member": 20,
    "staff": 40,
    "manager": 60,
    "admin": 80,
    "superadmin": 100,
}

# Setup Jinja2 environment
TEMPLATE_DIR = Path("templates")
env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True
)

# Paths for generated code
OUTPUT_DIR = Path("core")
VIEW_PATH = OUTPUT_DIR / "views"
TEMPLATE_PATH = OUTPUT_DIR / "templates"
FORM_PATH = OUTPUT_DIR / "forms"
MODEL_PATH = OUTPUT_DIR / "models"


def render_to_file(template_name, context, output_path):
    tpl = env.get_template(template_name)
    result = tpl.render(**context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result)
    print(f"✅ Generated: {output_path}")


def rank_from_role(role):
    return ROLE_RANK.get(role, 1000)


def generate_all(json_file):
    with open(json_file) as f:
        ctx = json.load(f)

    # Normalize ranks
    for tab in ctx.get("tabs", []):
        if isinstance(tab.get("required_rank"), str):
            tab["required_rank"] = rank_from_role(tab["required_rank"])

    # Add to context
    ctx["role_ranks"] = ROLE_RANK
    ctx["allowed_tabs"] = [tab["slug"] for tab in ctx.get("tabs", [])]

    # Generate everything
    render_to_file(
        "view_template.tpl.py", ctx, VIEW_PATH / f"{ctx['view_name'].lower()}.py"
    )
    render_to_file(
        "tab_nav.tpl.html", ctx, TEMPLATE_PATH / f"{ctx['view_name'].lower()}_nav.html"
    )
    render_to_file(
        "sidebar_menu.tpl.html",
        ctx,
        TEMPLATE_PATH / f"{ctx['view_name'].lower()}_sidebar.html",
    )

    for tab in ctx.get("tabs", []):
        tab_ctx = {"tab": tab, "view": ctx}
        render_to_file(
            "form_template.tpl.html", tab_ctx, TEMPLATE_PATH / tab["form_template"]
        )
        render_to_file(
            "form_class.tpl.py", tab_ctx, FORM_PATH / f"{tab['slug']}_form.py"
        )

    # Optional: Models
    if ctx.get("model"):
        render_to_file(
            "model_class.tpl.py", ctx, MODEL_PATH / f"{ctx['model'].lower()}.py"
        )


# Example run
if __name__ == "__main__":
    generate_all("account_view.json")
