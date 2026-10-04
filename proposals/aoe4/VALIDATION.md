# Verification record

Date: 2026-10-04. Host: Linux x86_64. Engine baseline:
`5a7a000bbe468323d96bdaf9ec5edf24de15e10c`, CrossOver 26.3.0 sources (Wine 11),
all existing Highball patches 0001–0016.

Game: proposed support for RelicCardinal.exe with SHA256
`5380c577805565817f528af6eac385263413fa6815553f9a31fa62561cb45e8c`.
Chip, macOS and runtime engine id: **not tested; unavailable on the verification host**.
Upstream: no issue or PR filed. Proposal branch only.

## Performed

- Downloaded and independently checked the complete 149054023-byte CodeWeavers source archive;
  SHA256 `ac99c8ca4b3848f3e81784135f023df266b61c2345726ea55a50b3e030dd6872` matches `inputs.json`.
- Applied every existing Highball patch in lexical order to the source archive.
- Applied this proposal to a second clean extraction using the checked preparation script.
  Confirmed a second application is refused by the preimage checks.
- Portable guard test: names, flag presence/default-off behavior, exact current PID bootstrap,
  known SHA256 vector, changed bytes, mismatched game digest, empty/invalid/nonregular descriptors,
  unchanged descriptor position.
- Relocator test: return fragment, RIP-relative operand, external near-Jcc, short jump; refusal
  of internal targets, calls, short-Jcc, truncated instructions and displacement overflow.
- Cache test: disabled, unverified and other-game profiles refused; duplicate fragment uses one
  slot and executes to return 42, original bytes retained, original PC recovered, unsupported
  fragments and addresses fall back.
- GCC syntax check of the changed x64 PE `signal_x86_64.c` against this source's Wine/MSVCRT
  headers (`-fsyntax-only -fno-builtin -fshort-wchar -D_WIN64 -D__WINESRC__ -D__WINE_PE_BUILD`).
  This checks C declarations, not assembly emission/linking or a macOS Wine build.

## Remaining acceptance work

1. Build both Wine halves on the supported macOS toolchain and the native arm64 helper; retain
   the build logs, helper checksum and `--probe` output for the actual test Mac.
2. Check an actual installed game's digest/version and record chip, macOS, engine id and date.
3. Exercise the software fault thunks with integer, flag, SSE and AVX state; verify both one-byte
   and two-byte fault recovery and unchanged behavior with both flags absent.
4. Run the game via Steam: menu, skirmish, campaign/map transitions, longer gameplay and shutdown.
   Compare baseline, softfault-only and softfault+cache for correctness and measured frame times.
5. Exercise failed helper attach, unsupported game digest, bridge/cache address collision and
   inherited environment in unrelated Steam children on macOS.
6. Confirm cached faults unwind/report original addresses and do not introduce signal, thread
   or fragment-lifetime regressions; exercise repeated launches and a populated cache.
7. Verify signed/notarized packaging, preserve corresponding sources and notices, and pin the
   resulting artifact only after the trial passes. Promote to the default series only after review.

Passing portable tests does not establish Rosetta compatibility or game playability. The supported
executable digest was taken from the public recovered profile; the game itself was not available
for independent validation here.
