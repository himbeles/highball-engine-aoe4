#!/usr/bin/env python3
"""Verify the source archive, extract Wine, apply the pinned series and proposal."""
import hashlib, json, pathlib, subprocess, sys
here = pathlib.Path(__file__).resolve().parent
repo = here.parents[1]
if len(sys.argv) != 3:
    sys.exit("usage: prepare-source.py /path/to/crossover-sources.tar.gz /new/work-directory")
archive, work = map(lambda value: pathlib.Path(value).resolve(), sys.argv[1:])
lock = json.loads((here / "inputs.lock.json").read_text())
expected = lock["wine_source"]
def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
if archive.stat().st_size != expected["size"] or sha256(archive) != expected["sha256"]:
    sys.exit("Source archive checksum/size mismatch")
patches = {str(path.relative_to(repo)): sha256(path) for path in (repo / "patches").glob("*.patch")}
if patches != lock["highball_patches_sha256"]:
    sys.exit("Highball patch series differs from the proposal's pinned baseline")
if work.exists():
    sys.exit("Work directory must not exist")
work.mkdir(parents=True)
subprocess.run(["tar", "-xzf", str(archive), "-C", str(work), expected["subdir"]], check=True)
source = work / expected["subdir"]
for name in sorted(patches):
    with (repo / name).open("rb") as stream:
        subprocess.run(["patch", "--batch", "-p1"], cwd=source, stdin=stream, check=True)
subprocess.run([sys.executable, str(here / "apply.py"), str(source)], check=True)
print("Patched Wine source:", source)
