# Experimental AoE IV engine proposal

This is a reviewable port of the recovered GameToMac Wine softfault bridge and immutable code
cache to Highball's Wine 11 engine. It is **not yet a verified Highball game fix**. The proposal
lives outside `patches/`, so the existing workflow and normal engine builds do not apply it.
No app manifest or game recipe changes are included. No issue, PR, release or workflow run has
been submitted.

Baseline: [highball-engine](https://github.com/gauthierpiarrette/highball-engine) commit
`5a7a000bbe468323d96bdaf9ec5edf24de15e10c`, CrossOver 26.3.0 source archive, and patches
0001–0016. [inputs.lock.json](inputs.lock.json) pins the source, existing patch hashes, helper
commit, executable digest and the Wine files this proposal changes.

## What changes

- Two x64 ntdll thunks deliver software illegal-instruction exceptions while preserving integer,
  floating-point and AVX context. A bridge at `0x180000000` exposes those thunks to the decoder.
- The AoE-aware native arm64 x87sidecar decoder recognizes the recovered game's fault range and
  redirects it to that bridge. Highball's existing i386 sidecar launch is insufficient: this is
  a separate x64 game launch using the existing cooperative Mach protocol.
- An opt-in cache deduplicates relocatable fragments in the game's generated-code ring without
  modifying the game's original bytes. Signal context reports map cached PCs back to game PCs;
  unsupported instructions, branches and relocation overflow fall back to the original fragment.
- Eligibility requires Rosetta on macOS 26 or later, the exact executable SHA256, an AMD64 image
  mapped at `0x140000000`, and an explicitly enabled profile. The digest is computed from the
  descriptor Wine subsequently uses for `SEC_IMAGE`, rather than reopening a path.
- The game attach happens after ntdll and the bridge are mapped. Missing helper, missing or stale
  bootstrap, failed attach and empty hook ranges fail closed. The AoE receive has a 30-second
  timeout. Non-game children discard the private bridge profile they inherited.

The recovered addresses are tied to **one build** of `RelicCardinal.exe`, Steam app 1466860:

```
5380c577805565817f528af6eac385263413fa6815553f9a31fa62561cb45e8c
```

An updated game with a different digest is refused. Updating this digest alone would be wrong:
the fault range, ring pointer and fragment layout must also be checked. Cache-only mode is a
diagnostic configuration; it does not supply the decoder fix that the softfault profile supplies.

## Source and licence provenance

The public sources used here are NerRobDog's mirrors, **not a claimed public GameToMac repository**:

- [wine-aoe4 at 711c6fc](https://github.com/NerRobDog/wine-aoe4/tree/711c6fc7559a565c417aab4d52d84b09767a9c1d):
  recovered Wine changes credited to Marc Ibrahim, plus NerRobDog's near-Jcc relocator and
  diagnostic extensions. Wine modifications are LGPL-2.1-or-later, as required by this repository.
- [x87sidecar at c407ddf](https://github.com/NerRobDog/x87sidecar/tree/c407ddfabbbe6bc5f5d56a258a4866ac89b04d8e):
  the matching softfault decoder, based on athei's sidecar and Lifeisawful's original work, MIT.
  `rosetta_loader/src/stub_asm.cpp` contains `buildSoftFaultHook` and the `AOE_SOFTFAULT_*` gates.
- HDE is Vyacheslav Patkov's BSD disassembler. Its full licence is retained in the imported
  headers and [Licenses/HDE-LICENSE.txt](Licenses/HDE-LICENSE.txt). The helper's MIT notice is
  copied to [Licenses/x87sidecar-MIT.txt](Licenses/x87sidecar-MIT.txt).

The CodeWeavers source archive's size and SHA256 were independently verified against Highball's
pin. The mirrors' claims about the original GameToMac archive were not independently verified
against an original vendor download. The helper is built from pinned source; no GameToMac
prebuilt helper or bundled graphics binary is redistributed here.

## Reproduce source preparation and tests

Requirements: Python 3, Git, `tar`, `patch`, a C compiler; Linux also needs OpenSSL development
headers and libcrypto. Use a new work directory. From the repository root:

```bash
curl --fail --location --output crossover-sources.tar.gz \
  https://media.codeweavers.com/pub/crossover/source/crossover-sources-26.3.0.tar.gz
python3 proposals/aoe4/prepare-source.py crossover-sources.tar.gz /absolute/new/aoe-work
proposals/aoe4/tests/run.sh /absolute/new/aoe-work/sources/wine
```

Preparation verifies the archive's size and SHA256 and the complete default patch series before
extraction. It applies that series, verifies each changed Wine file's preimage, checks the
proposal with `git apply --check`, then applies it. Changed/already-patched sources are refused.
For a tree with the default series already applied, use `proposals/aoe4/apply.py` directly.
Tests include executable-name and descriptor-hash guards, PID bootstrap matching, relocation
correctness/refusal and execution of a deduplicated x86_64 fragment. On an arm64 shell, the last
test is skipped; run it under Rosetta with an x86_64 compiler to cover it.

See [VALIDATION.md](VALIDATION.md) for checks actually performed and the remaining acceptance work.

## Build and launch for a local macOS trial

Build Wine from the prepared source with the configure flags/toolchain in
[the existing workflow](../../.github/workflows/build.yml). Its Unix half remains x86_64;
its PE halves remain i386 and x86_64. This proposal does not alter or dispatch the workflow.
To trial it in a fork's CI later, add `python3 proposals/aoe4/apply.py src/sources/wine` immediately
after the default patch step on a separate build branch and leave `publish_release=false`.
The workflow's existing artifact alone does not contain the helper; build that separately.

Build the native arm64 helper on macOS with Xcode tools and CMake >=3.27:

```bash
proposals/aoe4/build-sidecar.sh /absolute/new/helper-work
/absolute/new/helper-work/build/bin/x87sidecar --probe
```

`--probe` validates the installed Rosetta layout; it does not prove AoE gameplay works. Use a
copy of a test bottle and the newly built engine, then check `shasum -a 256 RelicCardinal.exe`.
With paths adjusted to your installation, run from the game's directory:

```bash
export WINEPREFIX=/absolute/path/to/test-bottle
export WINELOADER=/absolute/path/to/trial-engine/bin/wine
export WINESERVER=/absolute/path/to/trial-engine/bin/wineserver
export AOELAB_SIDECAR_PATH=/absolute/new/helper-work/build/bin/x87sidecar
export AOELAB_SOFTFAULT_GAME=1
export AOELAB_CODE_CACHE_GAME=1
"$WINELOADER" ./RelicCardinal.exe
```

Steam-launched trials need these values in Steam's launch environment so the game child inherits
them. Keep engine, ntdll and wineserver from the same trial build. Flags are presence-based:
`AOELAB_SOFTFAULT_GAME=0` still enables it; **unset** the flags for baseline comparisons.
Do not set the private `AOELAB_SOFTFAULT_BRIDGE`, `AOE_SOFTFAULT_*` or bootstrap variables yourself.
A matching helper is required; the existing generic x87 helper cannot substitute for it.

## Before proposing upstream adoption

Follow [patches/README.md](../../patches/README.md): keep the patch header's verification and
upstream-status fields truthful, then record game digest/version, chip, macOS, engine identifier,
date and measured results after a real trial. [Highball's contribution guide](https://github.com/gauthierpiarrette/highball/blob/4db5d5caf43acd54ec340d940f6b275b3f94ce7c/CONTRIBUTING.md)
places Wine patches here; application manifests require measured size, SHA256 and an independently
verified checksum note, while game recipes belong in highball-db.

After acceptance testing, decide helper packaging/signing and pin its actual artifact checksum,
then add a separate opt-in engine manifest and game recipe. Those changes need their own review.
The proposal does not port the graphics/shader/launcher adjustments in GameToMac's complete pack,
and its handshake has no protocol status proving that a particular decoder profile was installed.
A full game trial is required before calling this a working replacement for that pack.
