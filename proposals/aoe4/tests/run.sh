#!/usr/bin/env bash
set -euo pipefail
proposal_dir=$(cd "$(dirname "$0")/.." && pwd)
wine_source=${1:?usage: tests/run.sh /absolute/path/to/patched/wine}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cc=${CC:-cc}
common=(-std=gnu11 -O2 -I"$wine_source/dlls/ntdll/unix")
digest_flags=(-Wno-deprecated-declarations)
if [[ $(uname -s) != Darwin ]]; then
  digest_flags+=(-I"$proposal_dir/tests/compat" -lcrypto)
fi
"$cc" "${common[@]}" "$proposal_dir/tests/test_guard.c" "${digest_flags[@]}" -o "$work/guard"
"$cc" "${common[@]}" "$proposal_dir/tests/test_layout.c" "${digest_flags[@]}" -o "$work/layout"
"$work/layout"
"$work/guard"
if [[ $(uname -m) == x86_64 ]]; then
  "$cc" "${common[@]}" "$proposal_dir/tests/test_relocator.c" -o "$work/relocator"
  "$work/relocator"
  "$cc" "${common[@]}" "$proposal_dir/tests/test_cache.c" -pthread -o "$work/cache"
  "$work/cache" disabled
  "$work/cache" unverified
  "$work/cache" other-game
  "$work/cache" missing-profile
  AOELAB_COUNTERS_DIR="$work/counters" "$work/cache"
  python3 "$proposal_dir/cache-stats.py" "$work/counters" --require-active
else
  echo "SKIP: relocator and executable cache tests require x86_64 (run under Rosetta on macOS)"
fi
