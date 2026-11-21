# PurpleMulti

**English** | [Français](README.fr.md)

A Roblox account manager for Windows: organize your accounts, run several
Roblox clients at once, and automate the routine tasks.

PurpleMulti is a personal build of [Evanovar RAM](https://github.com/evanovar/RobloxAccountManager),
the open source project by evanovar. It keeps its features and its GPL-3.0
license, with a redesigned interface, stronger encryption and a lighter install.

## Features

- **Accounts**: groups, notes, avatars, drag-and-drop ordering, multi-select,
  import by cookie or sign-in through a browser.
- **Launching**: public games, private servers, a specific server, several
  accounts in a row.
- **Multi Roblox**: always on, several clients at once (default method or Handle64).
- **Automatic backup**: an encrypted copy of your accounts on a schedule, which
  can be restored on any PC.
- **Monitoring**: Auto-Rejoin, Anti-AFK, account presence and activity.
- **Windows**: rename, tile in a grid, or hide Roblox clients.
- **Tools**: game selector, private server links, Roblox settings with auto-apply.
- **Customization**: color themes, image, GIF or video backgrounds.

## What changes from the original

- **Encryption**: a new "Password + Windows account" mode, where the account
  file only opens with your password and on your Windows account. The
  "Windows account" mode uses DPAPI instead of a key built from hardware IDs
  that any program can read. Password mode moves to PBKDF2-SHA256 with 600,000
  iterations. Older files are converted when opened.
- **Lock**: the app locks after a period of inactivity, when minimized, or on
  Win+L (`Ctrl+L` locks it at once). Wrong passwords trigger a growing wait.
- **Interface**: purple theme, sidebar, cards, tabbed settings, `Ctrl+1`,
  `Ctrl+2`… shortcuts.
- **Lighter**: about 400 MB installed instead of 740 MB, a 48 MB exe instead of 78 MB.
- **Updates**: the app never replaces this build with the original one. When
  the original publishes a release, it explains how to merge it.

`.rambak` exports made with PurpleMulti do not open in the original app.

## Installation

You need Windows 10 or 11, [Git](https://git-scm.com/) and
[uv](https://docs.astral.sh/uv/). uv installs Python 3.15 by itself.

```powershell
git clone https://github.com/purplephantom200200/purplemulti.git
cd purplemulti
```

Then double-click **`Installer PurpleMulti.cmd`**. It builds the executable,
installs it for your Windows account and adds it to the Start Menu, so you can
find PurpleMulti in Windows Search and pin it to the taskbar (right-click >
Pin to taskbar). Run it again after each update.

To run from source without installing, double-click **`Lancer PurpleMulti.cmd`**.

## Data and privacy

Data lives in `%LOCALAPPDATA%\PurpleMulti`, outside the repository: encrypted
accounts and their backup, settings, groups, recent games, avatar cache and
logs. Pick another folder with `--data-dir "D:\Profiles\Alt"` or the
`RAM_DATA_DIR` variable.

An account's `.ROBLOSECURITY` cookie works like a signed-in session: whoever
has it controls the account. It is only sent to Roblox. The app has no
telemetry or ads. Its network requests serve the features you use: Roblox APIs,
release checks on GitHub, portable Chromium, Handle64, and connectivity checks
for Auto-Rejoin.

DPAPI encryption does not survive a Windows reinstall. Turn on automatic
backup (`Settings > Misc > Automatic Backup`) in a folder that does, such as
OneDrive.

## System changes

Depending on the features you turn on, the app can create shortcuts (Windows
startup, Start Menu), download Chromium, Handle64 or Roblox versions, edit the
Roblox settings file while keeping a `.ram.bak` copy, and temporarily lock
Roblox files while Multi Roblox runs.

To uninstall: turn off "Roblox Installer Fix" if you use it, quit the app, then
run `& ".\Installer PurpleMulti.cmd" --uninstall` in PowerShell from the repository folder.
It removes the program and its shortcuts. Delete `%LOCALAPPDATA%\PurpleMulti`
too if you want to remove your accounts and settings.

## Development

```powershell
uv run python scripts/run_tests.py --all    # tests
uvx ruff check .                            # lint
```

To pull changes from the original project:

```powershell
git remote add upstream https://github.com/evanovar/RobloxAccountManager.git   # once
git fetch upstream
git merge upstream/main
uv sync --locked
```

## Disclaimer

This project is meant for managing your own accounts. You are responsible for
following Roblox's Terms of Use. The authors are not responsible for
moderation, data loss or other consequences of using it.

## License

[GNU General Public License v3.0](LICENSE). Original copyright: evanovar.
