#!/usr/bin/env python3
"""Publish a versioned manifest for the fork's matching Wine and helper releases."""

import argparse
from base64 import b64decode
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote

STAMP = r"\d{8}T\d{6}Z"
WINE_TAG = re.compile(rf"engine-wine-11\.0-{STAMP}-aoe4-(r[1-9]\d*)")


def gh(*args):
    return subprocess.check_output(["gh", *args])


def api(repo, path):
    return json.loads(gh("api", f"repos/{repo}/{path}"))


def release_commit(repo, tag):
    ref = api(repo, "git/ref/tags/" + quote(tag, safe=""))["object"]
    if ref["type"] != "commit":
        raise ValueError(f"{tag} must point directly to a commit")
    return ref["sha"]


def newest(releases):
    return max(releases, key=lambda r: (r["published_at"], r["tag_name"]), default=None)


def archive_metadata(repo, release, extension):
    tag = release["tag_name"]
    name = tag + extension
    assets = {a["name"]: a for a in release["assets"] if a["state"] == "uploaded"}
    archive = assets[name]
    recorded_hash, recorded_name = gh(
        "release", "download", tag, "-R", repo, "--pattern", name + ".sha256", "--output", "-"
    ).decode("ascii").split()
    if (recorded_name.lstrip("*") != name or
            not re.fullmatch(r"[0-9a-f]{64}", recorded_hash) or
            archive.get("digest") != f"sha256:{recorded_hash}" or archive["size"] <= 0):
        raise ValueError(f"Archive and checksum metadata disagree for {name}")
    return {"url": archive["browser_download_url"], "sha256": recorded_hash, "size": archive["size"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Write the manifest locally")
    parser.add_argument("--output", type=Path, default=Path.cwd(), help="Output directory")
    args = parser.parse_args()

    repo = os.environ["GITHUB_REPOSITORY"]
    sha = os.environ["BUILD_COMMIT"]
    requested = os.environ.get("WINE_TAG", "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        parser.error("BUILD_COMMIT must be a full commit SHA")
    if requested and not WINE_TAG.fullmatch(requested):
        parser.error("WINE_TAG must be a timestamped AoE IV Wine release tag")
    pages = json.loads(gh("api", "--paginate", "--slurp", f"repos/{repo}/releases?per_page=100"))
    releases = [release for page in pages for release in page]
    eligible = [r for r in releases if r.get("published_at") and not r["draft"] and
                not r["prerelease"] and r["target_commitish"] == sha]
    wine = newest(r for r in eligible if WINE_TAG.fullmatch(r["tag_name"]) and
                  (not requested or r["tag_name"] == requested))
    if not wine:
        if os.environ.get("GITHUB_EVENT_NAME") == "workflow_run":
            print(f"Waiting for an AoE IV Wine release at {sha}")
            return
        raise ValueError(f"No matching AoE IV Wine release at {sha}")

    version = WINE_TAG.fullmatch(wine["tag_name"])[1]
    tag = "aoe4-" + version
    filename = f"aoe4-engine-{version}.json"
    existing = next((r for r in releases if r["tag_name"] == tag), None)
    if existing and not args.dry_run:
        if (existing["draft"] or release_commit(repo, tag) != sha or
                not any(a["name"] == filename and a["state"] == "uploaded" for a in existing["assets"])):
            raise ValueError(f"Conflicting or incomplete manifest release {tag}")
        print(f"Already published at {existing['html_url']}")
        return

    inputs = json.loads(b64decode(api(repo, f"contents/inputs.json?ref={sha}")["content"]))
    if not inputs["wine"]["name"].startswith("CrossOver 26.3."):
        raise ValueError("This install template is for CrossOver 26.3 Wine 11")
    pin = inputs["x87sidecar"]
    helper_tag = re.compile(rf"x87sidecar-{re.escape(pin['tag'])}-{STAMP}")
    helper = newest(r for r in eligible if helper_tag.fullmatch(r["tag_name"]))
    if not helper:
        if os.environ.get("GITHUB_EVENT_NAME") == "workflow_run":
            print(f"Waiting for a shared x87sidecar release at {sha}")
            return
        raise ValueError(f"No matching shared x87sidecar release at {sha}")

    for release in (wine, helper):
        if release_commit(repo, release["tag_name"]) != sha:
            raise ValueError(f"Source commit mismatch for {release['tag_name']}")
    template = Path(__file__).with_name("release-manifest-template.json")
    manifest = json.loads(template.read_text(encoding="utf-8"))
    manifest.update(id=f"x64-crossover26.3-aoe4-{version}",
                    displayName=f"Wine 11 — Age of Empires IV {version}")
    manifest["components"]["wine"].update(archive_metadata(repo, wine, ".tar.gz"),
                                        version=f"Wine 11.0 (CrossOver 26.3), AoE IV {version}")
    manifest["components"]["x87sidecar"].update(archive_metadata(repo, helper, ".tar.xz"),
                                               version=pin["commit"][:8] + " with Highball patch 0003")
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / filename
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.dry_run:
        print(path)
        return
    notes = (
        f"Highball install manifest for Age of Empires IV {version}. "
        f"It pins the Wine and x87sidecar archives built from `{sha[:8]}`.\n\n"
        f"[Wine release]({wine['html_url']}) · [Shared x87sidecar release]({helper['html_url']})\n"
    )
    published_versions = [
        int(match[1]) for release in releases if release.get("published_at") and not release["draft"]
        if (match := re.fullmatch(r"aoe4-r([1-9]\d*)", release["tag_name"]))
    ]
    latest = int(version[1:]) > max(published_versions, default=0)
    with tempfile.TemporaryDirectory() as directory:
        notes_file = Path(directory) / "notes.md"
        notes_file.write_text(notes, encoding="utf-8")
        result = gh("release", "create", tag, str(path), "-R", repo, "--target", sha,
                    "--title", f"Age of Empires IV {version} install manifest",
                    "--notes-file", str(notes_file), f"--latest={str(latest).lower()}")
    print(result.decode().strip())


if __name__ == "__main__":
    main()
