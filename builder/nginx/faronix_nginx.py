import os
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] ))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))

import subprocess

from jinja2 import Environment, FileSystemLoader
import json

from dotenv import load_dotenv # type: ignore


# === Bootstrap Environment ===
load_dotenv()

# Add scripts to path for `fenv()` + logging


from environmentloading import fenv  # type: ignore
from faronix_logger import log  # type: ignore # Make sure this is implemented correctly
fenv()  # Set os.environ variables from env/.manifestrc


ROOT = Path(os.getenv('FARONIX_ROOT'))
# Load required paths
MANIFEST = Path(ROOT, "manifest" )
BUILDER = Path(ROOT, "builder", "nginx")
SYSCONF = Path(ROOT, "sysconf" )

# === Logging ===
log("Nginx operation started")
if not SYSCONF.exists():
    log("Missing env variable or path: SYSCONF", "WARNING")
if not MANIFEST.exists():
    log("Manifest directory does not exist", "ERROR")

# === Resolve Manifest Filename ===
THIS = Path(__file__).resolve().parent.name
service_manifest = BUILDER / THIS / ".manifestrc"
TPLGET = Path(__file__).resolve().parent / "tpl"

# === Load Manifest ===
if not service_manifest.exists():
    log(f"Manifest file not found: {service_manifest}", "ERROR")
    sys.exit(1)

    with service_manifest.open(encoding="utf-8") as f:
        manifest = json.load(f)

# === Setup Jinja2 ===

env = Environment(loader=FileSystemLoader(str(TPLGET)))

def nginx_generator(manifest_path: Path):
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    if data.get("kind") != "nginx":
        log("Invalid manifest kind: expected 'nginx'", "ERROR")
        return
    if data.get("template_type") == "django":
        template_type = str("django")
        domain = data.get("server_name")
        tpl_name = f"{template_type}.tpl"
        tpl = env.get_template(tpl_name)
    
        nameconf = Path(f"/etc/nginx/sites-available/{domain}.conf")
        site = data.get("sites", {})
        output = tpl.render(site=site)
        target = nameconf

    Path(target).write_text(output.strip() + "\n")
    log(f"✅ NGINX config rendered: {target}")

if __name__ == "__main__":
    if not service_manifest.exists():
        log(f"Manifest file not found: {service_manifest}", "ERROR")
        sys.exit(1)

    nginx_generator(service_manifest)



# # === Entrypoint ===
if __name__ == "__main__":
    nginx_generator(service_manifest)
