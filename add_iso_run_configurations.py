#!/usr/bin/env python3
"""Adds CLion run configurations for Xbox ISO files to workspace.xml for the xemu project."""

from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

CONFIG_ATTRIBUTES: dict[str, str] = {
    "type": "CLionNativeAppRunConfigurationType",
    "REDIRECT_INPUT": "false",
    "ELEVATE": "false",
    "USE_EXTERNAL_CONSOLE": "false",
    "EMULATE_TERMINAL": "false",
    "PASS_PARENT_ENVS_2": "true",
    "PROJECT_NAME": "xemu",
    "TARGET_NAME": "xemu-make",
    "CONFIG_NAME": "xemu-make",
    "version": "1",
    "RUN_PATH": "$PROJECT_DIR$/build/qemu-system-i386",
}

RUN_MANAGER_PATTERN = re.compile(
    r"(<component\s+name=[\"']RunManager[\"'][^>]*>)(.*?)(</component>)",
    re.DOTALL,
)
SELF_CLOSING_RUN_MANAGER_PATTERN = re.compile(r"<component\s+name=[\"']RunManager[\"'][^>]*/>")


def format_program_params(iso_path: Path) -> str:
    path_str = str(iso_path)
    if " " in path_str:
        path_str = f'"{path_str}"'
    return f"-s -dvd_path {path_str}"


def ensure_method_child(cfg: ElementTree.Element) -> None:
    method = cfg.find("method")
    if method is None:
        method = ElementTree.SubElement(cfg, "method", {"v": "2"})
    else:
        method.set("v", "2")

    opt = method.find("option[@name='CLION.COMPOUND.BUILD']")
    if opt is None:
        ElementTree.SubElement(method, "option", {"name": "CLION.COMPOUND.BUILD", "enabled": "true"})
    else:
        opt.set("enabled", "true")


def update_run_manager(run_manager: ElementTree.Element, iso_paths: list[Path]) -> tuple[int, int]:
    added_count = 0
    updated_count = 0

    for iso_path in iso_paths:
        name = iso_path.stem
        program_params = format_program_params(iso_path)

        existing_cfg: ElementTree.Element | None = None
        for cfg in run_manager.findall("configuration"):
            if cfg.get("name") == name:
                existing_cfg = cfg
                break

        if existing_cfg is not None:
            existing_cfg.set("PROGRAM_PARAMS", program_params)
            for key, val in CONFIG_ATTRIBUTES.items():
                existing_cfg.set(key, val)
            ensure_method_child(existing_cfg)
            updated_count += 1
        else:
            attribs = {"name": name, "PROGRAM_PARAMS": program_params}
            attribs.update(CONFIG_ATTRIBUTES)
            new_cfg = ElementTree.SubElement(run_manager, "configuration", attribs)
            ensure_method_child(new_cfg)
            added_count += 1

    return added_count, updated_count


def collect_iso_paths(raw_patterns: list[str]) -> list[Path]:
    collected: list[Path] = []
    seen: set[Path] = set()

    for pattern in raw_patterns:
        if glob.has_magic(pattern):
            matched = [Path(p) for p in glob.glob(pattern, recursive=True)]
            if not matched:
                sys.stderr.write(f"Warning: No files matched pattern '{pattern}'\n")
            for p in sorted(matched):
                abs_p = p.resolve()
                if abs_p.is_file() and abs_p not in seen:
                    seen.add(abs_p)
                    collected.append(abs_p)
        else:
            p = Path(pattern)
            abs_p = p.resolve()
            if not abs_p.is_file():
                sys.stderr.write(f"Warning: File '{pattern}' ({abs_p}) not found or is not a file\n")
                continue
            if abs_p not in seen:
                seen.add(abs_p)
                collected.append(abs_p)

    return collected


def resolve_workspace_path(workspace_arg: str | Path) -> Path:
    ws_path = Path(workspace_arg)
    if ws_path.is_dir():
        cand = ws_path / ".idea" / "workspace.xml"
        if cand.is_file():
            return cand.resolve()
        cand = ws_path / "workspace.xml"
        if cand.is_file():
            return cand.resolve()
        return (ws_path / ".idea" / "workspace.xml").resolve()
    return ws_path.resolve()


def modify_workspace_content(xml_content: str, iso_paths: list[Path]) -> tuple[str, int, int]:
    match = RUN_MANAGER_PATTERN.search(xml_content)
    if match:
        run_manager = ElementTree.fromstring(match.group(0))  # noqa: S314
        added_count, updated_count = update_run_manager(run_manager, iso_paths)
        ElementTree.indent(run_manager, space="  ", level=1)
        new_block = ElementTree.tostring(run_manager, encoding="unicode")
        new_content = xml_content[: match.start()] + new_block + xml_content[match.end() :]
        return new_content, added_count, updated_count

    sc_match = SELF_CLOSING_RUN_MANAGER_PATTERN.search(xml_content)
    if sc_match:
        run_manager = ElementTree.Element("component", {"name": "RunManager"})
        added_count, updated_count = update_run_manager(run_manager, iso_paths)
        ElementTree.indent(run_manager, space="  ", level=1)
        new_block = ElementTree.tostring(run_manager, encoding="unicode")
        new_content = xml_content[: sc_match.start()] + new_block + xml_content[sc_match.end() :]
        return new_content, added_count, updated_count

    run_manager = ElementTree.Element("component", {"name": "RunManager"})
    added_count, updated_count = update_run_manager(run_manager, iso_paths)
    ElementTree.indent(run_manager, space="  ", level=1)
    new_block = ElementTree.tostring(run_manager, encoding="unicode")

    if "</project>" in xml_content:
        idx = xml_content.rfind("</project>")
        new_content = xml_content[:idx] + f"{new_block}\n" + xml_content[idx:]
    else:
        new_content = xml_content.rstrip() + f"\n{new_block}\n"

    return new_content, added_count, updated_count


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add CLion run configuration entries to workspace.xml for a set of ISO files in the xemu project."
    )
    parser.add_argument(
        "iso_paths",
        nargs="+",
        help="Path(s) or glob pattern(s) to ISO file(s) (e.g., game.iso, '*.iso').",
    )
    parser.add_argument(
        "-w",
        "--workspace",
        default=".idea/workspace.xml",
        help="Path to workspace.xml or project root directory (default: .idea/workspace.xml).",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Display the configurations to be added/updated without modifying workspace.xml.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    workspace_file = resolve_workspace_path(args.workspace)
    if not workspace_file.is_file():
        sys.stderr.write(
            f"Error: Workspace file '{workspace_file}' does not exist.\n"
            "Ensure you are running the script from within the project directory or pass --workspace.\n"
        )
        sys.exit(1)

    iso_paths = collect_iso_paths(args.iso_paths)
    if not iso_paths:
        sys.stderr.write("Error: No valid ISO files found to process.\n")
        sys.exit(1)

    try:
        with open(workspace_file, encoding="utf-8") as f:
            xml_content = f.read()
    except OSError as err:
        sys.stderr.write(f"Error reading '{workspace_file}': {err}\n")
        sys.exit(1)

    new_content, added, updated = modify_workspace_content(xml_content, iso_paths)

    if args.dry_run:
        sys.stdout.write(f"[Dry Run] Target workspace: {workspace_file}\n")
        sys.stdout.write(f"[Dry Run] Would add: {added}, would update: {updated}\n")
        for iso_path in iso_paths:
            sys.stdout.write(f"  Configuration: {iso_path.stem} -> {iso_path}\n")
        return

    try:
        with open(workspace_file, "w", encoding="utf-8") as f:
            f.write(new_content)
    except OSError as err:
        sys.stderr.write(f"Error writing to '{workspace_file}': {err}\n")
        sys.exit(1)

    sys.stdout.write(f"Successfully processed {workspace_file}:\n")
    sys.stdout.write(f"  Added: {added}\n")
    sys.stdout.write(f"  Updated: {updated}\n")
    for iso_path in iso_paths:
        sys.stdout.write(f"  - {iso_path.stem} ({iso_path})\n")


if __name__ == "__main__":
    main()
