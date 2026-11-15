# AoE IV trial validation

Tested on an Apple M2 Max running macOS 27.2.1 (26B131), with Rosetta and D3DMetal at
2560×1440 display output. AoE IV 17.0.12303.0 was Steam build 26559323. Its executable SHA-256
was `e047891780ec9a01e39185803288578b8385419e93c97b2216ebd24ee2bc1469`. Live inspection
confirmed the pointer at RVA `0x7c9f9d8`, the 16 MiB ring and 32-byte slots.

Gameplay used a local trial assembled from the stock Highball r32 archive with rebuilt
Darwin and PE ntdll modules and the signed arm64 helper. The installed Wine 10 Sikarugir r28
engine reproduced an illegal instruction at `0x143EE5588` before the menu. Unpatched Wine 11 r32
reached the skirmish when the driver warning was acknowledged.

## Unpatched and patched r32

Both launches used the same benchmark bottle, renderer components, executable, graphics
settings and Nagari skirmish save at game time 4:55. Unpatched ran first. Metal System Trace
was requested five seconds after pressing Play. The display numbers use the same trace
window from seconds 2 through 25 and count distinct game frames presented to the 60 Hz display.

| Metric | Unpatched r32 | Patched r32, cache enabled |
| --- | ---: | ---: |
| Displayed FPS | 37.8 | 58.7 |
| Median display interval | 33.3 ms | 16.7 ms |
| 99th percentile display interval | 50.0 ms | 33.3 ms |
| Intervals of at least three display refreshes | 17 | 0 |
| Longest display interval | 133.3 ms | 33.3 ms |
| Time from `OnBeginLoad` to `OnEndLoad` | 49.5 s | 17.1 s |

The patched run recorded 31 gaps of about 33 ms in that window and a 50 ms gap in the first
second of capture. A separate longer patched trace had a 467 ms interval during its first
second and one 50 ms gap after the first two seconds. The matched results apply to one scene
and cover the full patch set with caching enabled.

## Cache-only comparison

Separate 30-second Game Performance Overview captures used the same save and both decoder
hooks, with caching disabled first and then enabled.

| Metric | Cache disabled | Cache enabled |
| --- | ---: | ---: |
| Average FPS | 55.2 | 58.6 |
| Lowest one-second FPS sample | 48.0 | 56.0 |
| Game-process CPU usage | 228.5% | 163.2% |
| Time from `OnBeginLoad` to `OnEndLoad` | 30.2 s | 17.5 s |

The cache-enabled trace added 1,354,730 hits, with zero new entries and zero recorded
fallbacks. The disabled process logged the override and produced no cache counters. Loading
times can include OS cache and run-order effects.

## Discovery across game versions

The same detector found the measured pointer RVA `0x7af7ad0` in 16.3.11308.0 and `0x7c9f9d8`
in 17.0.12303.0. The rebuilt engine launched 17.0 through Steam with an empty profile directory,
validated the live allocation at `0x149e00000` and recorded 898,714 cache hits with the game at
the graphics-driver check. Native and Rosetta tests covered signature reads across a file
chunk boundary, mismatched and duplicate references, a changed slot shift and a truncated
live allocation. A synthetic executable named `RelicCardinal.exe` with a different PE image
base completed through the stock Wine launch.

## Steam browser startup

On the same D3DMetal bottle, Steam's browser GPU process repeatedly exited on both unpatched
and patched r32. The patched build reproduced its exit code with the AoE hooks explicitly
disabled. Forcing software rendering stopped the GPU process exits, and the D3DMetal Steam
window still displayed black. A screen recording verified that Steam's Library loaded and
responded on both engines when Steam was started with DXMT, following Highball's existing
[Steam window behavior](https://github.com/gauthierpiarrette/highball/issues/416).

## Build checks and remaining validation

- The [prototype Intel macOS build](https://github.com/himbeles/highball-engine-aoe4/actions/runs/43691361823)
  passed. Local gameplay used the trial modules described above.
- Native macOS and Rosetta portable tests passed. The freshly rebuilt arm64 helper passed
  strict signature verification and its Rosetta probe. All ten changed Wine source files in
  the prepared tree matched those used for the gameplay build.
- Highball installed the locally packaged trial in a fresh test home, unpacked the helper
  and profile, created a bottle and ran a Windows command in it.
- Review the final Actions artifact through a fresh Highball install. Also verify extended
  late-game play, replay and Windows multiplayer before publishing a game recipe or manifest.
