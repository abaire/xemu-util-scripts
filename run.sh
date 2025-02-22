#!/usr/bin/env bash
set -eu

command=(
  ./build/qemu-system-i386
)

if [[ $# -eq 1 ]]; then
  command+=(
    -dvd_path "$1"
  )
fi

script_dir="$(dirname "${0}")"
readonly script_dir

darwin_lib_subpath="${script_dir}/dist/xemu.app/Contents/Libraries/$(uname -m)"
DYLD_FALLBACK_LIBRARY_PATH=$(realpath "${darwin_lib_subpath}") "${command[@]}"

