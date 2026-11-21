"""
Shared filesystem paths for source runs and PyInstaller builds.
"""

from __future__ import annotations

import os
import sys


def get_project_root() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    source_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.basename(source_root).casefold() == "src":
        return os.path.dirname(source_root)
    return source_root


def get_app_dir() -> str:
    return get_project_root()


def get_bundle_root() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", get_project_root())
    return get_project_root()


def get_resource_path(*parts: str) -> str:
    return os.path.join(get_bundle_root(), *parts)


DATA_DIR_ENV = "RAM_DATA_DIR"
DATA_DIR_OPTION = "--data-dir"


APP_DATA_FOLDER = "PurpleMulti"
LEGACY_DATA_FOLDER = "AccountManagerData"
_LEGACY_MARKERS = ("saved_accounts.json", "encryption_config.json")


def default_data_dir() -> str:
    """%LOCALAPPDATA%\PurpleMulti: the same folder for the installed exe and source runs."""
    base = os.environ.get("LOCALAPPDATA", "").strip()
    if not base:
        base = os.path.join(os.path.expanduser("~"), "AppData", "Local")
    return os.path.join(base, APP_DATA_FOLDER)


def legacy_data_dir() -> str:
    return os.path.join(get_project_root(), LEGACY_DATA_FOLDER)


def resolve_data_dir() -> str:
    override = os.environ.get(DATA_DIR_ENV, "").strip()
    if override:
        return os.path.abspath(os.path.expandvars(os.path.expanduser(override)))
    legacy = legacy_data_dir()
    # A portable copy that already keeps its accounts next to the app goes on using them.
    if any(os.path.isfile(os.path.join(legacy, marker)) for marker in _LEGACY_MARKERS):
        return legacy
    return default_data_dir()


def get_data_dir() -> str:
    return resolve_data_dir()


def apply_data_dir_argument(argv: list[str]) -> list[str]:
    remaining = []
    index = 1
    remaining.extend(argv[:1])
    while index < len(argv):
        argument = argv[index]
        if argument == DATA_DIR_OPTION:
            value = argv[index + 1].strip() if index + 1 < len(argv) else ""
            index += 2
        elif argument.startswith(DATA_DIR_OPTION + "="):
            value = argument[len(DATA_DIR_OPTION) + 1:].strip()
            index += 1
        else:
            remaining.append(argument)
            index += 1
            continue
        if value:
            os.environ[DATA_DIR_ENV] = value
        else:
            print(f"[WARNING] {DATA_DIR_OPTION} needs a folder path and was ignored.", file=sys.stderr)
    return remaining
