# generator/fstab_render.py

import sys
from pathlib import Path
from dotenv import load_dotenv # type: ignore

import os
import subprocess
import argparse


load_dotenv()


from environmentloading import fenv # type: ignore
fenv()
from faronix_logger import log  # type: ignore # Make sure this is implemented correctly

def log(msg, level="INFO"):
    print(f"[{level}] {msg}")

log("Faronix control started")

from builder.nginx.faronix_nginx import nginx_generator
from builder.fstab.faronix_fstab import fstab_render, apply_fstab_from_manifest

# Load required paths
MANIFEST =  Path(os.getenv('MANIFEST'))
SYSCONF = Path(os.getenv('SYSCONF'))
BUILDER = Path(os.getenv('BUILDER'))


def run_script(path: Path, args=[]):
    if not path.exists():
        log(f"Script not found: {path}", "ERROR")
        sys.exit(1)
    subprocess.run([sys.executable, str(path)] + args)

def handle_fstab(args):
    if args.action == "apply":
        run_script(BUILDER / "fstab"/ "faronix_fstab.py")
    elif args.action == "status":
        subprocess.run(["systemctl", "status", "-t", "mount"])
    elif args.action == "render":
        fstab_render(BUILDER / "fstab" / ".manifestrc")
    elif args.action == "mount":
        apply_fstab_from_manifest(BUILDER / "fstab" / ".manifestrc")
    else:
        log(f"Unknown fstab action: {args.action}", "ERROR")
        

def handle_nginx(args):
    if args.action == "render":
        run_script(BUILDER / "nginx" / "faronix_nginx.py")
    elif args.action == "status":
        subprocess.run([ "sudo", "nginx", "-t"])
    elif args.action == "reload":
        subprocess.run([ "sudo", "systemctl", "reload", "nginx"])
    elif args.action == "django":
        nginx_generator(BUILDER / "nginx" / ".manifestrc")
    else:
        log(f"Unknown nginx action: {args.action}", "ERROR")



def handle_systemd(args):
    if args.action == "generate":
        run_script(BUILDER / "systemd" / "faronix_systemd.py")
    elif args.action == "status":
        subprocess.run(["systemctl", "list-units", "--type=service", "--all"])
    else:
        log(f"Unknown systemd action: {args.action}", "ERROR")

def handle_manifest(args):
    if args.action == "list":
        for f in sorted(MANIFEST.glob("*.manifestrc")):
            print(f"- {f.name}")
    elif args.action == "show":
        target = MANIFEST / args.name
        if not target.exists():
            log(f"Manifest not found: {args.name}", "ERROR")
        else:
            print(target.read_text())
    else:
        log(f"Unknown manifest action: {args.action}", "ERROR")

def main():
    parser = argparse.ArgumentParser(description="Faronix CLI Control")
    subparsers = parser.add_subparsers(dest="category")

    # fstab
    p_fstab = subparsers.add_parser("fstab", help="Fstab mount tools")
    p_fstab.add_argument("action", choices=["apply", "status", "render", "mount"])  # ← added 'render'
    p_fstab.set_defaults(func=handle_fstab)


    p_nginx = subparsers.add_parser("nginx", help="NGINX control")
    p_nginx.add_argument("action", choices=["render", "test", "reload", "django", "php" ])
    p_nginx.set_defaults(func=handle_nginx)


    # systemd
    p_systemd = subparsers.add_parser("systemd", help="Systemd unit generation")
    p_systemd.add_argument("action", choices=["generate", "status"])
    p_systemd.set_defaults(func=handle_systemd)

    # manifest
    p_manifest = subparsers.add_parser("manifest", help="Manifest utilities")
    p_manifest.add_argument("action", choices=["list", "show"])
    p_manifest.add_argument("name", nargs="?", help="Manifest name (for show)")
    p_manifest.set_defaults(func=handle_manifest)

    # Parse
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
