"""
Install PurpleMulti for the current Windows user, like a regular app.

- Builds dist/PurpleMulti.exe with scripts/build.py (skip with --no-build).
- Copies it to %LOCALAPPDATA%\\Programs\\PurpleMulti\\PurpleMulti.exe.
- Adds a Start Menu shortcut, which makes it show up in Windows Search and lets
  you pin it to the taskbar. --desktop also adds one on the desktop.

Run it again after pulling changes to update the installed copy.
Account data stays in %LOCALAPPDATA%\\PurpleMulti and is never touched.
--uninstall removes the program and its shortcuts, not the data.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILT_EXE = PROJECT_ROOT / "dist" / "PurpleMulti.exe"
APP_NAME = "PurpleMulti"
# Must match SetCurrentProcessExplicitAppUserModelID in src/main.py, so the running
# window and the pinned taskbar icon are treated as the same app.
APP_USER_MODEL_ID = "purplemulti.app"


def local_app_data() -> Path:
    base = os.environ.get("LOCALAPPDATA", "").strip()
    return Path(base) if base else Path.home() / "AppData" / "Local"


def install_dir() -> Path:
    return local_app_data() / "Programs" / APP_NAME


def installed_exe() -> Path:
    return install_dir() / f"{APP_NAME}.exe"


def start_menu_shortcut() -> Path:
    return Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / f"{APP_NAME}.lnk"


def desktop_shortcut() -> Path:
    from win32com.shell import shell, shellcon

    return Path(shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, None, 0)) / f"{APP_NAME}.lnk"


def running_copies(target: Path) -> list[int]:
    import psutil

    wanted = os.path.normcase(str(target))
    pids = []
    for process in psutil.process_iter(["pid", "exe"]):
        exe = process.info.get("exe")
        if exe and os.path.normcase(exe) == wanted:
            pids.append(process.info["pid"])
    return pids


def build() -> None:
    print("[INFO] Building the executable (about a minute)...")
    result = subprocess.run(["cmd", "/c", str(PROJECT_ROOT / "scripts" / "build.cmd")], cwd=PROJECT_ROOT)
    if result.returncode != 0:
        raise SystemExit("[ERROR] The build failed, nothing was installed.")


def copy_executable(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".new")
    shutil.copy2(source, temporary)
    os.replace(temporary, target)


def write_shortcut(path: Path, target: Path) -> None:
    import pythoncom
    from win32com.propsys import propsys, pscon
    from win32com.shell import shell

    pythoncom.CoInitialize()
    link = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
    )
    link.SetPath(str(target))
    link.SetArguments("")
    link.SetWorkingDirectory(str(target.parent))
    link.SetIconLocation(str(target), 0)
    link.SetDescription("Roblox account manager")
    store = link.QueryInterface(propsys.IID_IPropertyStore)
    store.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType(APP_USER_MODEL_ID, pythoncom.VT_LPWSTR))
    store.Commit()
    path.parent.mkdir(parents=True, exist_ok=True)
    link.QueryInterface(pythoncom.IID_IPersistFile).Save(str(path), 0)


def install(skip_build: bool, desktop: bool) -> None:
    target = installed_exe()
    if running_copies(target):
        raise SystemExit("[ERROR] PurpleMulti is running. Close it (also from the tray), then run this again.")
    if not skip_build:
        build()
    if not BUILT_EXE.is_file():
        raise SystemExit(f"[ERROR] {BUILT_EXE} was not found. Run without --no-build.")
    copy_executable(BUILT_EXE, target)
    print(f"[INFO] Installed {target}")
    write_shortcut(start_menu_shortcut(), target)
    print(f"[INFO] Start Menu shortcut: {start_menu_shortcut()}")
    if desktop:
        write_shortcut(desktop_shortcut(), target)
        print(f"[INFO] Desktop shortcut: {desktop_shortcut()}")
    print("[SUCCESS] Search for PurpleMulti in Windows. To pin it: right-click it > Pin to taskbar.")


def uninstall() -> None:
    target = installed_exe()
    if running_copies(target):
        raise SystemExit("[ERROR] PurpleMulti is running. Close it (also from the tray), then run this again.")
    for shortcut in (start_menu_shortcut(), desktop_shortcut()):
        if shortcut.is_file():
            shortcut.unlink()
            print(f"[INFO] Removed {shortcut}")
    if install_dir().is_dir():
        shutil.rmtree(install_dir())
        print(f"[INFO] Removed {install_dir()}")
    print("[SUCCESS] Uninstalled. Your accounts are still in %LOCALAPPDATA%\\PurpleMulti.")
    print("Unpin the taskbar icon by hand if you pinned it.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install PurpleMulti for this Windows user.")
    parser.add_argument("--no-build", action="store_true", help="install the existing dist/PurpleMulti.exe")
    parser.add_argument("--desktop", action="store_true", help="also add a desktop shortcut")
    parser.add_argument("--uninstall", action="store_true", help="remove the program and its shortcuts")
    options = parser.parse_args(argv)
    if options.uninstall:
        uninstall()
    else:
        install(options.no_build, options.desktop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
