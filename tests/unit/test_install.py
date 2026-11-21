"""Per-user install: copy the exe, add a searchable Start Menu shortcut, uninstall cleanly."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import install


def shortcut_details(path):
    import pythoncom
    from win32com.propsys import propsys, pscon
    from win32com.shell import shell

    pythoncom.CoInitialize()
    link = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
    )
    link.QueryInterface(pythoncom.IID_IPersistFile).Load(str(path))
    target = link.GetPath(shell.SLGP_UNCPRIORITY)[0]
    store = link.QueryInterface(propsys.IID_IPropertyStore)
    return target, store.GetValue(pscon.PKEY_AppUserModel_ID).GetValue()


class InstallTests(unittest.TestCase):
    def setUp(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.local = root / "Local"
        self.roaming = root / "Roaming"
        self.enterContext(patch.dict(os.environ, {"LOCALAPPDATA": str(self.local), "APPDATA": str(self.roaming)}))
        self.desktop = root / "Desktop"
        self.enterContext(patch.object(install, "desktop_shortcut", return_value=self.desktop / "PurpleMulti.lnk"))
        self.built = root / "dist" / "PurpleMulti.exe"
        self.built.parent.mkdir()
        self.built.write_bytes(b"MZ fake exe")
        self.enterContext(patch.object(install, "BUILT_EXE", self.built))
        self.build = self.enterContext(patch.object(install, "build"))

    def test_install_copies_the_exe_and_adds_a_searchable_shortcut(self):
        install.main(["--no-build"])
        self.build.assert_not_called()
        exe = self.local / "Programs" / "PurpleMulti" / "PurpleMulti.exe"
        self.assertEqual(exe.read_bytes(), b"MZ fake exe")
        shortcut = self.roaming / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "PurpleMulti.lnk"
        target, app_id = shortcut_details(shortcut)
        self.assertEqual(os.path.normcase(target), os.path.normcase(str(exe)))
        self.assertEqual(app_id, "purplemulti.app")
        self.assertFalse((self.desktop / "PurpleMulti.lnk").exists())

    def test_install_builds_first_and_can_add_a_desktop_shortcut(self):
        install.main(["--desktop"])
        self.build.assert_called_once_with()
        self.assertTrue((self.desktop / "PurpleMulti.lnk").is_file())

    def test_reinstall_replaces_the_exe(self):
        install.main(["--no-build"])
        self.built.write_bytes(b"MZ newer exe")
        install.main(["--no-build"])
        exe = self.local / "Programs" / "PurpleMulti" / "PurpleMulti.exe"
        self.assertEqual(exe.read_bytes(), b"MZ newer exe")

    def test_a_running_copy_blocks_install_and_uninstall(self):
        with patch.object(install, "running_copies", return_value=[1234]):
            with self.assertRaises(SystemExit):
                install.main(["--no-build"])
            with self.assertRaises(SystemExit):
                install.main(["--uninstall"])
        self.assertFalse((self.local / "Programs" / "PurpleMulti").exists())

    def test_uninstall_removes_program_and_shortcuts_but_not_data(self):
        data = self.local / "PurpleMulti" / "saved_accounts.json"
        data.parent.mkdir(parents=True)
        data.write_text("{}")
        install.main(["--no-build", "--desktop"])
        install.main(["--uninstall"])
        self.assertFalse((self.local / "Programs" / "PurpleMulti").exists())
        self.assertFalse((self.roaming / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "PurpleMulti.lnk").exists())
        self.assertFalse((self.desktop / "PurpleMulti.lnk").exists())
        self.assertTrue(data.is_file())


if __name__ == "__main__":
    unittest.main()
