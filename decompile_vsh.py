#!/usr/bin/env python3

# ruff: noqa: PLR2004 Magic value used in comparison
# ruff: noqa: T201 `print` found

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

_HEX_VALUE = "0x[0-9a-fA-F]+"

# nv2a_pgraph_method 0: 0x97 -> 0x0b00 NV097_SET_TRANSFORM_PROGRAM[0] 0x0
# nv2a_pgraph_method 0: NV20_KELVIN_PRIMITIVE<0x97> -> NV097_SET_TRANSFORM_PROGRAM[0]<0xB00> (0x0)
_TRANSFORM_PROGRAM_RE = re.compile(
    r"\s*nv2a_pgraph_method 0: (?:NV20_KELVIN_PRIMITIVE<)?0x97>?\s*->\s*(?:"
    + _HEX_VALUE
    + r")?\s*NV097_SET_TRANSFORM_PROGRAM\[(\d+)\](?:<.*>)?\s*\(?("
    + _HEX_VALUE
    + r")\)?"
)

# nv2a_pgraph_method 0: 0x97 -> 0x1ea4 NV097_SET_TRANSFORM_CONSTANT_LOAD[0] 0x5a
# nv2a_pgraph_method 0: NV20_KELVIN_PRIMITIVE<0x97> -> NV097_SET_TRANSFORM_CONSTANT_LOAD<0x1ea4> (0x0)
_TRANSFORM_CONSTANT_BASE_RE = re.compile(
    r"\s*nv2a_pgraph_method 0:.*NV097_SET_TRANSFORM_CONSTANT_LOAD(?:\[.*]|<.*>)\s+\(?("
    + _HEX_VALUE
    + r")\)?"
)

# nv2a_pgraph_method 0: 0x97 -> 0x0b9c NV097_SET_TRANSFORM_CONSTANT[28] 0x34969a08
# nv2a_pgraph_method 0: NV20_KELVIN_PRIMITIVE<0x97> -> NV097_SET_TRANSFORM_CONSTANT[0]<0xb80> (0x3F800000 => 1.000000)
_TRANSFORM_CONSTANT_RE = re.compile(
    r"\s*nv2a_pgraph_method 0:.*NV097_SET_TRANSFORM_CONSTANT\[\d+](?:<.*>)?\s+\(?("
    + _HEX_VALUE
    + r")(?:\s+=>.*)?"
)


def _extract_programs(infile):
    # Constants are 192 4-component vectors.
    constants = [0] * 192 * 4
    constant_load_base = 0
    program = []
    for full_line in infile:
        line = full_line.strip()

        match = _TRANSFORM_CONSTANT_BASE_RE.match(line)
        if match:
            constant_load_base = int(match.group(1), 16) * 4
            continue

        match = _TRANSFORM_CONSTANT_RE.match(line)
        if match:
            int_value = int(match.group(1), 16)
            print(f"Constant [{constant_load_base}] = {int_value}")
            constants[constant_load_base] = int_value
            constant_load_base += 1
            continue

        match = _TRANSFORM_PROGRAM_RE.match(line)
        if not match:
            if program:
                yield program, constants
            program = []
            continue

        # index = match.group(1)
        value = match.group(2)
        program.append(value)

    if program:
        yield program, constants


def _decompile_program(program: list[str]) -> str:
    tf = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False)
    tf.write(", ".join(program))
    tf.close()

    try:
        code = subprocess.check_output(["nv2avshd", "-t", tf.name])
    finally:
        os.unlink(tf.name)

    return code.decode("utf-8")


def _main(args):
    filename = os.path.expanduser(args[0])
    with open(filename, encoding="utf-8") as infile:
        for index, (program, constants) in enumerate(_extract_programs(infile)):
            program = _decompile_program(program)
            print(f"== {index} =========\n{program}-- CONSTANTS ----\n{constants}==============\n\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} pgraph_log_file")
        sys.exit(1)

    sys.exit(_main(sys.argv[1:]))
