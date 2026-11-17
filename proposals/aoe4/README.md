# Age of Empires IV on Rosetta

This engine combines the existing Rosetta cooperative x87 attach path with an AoE IV software-fault
decoder and a generated-code cache. It targets the x86-64 Wine 11 line and activates for
`RelicCardinal.exe` through its own engine manifest.

Wine checks the executable's PE layout before attaching the arm64 helper. The cache first looks
for a profile matching the executable's SHA-256. Otherwise it finds the ring pointer by matching
the allocator and slot writer in `.text`. Both must refer to the same unique, aligned location
in writable `.data`. The discovered pointer must also lead to a 16 MiB executable allocation
before the cache handles any 32-byte slots. Inconclusive discovery leaves the combined decoder
active with caching off. An unsupported image layout uses the stock Wine launch. Cache entries
retain the original game PC for exception reporting and refuse unsupported fragments.

The engine includes measured profiles for 16.3.11308.0 and 17.0.12303.0. The latter has been
tested in one solo skirmish. See [validation](VALIDATION.md) for the hardware, build, matched
comparisons and open checks.

## Changes in r3

r3 retains r2's relocated-instruction cache and adds a thread-local cache of validated
memory-page permissions. Most instruction lookups no longer acquire Wine's VM lock or
search its mapping tree. They still reread the live ring pointer and instruction bytes.
A VM generation changes around mapping/protection operations; a changed generation,
changed pointer, different page or failed copy falls back to the locked reader. Normal
resumes outside the ring preserve the useful page snapshot.

A private no-fault copy recovers only faults at its own load instruction, before Wine
consumes a Windows guard page. The optimization is limited to the AoE executable on
Darwin x86-64; the existing executable verification and ring discovery still gate use.
Steam and other executables do not enable VM generation tracking.

Three same-process Late Siege comparisons reduced P99 frame intervals from 75–83 ms
to 42 ms, with about 50 ms-or-longer frames falling from 40–41 to 4–7 per 20-second
window. Average FPS rose from 36.6–37.0 to 38.7–39.2. This does not eliminate every
stutter. See [r3 measurements and limitations](VALIDATION.md#r3-validated-page-cache).

## Changes in r2

- Wine reads the ring pointer and checks and copies the active fragment under one virtual
  memory lock. It checks the pointer and fragment again before accepting the copy.
- A thread-local lookup reuses already-relocated code across ring slots when the instruction
  prefix and absolute near-jump destination match. A miss uses the existing decoder and
  shared cache. Exception addresses continue to refer to the current game slot.
- The Wine changes are gated to the recognized AoE IV process, with the existing profile and
  auto-discovery checks.

In one matched 25-second Late Siege village capture, displayed FPS rose from 44.4 to 49.7
and the 99th-percentile frame interval fell from 166.7 ms to 108.3 ms. Periodic stalls still
occurred. See the [Late Siege measurements](VALIDATION.md#late-siege-frame-pacing).

## Install r3

Download `aoe4-engine.json` from the [r3 release](https://github.com/himbeles/highball-engine-aoe4/releases/tag/aoe4-r3).
Highball downloads and verifies the engine and helper from that manifest. Accept Apple's Game
Porting Toolkit license to enable D3DMetal.

```bash
highball engine install /path/to/aoe4-engine.json --accept-d3dmetal-license
highball bottle create AoE4 --engine x64-crossover26.3-aoe4-r3 --renderer d3dmetal
```

Install Steam and AoE IV in that bottle. In the Highball app, use **Open Steam** to browse
the Library and **Play** on the game's Highball page to launch with the bottle's D3DMetal renderer.
From the CLI, use `highball run --renderer dxmt AoE4 Steam` to open Steam's Library and
`highball play steam:1466860` to use the game's Highball **Play** action. The Steam shortcut
forces Wine synchronization off for Steam's Library. On a clean launch, **Play** uses the
game's renderer and the bottle's synchronization setting. If the bottle uses MSync, check the launch log for
`sync=msync`. The graphics driver check may display a modal because Wine presents an AMD
compatibility adapter. Acknowledge it to continue.
Check the Highball log for `AoE4 cache profile accepted` or `discovered ring allocation accepted`.
Use the bottle's counter directory to confirm that the game actually hit the cache.

```bash
python3 proposals/aoe4/cache-stats.py /path/to/bottle/aoe4-counters --require-active
```

For a cache-only comparison, stop the bottle and set `AOE4_CACHE=0` with
`highball bottle set AoE4 env AOE4_CACHE=0`. Use an empty value to restore the cache and start
a new game process. `AOE4_X87=0` selects the software-fault decoder alone.
`AOE4_DISABLED=1` bypasses the AoE IV hooks.

To compare only r3’s memory-page optimization with the r2 reader, set
`AOE4_DISABLE_VM_CACHE=1` and restart the game. Remove that environment variable
entirely to restore r3 (even an empty value disables this optimization).

## Build the engine

The r3 release rebuilds the x86-64 Wine Unix ntdll from the source used in the Late Siege
captures with a macOS 14 deployment target. It packages that module with the r2 engine
and helper binaries. The release includes the matching Wine patches, the pinned sources
and checksums. See `build-provenance.txt` among its assets for the base release, build
details and module digest.

To build the source in GitHub Actions, dispatch `build-engine` with `aoe4=true`.
The job verifies the pinned Wine source and patches,
builds the Intel engine and signed arm64 helper, and uploads the engine, helper and corresponding
source archives with checksums. Set `publish_release=true` to publish those archives and the
install manifest under a tag. Update the manifest engine revision before shipping a new version.

For local Actions downloads, use Python 3.11 or newer to generate a manifest from the extracted
archives.

```bash
python3 proposals/aoe4/make-manifest.py \
  --wine /path/to/engine-archive.tar.gz --helper /path/to/aoe4-helper.tar.gz \
  --output /path/to/aoe4-engine.json
```

## Verify the sources locally

```bash
python3 proposals/aoe4/prepare-source.py /path/to/crossover-sources-26.3.0.tar.gz /new/work-dir
proposals/aoe4/tests/run.sh /new/work-dir/sources/wine
python3 proposals/aoe4/tests/test_tools.py
```

The executable cache and relocator tests run on x86-64. On Apple Silicon, run the test
script under Rosetta with `arch -x86_64 /bin/bash`. The macOS build uses
`build-sidecar.sh` to validate and build the pinned arm64 helper with Xcode and CMake.

After an update, check the discovery and cache counters first. If the allocator or slot writer
changed, inspect the live ring and confirm the pointer location, allocation bounds, slot size,
wrap and cleanup before generating a profile with `profile.py`. Diagnostic scans with
`AOE4_CACHE_DIAGNOSTICS=1` print candidates for inspection. Refresh the source lock when rebasing
to a different Wine patch series.

## Provenance

The LGPL Wine thunks and cache derive from [Marc Ibrahim's Wine source as mirrored by
NerRobDog](https://github.com/NerRobDog/wine-aoe4/tree/711c6fc7559a565c417aab4d52d84b09767a9c1d).
The MIT helper comes from [NerRobDog's x87sidecar, based on athei and
Lifeisawful](https://github.com/NerRobDog/x87sidecar/tree/c407ddfabbbe6bc5f5d56a258a4866ac89b04d8e).
The decoder composition, GS fallback and FBLD fixes are [MIT-distributed MacGames
patches](https://github.com/tarikbc/macgames/tree/1579841b15ce569807b92af95b478c752c26df3d/patches/x87sidecar).
The source commits, patch digests and archive hash are recorded in [inputs.lock.json](inputs.lock.json).
The HDE and helper licence notices accompany the respective artifacts.
