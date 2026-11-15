# Age of Empires IV on Rosetta

This trial combines the existing Rosetta cooperative x87 attach path with an AoE IV software-fault
decoder and a generated-code cache. It targets the x86-64 Wine 11 line and activates for
`RelicCardinal.exe` through a separate trial engine manifest.

Wine checks the executable's PE layout before attaching the arm64 helper. The cache first looks
for a profile matching the executable's SHA-256. Otherwise it finds the ring pointer by matching
the allocator and slot writer in `.text`. Both must refer to the same unique, aligned location
in writable `.data`. The discovered pointer must also lead to a 16 MiB executable allocation
before the cache handles any 32-byte slots. Inconclusive discovery leaves the combined decoder
active with caching off. An unsupported image layout uses the stock Wine launch. Cache entries
retain the original game PC for exception reporting and refuse unsupported fragments.

The trial includes measured profiles for 16.3.11308.0 and 17.0.12303.0. The latter has been
tested in one solo skirmish. See [validation](VALIDATION.md) for the hardware, build, matched
comparisons and open checks.

## Build and install a trial

Dispatch `build-engine` with `aoe4_trial=true` and `publish_release=false`. The run verifies the
locked Wine archive and patch series, builds the Intel engine and signed arm64 helper, and uploads
the engine, helper and corresponding-source archives with checksums. Download and extract the
Actions artifact, verify the three archive checksums, and use Python 3.11 or newer to generate
a local manifest pointing to those archives.

```bash
python3 proposals/aoe4/make-manifest.py \
  --wine /path/to/engine-archive.tar.gz --helper /path/to/aoe4-helper.tar.gz \
  --output /path/to/aoe4-trial.json
highball engine install /path/to/aoe4-trial.json --accept-d3dmetal-license
highball bottle create AoE4 --engine x64-crossover26.3-aoe4-r1 --renderer d3dmetal
```

Install Steam and AoE IV in the trial bottle. In the Highball app, use **Open Steam** to browse
the Library and **Play** on the game's Highball page to launch with the bottle's D3DMetal renderer.
From the CLI, use `highball run --renderer dxmt AoE4 Steam` to open Steam's Library. To launch the
game with D3DMetal after browsing, quit Steam first and run
`highball run AoE4 Steam -- -silent -applaunch 1466860`. The graphics driver check
may display a modal because Wine presents an AMD compatibility adapter. Acknowledge it to continue.
Check the Highball log for `AoE4 cache profile accepted` or `discovered ring allocation accepted`.
Use the bottle's counter directory to confirm that the game actually hit the cache.

```bash
python3 proposals/aoe4/cache-stats.py /path/to/bottle/aoe4-counters --require-active
```

For a cache-only comparison, stop the bottle and set `AOE4_CACHE=0` with
`highball bottle set AoE4 env AOE4_CACHE=0`. Use an empty value to restore the cache and start
a new game process. `AOE4_X87=0` selects the software-fault decoder alone.
`AOE4_DISABLED=1` bypasses the trial hooks.

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
