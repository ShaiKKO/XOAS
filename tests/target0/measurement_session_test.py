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


def canonical_json_bytes(record: object) -> bytes:
    """Return the normative canonical JSON encoding for one test record."""
    return (
        json.dumps(
            record,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


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
        self.fake_perf_path = self.fixture_root / "perf"
        self.fake_perf_path.write_text(
            """#!/bin/sh
set -eu
output=''
events=''
while [ "$#" -gt 0 ]; do
  case "$1" in
    stat|--no-big-num)
      shift
      ;;
    -x)
      test "$2" = ';'
      shift 2
      ;;
    --output)
      output=$2
      shift 2
      ;;
    --event)
      events=$2
      shift 2
      ;;
    --)
      shift
      break
      ;;
    *)
      exit 91
      ;;
  esac
done
test -n "$output"
test "$events" = 'cycles,instructions'
test "$#" -gt 0
printf '100000000;;cycles;1;100.00;;\n' >"$output"
printf '200000000;;instructions;1;100.00;;\n' >>"$output"
exec "$@"
""",
            encoding="utf-8",
        )
        self.fake_perf_path.chmod(0o755)

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
            "XOAS_TARGET0_PERF_PATH": str(self.fake_perf_path),
        }

    def command(
        self,
        command: tuple[str, ...],
        *,
        cpu: int = 4,
        sibling: int = 16,
        target_user: str = "xoas-test",
        record_path: Path | None = None,
        execution_mode: str | None = None,
        perf_output: Path | None = None,
        perf_events: str | None = None,
    ) -> list[str]:
        """Build one real controller command with explicit evidence output."""
        self.assertTrue(SCRIPT_PATH.is_file(), "measurement_session.sh is missing")
        output_path = self.record_path if record_path is None else record_path
        controller_command = [
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
        ]
        if execution_mode is not None:
            controller_command.extend(("--execution-mode", execution_mode))
        if perf_output is not None:
            controller_command.extend(("--perf-output", str(perf_output)))
        if perf_events is not None:
            controller_command.extend(("--perf-events", perf_events))
        controller_command.extend(("--", *command))
        return controller_command

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

    def test_restoration_record_uses_exact_canonical_json_bytes(self) -> None:
        """Restoration evidence must use the normative byte representation."""
        completed = self.run_session(("/usr/bin/true",))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        retained_bytes = self.record_path.read_bytes()
        self.assertEqual(
            retained_bytes,
            canonical_json_bytes(json.loads(retained_bytes.decode("utf-8"))),
        )

    def test_restores_sibling_then_governor_then_energy_preference(self) -> None:
        """Restoration must follow the complete amd-pstate dependency order."""
        traced_command = self.command(("/usr/bin/true",))
        traced_command.insert(1, "-x")
        completed = subprocess.run(
            traced_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=self.environment(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
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
        sibling_restore = f"+ writeValue {sibling_path} 1"
        governor_restore = (
            f"+ writeValue {governor_path} powersave"
        )
        preference_restore = (
            f"+ writeValue {preference_path} balance_performance"
        )
        sibling_index = completed.stderr.rfind(sibling_restore)
        governor_index = completed.stderr.rfind(governor_restore)
        preference_index = completed.stderr.rfind(preference_restore)
        self.assertNotEqual(sibling_index, -1, completed.stderr)
        self.assertNotEqual(governor_index, -1, completed.stderr)
        self.assertNotEqual(preference_index, -1, completed.stderr)
        self.assertLess(sibling_index, governor_index)
        self.assertLess(governor_index, preference_index)

    def test_privileged_perf_mode_demotes_child_and_restores_exact_state(
        self,
    ) -> None:
        """The closed perf frontend must preserve child isolation and restore."""
        command_result = self.fixture_root / "perf-command-environment.json"
        perf_output = self.fixture_root / "perf-stat.txt"
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

        completed = self.run_session(
            ("/usr/bin/python3", "-c", python_source),
            execution_mode="privileged-perf",
            perf_output=perf_output,
            perf_events="cycles,instructions",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assert_restored()
        self.assertEqual(
            perf_output.read_text(encoding="utf-8"),
            "100000000;;cycles;1;100.00;;\n"
            "200000000;;instructions;1;100.00;;\n",
        )
        observations = json.loads(command_result.read_text(encoding="utf-8"))
        self.assertEqual(
            observations["environment"],
            {
                "HOME": "/nonexistent",
                "LANG": "C.UTF-8",
                "PATH": "/usr/bin:/usr/sbin",
            },
        )
        self.assertEqual(observations["governor"], "performance")
        self.assertEqual(observations["preference"], "performance")
        self.assertEqual(observations["sibling_online"], "0")
        record = json.loads(self.record_path.read_text(encoding="utf-8"))
        self.assertEqual(record["command_exit_status"], 0)
        self.assertIs(record["restored"], True)
        self.assertNotIn("xoas-test", json.dumps(record))

    def test_perf_output_alias_fails_before_command_or_control_mutation(
        self,
    ) -> None:
        """Perf output must not collide with the restoration evidence path."""
        command_marker = self.fixture_root / "aliased-command-ran"
        state_before = self.control_state()

        completed = self.run_session(
            ("/usr/bin/touch", str(command_marker)),
            execution_mode="privileged-perf",
            perf_output=self.record_path,
            perf_events="cycles,instructions",
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(command_marker.exists())
        self.assertEqual(self.control_state(), state_before)
        self.assertFalse(self.record_path.exists())

    def test_duplicate_perf_option_fails_before_control_mutation(self) -> None:
        """A repeated closed-interface option must not silently replace input."""
        command_marker = self.fixture_root / "duplicate-option-command-ran"
        perf_output = self.fixture_root / "duplicate-option-perf.txt"
        state_before = self.control_state()
        command = self.command(
            ("/usr/bin/touch", str(command_marker)),
            execution_mode="privileged-perf",
            perf_output=perf_output,
            perf_events="cycles,instructions",
        )
        separator_index = command.index("--")
        command[separator_index:separator_index] = (
            "--perf-events",
            "branches",
        )

        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=self.environment(),
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(command_marker.exists())
        self.assertEqual(self.control_state(), state_before)
        self.assertFalse(self.record_path.exists())
        self.assertFalse(perf_output.exists())

    def test_invalid_perf_preconditions_fail_before_mutation(self) -> None:
        """Missing, conflicting, or unapproved perf options must fail early."""
        cases = (
            {
                "name": "missing-output",
                "execution_mode": "privileged-perf",
                "perf_events": "cycles,instructions",
            },
            {
                "name": "missing-events",
                "execution_mode": "privileged-perf",
                "perf_output": "perf.txt",
            },
            {
                "name": "unknown-event-group",
                "execution_mode": "privileged-perf",
                "perf_output": "perf.txt",
                "perf_events": "cycles,branches",
            },
            {
                "name": "probe-with-perf-output",
                "execution_mode": "probe",
                "perf_output": "perf.txt",
            },
            {
                "name": "unknown-mode",
                "execution_mode": "root-command",
            },
        )

        for case in cases:
            with self.subTest(name=case["name"]):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    self.fixture_root = Path(temporary_directory)
                    make_session_fixture(self.fixture_root)
                    self.record_path = self.fixture_root / "restoration.json"
                    self.fake_perf_path = self.fixture_root / "perf"
                    self.fake_perf_path.write_text(
                        "#!/bin/sh\nexit 99\n",
                        encoding="utf-8",
                    )
                    self.fake_perf_path.chmod(0o755)
                    state_before = self.control_state()
                    marker = self.fixture_root / "invalid-command-ran"
                    perf_output_name = case.get("perf_output")
                    perf_output = (
                        self.fixture_root / str(perf_output_name)
                        if perf_output_name is not None
                        else None
                    )

                    completed = self.run_session(
                        ("/usr/bin/touch", str(marker)),
                        execution_mode=str(case["execution_mode"]),
                        perf_output=perf_output,
                        perf_events=case.get("perf_events"),
                    )

                    self.assertNotEqual(completed.returncode, 0)
                    self.assertFalse(marker.exists())
                    self.assertEqual(self.control_state(), state_before)
                    self.assertFalse(self.record_path.exists())

    def test_perf_failure_restores_and_retains_exact_command_status(self) -> None:
        """A failed perf frontend must restore controls and retain its status."""
        perf_output = self.fixture_root / "unsupported-perf.txt"

        completed = self.run_session(
            ("/bin/true",),
            execution_mode="privileged-perf",
            perf_output=perf_output,
            perf_events="branches",
        )

        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assert_restored()
        record = json.loads(self.record_path.read_text(encoding="utf-8"))
        self.assertEqual(record["command_exit_status"], 1)
        self.assertEqual(record["status"], "restored")

    def test_dangling_perf_output_symlink_fails_before_mutation(self) -> None:
        """The privileged frontend must never follow a dangling output link."""
        missing_target = self.fixture_root / "missing-perf-target"
        perf_output = self.fixture_root / "dangling-perf-output"
        perf_output.symlink_to(missing_target)
        marker = self.fixture_root / "symlink-command-ran"
        state_before = self.control_state()

        completed = self.run_session(
            ("/usr/bin/touch", str(marker)),
            execution_mode="privileged-perf",
            perf_output=perf_output,
            perf_events="cycles,instructions",
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(marker.exists())
        self.assertFalse(missing_target.exists())
        self.assertEqual(self.control_state(), state_before)
        self.assertFalse(self.record_path.exists())

    def test_dangling_restoration_symlink_fails_before_mutation(self) -> None:
        """Restoration evidence must never follow or collide with a link."""
        missing_target = self.fixture_root / "missing-restoration-target"
        self.record_path.symlink_to(missing_target)
        marker = self.fixture_root / "restoration-symlink-command-ran"
        state_before = self.control_state()

        completed = self.run_session(("/usr/bin/touch", str(marker)))

        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(marker.exists())
        self.assertFalse(missing_target.exists())
        self.assertEqual(self.control_state(), state_before)

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
