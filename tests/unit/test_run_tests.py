from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import run_tests


RUNNER = run_tests.PROJECT_ROOT / "scripts" / "run_tests.py"
CASE = "test_machine_id.StableMachineIdTests.test_result_is_cached"


class TestRunnerTests(unittest.TestCase):
    def run_cli(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, str(RUNNER), *args],
            cwd=cwd, capture_output=True, text=True, timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    def test_individual_test_can_run_outside_the_project_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("--suite", "unit", "--test", CASE, "-v", cwd=directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Ran 1 test", result.stderr)
        self.assertIn("test_result_is_cached", result.stderr)

    def test_list_filters_to_an_individual_test_without_running_it(self):
        result = self.run_cli("--suite", "unit", "--test", CASE, "--list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("tests.unit." + CASE, result.stdout)
        self.assertIn("1 test(s)", result.stdout)
        self.assertNotIn("Ran 1 test", result.stderr)

    def test_overlapping_file_and_method_selections_do_not_duplicate_tests(self):
        result = self.run_cli(
            "--suite", "unit", "--list", "--test",
            "tests/unit/test_machine_id.py", CASE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        ids = [line for line in result.stdout.splitlines() if line.startswith("tests.")]
        self.assertEqual(len(ids), 8)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(line.startswith("tests.unit.test_machine_id.") for line in ids))

    def test_unknown_selector_fails_even_when_another_selector_is_valid(self):
        result = self.run_cli("--suite", "unit", "--test", CASE, "missing_test")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("no tests match 'missing_test'", result.stderr)
        self.assertNotIn("Ran 1 test", result.stderr)

    def test_conflicting_selection_options_are_rejected(self):
        for args in (("--all", "--test", CASE), ("--all", "--suite", "unit")):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2, result.stderr)

    def test_failed_test_returns_exit_code_one(self):
        def fail():
            self.assertEqual(1, 2, "intentional runner fixture")

        suite = unittest.TestSuite([unittest.FunctionTestCase(fail)])
        output = io.StringIO()
        with patch.object(unittest.TestLoader, "discover", return_value=suite), redirect_stderr(output):
            self.assertEqual(run_tests.main(["--suite", "unit"]), 1)
        self.assertIn("FAILED (failures=1)", output.getvalue())

    def test_import_error_is_reported_instead_of_claiming_success(self):
        def discover(loader, *args, **kwargs):
            loader.errors.append("fixture: missing dependency")
            return unittest.TestSuite()

        output = io.StringIO()
        with patch.object(unittest.TestLoader, "discover", discover), redirect_stderr(output):
            self.assertEqual(run_tests.main(["--suite", "unit", "--list"]), 1)
        self.assertIn("fixture: missing dependency", output.getvalue())

    def test_suite_selection_limits_discovery_and_deduplicates_suites(self):
        output = io.StringIO()
        with patch.object(
            unittest.TestLoader, "discover",
            side_effect=lambda *a, **kw: unittest.TestSuite([unittest.FunctionTestCase(lambda: None)]),
        ) as discover, redirect_stdout(output):
            self.assertEqual(run_tests.main(["--suite", "unit", "--suite", "unit", "--list"]), 0)
        self.assertEqual(discover.call_count, 1)
        self.assertEqual(Path(discover.call_args.args[0]).name, "unit")


class ReportProblemsTests(unittest.TestCase):
    def result_with_failure(self):
        class Broken(unittest.TestCase):
            def test_it(self):
                self.assertEqual(1, 2, "values differ: a, b")

        result = unittest.TestResult()
        Broken("test_it").run(result)
        return result

    def report(self, env):
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(run_tests.os.environ, env, clear=False), redirect_stdout(out), redirect_stderr(err):
            run_tests.report_problems(self.result_with_failure())
        return out.getvalue(), err.getvalue()

    def test_failures_are_repeated_at_the_end(self):
        out, err = self.report({"GITHUB_ACTIONS": "false"})
        self.assertIn("1 test(s) did not pass", err)
        self.assertIn("FAIL: ", err)
        self.assertIn("test_it", err)
        self.assertIn("values differ", err)
        self.assertEqual(out, "")

    def test_github_actions_gets_one_escaped_annotation_per_failure(self):
        out, _err = self.report({"GITHUB_ACTIONS": "true"})
        lines = [line for line in out.splitlines() if line.startswith("::error ")]
        self.assertEqual(len(lines), 1)
        title, message = lines[0][len("::error title="):].split("::", 1)
        self.assertNotIn(":", title)
        self.assertNotIn(",", title)
        self.assertIn("%0A", message)
        self.assertIn("values differ", message)

    def test_nothing_is_printed_when_everything_passes(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            run_tests.report_problems(unittest.TestResult())
        self.assertEqual((out.getvalue(), err.getvalue()), ("", ""))
