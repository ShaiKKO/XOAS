#!/usr/bin/env python3
"""Behavioral tests for reversible Target 0 measurement sessions."""

from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPOSITORY_ROOT / "tools/target0/measurement_session.sh"


def write_text(root: Path, relative_path: str, content: str) -> None:
    """Write one controlled sysfs or procfs fixture value."""
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_session_fixture(root: Path) -> None:
    """Create one valid selected-CPU and SMT-sibling control fixture."""
    write_text(
        root,
        "sys/devices/system/cpu/cpu4/topology/thread_siblings_list",
        "4,16\n",
    )
    write_text(
        root,
        "sys/devices/system/cpu/cpu16/topology/thread_siblings_list",
        "4,16\n",
    )
    write_text(root, "sys/devices/system/cpu/cpu16/online", "1\n")
    write_text(
        root,
        "sys/devices/system/cpu/cpu4/cpufreq/scaling_governor",
        "powersave\n",
    )
    write_text(
        root,
        "sys/devices/system/cpu/cpu4/cpufreq/scaling_available_governors",
        "performance powersave\n",
    )
    write_text(
        root,
        "sys/devices/system/cpu/cpu4/cpufreq/energy_performance_preference",
        "balance_performance\n",
    )
    write_text(
        root,
        "sys/devices/system/cpu/cpu4/cpufreq/energy_performance_available_preferences",
        "performance balance_performance power\n",
    )
    write_text(root, "sys/devices/system/cpu/cpufreq/boost", "1\n")
    write_text(
        root,
        "proc/interrupts",
        "           CPU4 CPU16\n  0: 10 20 IO-APIC timer\n",
    )


def read_control(root: Path, relative_path: str) -> str:
    """Read a fixture control after the session exits."""
    return (root / relative_path).read_text(encoding="utf-8").strip()


class MeasurementSessionTest(unittest.TestCase):
    """Verify apply, command, signal, and exact-restoration behavior."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.fixture_root = Path(self.temporary_directory.name)
        make_session_fixture(self.fixture_root)
        self.record_path = self.fixture_root / "restoration.json"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def environment(self) -> dict[str, str]:
        """Build the explicitly guarded non-root fixture environment."""
        return {
            "HOME": os.environ.get("HOME", "/nonexistent"),
            "LANG": "C.UTF-8",
            "PATH": "/usr/bin:/usr/sbin:/bin",
            "XOAS_TARGET0_TESTING": "1",
            "XOAS_TARGET0_SYSFS_ROOT": str(self.fixture_root / "sys"),
            "XOAS_TARGET0_PROCFS_ROOT": str(self.fixture_root / "proc"),
        }

    def command(
        self,
        command: tuple[str, ...],
        *,
        cpu: int = 4,
        sibling: int = 16,
        target_user: str = "xoas-test",
        record_path: Path | None = None,
    ) -> list[str]:
        """Build one real controller command with explicit evidence output."""
        self.assertTrue(SCRIPT_PATH.is_file(), "measurement_session.sh is missing")
        output_path = self.record_path if record_path is None else record_path
        return [
            "/bin/bash",
            str(SCRIPT_PATH),
            "--cpu",
            str(cpu),
            "--sibling",
            str(sibling),
            "--target-user",
            target_user,
            "--restoration-record",
            str(output_path),
            "--",
            *command,
        ]

    def run_session(
        self,
        command: tuple[str, ...],
        **options: object,
    ) -> subprocess.CompletedProcess[str]:
        """Execute the real controller against the fixture boundary."""
        return subprocess.run(
            self.command(command, **options),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=self.environment(),
        )

    def assert_restored(self) -> None:
        """Require every mutable control to equal its exact pre-state."""
        self.assertEqual(self.control_state(), self.default_control_state())

    def control_state(self) -> tuple[str, str, str, str]:
        """Read the complete mutable fixture state."""
        return (
            read_control(
                self.fixture_root,
                "sys/devices/system/cpu/cpu4/cpufreq/scaling_governor",
            ),
            read_control(
                self.fixture_root,
                "sys/devices/system/cpu/cpu4/cpufreq/energy_performance_preference",
            ),
            read_control(
                self.fixture_root,
                "sys/devices/system/cpu/cpu16/online",
            ),
            read_control(
                self.fixture_root,
                "sys/devices/system/cpu/cpufreq/boost",
            ),
        )

    @staticmethod
    def default_control_state() -> tuple[str, str, str, str]:
        """Return the hand-authored valid fixture state."""
        return ("powersave", "balance_performance", "1", "1")

    def test_success_restores_exact_state_and_emits_closed_record(self) -> None:
        """A successful command must run minimally and restore every control."""
        command_result = self.fixture_root / "command-environment.json"
        governor_path = (
            self.fixture_root
            / "sys/devices/system/cpu/cpu4/cpufreq/scaling_governor"
        )
        preference_path = (
            self.fixture_root
            / "sys/devices/system/cpu/cpu4/cpufreq/energy_performance_preference"
        )
        sibling_path = (
            self.fixture_root / "sys/devices/system/cpu/cpu16/online"
        )
        python_source = (
            "import json, os, pathlib; "
            f"pathlib.Path({str(command_result)!r}).write_text("
            "json.dumps({"
            "'environment': dict(os.environ), "
            f"'governor': pathlib.Path({str(governor_path)!r}).read_text().strip(), "
            f"'preference': pathlib.Path({str(preference_path)!r}).read_text().strip(), "
            f"'sibling_online': pathlib.Path({str(sibling_path)!r}).read_text().strip()"
            "}, sort_keys=True), encoding='utf-8')"
        )
        completed = self.run_session(("/usr/bin/python3", "-c", python_source))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assert_restored()
        command_observations = json.loads(
            command_result.read_text(encoding="utf-8")
        )
        self.assertEqual(
            command_observations["environment"],
            {
                "HOME": "/nonexistent",
                "LANG": "C.UTF-8",
                "PATH": "/usr/bin:/usr/sbin",
            },
        )
        self.assertEqual(command_observations["governor"], "performance")
        self.assertEqual(command_observations["preference"], "performance")
        self.assertEqual(command_observations["sibling_online"], "0")
        record = json.loads(self.record_path.read_text(encoding="utf-8"))
        self.assertEqual(
            set(record),
            {
                "boost_unchanged",
                "command_exit_status",
                "cpu",
                "failure_reasons",
                "manifest_version",
                "performance_claim",
                "post_state",
                "pre_state",
                "restored",
                "sibling",
                "status",
            },
        )
        self.assertEqual(
            record["manifest_version"],
            "xoas.target0-measurement-session-restoration.v1",
        )
        self.assertIs(record["performance_claim"], False)
        self.assertEqual(record["status"], "restored")
        self.assertEqual(record["command_exit_status"], 0)
        self.assertIs(record["restored"], True)
        self.assertEqual(record["pre_state"], record["post_state"])
        self.assertIs(record["boost_unchanged"], True)
        self.assertNotIn("xoas-test", json.dumps(record))

    def test_command_failure_and_term_restore_exact_state(self) -> None:
        """Command failure and TERM must retain status while restoring controls."""
        failed = self.run_session(("/bin/sh", "-c", "exit 23"))
        self.assertEqual(failed.returncode, 23, failed.stderr)
        self.assert_restored()
        failed_record = json.loads(self.record_path.read_text(encoding="utf-8"))
        self.assertEqual(failed_record["command_exit_status"], 23)
        self.assertEqual(failed_record["status"], "restored")

        self.record_path.unlink()
        marker_path = self.fixture_root / "command-started"
        long_command = (
            "/bin/sh",
            "-c",
            f"touch {marker_path}; while :; do sleep 1; done",
        )
        process = subprocess.Popen(
            self.command(long_command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self.environment(),
        )
        deadline = time.monotonic() + 5
        while not marker_path.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertTrue(marker_path.exists(), "session command did not start")
        process.send_signal(signal.SIGTERM)
        _, standard_error = process.communicate(timeout=10)

        self.assertEqual(process.returncode, 143, standard_error)
        self.assert_restored()
        term_record = json.loads(self.record_path.read_text(encoding="utf-8"))
        self.assertEqual(term_record["command_exit_status"], 143)
        self.assertEqual(term_record["status"], "restored")

    def test_apply_write_failure_restores_prior_changes(self) -> None:
        """A partial apply failure must roll back every completed mutation."""
        sibling_online = (
            self.fixture_root
            / "sys/devices/system/cpu/cpu16/online"
        )
        sibling_online.chmod(0o444)

        completed = self.run_session(("/bin/true",))

        self.assertNotEqual(completed.returncode, 0)
        self.assert_restored()
        record = json.loads(self.record_path.read_text(encoding="utf-8"))
        self.assertEqual(record["status"], "apply_failed")
        self.assertIs(record["restored"], True)
        self.assertIsNone(record["command_exit_status"])

    def test_invalid_preconditions_fail_before_mutation(self) -> None:
        """Pair, policy, user, and command errors must fail without mutation."""
        cases = (
            ("not-pair", lambda: None, {"sibling": 17}, ("/bin/true",)),
            (
                "sibling-offline",
                lambda: write_text(
                    self.fixture_root,
                    "sys/devices/system/cpu/cpu16/online",
                    "0\n",
                ),
                {},
                ("/bin/true",),
            ),
            (
                "governor-unavailable",
                lambda: write_text(
                    self.fixture_root,
                    "sys/devices/system/cpu/cpu4/cpufreq/scaling_available_governors",
                    "powersave\n",
                ),
                {},
                ("/bin/true",),
            ),
            (
                "epp-unavailable",
                lambda: write_text(
                    self.fixture_root,
                    "sys/devices/system/cpu/cpu4/cpufreq/energy_performance_available_preferences",
                    "balance_performance power\n",
                ),
                {},
                ("/bin/true",),
            ),
            ("root-user", lambda: None, {"target_user": "root"}, ("/bin/true",)),
            ("empty-command", lambda: None, {}, ()),
        )

        for name, mutate, options, command in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    self.fixture_root = Path(temporary_directory)
                    make_session_fixture(self.fixture_root)
                    self.record_path = self.fixture_root / "restoration.json"
                    mutate()
                    state_before = self.control_state()
                    completed = self.run_session(command, **options)
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertEqual(self.control_state(), state_before)
                    self.assertFalse(self.record_path.exists())


if __name__ == "__main__":
    unittest.main()
