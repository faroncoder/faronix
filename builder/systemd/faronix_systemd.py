import os
from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parent.parent

from jinja2 import Environment, FileSystemLoader
# env = Environment(loader=FileSystemLoader( Path(__file__).resolve().parent / ".env" ))

# IS_PRODUCTION = Path("/etc/faronix.prod").exists()
# if IS_PRODUCTION:
#     OUTPUT_DIR = Path("/etc/systemd/system")
# else:
#     OUTPUT_DIR = SYSCONF

# builder/faronix_systemd.py

import json
import argparse
from pathlib import Path
import subprocess
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent / "tpl"
TEMPLATE_ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

DEFAULT_OUTPUT = Path("sysconf")

def load_manifest(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def render(template_name: str, context: dict) -> str:
    template = TEMPLATE_ENV.get_template(template_name)
    return template.render(context)

def write_unit(name: str, content: str, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / name
    dest.write_text(content, encoding="utf-8")
    print(f"✅ Wrote: {dest}")
    return dest

def install_unit(source: Path, user=False):
    target_dir = Path.home() / ".config/systemd/user" if user else Path("/etc/systemd/system")
    target_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", str(source), str(target_dir / source.name)], check=True)
    print(f"📦 Installed: {source.name} → {target_dir}")

def reload_daemon(user=False):
    cmd = ["systemctl", "--user", "daemon-reexec"] if user else ["systemctl", "daemon-reexec"]
    subprocess.run(cmd, check=True)

def enable_start(name: str, user=False):
    base = ["systemctl", "--user"] if user else ["systemctl"]
    subprocess.run(base + ["enable", name], check=True)
    subprocess.run(base + ["start", name], check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="Path to .manifestrc")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT, help="Where to write unit files")
    parser.add_argument("--install", action="store_true", help="Install to systemd dir")
    parser.add_argument("--enable", action="store_true", help="Enable the service")
    parser.add_argument("--start", action="store_true", help="Start the service")
    parser.add_argument("--user", action="store_true", help="Use user mode instead of system")
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest))
    systemd = manifest.get("systemd", {})

    service_name = systemd.get("service_name", "faronix-runtime.service")
    context = {
        "description": systemd.get("description", "Faronix Runtime"),
        "working_dir": systemd.get("working_directory", str(Path.cwd())),
        "exec_start": systemd.get("exec_start", "/usr/bin/python manage.py runserver"),
        "restart": systemd.get("restart", "on-failure"),
    }

    rendered_service = render("tpl/faronix.service.tpl", context)
    service_path = write_unit(service_name, rendered_service, Path(args.output_dir))

    if "watch_files" in systemd:
        context["path"] = systemd["watch_files"]
        rendered_path = render("tpl/faronix.path.tpl", context)
        path_unit = service_name.replace(".service", ".path")
        write_unit(path_unit, rendered_path, Path(args.output_dir))

    if args.install:
        install_unit(service_path, user=args.user)
        if "watch_files" in systemd:
            install_unit(Path(args.output_dir) / path_unit, user=args.user)
        reload_daemon(user=args.user)

    if args.enable:
        enable_start(service_name, user=args.user)

if __name__ == "__main__":
    main()
