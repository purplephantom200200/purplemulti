"""A verification during a browser login brings the window forward and is reported once."""

import tempfile
import unittest
from unittest import mock

from classes import account_manager as am


class Clock:
    def __init__(self, step):
        self.now = 0.0
        self.step = step

    def __call__(self):
        self.now += self.step
        return self.now


class Driver:
    def __init__(self, states):
        self.states = list(states)
        self.calls = []

    def execute_script(self, script, *args):
        if script.lstrip().startswith("return {href"):
            return self.states.pop(0) if len(self.states) > 1 else self.states[0]
        return None

    def get_window_rect(self):
        self.calls.append("get_window_rect")
        return {"x": 10, "y": 20, "width": 500, "height": 600}

    def minimize_window(self):
        self.calls.append("minimize_window")

    def set_window_rect(self, **rect):
        self.calls.append(("set_window_rect", rect))


def state(challenge=False, href="https://www.roblox.com/login", detected=False):
    return {"href": href, "alive": True, "detected": detected, "challenge": challenge}


class LoginChallengeTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        patcher = mock.patch.object(am, "get_data_dir", return_value=folder.name)
        patcher.start()
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(am.time, "sleep").start()
        self.manager = am.RobloxAccountManager()
        self.reports = []
        self.manager.login_challenge_callback = self.reports.append

    def test_a_verification_raises_the_window_and_is_reported_once(self):
        driver = Driver([state(), state(True), state(True), state(True), state(detected=True)])
        self.assertTrue(self.manager.wait_for_login(driver, timeout=60, label="PurpleFox"))
        self.assertEqual(self.reports, ["PurpleFox"])
        self.assertEqual(driver.calls, [
            "get_window_rect", "minimize_window",
            ("set_window_rect", {"x": 10, "y": 20, "width": 500, "height": 600}),
        ])

    def test_a_new_verification_after_one_is_solved_is_reported_again(self):
        driver = Driver([state(True), state(), state(True), state(detected=True)])
        self.manager.wait_for_login(driver, timeout=60, label="NightOwl")
        self.assertEqual(self.reports, ["NightOwl", "NightOwl"])

    def test_a_verification_gives_five_more_minutes_once(self):
        # Each check advances the clock by 100 s: without a verification a 300 s wait
        # stops after a few checks; with one it lasts about 300 s longer.
        quiet = Driver([state()])
        with mock.patch.object(am.time, "time", Clock(100)):
            self.assertFalse(self.manager.wait_for_login(quiet, timeout=300))
        busy = Driver([state(True)])
        clock = Clock(100)
        with mock.patch.object(am.time, "time", clock):
            self.assertFalse(self.manager.wait_for_login(busy, timeout=300))
        self.assertGreaterEqual(clock.now, 500)
        self.assertLess(clock.now, 900)

    def test_a_failing_window_or_callback_does_not_stop_the_login(self):
        driver = Driver([state(True), state(detected=True)])
        driver.minimize_window = mock.Mock(side_effect=RuntimeError("no window"))
        self.manager.login_challenge_callback = mock.Mock(side_effect=RuntimeError("ui gone"))
        self.assertTrue(self.manager.wait_for_login(driver, timeout=60))

    def test_without_a_label_the_report_names_the_account_generically(self):
        driver = Driver([state(True), state(detected=True)])
        self.manager.wait_for_login(driver, timeout=60)
        self.assertEqual(self.reports, ["this account"])


if __name__ == "__main__":
    unittest.main()
