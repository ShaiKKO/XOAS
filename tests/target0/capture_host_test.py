#!/usr/bin/env python3
"""Fixture-driven tests for non-secret Target 0 host capture."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import ModuleType, SimpleNamespace
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPOSITORY_ROOT / "tools/target0/capture_host.py"


class FakeCommandRunner:
    """Return controlled results only at external command boundaries."""

    def __init__(self, *, virtualization: str = "none", perf_available: bool = True):
        self.virtualization = virtualization
        self.perf_available = perf_available
        self.calls: list[tuple[tuple[str, ...], Path | None]] = []

    def __call__(
        self,
        command: tuple[str, ...],
        working_directory: Path | None = None,
    ) -> SimpleNamespace:
        self.calls.append((command, working_directory))
        if command == ("systemd-detect-virt",):
            return SimpleNamespace(
                returncode=1 if self.virtualization == "none" else 0,
                stdout=f"{self.virtualization}\n",
                stderr="",
            )
        if command[:2] == ("sudo", "-n") and "perf" in command:
            return SimpleNamespace(
                returncode=0 if self.perf_available else 1,
                stdout="",
                stderr="",
            )
        if command[:2] == ("git", "rev-parse"):
            return SimpleNamespace(returncode=0, stdout="a" * 40 + "\n", stderr="")
        if command[:2] == ("git", "status"):
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[0] == "dpkg-query":
            return SimpleNamespace(returncode=0, stdout="not-installed\n", stderr="")
        return SimpleNamespace(
            returncode=0,
            stdout=f"{command[0]} fixture-version\n",
            stderr="",
        )


def write_text(root: Path, relative_path: str, content: str) -> None:
    """Write one controlled virtual host file."""
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_host_fixture(root: Path) -> None:
    """Create a four-thread, two-core bare-metal AMD fixture."""
    write_text(root, "etc/os-release", "ID=ubuntu\nVERSION_ID=26.04\nVERSION_CODENAME=resolute\n")
    write_text(root, "proc/sys/kernel/osrelease", "7.0.0-30-generic\n")
    write_text(root, "proc/sys/kernel/version", "fixture-kernel\n")
    write_text(root, "proc/sys/kernel/random/boot_id", "11111111-2222-3333-4444-555555555555\n")
    write_text(root, "proc/sys/kernel/perf_event_paranoid", "4\n")
    write_text(root, "proc/sys/kernel/nmi_watchdog", "1\n")
    write_text(root, "proc/cmdline", "quiet splash\n")
    write_text(root, "proc/loadavg", "0.10 0.20 0.30 1/100 1000\n")
    write_text(
        root,
        "proc/meminfo",
        "MemTotal:       32768000 kB\n"
        "HugePages_Total:       0\n"
        "HugePages_Free:        0\n"
        "Hugepagesize:       2048 kB\n",
    )
    cpu_blocks = []
    for cpu in range(4):
        cpu_blocks.append(
            f"processor\t: {cpu}\n"
            "vendor_id\t: AuthenticAMD\n"
            "cpu family\t: 25\n"
            "model\t\t: 97\n"
            "model name\t: AMD Ryzen 9 7900X 12-Core Processor\n"
            "stepping\t: 2\n"
            "microcode\t: 0x0a60120a\n"
            "flags\t\t: fpu avx avx2 avx512f fma\n"
        )
    write_text(root, "proc/cpuinfo", "\n".join(cpu_blocks))
    write_text(
        root,
        "proc/interrupts",
        "           CPU0 CPU1 CPU2 CPU3\n  0: 10 20 30 40 IO-APIC timer\n",
    )
    write_text(root, "sys/devices/system/cpu/online", "0-3\n")
    write_text(root, "sys/devices/system/cpu/smt/active", "1\n")
    write_text(root, "sys/devices/system/cpu/cpufreq/boost", "1\n")
    write_text(root, "sys/devices/system/clocksource/clocksource0/current_clocksource", "tsc\n")
    write_text(
        root,
        "sys/devices/system/clocksource/clocksource0/available_clocksource",
        "tsc hpet\n",
    )
    write_text(root, "sys/kernel/mm/transparent_hugepage/enabled", "always [madvise] never\n")

    for cpu, core, sibling, ranking in (
        (0, 0, 2, 200),
        (1, 1, 3, 200),
        (2, 0, 0, 200),
        (3, 1, 1, 200),
    ):
        prefix = f"sys/devices/system/cpu/cpu{cpu}"
        write_text(root, f"{prefix}/topology/core_id", f"{core}\n")
        write_text(root, f"{prefix}/topology/physical_package_id", "0\n")
        write_text(
            root,
            f"{prefix}/topology/thread_siblings_list",
            f"{min(cpu, sibling)},{max(cpu, sibling)}\n",
        )
        write_text(root, f"{prefix}/cpufreq/amd_pstate_prefcore_ranking", f"{ranking}\n")
        write_text(root, f"{prefix}/cpufreq/scaling_driver", "amd-pstate-epp\n")
        write_text(root, f"{prefix}/cpufreq/scaling_governor", "powersave\n")
        write_text(root, f"{prefix}/cpufreq/scaling_available_governors", "performance powersave\n")
        write_text(root, f"{prefix}/cpufreq/energy_performance_preference", "balance_performance\n")
        write_text(
            root,
            f"{prefix}/cpufreq/energy_performance_available_preferences",
            "performance balance_performance power\n",
        )
        write_text(root, f"{prefix}/cpufreq/cpuinfo_min_freq", "400000\n")
        write_text(root, f"{prefix}/cpufreq/cpuinfo_max_freq", "5600000\n")
        write_text(root, f"{prefix}/cpufreq/scaling_cur_freq", "4700000\n")
        (root / f"{prefix}/node0").mkdir(parents=True, exist_ok=True)
        for cache_index, level, size, shared in (
            (0, 1, "32K", str(cpu)),
            (2, 2, "1024K", str(cpu)),
            (3, 3, "32768K", "0-3"),
        ):
            cache_prefix = f"{prefix}/cache/index{cache_index}"
            write_text(root, f"{cache_prefix}/level", f"{level}\n")
            write_text(root, f"{cache_prefix}/type", "Unified\n")
            write_text(root, f"{cache_prefix}/size", f"{size}\n")
            write_text(root, f"{cache_prefix}/shared_cpu_list", f"{shared}\n")

    (root / "sys/devices/system/node/node0").mkdir(parents=True)
    write_text(root, "sys/class/hwmon/hwmon0/name", "k10temp\n")
    write_text(root, "sys/class/hwmon/hwmon0/temp1_input", "45500\n")


def load_capture_module(test_case: unittest.TestCase) -> ModuleType:
    """Load the real module after making absence an assertion failure."""
    test_case.assertTrue(MODULE_PATH.is_file(), "capture_host.py is missing")
    specification = importlib.util.spec_from_file_location("xoas_capture_host", MODULE_PATH)
    test_case.assertIsNotNone(specification)
    test_case.assertIsNotNone(specification.loader)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class CaptureHostTest(unittest.TestCase):
    """Verify host capture and deterministic core selection."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.fixture_root = Path(self.temporary_directory.name)
        make_host_fixture(self.fixture_root)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def build_capture(
        self,
        module: ModuleType | None = None,
        **runner_options: object,
    ) -> tuple[ModuleType, dict[str, object]]:
        """Build one real record from the controlled virtual host."""
        if module is None:
            module = load_capture_module(self)
        record = module.build_capture(
            phase="prestate",
            source_root=self.fixture_root,
            command_runner=FakeCommandRunner(**runner_options),
            captured_at_utc="2026-08-29T00:00:00Z",
            repository_root=REPOSITORY_ROOT,
        )
        return module, record

    def test_capture_emits_closed_non_secret_topology(self) -> None:
        """A valid bare-metal fixture must produce the complete safe boundary."""
        module, record = self.build_capture()

        self.assertEqual(record["manifest_version"], "xoas.target0-host-capture.v1")
        self.assertIs(record["performance_claim"], False)
        self.assertEqual(record["phase"], "prestate")
        self.assertEqual(record["host"]["cpu"]["vendor_id"], "AuthenticAMD")
        self.assertEqual(record["host"]["topology"]["logical_cpu_count"], 4)
        self.assertEqual(record["host"]["topology"]["physical_core_count"], 2)
        self.assertEqual(record["host"]["clocksource"]["current"], "tsc")
        self.assertIs(record["host"]["perf"]["cycles_available"], True)
        self.assertEqual(len(record["host"]["boot_id_sha256"]), 64)
        module.validate_capture(record)
        serialized = json.dumps(record, sort_keys=True)
        for forbidden_text in ("hostname", "username", "home_directory", "ssh", "ip_address"):
            self.assertNotIn(forbidden_text, serialized)

    def test_capture_executes_git_in_declared_repository(self) -> None:
        """Repository identity must not depend on the caller's directory."""
        module = load_capture_module(self)
        runner = FakeCommandRunner()

        module.build_capture(
            phase="prestate",
            source_root=self.fixture_root,
            command_runner=runner,
            captured_at_utc="2026-08-29T00:00:00Z",
            repository_root=REPOSITORY_ROOT,
        )

        git_calls = [
            working_directory
            for command, working_directory in runner.calls
            if command[:2] in {("git", "rev-parse"), ("git", "status")}
        ]
        self.assertEqual(git_calls, [REPOSITORY_ROOT, REPOSITORY_ROOT])

    def test_capture_rejects_invalid_host_boundaries(self) -> None:
        """Qualification capture must fail closed on load-bearing host mismatches."""
        module, valid_record = self.build_capture()

        mutations = []
        missing_topology = copy.deepcopy(valid_record)
        missing_topology["host"]["topology"]["cpus"] = []
        mutations.append(missing_topology)

        mismatched_siblings = copy.deepcopy(valid_record)
        mismatched_siblings["host"]["topology"]["cpus"][0]["siblings"] = [0, 3]
        mutations.append(mismatched_siblings)

        wrong_clock = copy.deepcopy(valid_record)
        wrong_clock["host"]["clocksource"]["current"] = "hpet"
        mutations.append(wrong_clock)

        missing_pmu = copy.deepcopy(valid_record)
        missing_pmu["host"]["perf"]["cycles_available"] = False
        mutations.append(missing_pmu)

        credential_field = copy.deepcopy(valid_record)
        credential_field["host"]["username"] = "not allowed"
        mutations.append(credential_field)

        unknown_field = copy.deepcopy(valid_record)
        unknown_field["host"]["unreviewed_field"] = "not allowed"
        mutations.append(unknown_field)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(module.CaptureError):
                    module.validate_capture(mutation)

        with self.assertRaises(module.CaptureError):
            self.build_capture(module=module, virtualization="kvm")
        with self.assertRaises(module.CaptureError):
            self.build_capture(module=module, perf_available=False)

    def test_core_selector_applies_rank_interrupt_and_cpu_order(self) -> None:
        """Core selection must implement the locked three-key ordering."""
        module, record = self.build_capture()
        before = {0: 100, 1: 100, 2: 100, 3: 100}

        ranked_record = copy.deepcopy(record)
        ranked_record["host"]["topology"]["cpus"][0]["preferred_core_ranking"] = 250
        ranked_record["host"]["topology"]["cpus"][2]["preferred_core_ranking"] = 250
        ranked = module.select_core(
            ranked_record,
            before_interrupts=before,
            after_interrupts={0: 200, 1: 101, 2: 100, 3: 100},
            window_seconds=60,
        )
        self.assertEqual(ranked["cpu"], 0)
        self.assertEqual(ranked["sibling"], 2)

        quiet = module.select_core(
            record,
            before_interrupts=before,
            after_interrupts={0: 110, 1: 102, 2: 100, 3: 100},
            window_seconds=60,
        )
        self.assertEqual(quiet["cpu"], 1)
        self.assertEqual(quiet["interrupt_delta"], 2)

        lowest_cpu = module.select_core(
            record,
            before_interrupts=before,
            after_interrupts={0: 105, 1: 105, 2: 100, 3: 100},
            window_seconds=60,
        )
        self.assertEqual(lowest_cpu["cpu"], 0)

        with self.assertRaises(module.CaptureError):
            module.select_core(
                record,
                before_interrupts=before,
                after_interrupts=before,
                window_seconds=59,
            )


if __name__ == "__main__":
    unittest.main()
