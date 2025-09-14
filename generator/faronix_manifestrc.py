# generator/sync_manifestrc.py

from pathlib import Path
import shutil
from .._scripts._config import BUILDER, MANIFEST, SYSCONF



for subdir in BUILDER.iterdir():
    if not subdir.is_dir():
        continue

    manifest_path = subdir / ".manifestrc"
    if manifest_path.exists():
        dest_file = MANIFEST / f"{subdir.name}.manifestrc"
        shutil.copy2(manifest_path, dest_file)
        print(f"✅ Copied: {manifest_path} → {dest_file}")
    else:
        print(f"⚠️ No manifest found in {subdir.name}")
