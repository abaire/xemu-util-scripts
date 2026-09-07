#!/usr/bin/env python3
"""
Normalizes build/compile_commands.json to the repository root for CLion.

Pre-indexes the build directory into a lookup map to resolve generated files
in O(1) time, repoints working directories to the repository root, and converts
relative include/source flags to absolute paths.
"""

import json
import os
from pathlib import Path
import shlex
import sys


def build_index(build_dir: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for root, _, files in os.walk(build_dir):
        root_path = Path(root)
        for f in files:
            index.setdefault(f, (root_path / f).resolve())
    return index


def resolve_candidate_path(
    path_str: str, base_dir: Path, build_dir: Path, index: dict[str, Path]
) -> str:
    path = Path(path_str)
    if path.is_absolute():
        return path_str

    cand = (base_dir / path).resolve()
    if cand.exists():
        return str(cand)

    alt = (build_dir / path).resolve()
    if alt.exists():
        return str(alt)

    indexed = index.get(path.name)
    if indexed is not None:
        return str(indexed)

    return path_str


def transform_arguments(
    args: list[str], base_dir: Path, build_dir: Path, index: dict[str, Path]
) -> list[str]:
    transformed: list[str] = []
    skip_next = False
    path_flags = {"-I", "-iquote", "-isystem", "-c"}

    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue

        if arg in path_flags:
            transformed.append(arg)
            if i + 1 < len(args):
                transformed.append(
                    resolve_candidate_path(args[i + 1], base_dir, build_dir, index)
                )
                skip_next = True
            continue

        for flag in ("-I", "-iquote", "-isystem"):
            if arg.startswith(flag) and len(arg) > len(flag):
                target = arg[len(flag) :]
                transformed.append(
                    f"{flag}{resolve_candidate_path(target, base_dir, build_dir, index)}"
                )
                break
        else:
            transformed.append(resolve_candidate_path(arg, base_dir, build_dir, index))

    return transformed


def main():
    root_dir = Path(__file__).resolve().parent
    build_dir = root_dir / "build"
    src_db = build_dir / "compile_commands.json"
    dst_db = root_dir / "compile_commands.json"

    if not src_db.is_file():
        print(f"Error: {src_db} not found.", file=sys.stderr)
        sys.exit(1)

    build_index_map = build_index(build_dir)

    with open(src_db, "r", encoding="utf-8") as f:
        db = json.load(f)

    for entry in db:
        old_dir = Path(entry.get("directory", build_dir))

        if "file" in entry:
            resolved_file = resolve_candidate_path(
                entry["file"], old_dir, build_dir, build_index_map
            )
            file_path = Path(resolved_file).resolve()
            try:
                entry["file"] = str(file_path.relative_to(root_dir))
            except ValueError:
                entry["file"] = str(file_path)

        if "arguments" in entry:
            entry["arguments"] = transform_arguments(
                entry["arguments"], old_dir, build_dir, build_index_map
            )
        elif "command" in entry:
            tokens = shlex.split(entry["command"])
            entry["command"] = shlex.join(
                transform_arguments(tokens, old_dir, build_dir, build_index_map)
            )

        entry["directory"] = str(root_dir)

    with open(dst_db, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

    print(f"Generated valid {dst_db} targeting {root_dir}")


if __name__ == "__main__":
    main()
