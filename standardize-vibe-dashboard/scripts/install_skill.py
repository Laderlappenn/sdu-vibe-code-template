#!/usr/bin/env python3
"""Install this skill into a local agent skills directory.

Usage from a project that contains this skill folder:

  python3 standardize-vibe-dashboard/scripts/install_skill.py
  python3 standardize-vibe-dashboard/scripts/install_skill.py --target codex
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


IGNORE_NAMES = {
    ".DS_Store",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}


def skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def skill_name(path: Path) -> str:
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        raise SystemExit(f"Missing SKILL.md in {path}")
    for line in skill_md.read_text(encoding="utf-8").splitlines():
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip('"').strip("'")
            if name:
                return name
    raise SystemExit(f"Missing name: in {skill_md}")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude")).expanduser()


def ignored(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORE_NAMES or name.endswith(".pyc")}


def install(source: Path, destination_root: Path, name: str) -> Path:
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = destination_root / name
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=ignored)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Install standardize-vibe-dashboard skill")
    parser.add_argument("--target", choices=["codex", "claude", "both"], default="both")
    args = parser.parse_args()

    source = skill_dir()
    name = skill_name(source)
    installed: list[Path] = []

    if args.target in {"codex", "both"}:
        installed.append(install(source, codex_home() / "skills", name))
    if args.target in {"claude", "both"}:
        installed.append(install(source, claude_home() / "skills", name))

    for path in installed:
        print(f"Installed {name} -> {path}")


if __name__ == "__main__":
    main()
