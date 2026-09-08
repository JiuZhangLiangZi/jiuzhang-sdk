#!/usr/bin/env python3
"""Initialize the JupyterHub user home directory from the SDK template."""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_TEMPLATE_DIR = "/opt/jiuzhang/init/user-home-template"


class InitError(Exception):
    """Raised when user-home initialization cannot proceed."""


def require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise InitError(f"Missing environment variable: {name}")
    return value


def require_int_env(name: str) -> int:
    value = require_env(name)
    try:
        return int(value)
    except ValueError as exc:
        raise InitError(f"Invalid integer value for {name}: {value}") from exc


def save_meta(meta_file: Path, meta: dict[str, object]) -> None:
    tmp_file = meta_file.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_file, meta_file)


def fix_tree_permissions(path: Path, uid: int, gid: int) -> None:
    for root, dirs, files in os.walk(path):
        os.chown(root, uid, gid)
        os.chmod(root, 0o755)
        for dirname in dirs:
            directory = os.path.join(root, dirname)
            os.chown(directory, uid, gid)
            os.chmod(directory, 0o755)
        for filename in files:
            file_path = os.path.join(root, filename)
            os.chown(file_path, uid, gid)
            os.chmod(file_path, 0o644)


def lock_meta(meta_dir: Path, meta_file: Path) -> None:
    os.chown(meta_dir, 0, 0)
    os.chmod(meta_dir, 0o755)
    os.chown(meta_file, 0, 0)
    os.chmod(meta_file, 0o644)


def main() -> None:
    if os.geteuid() != 0:
        raise InitError("This script must run as root, normally in an initContainer")

    nb_user = require_env("NB_USER")
    nb_uid = require_int_env("NB_UID")
    nb_gid = require_int_env("NB_GID")
    template_dir = Path(os.environ.get("JIUZHANG_HOME_TEMPLATE", DEFAULT_TEMPLATE_DIR))
    home_dir = Path("/home") / nb_user
    meta_dir = home_dir / ".jiuzhang"
    meta_file = meta_dir / "meta.json"
    now = datetime.now(timezone.utc).isoformat()

    if not template_dir.is_dir():
        raise InitError(f"User home template directory does not exist: {template_dir}")

    home_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    if not meta_file.exists():
        print(f"[init-home] First run: copying template files from {template_dir}")
        shutil.copytree(template_dir, home_dir, dirs_exist_ok=True)
        fix_tree_permissions(home_dir, nb_uid, nb_gid)
        meta_dir.mkdir(parents=True, exist_ok=True)
        save_meta(
            meta_file,
            {
                "init_completed": True,
                "init_time": now,
                "start_time": now,
                "template_dir": str(template_dir),
            },
        )
    else:
        print("[init-home] Restore: keeping existing files and refreshing access")
        os.chown(home_dir, nb_uid, nb_gid)
        os.chmod(home_dir, 0o755)
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            if not isinstance(meta, dict):
                meta = {}
        except (OSError, json.JSONDecodeError):
            meta = {}
        meta.setdefault("init_completed", True)
        meta.setdefault("init_time", now)
        meta["start_time"] = now
        meta["template_dir"] = str(template_dir)
        save_meta(meta_file, meta)

    lock_meta(meta_dir, meta_file)
    print(f"[init-home] Home ready: {home_dir}")


if __name__ == "__main__":
    try:
        main()
    except InitError as exc:
        print(f"[init-home] {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[init-home] Error: {exc}", file=sys.stderr)
        sys.exit(1)
