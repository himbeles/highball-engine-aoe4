#!/usr/bin/env bash
set -euo pipefail
[[ $(uname -s) == Darwin ]] || { echo "Build the native helper on macOS with Xcode and CMake >=3.27" >&2; exit 1; }
proposal_dir=$(cd "$(dirname "$0")" && pwd)
work=${1:?usage: build-sidecar.sh /path/to/new/work-directory}
[[ ! -e "$work" ]] || { echo "Work directory must not exist" >&2; exit 1; }
helper_repo=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["sidecar"]["repository"])' "$proposal_dir/inputs.lock.json")
helper_commit=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["sidecar"]["commit"])' "$proposal_dir/inputs.lock.json")
git clone --no-checkout "$helper_repo" "$work/source"
git -C "$work/source" checkout --detach "$helper_commit"
cmake -S "$work/source" -B "$work/build" -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_BUILD_TYPE=Release
cmake --build "$work/build" --target x87sidecar --parallel
shasum -a 256 "$work/build/bin/x87sidecar"
echo "Helper: $work/build/bin/x87sidecar; run --probe on the target Apple Silicon Mac"
