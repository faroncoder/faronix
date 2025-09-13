# generate_manifest.py (tpl-enabled version)

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone

# Assigning the timestamp to a variable
from datetime import datetime, timezone

# Setup Jinja2 environment
TEMPLATE_DIR = Path(__file__).parent / "templates"
MANIFEST_DIR = Path(__file__).parent / "manifest"

# Define and parse command-line arguments
parser = argparse.ArgumentParser(description="Generate manifest files.")
parser.add_argument(
    "--version", required=True, help="Specify the version for the manifest."
)
parser.add_argument("--verbose", action="store_true", help="Enable verbose output.")
args = parser.parse_args()

# Define the bootstrap data
bootstrap = {
    "version": args.version,
    "timestamp": datetime.now(timezone.utc).isoformat()
}

# Add roles to the bootstrap data
bootstrap["roles"] = {
    "admin": {"permissions": ["manage", "edit", "view"]},
    "user": {"permissions": ["edit", "view"]},
    "guest": {"permissions": ["view"]}
}

# Add features to the bootstrap data
bootstrap["features"] = {
    "edu_pro": ["record_video", "export_transcript", "dashboard"],
    "team": ["team_dashboard", "member_invite", "audit_log"],
    "lifetime": ["record_video", "dashboard"],
    "guest": []
}



env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

EXT_MAP = {".js": "web", ".dart": "flutter", ".swift": "ios", ".kt": "android"}


def parse_snippet_filename(filename):
    stem = filename.stem
    parts = stem.split("_", 1)
    if len(parts) != 2:
        return None, None
    ext = filename.suffix
    platform = EXT_MAP.get(ext, parts[0])
    entitlement = parts[1]
    return platform, entitlement


def collect_snippet_data(snippets_dir, verbose=False):
    platforms = defaultdict(list)
    for file in snippets_dir.glob("*.*"):
        platform, entitlement = parse_snippet_filename(file)
        if platform and entitlement:
            platforms[platform].append(entitlement)
            if verbose:
                print(f"✓ Snippet: {file.name} → {platform}/{entitlement}")
        elif verbose:
            print(f"⚠️ Skipping: {file.name}")
    return dict(platforms)


def collect_menu_data(menus_dir, verbose=False):
    menus = defaultdict(list)
    for file in menus_dir.glob("*.json"):
        name = file.stem
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    items = [
                        item.get("label") or item.get("name")
                        for item in data
                        if isinstance(item, dict)
                    ]
                    menus[name] = items
                    if verbose:
                        print(f"✓ Menu: {name} → {items}")
        except Exception as e:
            print(f"❌ Error reading {file.name}: {e}")
    return dict(menus)


# Define the directory containing snippets
snippets_dir = Path(__file__).parent / "snippets"

# Collect snippet data
snippet_data = collect_snippet_data(snippets_dir, verbose=args.verbose)


def render_manifest(template_name, context, output_file):
    template = env.get_template(template_name)
    rendered = template.render(context)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(rendered, encoding="utf-8")
    print(f"✅ Manifest written: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate manifests from tpl files and media folders"
    )
    parser.add_argument(
        "--media-root",
        default="snippets",
        help="Where to find snippets/ (default: snippets/)",
    )
    parser.add_argument(
        "--menu-dir", default="templates/menus", help="Where to find menu JSONs"
    )
    parser.add_argument(
        "--output-dir", default="manifest", help="Where to write manifest JSON files"
    )
    parser.add_argument(
        "--version",
        default=datetime.today().strftime("%Y.%m.%d"),
        help="Version string",
    )
    parser.add_argument("--verbose", action="store_true", help="Print debug info")
    args = parser.parse_args()

    # Collect Data
    snippet_data = collect_snippet_data(Path(args.media_root), verbose=args.verbose)
    menu_data = collect_menu_data(Path(args.menu_dir), verbose=args.verbose)

    context = {
        "version": args.version,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),  # "timestamp": datetime.now(timezone.utc).isoformat(),
        "platforms": snippet_data,
        "menus": menu_data,
    }

    # Hardcoded roles (you could load from roles.json, YAML, or DB later)
    role_data = {
        "superadmin": {
            "rank": 100,
            "can_manage": True,
            "can_edit": True,
            "label": "Platform Owner",
        },
        "admin": {
            "rank": 80,
            "can_manage": True,
            "can_edit": True,
            "label": "Site Admin",
        },
        "staff": {
            "rank": 60,
            "can_manage": False,
            "can_edit": True,
            "label": "Team Member",
        },
        "user": {
            "rank": 40,
            "can_manage": False,
            "can_edit": False,
            "label": "Subscriber",
        },
        "guest": {"rank": 0, "can_manage": False, "can_edit": False, "label": "Public"},
    }

    context["roles"] = role_data
    render_manifest("roles_manifest.tpl", context, Path(args.output_dir) / "roles.json")

    # === Features.json ===
    feature_data = {
        "edu_pro": ["record_video", "export_transcript", "dashboard"],
        "team": ["team_dashboard", "member_invite", "audit_log"],
        "lifetime": ["record_video", "dashboard"],
        "guest": [],
    }

    context["features"] = feature_data
    render_manifest(
        "features_manifest.tpl", context, Path(args.output_dir) / "features.json"
    )

    render_manifest("index_manifest.tpl", context, Path(args.output_dir) / "index.json")

    # Render using templates
    render_manifest(
        "snippets_manifest.tpl", context, Path(args.output_dir) / "snippets.json"
    )
    render_manifest("menu_manifest.tpl", context, Path(args.output_dir) / "menu.json")
    # Add bootstrap to the context
    context["bootstrap"] = bootstrap

    # Render using templates
    render_manifest("bootstrap_manifest.tpl", context, Path(args.output_dir) / "bootstrap.json")




if __name__ == "__main__":
    main()
