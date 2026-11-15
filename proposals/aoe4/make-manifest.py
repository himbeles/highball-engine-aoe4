#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Generate an install manifest for downloaded trial artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--wine", type=Path, required=True)
parser.add_argument("--helper", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
manifest_path = Path(__file__).resolve().with_name("manifest-template.json")
manifest = json.loads(manifest_path.read_text())

components = (
    ("wine", args.wine, {
        "engine/bin/wine",
        "engine/lib/wine/x86_64-unix/ntdll.so",
        "engine/lib/wine/x86_64-windows/ntdll.dll",
    }),
    ("aoe4-helper", args.helper, {"aoe4/x87sidecar", "aoe4/inputs.lock.json"}),
)
for key, path, required in components:
    with tarfile.open(path) as archive:
        names = {member.name.removeprefix("./") for member in archive if member.isfile()}
    missing = required - names
    if missing:
        parser.error(f"{path} is missing {', '.join(sorted(missing))}")
    with path.open("rb") as archive:
        digest = hashlib.file_digest(archive, "sha256").hexdigest()
    manifest["components"][key].update(
        sha256=digest, size=path.stat().st_size, url=path.resolve().as_uri()
    )

args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
print(args.output)
