#!/usr/bin/env python3
"""Apply only to the pinned Wine source after Highball's default patch series."""
import hashlib, json, pathlib, subprocess, sys
here = pathlib.Path(__file__).resolve().parent
if len(sys.argv) != 2:
    sys.exit("usage: apply.py /path/to/wine (after default patches)")
source = pathlib.Path(sys.argv[1]).resolve()
lock = json.loads((here / "inputs.lock.json").read_text())
for name, expected in lock["post_highball_preimages_sha256"].items():
    path = source / name
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    if actual != expected or (expected is None and path.exists()):
        sys.exit("Refusing different/already patched source: " + name)
patch = here / "patches/0017-aoe4-rosetta-softfault-cache.patch"
subprocess.run(["git", "apply", "--check", str(patch)], cwd=source, check=True)
subprocess.run(["git", "apply", str(patch)], cwd=source, check=True)
print("Applied opt-in AoE IV proposal. Default engine patch series was not changed.")
