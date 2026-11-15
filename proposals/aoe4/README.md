# AoE IV trial engine for Highball

This branch implements an optional Wine 11 engine, `x64-crossover26.3-aoe4-r1`. It builds from
Highball's Intel line at `161d7a8495d041d2901d07ff3b4fffeed9be1a4b` (CrossOver 26.3), adds
`0031-aoe4-rosetta-profile-cache.patch`, builds the AoE-aware arm64 helper and produces a Highball
install manifest. It is experimental: Linux checks pass; a macOS build and actual game acceptance
are still required. No verified compatibility claim or FPS claim is made.

The normal upstream patch folder is retained. In this fork, the existing `build-engine` workflow
has an `aoe4_trial` input, default true, that adds the separate AoE patch and helper; false builds
the unchanged upstream Wine series. Nothing has been submitted upstream and no PR is opened.

## Implemented behavior

- The x64 ntdll software-fault thunks and bridge are retained. The cooperative attach occurs after
  the game and ntdll bridge are mapped, with bounded receive and protocol validation.
- The helper composes software-fault and x87 decoding, and includes the explicitly MIT-licensed
  GS/TLS fallback and FBLD deferred-pop fixes. `X87_ALWAYS_NONE` is removed for the game.
- Wine independently parses the executable's PE64 headers before launching the helper. It accepts
  the recovered image base/text-start contract, derives the range end from `.text` minus the
  observed 0x500 tail, and hashes the file. Before `SEC_IMAGE`, Wine checks the same descriptor
  it will map against that digest. Layout checks are structural checks, not proof of gameplay
  compatibility with arbitrary updates. An unsupported layout or failed attach stops this explicit
  trial launch with a diagnostic; launches with the flags absent are unchanged.
- The immutable generated-code cache remains implemented and requested by the trial recipe.
  A measured profile bound to the actual executable SHA256 supplies the pointer RVA. The pointer
  must be aligned and inside writable `.data`; version 1 supports only the observed 16 MiB ring
  and 32-byte slots. The pointer is read at runtime, never replaced by an unverified absolute
  address. Missing/bad profiles are reported and leave the cache inactive while softfault+x87 runs.
- The cache preserves original bytes, refuses unsupported instructions and relocation overflow,
  checks for changing source bytes and maps cached exception PCs to originals. Short jumps are
  now refused because widening them does not preserve the byte-offset context map. The production
  test-ring bypass was removed. `AOELAB_COUNTERS_DIR` retains cache-hit/redirect/refusal counters.

**Current cache coverage:** the bundled profile is only for the recovered executable SHA256
`5380c577805565817f528af6eac385263413fa6815553f9a31fa62561cb45e8c` (16.3.11308), with pointer
RVA `0x7af7ad0`. The game binary is not available here. No address for 17.x has been guessed or
claimed verified. Calibrating that ring is required to enable caching on a current build.

## Build a trial

The preparation/profile/manifest tools require Python 3.11 or newer.

On the fork's Actions page, choose **aoe4-trial-build** and this branch. That wrapper always
sets `aoe4_trial=true` and `publish_release=false`. Its first push also starts a trial build. This compiles Wine on the existing Intel macOS runner and cross-builds
and signs the native arm64 helper. A separate Linux workflow runs the portable checks on pushes.
The engine artifact includes:

- the Wine engine archive and checksum;
- `aoe4-helper.tar.gz` and checksum (helper, profiles, licences and source pins);
- `aoe4-corresponding-source.tar.gz` and checksum (original Wine archive, patches/build inputs,
  and the patched helper source);
- `aoe4-engine.json`, with actual archive hashes, sizes and the tagged-release URLs.

A non-publishing trial produces artifacts; its future release URLs do not become downloadable
until the assets are hosted. After a successful Mac/game trial, the same workflow's explicit
`publish_release=true` publishes them together. No release is published automatically.
The manifest reuses Highball r31's renderer/runtime component data and licence gates; it adds the
fork's Wine archive and helper component. It does not redistribute Apple's graphics binaries in
our Wine/helper archives. D3DMetal requires the usual Highball licence acceptance.

To generate a manifest after building/hosting manually:

```bash
python3 proposals/aoe4/make-manifest.py --wine engine-....tar.gz --helper aoe4-helper.tar.gz \
  --release-url https://github.com/himbeles/highball-engine-aoe4/releases/download/TAG \
  --output aoe4-engine.json
highball engine install aoe4-engine.json --accept-d3dmetal-license
highball bottle create AoE4 --engine x64-crossover26.3-aoe4-r1 --renderer d3dmetal
```

Install/launch Steam and your own AoE IV normally in this dedicated environment. The distinct
engine manifest sets the AoE flags itself; Wine gates them to `RelicCardinal.exe`. This works
before Highball's database knows this game or its recipe. `recipe-trial.json` is future/local
recipe data, not a submission-ready verified recipe; it intentionally has no invented
`lastVerified`. A local game recipe alone would not activate scoped flags through the app without
a matching database entry; the engine flags remove that dependency for this trial.
The manifest resolves the helper/profile paths through `${frameworks}`, so no user-specific
absolute paths or app changes are needed. Wine resolves its own loader after `init_paths`.

For source-only preparation on Linux or macOS:

```bash
python3 proposals/aoe4/prepare-source.py /path/to/crossover-sources.tar.gz /new/work-directory
proposals/aoe4/tests/run.sh /new/work-directory/sources/wine
python3 proposals/aoe4/tests/test_tools.py
```

`inputs.lock.json` checks archive size/hash, the entire upstream patch series and all changed Wine
preimages. The helper build checks its source commit and each MIT patch's checksum. These inputs
must be refreshed intentionally when rebasing, rather than bypassing failed checks.

## Calibrate the cache for a newer game build

1. Launch with both recipe flags and `AOE4_CACHE_DIAGNOSTICS=1`. The log prints the actual game
   SHA256, missing-profile status and candidate pointer RVAs from writable `.data`. Diagnostic
   scans are bounded and disabled in normal launches. Candidates are clues, never automatically
   accepted: other data pointers may fit the numeric range.
2. On the test Mac, inspect live memory across repeated generated-code resumes and ring wrap.
   Confirm the candidate points to the complete 16 MiB generated arena, not its current cursor,
   and that the 32-byte fragment contract, the recovered 0x140000000–0x180000000 code window
   and the allocation lifecycle still hold. Also test allocation/cleanup
   and more than one save/map. If they differ, change the profile schema/cache, not just its RVA.
3. Create a digest-bound profile from that exact executable and measured RVA:

   ```bash
   python3 proposals/aoe4/profile.py /path/to/RelicCardinal.exe \
     --ring-pointer-rva 0xMEASURED --output-dir /path/to/installed/frameworks/aoe4/profiles
   ```

4. Restart the environment. Require the log's **cache profile accepted** message, nonzero redirect
   and hit counters, and an actual replay comparison. Record the digest and chip/macOS/game build.
   Then commit the measured profile under `profiles/` and rebuild the helper package.

   The trial recipe writes per-process counters under the bottle's `aoe4-counters` directory:

   ```bash
   python3 proposals/aoe4/cache-stats.py /path/to/bottle/aoe4-counters --require-active
   ```

   Use a fresh counters directory for comparisons. A successful exit requires positive cache hits
   and redirects; merely having the flag or a profile does not pass this check.

The profile-writing tool checks the file hash and pointer's section/alignment. It cannot validate
live allocation size, slot semantics or game correctness. No automatic scanning heuristic turns
caching on. `AOELAB_CODE_CACHE_GAME=0` still enables it (presence-based original flag); unset it
for ordinary recipes. This trial manifest supplies both flags, so use bottle overrides
`AOE4_CACHE=0` for combined without cache, `AOE4_X87=0` for softfault-only, and
`AOE4_DISABLED=1` for the unmodified launch path. Stop the environment between comparisons.
For example: `highball bottle set AoE4 env AOE4_CACHE=0`.

## Acceptance before upstream integration

Run the same replay with baseline, softfault-only (`AOE4_X87=0`), combined x87, and combined x87+cache. Record FPS and frame-time percentiles, exceptions,
cache hits/refusals, a longer late-game session, save/load, and a match with Windows players.
Exercise missing helper, invalid layout/profile, ring changes and unrelated Steam children.
See `VALIDATION.md` for checks actually performed. A compiled engine alone does not verify AoE IV.

Upstream's structure remains: Wine/helper patches and builds in `highball-engine`, download
manifest in Highball, measured game recipe in `highball-db`. The local manifest/recipe let us
validate before requesting upstream changes. The native ARM64/FEX engine is a separate project.

## Provenance

Wine thunks/cache derive from Marc Ibrahim's LGPL sources mirrored at
[NerRobDog/wine-aoe4](https://github.com/NerRobDog/wine-aoe4/tree/711c6fc7559a565c417aab4d52d84b09767a9c1d),
with NerRobDog's relocator extensions. The helper baseline is
[NerRobDog/x87sidecar](https://github.com/NerRobDog/x87sidecar/tree/c407ddfabbbe6bc5f5d56a258a4866ac89b04d8e),
based on athei and Lifeisawful (MIT). Decoder composition/GS/FBLD patches are explicitly MIT in
[MacGames](https://github.com/tarikbc/macgames/tree/1579841b15ce569807b92af95b478c752c26df3d/patches/x87sidecar).
The new Wine layout/profile code and tools were independently implemented here. No PolyForm
MacGames application/Swift bridge code is copied. HDE's BSD notice and helper MIT notice are
retained under `Licenses/`. Highball manifest/recipe data remain data with their original terms.
