#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Generate an installable manifest from actual built archives; no invented checksums."""
import argparse,hashlib,json,pathlib,tarfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--wine",type=pathlib.Path,required=True)
p.add_argument("--helper",type=pathlib.Path,required=True)
p.add_argument("--release-url",required=True)
p.add_argument("--output",type=pathlib.Path,required=True)
a=p.parse_args()
if not a.release_url.startswith("https://github.com/himbeles/highball-engine-aoe4/releases/download/"):
    p.error("release URL must point to this fork's immutable tagged release")
m=json.loads((pathlib.Path(__file__).resolve().parent/"manifest-template.json").read_text())
for key,path in (("wine",a.wine),("aoe4-helper",a.helper)):
    with tarfile.open(path) as archive:
        names={n.removeprefix("./") for n in archive.getnames()}
    required=({"engine/bin/wine","engine/lib/wine/x86_64-unix/ntdll.so","engine/lib/wine/x86_64-windows/ntdll.dll"}
              if key=="wine" else {"aoe4/x87sidecar","aoe4/inputs.lock.json"})
    if not required.issubset(names):p.error("archive missing engine/helper files: "+str(required-names))
    c=m["components"][key]
    with path.open("rb") as f:c["sha256"]=hashlib.file_digest(f,"sha256").hexdigest()
    c["size"]=path.stat().st_size
    c["url"]=a.release_url.rstrip("/")+"/"+path.name
    if not c["size"]:p.error("archive is empty")
a.output.write_text(json.dumps(m,indent=2,ensure_ascii=False)+"\n")
print(a.output)
