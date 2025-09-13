import os
from pathlib import Path
from django.core.management.base import BaseCommand
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates/revcat"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "media/snippets"
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


class Command(BaseCommand):
    help = "Generate RevenueCat platform snippet (web/flutter/ios/android)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--platform", required=True, help="Platform: web, flutter, ios, android"
        )
        parser.add_argument(
            "--entitlement", default="pro", help="Entitlement key (default: pro)"
        )
        parser.add_argument(
            "--license_type", default="public", help="License type (e.g. public, lti)"
        )

    def handle(self, *args, **options):
        platform = options["platform"]
        entitlement = options["entitlement"]
        license_type = options["license_type"]

        tpl_file = f"{platform}.tpl"
        if not (TEMPLATE_DIR / tpl_file).exists():
            self.stderr.write(self.style.ERROR(f"Template for '{platform}' not found."))
            return

        context = {
            "entitlement": entitlement,
            "license_type": license_type,
            "platform": platform,
        }

        template = env.get_template(tpl_file)
        output = template.render(context)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        outfile = OUTPUT_DIR / f"{platform}_snippet.{get_ext(platform)}"
        outfile.write_text(output, encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"✅ Snippet generated: {outfile}"))


def get_ext(platform):
    return {
        "web": "js",
        "flutter": "dart",
        "ios": "swift",
        "android": "kt",
    }.get(platform, "txt")
