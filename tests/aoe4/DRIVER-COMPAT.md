# AoE IV driver-query compatibility

Patch `0036-aoe4-adl-driver-query.patch` adds Proton's ADL implementation as a
normal Wine module. The source is copied unchanged from ValveSoftware/wine at
`0be231deb686bc9c9dd15dae836baa5b3b02150e`; the patch records the three file
hashes. The engine packages the LGPL notice and licence with the module.

## Activation and packaging

The normal configure/make/install build produces `atiadlxx.dll`. The engine
layout step moves it out of both global Wine builtin directories into
`engine/share/wine/aoe4/driver-compat/<arch>-windows/`. No prefix placeholder,
DLL override, registry setting, or inherited DLL search path is installed.

The existing 0032 launch flow must accept `RelicCardinal.exe`: explicit
`HB_AOE4=1`, the supported macOS/Rosetta launch, executable layout inspection,
and descriptor SHA-256 matching the image selected by the launcher. Only after
that verification does the process register the private directory. A narrowly
scoped ntdll Unix call resolves its ADL PE file when normal DLL searches fail.
Other executable names, including children inheriting `HB_AOE4`, do not receive
that path. This reuses 0032's executable verification; it does not introduce a
new fixed game-build hash allowlist.

`HB_AOE4_ADL=0` disables this addition while retaining the other AoE engine
features. `HB_AOE4=0` or `HB_AOE4_DISABLED=1` disables the existing AoE opt-in.
A missing private module keeps the normal driver-query behavior. Game files,
including the native `amd_ags_x64.dll`, are unchanged.

## Validation

On macOS/Rosetta, run the existing fixtures:

```sh
arch -x86_64 /bin/bash tests/aoe4/run.sh /path/to/patched/wine
```

`test_driver_gate.c` checks verification, executable name, inherited markers,
and off switches. For the runtime loader boundary, build the integration probe
and use an isolated engine/prefix:

```sh
x86_64-w64-mingw32-gcc -O2 -static tests/aoe4/test_driver_load.c -o RelicCardinal.exe
cp RelicCardinal.exe OtherGameProbe.exe
```

With `HB_AOE4=1 HB_AOE4_CACHE=0`, launch `RelicCardinal.exe present`: it must
exit zero and report the ADL driver version. Pass the child probe's Windows
path as the next argument to check that a child cannot load ADL. Launch
`OtherGameProbe.exe` with no arguments: it must exit zero and report ADL absent.
Run the named game probe without `present` and with each off switch to confirm
absence. Keep the probe directory free of ADL files and `.local` folders.

Local results on 2026-11-28:

- Normal Wine-built ADL and PE ntdll compiled for x86_64 and i386; Unix ntdll
  compiled for x86_64.
- All 34 Intel patches applied without fuzz to the pinned CrossOver archive.
- The workflow packaging shell moved both DLLs out of the shared directories
  and wrote the module licence and attribution.
- The full x86_64 AoE fixture suite passed under Rosetta.
- Engine-integrated native AGS 6.2.0 initialization returned success (0).
- The same AGS probe as another executable, with `HB_AOE4_ADL=0`, or with
  `HB_AOE4=0` returned the baseline `AGS_NO_AMD_DRIVER_INSTALLED` (6).
- The verified parent loaded ADL; its child inherited the environment and
  reported ADL absent (error 126).

## Full-game startup comparison (test branch, 2026-11-28)

The integration is being tested on `himbeles/highball-engine-aoe4` branch
`aoe4-adl-testing`; the ADL commit was removed from upstream PR 49. The game
folder's temporary DLL was removed before these runs.

A separate APFS-cloned prefix and a private copy of the game's Documents folder
were used with D3DMetal. The installed engine and original game files were not
modified. The actual `RelicCardinal.exe` and native `amd_ags_x64.dll` hashes
matched the original installation. No ADL was present in the game folder or
the prefix's system32/syswow64 directories.

| Engine / switch | Startup result |
|---|---|
| Existing r6 engine | Reached Graphics driver check; no installed driver version or main menu during observation. |
| Integrated ADL engine, normal opt-in | Three launches reached MainMenuPage without input. Driver 99.19.02 was reported against required 21.20.01.14. The repeated launch was observed for 179 seconds from Steam startup; the game and shared helper remained alive. |
| Same integrated engine, `HB_AOE4_ADL=0` | Restored the baseline graphics-check behavior; no installed driver version or main menu during 107 seconds from Steam startup. |

The GPU class remained `Gen7 Only`. The system graphics configuration changed
only its `last_modified` timestamp. While the actual patched game was running,
another native AGS probe in the same prefix still returned the original
`AGS_NO_AMD_DRIVER_INSTALLED` result. This checks that the private module is
not exposed to another process even during the real game session.

These are startup and main-menu checks from game/process logs. No mission
playthrough or visual rendering validation was performed. Compatibility
metadata does not add AMD hardware features.

The normal engine workflow was also dispatched on the testing branch with
release publication disabled: [branch build](https://github.com/himbeles/highball-engine-aoe4/actions/runs/46157701602).
