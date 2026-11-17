#!/usr/bin/env python3
"""Apply only to the pinned Wine source after Highball's default patch series."""
import hashlib, json, os, pathlib, subprocess, sys
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
# Keep Git from discovering the enclosing Actions checkout when Wine is extracted under src/.
env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(source.parent)}
for patch in sorted((here / "patches").glob("*.patch")):
    subprocess.run(["git", "apply", "--check", str(patch)], cwd=source, env=env, check=True)
    subprocess.run(["git", "apply", str(patch)], cwd=source, env=env, check=True)
if not (source / "dlls/ntdll/unix/aoe_ring_discovery.h").is_file():
    sys.exit("AoE IV patch did not create its ring discovery source")
print("Applied opt-in AoE IV proposal. Default engine patch series was not changed.")
