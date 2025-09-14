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
MANIFEST = Path(os.getenv("MANIFEST"))
SYSCONF = Path(os.getenv("SYSCONF"))
BUILDER = Path(os.getenv("BUILDER"))

# === Logging ===
log("Mount operation started")
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
env = Environment(loader=FileSystemLoader(TPLGET))

# === Render Function ===
def fstab_render(manifest_path: Path):
    data = json.loads(manifest_path.read_text())
    tpl = env.get_template("fstab.tpl")
    output = tpl.render(mounts=data.get("mounts", []))

    out_file = Path("/etc/fstab") if Path("/etc/faronix.prod").exists() else SYSCONF / "fstab.conf"

    if Path("/etc/fstab").exists() and out_file != Path("/etc/fstab"):
        with open("/etc/fstab", "r") as existing_fstab:
            existing_content = existing_fstab.read()
        with open(out_file, "w") as fstab_file:
            fstab_file.write(existing_content)
            fstab_file.write("\n# Appended from template\n")
            fstab_file.write(output.strip() + "\n")
    else:
        out_file.write_text(output.strip() + "\n")

    log(f"✅ Rendered fstab to: {out_file}")


def apply_fstab_from_manifest(manifest_path: Path):
    with open(manifest_path) as f:
        manifest = json.load(f)

    if manifest.get("kind") != "fstab":
        log("Invalid manifest kind. Expected 'fstab'", "ERROR")
        return

    for mount in manifest.get("mounts", []):
        src = mount["source"]
        tgt = mount["target"]
        readonly = "ro" in mount.get("options", "").replace(" ", "") or mount.get("readonly", False)

        if not Path(src).exists():
            log(f"Source does not exist: {src}", "ERROR")
            continue

        Path(tgt).mkdir(parents=True, exist_ok=True)
        log(f"Ensured target directory exists: {tgt}")

        cmd = ["sudo", "mount", "--bind", src, tgt]
        try:
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                log(f"✅ Mounted: {src} → {tgt}")
            else:
                log(f"❌ Failed to mount: {src} → {tgt}\n{result.stderr.decode()}", "ERROR")
                continue
        except Exception as e:
            log(f"Exception during mount: {e}", "ERROR")
            continue

        if readonly:
            ro_cmd = ["sudo", "mount", "-o", "remount,ro", tgt]
            try:
                ro_result = subprocess.run(ro_cmd, capture_output=True)
                if ro_result.returncode == 0:
                    log(f"🔒 Remounted read-only: {tgt}")
                else:
                    log(f"⚠️ Failed to remount read-only: {tgt}\n{ro_result.stderr.decode()}", "WARNING")
            except Exception as e:
                log(f"Exception during remount: {e}", "WARNING")



# # === Entrypoint ===
if __name__ == "__main__":
    fstab_render(service_manifest)
