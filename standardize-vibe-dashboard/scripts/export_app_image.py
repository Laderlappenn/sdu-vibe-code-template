#!/usr/bin/env python3
"""Build, verify, and export the dashboard app image for a Linux server."""

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path


SLUG_RE = re.compile(r"^[a-z0-9]+(?:[a-z0-9-]*[a-z0-9])?$")


def run(command, *, cwd: Path, env: dict, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        text=True,
        capture_output=capture,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and export a platform-verified Linux app image with no SQL files."
    )
    parser.add_argument("--app-slug", required=True, help="Lowercase app slug, for example appeals-dashboard")
    parser.add_argument("--project-dir", default=".", help="Dashboard project root")
    parser.add_argument("--compose-file", default="docker-compose.yml", help="Compose file relative to project root")
    parser.add_argument("--service", default="app", help="Compose app service name")
    parser.add_argument("--platform", default="linux/amd64", help="Target Linux platform")
    parser.add_argument("--image", help="Image tag; defaults to <app-slug>-app:latest")
    parser.add_argument("--env-template", default=".env.example", help="Deployable env template")
    parser.add_argument("--output-dir", default="image", help="Output directory relative to project root")
    parser.add_argument("--date", default=date.today().isoformat(), help="Artifact date in YYYY-MM-DD form")
    parser.add_argument("--skip-build", action="store_true", help="Verify and export an existing image")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not SLUG_RE.fullmatch(args.app_slug):
        raise SystemExit("--app-slug must contain lowercase letters, digits, and internal hyphens only")
    if not args.platform.startswith("linux/"):
        raise SystemExit("--platform must target Linux, for example linux/amd64")

    project_dir = Path(args.project_dir).resolve()
    compose_file = project_dir / args.compose_file
    env_template = project_dir / args.env_template
    output_dir = project_dir / args.output_dir
    image = args.image or f"{args.app_slug}-app:latest"

    if not compose_file.is_file():
        raise SystemExit(f"Compose file not found: {compose_file}")
    if not env_template.is_file():
        raise SystemExit(f"Env template not found: {env_template}")

    env = os.environ.copy()
    env["APP_IMAGE"] = image
    env["APP_PLATFORM"] = args.platform

    if not args.skip_build:
        run(
            ["docker", "compose", "-f", str(compose_file), "build", args.service],
            cwd=project_dir,
            env=env,
        )

    inspect = run(
        ["docker", "image", "inspect", image],
        cwd=project_dir,
        env=env,
        capture=True,
    )
    image_data = json.loads(inspect.stdout)[0]
    actual_platform = "/".join(
        part
        for part in (
            image_data.get("Os", ""),
            image_data.get("Architecture", ""),
            image_data.get("Variant", ""),
        )
        if part
    )
    if actual_platform != args.platform:
        raise SystemExit(
            f"Image platform mismatch: expected {args.platform}, built {actual_platform or 'unknown'}"
        )

    run(
        [
            "docker",
            "run",
            "--rm",
            "--platform",
            args.platform,
            "--entrypoint",
            "sh",
            image,
            "-c",
            'test ! -d /app/sql && test -z "$(find /app -type f -name "*.sql" -print -quit)"',
        ],
        cwd=project_dir,
        env=env,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    platform_suffix = args.platform.replace("/", "-")
    tar_path = output_dir / f"{args.app_slug}-app_{platform_suffix}_{args.date}.tar"
    temporary_tar = tar_path.with_suffix(".tar.tmp")
    try:
        run(
            ["docker", "save", "--output", str(temporary_tar), image],
            cwd=project_dir,
            env=env,
        )
        temporary_tar.replace(tar_path)
    finally:
        temporary_tar.unlink(missing_ok=True)

    shutil.copy2(env_template, output_dir / ".env.example")
    print(f"Exported {image} ({actual_platform}) to {tar_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
