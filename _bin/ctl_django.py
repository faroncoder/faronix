from pathlib import Path
from django.core.management.base import BaseCommand
import json
from jinja2 import Environment, FileSystemLoader


class Command(BaseCommand):
    help = "Scaffold components, views, forms, and models using Yofaron JSON + Jinja2 system."

    def add_arguments(self, parser):
        parser.add_argument("--json", type=str, help="Path to JSON snippet file")
        parser.add_argument(
            "--mode",
            type=str,
            choices=["html", "view", "form", "model", "all"],
            default="html",
        )
        parser.add_argument("--output", type=str, default="builder/templates/output")

    def handle(self, *args, **opts):
        json_path = Path(opts["json"])
        mode = opts["mode"]
        output_root = Path(opts["output"])

        if not json_path.exists():
            self.stderr.write(f"❌ JSON not found: {json_path}")
            return

        with open(json_path) as f:
            ctx = json.load(f)

        # Load the component index
        index_path = Path("builder/tpl/component_index.json")
        if not index_path.exists():
            self.stderr.write("❌ Missing builder/tpl/component_index.json")
            return

        with open(index_path) as f:
            component_map = json.load(f)

        # Resolve component template
        component = ctx.get("component")
        if not component:
            self.stderr.write("❌ Missing 'component' field in JSON")
            return

        template_file = None
        for folder, files in component_map.items():
            if component in [f.replace(".tpl", "") for f in files]:
                template_file = f"{folder}/{component}.tpl.html"
                break

        if not template_file:
            self.stderr.write(
                f"❌ Component '{component}' not found in component_index.json"
            )
            return

        # Setup Jinja environment
        env = Environment(
            loader=FileSystemLoader("builder/tpl"), trim_blocks=True, lstrip_blocks=True
        )

        def render(name, ctx_obj, outdir, suffix):
            tpl = env.get_template(name)
            output = output_root / outdir / f"{component}.{suffix}"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(tpl.render(**ctx_obj))
            self.stdout.write(f"✅ {output.relative_to(Path.cwd())}")

        if mode in ("html", "all"):
            render(template_file, ctx, "components", "html")

        if mode in ("view", "all") and "view_template" in ctx:
            render(ctx["view_template"], ctx, "views", "py")

        if mode in ("form", "all") and "form_template" in ctx:
            render(ctx["form_template"], ctx, "forms", "py")

        if mode in ("model", "all") and "model_template" in ctx:
            render(ctx["model_template"], ctx, "models", "py")
