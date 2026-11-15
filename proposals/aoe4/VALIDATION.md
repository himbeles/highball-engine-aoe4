# Verification record

Date: 2026-11-15. Local host: Linux x86_64; CI: hosted Intel macOS runner. Wine baseline: Highball engine
`161d7a8495d041d2901d07ff3b4fffeed9be1a4b`, pinned CrossOver 26.3 sources.
Status: implementation in a fork; no PR, release or game verification claimed.

Performed:

- Verified the CodeWeavers archive's 149054023-byte size and SHA256
  `ac99c8ca4b3848f3e81784135f023df266b61c2345726ea55a50b3e030dd6872`.
- Applied the current Highball patch series, resolved the cooperative-protocol changes, regenerated
  the AoE patch and preimage lock, and applied it to a fresh extraction through `prepare-source.py`.
- Applied all three checksum-pinned MIT sidecar patches to the pinned baseline without fuzz.
- Portable tests passed: descriptor hashing and offset preservation; name/PID/flag checks; PE64
  image/text/data bounds and malformed headers; profile digest, pointer alignment and data bounds;
  fragment relocation/refusal; cache deduplication/execution/original-PC mapping; absent profile,
  changed fragments and invalid ring-pointer fallbacks.
- Tool tests passed: profiles use the actual file SHA256, reject invalid pointer RVAs and refuse
  overwriting existing profiles; generated manifests use actual archive size/SHA256, reject
  missing engine/helper files and preserve Highball's Apple licence declaration.
- GCC C syntax check of the modified PE signal source against Wine's headers; workflow YAML and
  shell syntax checks. These do not establish macOS linking, native sidecar execution or gameplay.

CI evidence:

- Portable CI passed at `d98b0fa`:
  https://github.com/himbeles/highball-engine-aoe4/actions/runs/43691279746
- The macOS trial at `f941ea7` compiled the patched arm64 helper and all three changed ntdll
  objects (Unix loader, Unix signal handler and x64 PE signal/assembly object) successfully.
  Its remaining full build was superseded by the final file-state-check revision.
- The final revision's full, non-publishing trial is:
  https://github.com/himbeles/highball-engine-aoe4/actions/runs/43691361823
  Its outcome must be checked before calling the complete engine build verified.

Remaining:

- Run the macOS engine workflow and native sidecar `--probe` on an Apple Silicon Mac; retain logs.
- Verify one- and two-byte software exceptions, x87/AVX/integer state and cached exception contexts.
- Measure and validate the live generated-code ring for current game builds; no 17.x cache profile
  is supplied. The old profile was recovered from public source, not independently measured here.
- Test baseline/combined/cache configurations with the same save/replay, long sessions, save/load
  and Windows multiplayer. Record actual game SHA256, version, chip, macOS and runtime engine id.
- Review helper signing/notarization and component loading through Highball on the target Mac.
- Independently verify release checksums and create a truthful `lastVerified` recipe only after
  acceptance. Evaluate newer athei sidecar commits separately; this trial pins the known AoE
  baseline plus explicit MIT fixes instead of claiming an untested upstream-version upgrade.
