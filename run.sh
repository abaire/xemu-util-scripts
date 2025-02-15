#!/usr/bin/env bash
set -eu

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <xiso_path>"
  exit 1
fi

script_dir="$(dirname "${0}")"
readonly script_dir

darwin_lib_subpath="${script_dir}/dist/xemu.app/Contents/Libraries/$(uname -m)"
DYLD_FALLBACK_LIBRARY_PATH=$(realpath "${darwin_lib_subpath}") ./build/qemu-system-i386 -dvd_path "$1"
