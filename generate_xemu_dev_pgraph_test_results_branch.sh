#!/usr/bin/env bash
set -eu


xemu_dev_pgraph_test_results_path="$(realpath ../pgraph_xemu_results/xemu-dev_pgraph)"
readonly xemu_dev_pgraph_test_results_path

xemu_dir="${PWD}"
readonly xemu_dir

local_binary_dir=local/xemu
readonly local_binary_dir

current_branch=$(git symbolic-ref --short HEAD)
readonly current_branch

use_vulkan=""

set +u
while [ ! -z "${1}" ]; do
  case "${1}" in
  '--use-vulkan'*)
    use_vulkan="--use-vulkan"
    shift
    ;;
  *)
    echo "Ignoring unknown option '${1}'"
    break
    ;;
  esac
done
set -u

xemu_binary="${xemu_dir}/build/qemu-system-i386"
if [[ ! -x "${xemu_binary}" ]]; then
  echo "Invalid xemu repository root - missing ${xemu_binary}. Did you forget to build?"
  exit 1
fi


pushd "${xemu_dev_pgraph_test_results_path}"

function clone_binary() {

  # Avoid leaving/modifying xemu.toml files owned by the user by copying to a local cache dir.
  rm -rf "${local_binary_dir}"
  mkdir -p "${local_binary_dir}"
  cp "${xemu_binary}" "${local_binary_dir}/"
  xemu_binary="${local_binary_dir}/qemu-system-i386"

  readonly xemu_binary

  if [[ "$(uname)" == "Darwin" ]]; then
    app_bundle="${xemu_dir}/dist/xemu.app"
    if [[ ! -d "${app_bundle}" ]]; then
      echo "Missing xemu.app bundle at ${app_bundle}. Did you forget to build?"
      exit 1
    fi

    cp -R "${app_bundle}" "${local_binary_dir}/"
    app_bundle="${local_binary_dir}/xemu.app"
    readonly app_bundle

    library_path="${app_bundle}/Contents/Libraries/$(uname -m)"
    readonly library_path
    if [[ ! -d "${library_path}" ]]; then
      echo "Missing libraries for $(uname -m) in ${app_bundle}. Cannot set DYLD_FALLBACK_LIBRARY_PATH, xemu will fail."
      exit 1
    fi

    export DYLD_FALLBACK_LIBRARY_PATH="${library_path}:DYLD_FALLBACK_LIBRARY_PATH"
  fi
}

function create_venv() {
  if [[ ! -d .venv ]]; then
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
  fi
}

function create_branch {
  git checkout main 2> /dev/null

  echo "Switching to ${current_branch}"
  git checkout "${current_branch}" 2> /dev/null || git checkout -b "${current_branch}" 2> /dev/null
}

function execute_tests() {
  local output
  local exit_result
  local command

  set +e
  command=(
    .venv/bin/python3
    execute.py
    --xemu "${xemu_binary}"
    --no-bundle
    -f
    "${use_vulkan}"
  )

  echo "Executing tests: ${command[*]}"
  output=$(${command[*]} 2>&1)
  exit_result=$?
  set -e

  if [[ ${exit_result} && ${exit_result} -ne 200 ]]; then
    echo "Test result generation failed with code ${exit_result}"
    echo "${output}"
    exit ${exit_result}
  fi
}


clone_binary
create_venv
create_branch
execute_tests

echo ""
echo "Next:"
echo "1. Examine outputs in ${xemu_dev_pgraph_test_results_path}."
echo "2. 'git commit' them to the new branch."
echo "3. 'git push' the branch to the upstream."
echo "4. Create a new PR and wait for the GitHub workflow to populate the wiki."

