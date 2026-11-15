#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Generate an install manifest for local archives or a tagged GitHub release."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
from urllib.parse import quote

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--wine", type=Path, required=True)
parser.add_argument("--helper", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--release-url", help="GitHub asset base URL for a specific release tag")
args = parser.parse_args()
release_url = args.release_url.rstrip("/") if args.release_url else None
if release_url and not re.fullmatch(
    r"https://github\.com/[\w.-]+/[\w.-]+/releases/download/[\w.%+-]+", release_url, re.ASCII
):
    parser.error("--release-url must point to the assets of a tagged GitHub release")
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
    url = f"{release_url}/{quote(path.name)}" if release_url else path.resolve().as_uri()
    manifest["components"][key].update(sha256=digest, size=path.stat().st_size, url=url)

args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
print(args.output)
