#!/usr/bin/env bash
set -eu

command=(
  ./build/qemu-system-i386
)

if [[ $# -ge 1 ]]; then
  command+=(
    -dvd_path "$1"
  )
  shift
fi

while [[ $# -gt 0 ]]; do
  command+=(
    "$1"
  )
  shift
done

script_dir="$(dirname "${0}")"
readonly script_dir

darwin_lib_subpath="${script_dir}/dist/xemu.app/Contents/Libraries/$(uname -m)"
darwin_lib_path=$(realpath "${darwin_lib_subpath}")

set -x
DYLD_FALLBACK_LIBRARY_PATH="${darwin_lib_path}" "${command[@]}"

