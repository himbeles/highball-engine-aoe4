#!/usr/bin/env bash
set -euo pipefail
proposal_dir=$(cd "$(dirname "$0")/.." && pwd)
wine_source=${1:?usage: tests/run.sh /absolute/path/to/patched/wine}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cc=${CC:-cc}
common=(-std=gnu11 -O2 -Wno-deprecated-declarations -I"$wine_source/dlls/ntdll/unix")
crypto=()
if [[ $(uname -s) != Darwin ]]; then
  common+=(-I"$proposal_dir/tests/compat")
  crypto=(-lcrypto)
fi
"$cc" "${common[@]}" "$proposal_dir/tests/test_guard.c" "${crypto[@]}" -o "$work/guard"
"$cc" "${common[@]}" "$proposal_dir/tests/test_relocator.c" -o "$work/relocator"
"$work/guard"
"$work/relocator"
if [[ $(uname -m) == x86_64 ]]; then
  "$cc" "${common[@]}" "$proposal_dir/tests/test_cache.c" -pthread -o "$work/cache"
  "$work/cache" disabled
  "$work/cache" unverified
  "$work/cache" other-game
  "$work/cache"
else
  echo "SKIP: executable x86_64 cache test requires an x86_64 host (run under Rosetta on macOS)"
fi
