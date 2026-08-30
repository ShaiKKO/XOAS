#!/usr/bin/env python3
"""Fixture-driven tests for Target 0 qualification campaign orchestration."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from typing import Callable
import unittest

sys.dont_write_bytecode = True


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TARGET0_TOOL_ROOT = REPOSITORY_ROOT / "tools/target0"
RUNNER_PATH = TARGET0_TOOL_ROOT / "run_qualification_campaign.py"
CAMPAIGN_VERIFIER_PATH = (
    TARGET0_TOOL_ROOT / "verify_qualification_campaign.py"
)
PREPARATION_PATH = TARGET0_TOOL_ROOT / "prepare_qualification_bundle.py"
CAPTURE_PATH = TARGET0_TOOL_ROOT / "capture_host.py"
CAPTURE_TEST_PATH = REPOSITORY_ROOT / "tests/target0/capture_host_test.py"
BUNDLE_SCHEMA_PATH = (
    REPOSITORY_ROOT / "schemas/target0-qualification-tool-bundle-v1.schema.json"
)
BUNDLE_EXAMPLE_PATH = (
    REPOSITORY_ROOT
    / "tests/target0/fixtures/qualification-tool-bundle-v1.example.json"
)
TOOLCHAIN_LOCK_PATH = (
    REPOSITORY_ROOT / "toolchains/target0-amd-ryzen9-7900x-v1.lock.json"
)
NONFINITE_JSON_TOKENS = {
    "nan": b"NaN",
    "positive_infinity": b"Infinity",
    "negative_infinity": b"-Infinity",
    "overflow": b"1e309",
}


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


def replace_json_number(
    content: bytes,
    key: str,
    replacement: bytes,
) -> bytes:
    """Replace one numeric JSON member with an explicit test token."""
    pattern = rb'("' + key.encode("ascii") + rb'":)-?\d+'
    updated, replacement_count = re.subn(
        pattern,
        rb"\g<1>" + replacement,
        content,
        count=1,
    )
    if replacement_count != 1:
        raise AssertionError(f"numeric JSON member is missing: {key}")
    return updated


def load_runner_module() -> ModuleType:
    """Load the real campaign runner after asserting its ownership path."""
    if not RUNNER_PATH.is_file():
        raise AssertionError("qualification campaign runner is missing")
    specification = importlib.util.spec_from_file_location(
        "xoas_run_qualification_campaign",
        RUNNER_PATH,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("qualification campaign runner cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    sys.path.insert(0, str(TARGET0_TOOL_ROOT))
    try:
        specification.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def load_preparation_module() -> ModuleType:
    """Load the real deployment validators used by campaign identity."""
    specification = importlib.util.spec_from_file_location(
        "xoas_prepare_qualification_bundle_for_campaign",
        PREPARATION_PATH,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("qualification bundle module cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def load_module(path: Path, name: str) -> ModuleType:
    """Load one repository test or tool support module by exact path."""
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise AssertionError(f"support module cannot be loaded: {path.name}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def run_git(repository: Path, *arguments: str) -> str:
    """Run one real fixture Git operation and return stripped output."""
    completed = subprocess.run(
        ("/usr/bin/git", "-C", repository, *arguments),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


class IdentityCommandRunner:
    """Run real fixture Git and literal authenticated toolchain responses."""

    def __init__(
        self,
        lock: dict[str, object],
        *,
        overrides: dict[tuple[str, ...], str] | None = None,
        after_command: Callable[[tuple[str, ...]], None] | None = None,
    ) -> None:
        """Bind command responses to one validated lock fixture."""
        compiler = next(
            executable
            for executable in lock["existing_executables"]
            if executable["name"] == "clang++-21"
        )
        linker_package = next(
            package
            for package in lock["apt"]["prestate"]["packages"]
            if package["name"] == "lld-21"
        )
        self.compiler = compiler
        self.linker_digest = "29" * 32
        self.linker_package = linker_package
        self.linker_version = "Ubuntu LLD 21.1.8 (compatible with GNU linkers)"
        self.overrides = {} if overrides is None else dict(overrides)
        self.after_command = after_command

    def __call__(
        self,
        command: tuple[str, ...],
        working_directory: Path | None = None,
        *,
        environment: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> SimpleNamespace:
        """Return one real Git or literal system-identity response."""
        del environment
        if command[0] == "/usr/bin/git":
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                cwd=working_directory,
                text=True,
                timeout=timeout,
            )
            result = SimpleNamespace(
                returncode=completed.returncode,
                stdout=self.overrides.get(command, completed.stdout),
                stderr=completed.stderr,
            )
            if self.after_command is not None:
                self.after_command(command)
            return result
        responses = {
            ("/usr/bin/readlink", "-f", "/usr/bin/clang++-21"): (
                f"{self.compiler['path']}\n"
            ),
            ("/usr/bin/clang++-21", "--version"): (
                f"{self.compiler['version_line']}\n"
            ),
            ("/usr/bin/clang++-21", "-dumpmachine"): "x86_64-pc-linux-gnu\n",
            ("/usr/bin/sha256sum", str(self.compiler["path"])): (
                f"{self.compiler['sha256']}  {self.compiler['path']}\n"
            ),
            ("/usr/bin/readlink", "-f", "/usr/bin/ld.lld-21"): (
                "/usr/lib/llvm-21/bin/lld\n"
            ),
            (
                "/usr/bin/dpkg-query",
                "-W",
                "-f=${Version}\\n",
                "lld-21",
            ): f"{self.linker_package['version']}\n",
            ("/usr/bin/dpkg-query", "-S", "/usr/lib/llvm-21/bin/lld"): (
                "lld-21: /usr/lib/llvm-21/bin/lld\n"
            ),
            ("/usr/bin/ld.lld-21", "--version"): f"{self.linker_version}\n",
            ("/usr/bin/sha256sum", "/usr/lib/llvm-21/bin/lld"): (
                f"{self.linker_digest}  /usr/lib/llvm-21/bin/lld\n"
            ),
        }
        if command == ("/usr/bin/dpkg", "-V", "lld-21"):
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command not in responses:
            raise AssertionError(f"unexpected identity command: {command!r}")
        result = SimpleNamespace(
            returncode=0,
            stdout=self.overrides.get(command, responses[command]),
            stderr="",
        )
        if self.after_command is not None:
            self.after_command(command)
        return result


class PreflightCommandRunner:
    """Compose real identity validation with controlled host observations."""

    def __init__(
        self,
        identity_runner: IdentityCommandRunner,
        host_runner: object,
        expected_commit: str,
    ) -> None:
        """Bind one checkout and host fixture to the operator command surface."""
        self.identity_runner = identity_runner
        self.host_runner = host_runner
        self.expected_commit = expected_commit

    def __call__(
        self,
        command: tuple[str, ...],
        working_directory: Path | None = None,
        *,
        environment: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> SimpleNamespace:
        """Route absolute deployment commands and relative host commands."""
        if command == (
            "/usr/bin/loginctl",
            "list-sessions",
            "--no-legend",
            "--no-pager",
        ):
            return SimpleNamespace(
                returncode=0,
                stdout="10 1000 target-user - pts/0 active no -\n",
                stderr="",
            )
        if command[0].startswith("/"):
            return self.identity_runner(
                command,
                working_directory,
                environment=environment,
                timeout=timeout,
            )
        if command[:2] == ("git", "rev-parse"):
            return SimpleNamespace(
                returncode=0,
                stdout=f"{self.expected_commit}\n",
                stderr="",
            )
        if command[:2] == ("git", "status"):
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return self.host_runner(command, working_directory)


def make_primary_process_record(cpu: int, seed: int) -> dict[str, object]:
    """Return one complete literal primary-process output fixture."""
    samples = [
        {
            "checksum": f"{round_index + 1:016x}",
            "elapsed_ns": 100_000_000,
            "involuntary_context_switches": 0,
            "observed_cpu_end": cpu,
            "observed_cpu_start": cpu,
            "round": round_index,
            "voluntary_context_switches": 0,
        }
        for round_index in range(30)
    ]
    return {
        "affinity_cpus": [cpu],
        "checksum": f"{sum(range(1, 31)):016x}",
        "failure_reasons": [],
        "iterations": 16_777_216,
        "manifest_version": "xoas.target0-qualification-process.v1",
        "max_observed_threads": 1,
        "performance_claim": False,
        "process_context_switches": {
            "involuntary_delta": 0,
            "voluntary_delta": 0,
        },
        "process_id": 100,
        "requested_cpu": cpu,
        "retained_rounds": 30,
        "samples": samples,
        "seed": seed,
        "status": "passed",
        "timer_clock": "CLOCK_MONOTONIC_RAW",
        "timer_overhead_ns": [10] * 10_000,
        "warmup_checksum": "0123456789abcdef",
        "warmup_rounds": 5,
    }


def assert_bounded_session_command(command: tuple[str, ...]) -> None:
    """Require the fixed TERM-restoring controller timeout boundary."""
    if command[:7] != (
        "/usr/bin/timeout",
        "--foreground",
        "--kill-after=5s",
        "--preserve-status",
        "--signal=TERM",
        "20s",
        "/usr/bin/bash",
    ):
        raise AssertionError("measurement session is not bounded")


class PrimarySessionRunner:
    """Materialize probe and restoration fixtures from the real command array."""

    def __init__(
        self,
        *,
        mutation: str | None = None,
        mutation_process: int = 1,
        source_root: Path | None = None,
    ) -> None:
        """Start with an optional one-session failure injection."""
        self.calls: list[tuple[str, ...]] = []
        self.mutation = mutation
        self.mutation_process = mutation_process
        self.source_root = source_root

    def __call__(
        self,
        command: tuple[str, ...],
        working_directory: Path | None = None,
        *,
        environment: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> SimpleNamespace:
        """Write exact child outputs and report one restored zero-status run."""
        del environment
        if timeout != 35:
            raise AssertionError("primary controller timeout is not bounded")
        assert_bounded_session_command(command)
        self.calls.append(command)
        if working_directory is None:
            raise AssertionError("primary session working directory is missing")
        separator = command.index("--")
        restoration_path = Path(
            command[command.index("--restoration-record") + 1]
        )
        cpu = int(command[command.index("--cpu") + 1])
        sibling = int(command[command.index("--sibling") + 1])
        child = command[separator + 1 :]
        seed = int(child[child.index("--seed") + 1])
        process_path = Path(child[child.index("--output") + 1])
        if stat.S_IMODE(process_path.parent.stat().st_mode) != 0o1733:
            raise AssertionError("primary child output boundary is not writable")
        process_record = make_primary_process_record(cpu, seed)
        inject = len(self.calls) == self.mutation_process
        if inject and self.mutation == "invalid_schema":
            process_record["unknown"] = False
        elif inject and self.mutation == "duration_low":
            process_record["samples"][0]["elapsed_ns"] = 19_000_000
        elif inject and self.mutation == "duration_high":
            process_record["samples"][0]["elapsed_ns"] = 201_000_000
        elif inject and self.mutation == "migration":
            process_record["samples"][0]["observed_cpu_end"] = cpu + 1
        elif inject and self.mutation == "thread":
            process_record["max_observed_threads"] = 2
            process_record["status"] = "failed"
            process_record["failure_reasons"] = ["thread_count_changed"]
        elif inject and self.mutation == "checksum":
            process_record["checksum"] = "0000000000000000"
        process_bytes = canonical_json_bytes(process_record)
        if inject and self.mutation == "noncanonical_process":
            process_bytes = (json.dumps(process_record, indent=2) + "\n").encode(
                "utf-8"
            )
        if inject and self.mutation is not None and self.mutation.startswith(
            "nonfinite_process_"
        ):
            token_name = self.mutation.removeprefix("nonfinite_process_")
            process_bytes = replace_json_number(
                process_bytes,
                "iterations",
                NONFINITE_JSON_TOKENS[token_name],
            )
        process_path.write_bytes(process_bytes)
        state = {
            "boost": 1,
            "energy_performance_preference": "balance_performance",
            "governor": "powersave",
            "selected_cpu_interrupts": 100,
            "sibling_online": 1,
        }
        post_state = dict(state)
        post_state["selected_cpu_interrupts"] = 101
        return_status = (
            9 if inject and self.mutation == "process_execution" else 0
        )
        restoration = {
            "boost_unchanged": True,
            "command_exit_status": return_status,
            "cpu": cpu,
            "failure_reasons": [],
            "manifest_version": (
                "xoas.target0-measurement-session-restoration.v1"
            ),
            "performance_claim": False,
            "post_state": post_state,
            "pre_state": state,
            "restored": True,
            "sibling": sibling,
            "status": "restored",
        }
        if inject and self.mutation == "restoration":
            restoration["boost_unchanged"] = False
            restoration["failure_reasons"] = ["restoration_failed"]
            restoration["restored"] = False
            restoration["status"] = "restoration_failed"
            return_status = 70
        if inject and self.mutation in {"thermal_alarm", "thermal_threshold"}:
            if self.source_root is None:
                raise AssertionError("thermal mutation source root is missing")
            if self.mutation == "thermal_alarm":
                write_text(
                    self.source_root,
                    "sys/class/hwmon/hwmon0/temp1_crit_alarm",
                    "1\n",
                )
            else:
                write_text(
                    self.source_root,
                    "sys/class/hwmon/hwmon0/temp1_crit",
                    "45500\n",
                )
        restoration_bytes = canonical_json_bytes(restoration)
        if inject and self.mutation == "noncanonical_restoration":
            restoration_bytes = (
                json.dumps(restoration, indent=2) + "\n"
            ).encode("utf-8")
        if inject and self.mutation is not None and self.mutation.startswith(
            "nonfinite_restoration_"
        ):
            token_name = self.mutation.removeprefix(
                "nonfinite_restoration_"
            )
            restoration_bytes = replace_json_number(
                restoration_bytes,
                "cpu",
                NONFINITE_JSON_TOKENS[token_name],
            )
        restoration_path.write_bytes(restoration_bytes)
        return SimpleNamespace(returncode=return_status, stdout="", stderr="")


class PmuSessionRunner:
    """Materialize supported or unsupported perf-session fixture evidence."""

    def __init__(
        self,
        unsupported_events: set[str] | None = None,
        *,
        running_percentages: dict[str, str] | None = None,
        unsupported_exit_statuses: dict[str, int] | None = None,
    ) -> None:
        """Select unsupported events and explicit supported-event scaling."""
        self.unsupported_events = (
            set() if unsupported_events is None else set(unsupported_events)
        )
        self.running_percentages = (
            {} if running_percentages is None else dict(running_percentages)
        )
        self.unsupported_exit_statuses = (
            {}
            if unsupported_exit_statuses is None
            else dict(unsupported_exit_statuses)
        )
        self.calls: list[tuple[str, ...]] = []

    def __call__(
        self,
        command: tuple[str, ...],
        working_directory: Path | None = None,
        *,
        environment: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> SimpleNamespace:
        """Write raw perf, process, and restoration records for one session."""
        del environment
        if timeout != 35:
            raise AssertionError("PMU controller timeout is not bounded")
        if working_directory is None:
            raise AssertionError("PMU session working directory is missing")
        assert_bounded_session_command(command)
        self.calls.append(command)
        events = command[command.index("--perf-events") + 1]
        perf_output = Path(command[command.index("--perf-output") + 1])
        separator = command.index("--")
        cpu = int(command[command.index("--cpu") + 1])
        sibling = int(command[command.index("--sibling") + 1])
        restoration_path = Path(
            command[command.index("--restoration-record") + 1]
        )
        child = command[separator + 1 :]
        seed = int(child[child.index("--seed") + 1])
        process_path = Path(child[child.index("--output") + 1])
        if stat.S_IMODE(process_path.parent.stat().st_mode) != 0o1733:
            raise AssertionError("PMU child output boundary is not writable")
        process_path.write_bytes(
            canonical_json_bytes(make_primary_process_record(cpu, seed))
        )
        requested_events = events.split(",")
        unsupported = any(
            event in self.unsupported_events for event in requested_events
        )
        if unsupported:
            raw_lines = [
                f"<not supported>;;{event};0;;;"
                for event in requested_events
            ]
            command_status = self.unsupported_exit_statuses.get(
                requested_events[0],
                129,
            )
        else:
            raw_lines = [
                f"{1000 + index};;{event};0;"
                f"{self.running_percentages.get(event, '100.00')};;"
                for index, event in enumerate(requested_events)
            ]
            command_status = 0
        perf_output.write_text("\n".join(raw_lines) + "\n", encoding="utf-8")
        state = {
            "boost": 1,
            "energy_performance_preference": "balance_performance",
            "governor": "powersave",
            "selected_cpu_interrupts": 100,
            "sibling_online": 1,
        }
        post_state = dict(state)
        post_state["selected_cpu_interrupts"] = 101
        restoration_path.write_bytes(
            canonical_json_bytes(
                {
                    "boost_unchanged": True,
                    "command_exit_status": command_status,
                    "cpu": cpu,
                    "failure_reasons": [],
                    "manifest_version": (
                        "xoas.target0-measurement-session-restoration.v1"
                    ),
                    "performance_claim": False,
                    "post_state": post_state,
                    "pre_state": state,
                    "restored": True,
                    "sibling": sibling,
                    "status": "restored",
                }
            )
        )
        return SimpleNamespace(returncode=command_status, stdout="", stderr="")


def make_identity_repository(
    root: Path,
    source_paths: list[str],
) -> tuple[Path, str]:
    """Create one clean real checkout containing the fixed identity sources."""
    repository = root / "XOAS"
    repository.mkdir()
    run_git(repository, "init", "--quiet")
    run_git(repository, "config", "user.name", "XOAS Test")
    run_git(repository, "config", "user.email", "test@xoas.invalid")
    for relative_path in source_paths:
        path = repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative_path.startswith("schemas/"):
            path.write_bytes((REPOSITORY_ROOT / relative_path).read_bytes())
        else:
            path.write_text(f"fixture:{relative_path}\n", encoding="utf-8")
    campaign_schema = (
        repository / "schemas/target0-qualification-campaign-v1.schema.json"
    )
    if not campaign_schema.exists():
        campaign_schema.write_bytes(
            (
                REPOSITORY_ROOT
                / "schemas/target0-qualification-campaign-v1.schema.json"
            ).read_bytes()
        )
    repository_lock = (
        repository / "toolchains/target0-amd-ryzen9-7900x-v1.lock.json"
    )
    repository_lock.parent.mkdir(parents=True, exist_ok=True)
    repository_lock.write_bytes(TOOLCHAIN_LOCK_PATH.read_bytes())
    run_git(repository, "add", ".")
    run_git(repository, "commit", "--quiet", "-m", "identity fixture")
    run_git(
        repository,
        "remote",
        "add",
        "origin",
        "https://github.com/ShaiKKO/XOAS.git",
    )
    return repository, run_git(repository, "rev-parse", "HEAD")


def finalize_identity_bundle(
    bundle_root: Path,
    manifest: dict[str, object],
    preparation: ModuleType,
) -> None:
    """Materialize and finalize one accepted synthetic deployment bundle."""
    executable_bytes = b"synthetic accepted ELF\n"
    executable_digest = hashlib.sha256(executable_bytes).hexdigest()
    for executable in [
        *manifest["build"]["builds"],
        manifest["build"]["accepted_executable"],
    ]:
        path = bundle_root / executable["path"]
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_bytes(executable_bytes)
        path.chmod(0o700)
        executable["sha256"] = executable_digest
        executable["size_bytes"] = len(executable_bytes)
    manifest["build"]["executable_sha256"] = executable_digest
    manifest["build"]["identical"] = True
    inspection_directory = bundle_root / "inspection"
    inspection_directory.mkdir(mode=0o700)
    for log in manifest["elf"]["inspection_logs"]:
        record = {
            "command": ["/usr/bin/readelf", "-h"],
            "exit_status": 0,
            "name": log["name"],
            "status": "passed",
            "stderr_sha256": hashlib.sha256(b"").hexdigest(),
            "stdout_sha256": hashlib.sha256(b"ELF fixture\n").hexdigest(),
        }
        path = inspection_directory / f"{log['name']}.json"
        path.write_bytes(preparation.canonical_json_bytes(record))
        path.chmod(0o600)
        log["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    compatibility_directory = bundle_root / "compatibility"
    compatibility_directory.mkdir(mode=0o700)
    for record in manifest["compatibility_tests"]:
        stdout_bytes = b"compatibility passed\n"
        stderr_bytes = b""
        record["stdout_sha256"] = hashlib.sha256(stdout_bytes).hexdigest()
        record["stderr_sha256"] = hashlib.sha256(stderr_bytes).hexdigest()
        outputs = {
            f"{record['name']}.stdout.log": stdout_bytes,
            f"{record['name']}.stderr.log": stderr_bytes,
            f"{record['name']}.json": preparation.canonical_json_bytes(record),
        }
        for name, content in outputs.items():
            path = compatibility_directory / name
            path.write_bytes(content)
            path.chmod(0o600)
    preparation.finalize_bundle(bundle_root, manifest, BUNDLE_SCHEMA_PATH)


def write_text(root: Path, relative_path: str, content: str) -> None:
    """Write one controlled sysfs or command fixture value."""
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class QualificationCampaignIdentityTest(unittest.TestCase):
    """Verify live identity recomputation against real retained inputs."""

    def test_runner_help_is_read_only(self) -> None:
        """Inspecting the runner interface must not dirty the source tree."""
        bytecode_directory = TARGET0_TOOL_ROOT / "__pycache__"
        self.assertFalse(bytecode_directory.exists())
        result = subprocess.run(
            (sys.executable, RUNNER_PATH, "--help"),
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("preflight", result.stdout)
        self.assertIn("run", result.stdout)
        self.assertFalse(bytecode_directory.exists())

    def test_live_identity_accepts_exact_checkout_bundle_and_toolchain(
        self,
    ) -> None:
        """Every independently recomputed identity must bind to the bundle."""
        runner = load_runner_module()
        self.assertTrue(
            hasattr(runner, "collect_live_identity"),
            "live identity collector is missing",
        )
        preparation = load_preparation_module()
        example = json.loads(BUNDLE_EXAMPLE_PATH.read_text(encoding="utf-8"))
        lock = json.loads(TOOLCHAIN_LOCK_PATH.read_text(encoding="utf-8"))
        command_runner = IdentityCommandRunner(lock)
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            toolchain_lock = fixture_root / "toolchain-lock.json"
            toolchain_lock.write_bytes(TOOLCHAIN_LOCK_PATH.read_bytes())
            repository, expected_commit = make_identity_repository(
                fixture_root,
                [source["path"] for source in example["sources"]],
            )
            repository_identity = preparation.validate_repository(
                repository,
                expected_commit,
                command_runner,
            )
            provisioning_lock = preparation.validate_toolchain_lock(
                toolchain_lock,
                repository / "schemas/target0-toolchain-lock-v1.schema.json",
            )
            compiler = preparation.validate_compiler(lock, command_runner)
            linker = preparation.validate_linker(lock, command_runner)
            manifest = copy.deepcopy(example)
            manifest["repository"] = repository_identity
            manifest["provisioning_lock"] = provisioning_lock
            manifest["sources"] = preparation.collect_source_records(repository)
            manifest["toolchain"] = {"compiler": compiler, "linker": linker}
            bundle_root = fixture_root / "bundle"
            bundle_root.mkdir()
            finalize_identity_bundle(bundle_root, manifest, preparation)

            identity = runner.collect_live_identity(
                repository_root=repository,
                expected_commit=expected_commit,
                bundle_directory=bundle_root,
                bundle_schema=BUNDLE_SCHEMA_PATH,
                toolchain_lock=toolchain_lock,
                selected_cpu=4,
                sibling=16,
                boot_id_sha256="42" * 32,
                command_runner=command_runner,
            )
            campaign_root = fixture_root / "campaign"
            campaign_root.mkdir(mode=0o700)
            retained_inputs = runner.retain_verified_bundle_inputs(
                campaign_root=campaign_root,
                bundle_directory=bundle_root,
                bundle_schema=BUNDLE_SCHEMA_PATH,
            )

            self.assertEqual(
                identity["repository"],
                {
                    field: repository_identity[field]
                    for field in (
                        "actual_commit",
                        "expected_commit",
                        "tree",
                        "tree_state",
                    )
                },
            )
            self.assertEqual(identity["sources"], manifest["sources"])
            self.assertEqual(
                identity["selected_core"],
                {"cpu": 4, "sibling": 16},
            )
            self.assertNotIn(
                "execution_subject",
                identity["provisioning_lock"],
            )
            self.assertEqual(
                sorted(retained_inputs),
                [
                    "bundle_acceptance",
                    "bundle_inventory",
                    "bundle_manifest",
                    "executable",
                ],
            )
            for record in retained_inputs.values():
                retained_path = campaign_root / record["path"]
                self.assertTrue(retained_path.is_file())
                self.assertEqual(
                    hashlib.sha256(retained_path.read_bytes()).hexdigest(),
                    record["sha256"],
                )
            self.assertEqual(
                (
                    campaign_root / retained_inputs["executable"]["path"]
                ).read_bytes(),
                (
                    bundle_root / "bin/xoas-target0-qualification-probe"
                ).read_bytes(),
            )
            with self.assertRaises(runner.CampaignPhaseError) as caught:
                runner.retain_verified_bundle_inputs(
                    campaign_root=campaign_root,
                    bundle_directory=bundle_root,
                    bundle_schema=BUNDLE_SCHEMA_PATH,
                )
            self.assertEqual(
                caught.exception.code,
                "evidence_inventory_failure",
            )

    def test_live_identity_reports_closed_codes_for_every_drift_class(
        self,
    ) -> None:
        """No identity failure may expose arbitrary validator diagnostics."""
        runner = load_runner_module()
        preparation = load_preparation_module()
        example = json.loads(BUNDLE_EXAMPLE_PATH.read_text(encoding="utf-8"))
        lock_bytes = TOOLCHAIN_LOCK_PATH.read_bytes()
        lock = json.loads(lock_bytes.decode("utf-8"))
        base_runner = IdentityCommandRunner(lock)
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            toolchain_lock = fixture_root / "toolchain-lock.json"
            toolchain_lock.write_bytes(lock_bytes)
            repository, expected_commit = make_identity_repository(
                fixture_root,
                [source["path"] for source in example["sources"]],
            )
            repository_identity = preparation.validate_repository(
                repository,
                expected_commit,
                base_runner,
            )
            provisioning_lock = preparation.validate_toolchain_lock(
                toolchain_lock,
                repository / "schemas/target0-toolchain-lock-v1.schema.json",
            )
            compiler = preparation.validate_compiler(lock, base_runner)
            linker = preparation.validate_linker(lock, base_runner)
            manifest = copy.deepcopy(example)
            manifest["repository"] = repository_identity
            manifest["provisioning_lock"] = provisioning_lock
            manifest["sources"] = preparation.collect_source_records(repository)
            manifest["toolchain"] = {"compiler": compiler, "linker": linker}
            bundle_root = fixture_root / "bundle"
            bundle_root.mkdir()
            finalize_identity_bundle(bundle_root, manifest, preparation)

            def assert_rejection(
                expected_code: str,
                *,
                command_runner: IdentityCommandRunner = base_runner,
                commit: str = expected_commit,
                boot_digest: str = "42" * 32,
            ) -> None:
                with self.assertRaises(runner.CampaignPhaseError) as caught:
                    runner.collect_live_identity(
                        repository_root=repository,
                        expected_commit=commit,
                        bundle_directory=bundle_root,
                        bundle_schema=BUNDLE_SCHEMA_PATH,
                        toolchain_lock=toolchain_lock,
                        selected_cpu=4,
                        sibling=16,
                        boot_id_sha256=boot_digest,
                        command_runner=command_runner,
                    )
                self.assertEqual(caught.exception.code, expected_code)
                self.assertEqual(str(caught.exception), expected_code)

            assert_rejection("preflight_identity_mismatch", commit="0" * 40)
            assert_rejection(
                "preflight_identity_mismatch",
                command_runner=IdentityCommandRunner(
                    lock,
                    overrides={
                        ("/usr/bin/git", "rev-parse", "HEAD^{tree}"): (
                            f"{'1' * 40}\n"
                        )
                    },
                ),
            )
            dirty_path = repository / "untracked.fixture"
            dirty_path.write_text("dirty\n", encoding="utf-8")
            assert_rejection("preflight_identity_mismatch")
            dirty_path.unlink()
            assert_rejection(
                "preflight_identity_mismatch",
                command_runner=IdentityCommandRunner(
                    lock,
                    overrides={
                        (
                            "/usr/bin/git",
                            "remote",
                            "get-url",
                            "origin",
                        ): "https://example.invalid/not-xoas.git\n"
                    },
                ),
            )
            bundle_manifest_path = bundle_root / "bundle.json"
            bundle_manifest_bytes = bundle_manifest_path.read_bytes()
            bundle_manifest_path.write_bytes(bundle_manifest_bytes + b" ")
            assert_rejection("bundle_verification_failure")
            bundle_manifest_path.write_bytes(bundle_manifest_bytes)
            executable_path = bundle_root / "bin/xoas-target0-qualification-probe"
            executable_bytes = executable_path.read_bytes()
            executable_path.write_bytes(executable_bytes + b"changed")
            assert_rejection("bundle_verification_failure")
            executable_path.write_bytes(executable_bytes)
            assert_rejection(
                "preflight_identity_mismatch",
                command_runner=IdentityCommandRunner(
                    lock,
                    overrides={
                        ("/usr/bin/clang++-21", "--version"): (
                            "different compiler\n"
                        )
                    },
                ),
            )
            assert_rejection(
                "preflight_identity_mismatch",
                command_runner=IdentityCommandRunner(
                    lock,
                    overrides={
                        ("/usr/bin/ld.lld-21", "--version"): (
                            "different linker\n"
                        )
                    },
                ),
            )
            source_path = repository / manifest["sources"][0]["path"]
            source_bytes = source_path.read_bytes()

            def mutate_source_after_repository_validation(
                command: tuple[str, ...],
            ) -> None:
                if command == (
                    "/usr/bin/git",
                    "remote",
                    "get-url",
                    "origin",
                ):
                    source_path.write_bytes(source_bytes + b"changed")

            assert_rejection(
                "preflight_identity_mismatch",
                command_runner=IdentityCommandRunner(
                    lock,
                    after_command=mutate_source_after_repository_validation,
                ),
            )
            source_path.write_bytes(source_bytes)
            toolchain_lock.write_bytes(lock_bytes + b"changed")
            assert_rejection("preflight_identity_mismatch")
            toolchain_lock.write_bytes(lock_bytes)
            assert_rejection(
                "preflight_identity_mismatch",
                boot_digest="not-a-digest",
            )


class QualificationCampaignThermalTest(unittest.TestCase):
    """Verify exact thermal input, threshold, alarm, and fault capture."""

    def test_thermal_capture_retains_thresholds_and_unavailable_state(
        self,
    ) -> None:
        """A missing threshold must be explicit without inventing a limit."""
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_root = Path(temporary_directory)
            write_text(source_root, "sys/class/hwmon/hwmon0/name", "amdgpu\n")
            write_text(
                source_root,
                "sys/class/hwmon/hwmon0/temp1_label",
                "edge\n",
            )
            write_text(
                source_root,
                "sys/class/hwmon/hwmon0/temp1_input",
                "65000\n",
            )
            write_text(
                source_root,
                "sys/class/hwmon/hwmon0/temp1_crit",
                "100000\n",
            )
            write_text(
                source_root,
                "sys/class/hwmon/hwmon0/temp1_emergency",
                "105000\n",
            )
            write_text(
                source_root,
                "sys/class/hwmon/hwmon0/temp1_crit_alarm",
                "0\n",
            )
            write_text(
                source_root,
                "sys/class/hwmon/hwmon0/temp1_fault",
                "0\n",
            )
            write_text(source_root, "sys/class/hwmon/hwmon1/name", "k10temp\n")
            write_text(
                source_root,
                "sys/class/hwmon/hwmon1/temp3_label",
                "Tccd1\n",
            )
            write_text(
                source_root,
                "sys/class/hwmon/hwmon1/temp3_input",
                "54000\n",
            )

            record = runner.capture_thermal_state(source_root)

        self.assertEqual(
            record,
            {
                "failure_reasons": [],
                "manifest_version": "xoas.target0-thermal-state.v1",
                "performance_claim": False,
                "sensors": [
                    {
                        "critical_millidegrees_c": 100000,
                        "critical_alarm": 0,
                        "device_index": 0,
                        "device_name": "amdgpu",
                        "emergency_alarm": None,
                        "emergency_millidegrees_c": 105000,
                        "fault": 0,
                        "input_millidegrees_c": 65000,
                        "label": "edge",
                        "maximum_millidegrees_c": None,
                        "sensor": "temp1",
                        "threshold_status": "below_threshold",
                    },
                    {
                        "critical_millidegrees_c": None,
                        "critical_alarm": None,
                        "device_index": 1,
                        "device_name": "k10temp",
                        "emergency_alarm": None,
                        "emergency_millidegrees_c": None,
                        "fault": None,
                        "input_millidegrees_c": 54000,
                        "label": "Tccd1",
                        "maximum_millidegrees_c": None,
                        "sensor": "temp3",
                        "threshold_status": "threshold_unavailable",
                    },
                ],
                "status": "passed",
                "summary": {
                    "alarm_count": 0,
                    "fault_count": 0,
                    "sensor_count": 2,
                    "threshold_unavailable_count": 1,
                    "threshold_violation_count": 0,
                },
            },
        )

    def test_thermal_capture_rejects_alarm_fault_and_threshold(self) -> None:
        """Every objective unsafe thermal condition must fail independently."""
        runner = load_runner_module()
        fixtures = (
            ("temp1_crit_alarm", "1\n", 65000, 100000, "thermal_alarm"),
            ("temp1_fault", "1\n", 65000, 100000, "thermal_sensor_fault"),
            (
                "temp1_crit_alarm",
                "0\n",
                100000,
                100000,
                "thermal_threshold_violation",
            ),
        )
        for state_name, state, temperature, critical, reason in fixtures:
            with self.subTest(reason=reason):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    source_root = Path(temporary_directory)
                    write_text(
                        source_root,
                        "sys/class/hwmon/hwmon0/name",
                        "amdgpu\n",
                    )
                    write_text(
                        source_root,
                        "sys/class/hwmon/hwmon0/temp1_input",
                        f"{temperature}\n",
                    )
                    write_text(
                        source_root,
                        "sys/class/hwmon/hwmon0/temp1_crit",
                        f"{critical}\n",
                    )
                    write_text(
                        source_root,
                        f"sys/class/hwmon/hwmon0/{state_name}",
                        state,
                    )

                    record = runner.capture_thermal_state(source_root)

                self.assertEqual(record["status"], "failed")
                self.assertIn(reason, record["failure_reasons"])


class QualificationCampaignSessionTest(unittest.TestCase):
    """Verify non-secret interactive-session eligibility aggregation."""

    def test_session_capture_retains_only_aggregate_target_eligibility(
        self,
    ) -> None:
        """A retained username or session identifier must fail this contract."""
        runner = load_runner_module()
        self.assertTrue(
            hasattr(runner, "capture_interactive_sessions"),
            "interactive-session capture is missing",
        )

        def command_runner(
            command: tuple[str, ...],
        ) -> SimpleNamespace:
            self.assertEqual(
                command,
                (
                    "/usr/bin/loginctl",
                    "list-sessions",
                    "--no-legend",
                    "--no-pager",
                ),
            )
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "10 1000 target-user - pts/0 active no -\n"
                    "11 1000 target-user - pts/1 active no -\n"
                    "12 1000 target-user - pts/2 active no -\n"
                ),
                stderr="",
            )

        record = runner.capture_interactive_sessions(
            command_runner,
            "target-user",
        )

        self.assertEqual(
            record,
            {
                "expected": 3,
                "manifest_version": "xoas.target0-interactive-sessions.v1",
                "performance_claim": False,
                "root": 0,
                "status": "passed",
                "total": 3,
                "unexpected": 0,
            },
        )
        self.assertNotIn("target-user", json.dumps(record))

    def test_session_capture_rejects_root_or_unexpected_users(self) -> None:
        """Only aggregate sessions for the declared non-root user are eligible."""
        runner = load_runner_module()
        for output, expected_counts in (
            (
                "10 0 root - pts/0 active no -\n",
                {"expected": 0, "root": 1, "unexpected": 0},
            ),
            (
                "10 1001 another-user - pts/0 active no -\n",
                {"expected": 0, "root": 0, "unexpected": 1},
            ),
        ):
            with self.subTest(output=output):
                record = runner.capture_interactive_sessions(
                    lambda command: SimpleNamespace(
                        returncode=0,
                        stdout=output,
                        stderr="",
                    ),
                    "target-user",
                )
                self.assertEqual(record["status"], "failed")
                for field, value in expected_counts.items():
                    self.assertEqual(record[field], value)


class QualificationCampaignPreflightTest(unittest.TestCase):
    """Verify fail-closed qualification preflight eligibility."""

    @staticmethod
    def host_capture(load_average_1m: float) -> dict[str, object]:
        """Return the exact load-bearing subset of a validated host capture."""
        return {
            "host": {
                "clocksource": {"current": "tsc"},
                "load": {
                    "load_average": [load_average_1m, 0.1, 0.1]
                },
                "perf": {
                    "cycles_available": True,
                    "instructions_available": True,
                },
                "virtualization": {"kind": "none"},
            },
            "repository": {"tree_state": "clean"},
        }

    @staticmethod
    def session_record() -> dict[str, object]:
        """Return one accepted aggregate interactive-session record."""
        return {
            "expected": 3,
            "manifest_version": "xoas.target0-interactive-sessions.v1",
            "performance_claim": False,
            "root": 0,
            "status": "passed",
            "total": 3,
            "unexpected": 0,
        }

    @staticmethod
    def thermal_record() -> dict[str, object]:
        """Return one accepted aggregate thermal record."""
        return {
            "failure_reasons": [],
            "manifest_version": "xoas.target0-thermal-state.v1",
            "performance_claim": False,
            "sensors": [{"sensor": "fixture"}],
            "status": "passed",
            "summary": {
                "alarm_count": 0,
                "fault_count": 0,
                "sensor_count": 1,
                "threshold_unavailable_count": 1,
                "threshold_violation_count": 0,
            },
        }

    def test_preflight_accepts_0_499_and_rejects_0_5_load(self) -> None:
        """The one-minute load threshold must remain strictly below 0.5."""
        runner = load_runner_module()
        self.assertTrue(
            hasattr(runner, "evaluate_preflight"),
            "preflight evaluator is missing",
        )

        accepted = runner.evaluate_preflight(
            host_capture=self.host_capture(0.499),
            thermal=self.thermal_record(),
            sessions=self.session_record(),
            exclusive_use_confirmed=True,
        )
        rejected = runner.evaluate_preflight(
            host_capture=self.host_capture(0.5),
            thermal=self.thermal_record(),
            sessions=self.session_record(),
            exclusive_use_confirmed=True,
        )

        self.assertEqual(accepted["status"], "passed")
        self.assertEqual(accepted["failure_reasons"], [])
        self.assertEqual(accepted["load_average_1m"], 0.499)
        self.assertEqual(rejected["status"], "failed")
        self.assertEqual(rejected["failure_reasons"], ["load_average_too_high"])

    def test_preflight_parser_requires_every_approved_option(self) -> None:
        """No path, identity, campaign, user, or exclusivity input is implicit."""
        runner = load_runner_module()
        with self.assertRaises(SystemExit):
            runner.parse_arguments(["preflight"])
        options = runner.parse_arguments(
            [
                "preflight",
                "--repository-root",
                "/fixture/XOAS",
                "--expected-commit",
                "1" * 40,
                "--bundle-directory",
                "/fixture/bundle",
                "--bundle-schema",
                "/fixture/bundle.schema.json",
                "--campaign-schema",
                "/fixture/campaign.schema.json",
                "--process-schema",
                "/fixture/process.schema.json",
                "--toolchain-lock",
                "/fixture/toolchain.lock.json",
                "--campaign-id",
                "target0-campaign-01",
                "--campaign-number",
                "1",
                "--target-user",
                "target-user",
                "--output-directory",
                "/var/tmp/xoas-target0-qualification-campaign.fixture",
                "--exclusive-use-confirmed",
            ]
        )
        self.assertEqual(options.command, "preflight")
        self.assertEqual(options.campaign_number, 1)
        self.assertTrue(options.exclusive_use_confirmed)

        with self.assertRaises(SystemExit):
            runner.parse_arguments(["run"])
        run_options = runner.parse_arguments(
            [
                "run",
                "--repository-root",
                "/fixture/XOAS",
                "--campaign-directory",
                "/var/tmp/xoas-target0-qualification-campaign.fixture",
                "--target-user",
                "target-user",
            ]
        )
        self.assertEqual(run_options.command, "run")
        self.assertEqual(run_options.target_user, "target-user")

        with self.assertRaises(RuntimeError):
            runner.validate_run_authority(
                target_user="target-user",
                effective_uid=1000,
                user_lookup=lambda name: SimpleNamespace(pw_uid=1000),
            )
        with self.assertRaises(RuntimeError):
            runner.validate_run_authority(
                target_user="root-alias",
                effective_uid=0,
                user_lookup=lambda name: SimpleNamespace(pw_uid=0),
            )
        runner.validate_run_authority(
            target_user="target-user",
            effective_uid=0,
            user_lookup=lambda name: SimpleNamespace(pw_uid=1000),
        )

        observed_commands: list[tuple[str, ...]] = []

        def observe_command(
            command: tuple[str, ...],
            working_directory: Path | None = None,
            *,
            environment: dict[str, str] | None = None,
            timeout: int = 30,
        ) -> SimpleNamespace:
            """Retain the exact root-side Git command without executing it."""
            del working_directory, environment, timeout
            observed_commands.append(command)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        runner.run_campaign_command(
            ("/usr/bin/git", "status", "--porcelain"),
            REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            delegate=observe_command,
        )
        self.assertEqual(
            observed_commands,
            [
                (
                    "/usr/bin/git",
                    "-c",
                    f"safe.directory={REPOSITORY_ROOT}",
                    "status",
                    "--porcelain",
                )
            ],
        )

    def test_preflight_rejects_incomplete_session_aggregates_normally(
        self,
    ) -> None:
        """Malformed operator-facing evidence must raise the campaign error."""
        runner = load_runner_module()
        sessions = self.session_record()
        del sessions["expected"]

        try:
            runner.evaluate_preflight(
                host_capture=self.host_capture(0.1),
                thermal=self.thermal_record(),
                sessions=sessions,
                exclusive_use_confirmed=True,
            )
        except Exception as error:
            self.assertIsInstance(error, RuntimeError)
        else:
            self.fail("incomplete session aggregates were accepted")

    def test_campaign_root_creation_is_new_canonical_and_nonoverlapping(
        self,
    ) -> None:
        """An existing, relative, or protected attempt root must be rejected."""
        runner = load_runner_module()
        self.assertTrue(
            hasattr(runner, "create_campaign_root"),
            "campaign root creator is missing",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            allowed_root = fixture_root / "evidence"
            repository_root = fixture_root / "repository"
            bundle_root = fixture_root / "bundle"
            install_prefix = fixture_root / "install"
            home_directory = fixture_root / "home"
            for path in (
                allowed_root,
                repository_root,
                bundle_root,
                install_prefix,
                home_directory,
            ):
                path.mkdir()
            output_directory = (
                allowed_root / "xoas-target0-qualification-campaign.attempt-01"
            )

            created = runner.create_campaign_root(
                output_directory,
                allowed_root=allowed_root,
                repository_root=repository_root,
                bundle_root=bundle_root,
                install_prefix=install_prefix,
                home_directory=home_directory,
            )

            self.assertEqual(created, output_directory)
            self.assertTrue(created.is_dir())
            self.assertEqual(created.stat().st_mode & 0o777, 0o700)
            with self.assertRaises(RuntimeError):
                runner.create_campaign_root(
                    output_directory,
                    allowed_root=allowed_root,
                    repository_root=repository_root,
                    bundle_root=bundle_root,
                    install_prefix=install_prefix,
                    home_directory=home_directory,
                )
            with self.assertRaises(RuntimeError):
                runner.create_campaign_root(
                    Path("xoas-target0-qualification-campaign.relative"),
                    allowed_root=allowed_root,
                    repository_root=repository_root,
                    bundle_root=bundle_root,
                    install_prefix=install_prefix,
                    home_directory=home_directory,
                )

    def test_core_observation_supplies_exact_60_second_selector_input(
        self,
    ) -> None:
        """The test clock may skip waiting but cannot change selector duration."""
        runner = load_runner_module()
        capture = load_module(CAPTURE_PATH, "xoas_capture_for_campaign_test")
        capture_test = load_module(
            CAPTURE_TEST_PATH,
            "xoas_capture_test_support_for_campaign",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_root = Path(temporary_directory)
            capture_test.make_host_fixture(source_root)
            host_capture = capture.build_capture(
                phase="campaign",
                source_root=source_root,
                command_runner=capture_test.FakeCommandRunner(),
                captured_at_utc="2026-08-29T00:00:00Z",
                repository_root=REPOSITORY_ROOT,
            )
            waits: list[int] = []

            def wait(seconds: int) -> None:
                waits.append(seconds)
                write_text(
                    source_root,
                    "proc/interrupts",
                    (
                        "           CPU0 CPU1 CPU2 CPU3\n"
                        "  0: 15 22 30 40 IO-APIC timer\n"
                    ),
                )

            timestamps = iter((0, 60_000_000_000))
            selection = runner.observe_core_selection(
                host_capture,
                source_root=source_root,
                sleep=wait,
                monotonic_ns=lambda: next(timestamps),
            )

        self.assertEqual(waits, [60])
        self.assertEqual(selection["window_seconds"], 60)
        self.assertEqual(selection["observed_window_ns"], 60_000_000_000)
        self.assertEqual(
            selection["interrupts_before"],
            {"0": 10, "1": 20, "2": 30, "3": 40},
        )
        self.assertEqual(
            selection["interrupts_after"],
            {"0": 15, "1": 22, "2": 30, "3": 40},
        )
        self.assertEqual(selection["cpu"], 1)
        self.assertEqual(selection["sibling"], 3)

    def test_read_only_preflight_publishes_closed_accepted_evidence(self) -> None:
        """The real preflight pipeline must retain inputs without host mutation."""
        runner = load_runner_module()
        preparation = load_preparation_module()
        capture_test = load_module(
            CAPTURE_TEST_PATH,
            "xoas_capture_test_support_for_preflight",
        )
        example = json.loads(BUNDLE_EXAMPLE_PATH.read_text(encoding="utf-8"))
        lock_bytes = TOOLCHAIN_LOCK_PATH.read_bytes()
        lock = json.loads(lock_bytes.decode("utf-8"))
        identity_runner = IdentityCommandRunner(lock)
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            source_root = fixture_root / "host"
            source_root.mkdir()
            capture_test.make_host_fixture(source_root)
            toolchain_lock = fixture_root / "toolchain-lock.json"
            toolchain_lock.write_bytes(lock_bytes)
            repository, expected_commit = make_identity_repository(
                fixture_root,
                [source["path"] for source in example["sources"]],
            )
            repository_identity = preparation.validate_repository(
                repository,
                expected_commit,
                identity_runner,
            )
            provisioning_lock = preparation.validate_toolchain_lock(
                toolchain_lock,
                repository / "schemas/target0-toolchain-lock-v1.schema.json",
            )
            manifest = copy.deepcopy(example)
            manifest["repository"] = repository_identity
            manifest["provisioning_lock"] = provisioning_lock
            manifest["sources"] = preparation.collect_source_records(repository)
            manifest["toolchain"] = {
                "compiler": preparation.validate_compiler(
                    lock,
                    identity_runner,
                ),
                "linker": preparation.validate_linker(lock, identity_runner),
            }
            bundle_root = fixture_root / "bundle"
            bundle_root.mkdir()
            finalize_identity_bundle(bundle_root, manifest, preparation)
            allowed_root = fixture_root / "evidence"
            allowed_root.mkdir()
            install_prefix = fixture_root / "install"
            home_directory = fixture_root / "home"
            install_prefix.mkdir()
            home_directory.mkdir()
            output_directory = (
                allowed_root
                / "xoas-target0-qualification-campaign.preflight-fixture"
            )
            options = runner.parse_arguments(
                [
                    "preflight",
                    "--repository-root",
                    str(repository),
                    "--expected-commit",
                    expected_commit,
                    "--bundle-directory",
                    str(bundle_root),
                    "--bundle-schema",
                    str(BUNDLE_SCHEMA_PATH),
                    "--campaign-schema",
                    str(
                        REPOSITORY_ROOT
                        / "schemas/target0-qualification-campaign-v1.schema.json"
                    ),
                    "--process-schema",
                    str(
                        REPOSITORY_ROOT
                        / "schemas/target0-host-qualification-v1.schema.json"
                    ),
                    "--toolchain-lock",
                    str(toolchain_lock),
                    "--campaign-id",
                    "target0-campaign-01",
                    "--campaign-number",
                    "1",
                    "--target-user",
                    "target-user",
                    "--output-directory",
                    str(output_directory),
                    "--exclusive-use-confirmed",
                ]
            )
            command_runner = PreflightCommandRunner(
                identity_runner,
                capture_test.FakeCommandRunner(),
                expected_commit,
            )

            def wait(seconds: int) -> None:
                self.assertEqual(seconds, 60)
                write_text(
                    source_root,
                    "proc/interrupts",
                    (
                        "           CPU0 CPU1 CPU2 CPU3\n"
                        "  0: 15 22 30 40 IO-APIC timer\n"
                    ),
                )

            timestamps = iter((0, 60_000_000_000))
            record = runner.execute_preflight(
                options,
                source_root=source_root,
                allowed_root=allowed_root,
                install_prefix=install_prefix,
                home_directory=home_directory,
                command_runner=command_runner,
                sleep=wait,
                monotonic_ns=lambda: next(timestamps),
                captured_at_utc="2026-08-29T00:00:00Z",
            )

            self.assertEqual(record["status"], "accepted")
            self.assertEqual(record["campaign_id"], "target0-campaign-01")
            self.assertEqual(record["campaign_number"], 1)
            self.assertEqual(record["eligibility"]["status"], "passed")
            self.assertEqual(record["identity"]["selected_core"]["cpu"], 1)
            self.assertTrue((output_directory / "preflight.json").is_file())
            self.assertTrue((output_directory / "core-selection.json").is_file())
            self.assertFalse((output_directory / "rejection.json").exists())
            serialized = json.dumps(record, sort_keys=True)
            for prohibited in (
                "target-user",
                str(repository),
                str(bundle_root),
                str(toolchain_lock),
            ):
                self.assertNotIn(prohibited, serialized)
            write_text(
                source_root,
                "proc/loadavg",
                "0.50 0.20 0.30 1/100 1000\n",
            )
            rejected_options = copy.copy(options)
            rejected_options.output_directory = (
                allowed_root
                / "xoas-target0-qualification-campaign.rejected-fixture"
            )
            with self.assertRaises(runner.CampaignPhaseError) as caught:
                runner.execute_preflight(
                    rejected_options,
                    source_root=source_root,
                    allowed_root=allowed_root,
                    install_prefix=install_prefix,
                    home_directory=home_directory,
                    command_runner=command_runner,
                    sleep=lambda seconds: self.fail(
                        f"failed preflight slept for {seconds} seconds"
                    ),
                    monotonic_ns=lambda: 0,
                    captured_at_utc="2026-08-29T00:01:00Z",
                )
            self.assertEqual(caught.exception.code, "load_failure")
            rejection_root = rejected_options.output_directory
            rejection = json.loads(
                (rejection_root / "rejection.json").read_text(encoding="utf-8")
            )
            self.assertEqual(rejection["reason_code"], "load_failure")
            self.assertEqual(rejection["phase"], "preflight")
            self.assertFalse((rejection_root / "preflight.json").exists())
            self.assertFalse((rejection_root / "core-selection.json").exists())


class QualificationCampaignPrimaryProcessTest(unittest.TestCase):
    """Verify five ordered primary sessions through the real operator loop."""

    def test_five_primary_processes_are_ordered_unique_and_complete(self) -> None:
        """The loop must construct and validate exactly five fresh sessions."""
        runner = load_runner_module()
        preparation = load_preparation_module()
        capture_test = load_module(
            CAPTURE_TEST_PATH,
            "xoas_capture_test_support_for_primary",
        )
        example = json.loads(BUNDLE_EXAMPLE_PATH.read_text(encoding="utf-8"))
        lock_bytes = TOOLCHAIN_LOCK_PATH.read_bytes()
        lock = json.loads(lock_bytes.decode("utf-8"))
        identity_runner = IdentityCommandRunner(lock)
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            source_root = fixture_root / "host"
            source_root.mkdir()
            capture_test.make_host_fixture(source_root)
            toolchain_lock = fixture_root / "toolchain-lock.json"
            toolchain_lock.write_bytes(lock_bytes)
            repository, expected_commit = make_identity_repository(
                fixture_root,
                [source["path"] for source in example["sources"]],
            )
            repository_identity = preparation.validate_repository(
                repository,
                expected_commit,
                identity_runner,
            )
            provisioning_lock = preparation.validate_toolchain_lock(
                toolchain_lock,
                repository / "schemas/target0-toolchain-lock-v1.schema.json",
            )
            manifest = copy.deepcopy(example)
            manifest["repository"] = repository_identity
            manifest["provisioning_lock"] = provisioning_lock
            manifest["sources"] = preparation.collect_source_records(repository)
            manifest["toolchain"] = {
                "compiler": preparation.validate_compiler(
                    lock,
                    identity_runner,
                ),
                "linker": preparation.validate_linker(lock, identity_runner),
            }
            bundle_root = fixture_root / "bundle"
            bundle_root.mkdir()
            finalize_identity_bundle(bundle_root, manifest, preparation)
            allowed_root = fixture_root / "evidence"
            allowed_root.mkdir()
            install_prefix = fixture_root / "install"
            home_directory = fixture_root / "home"
            install_prefix.mkdir()
            home_directory.mkdir()
            campaign_root = (
                allowed_root / "xoas-target0-qualification-campaign.primary"
            )
            options = runner.parse_arguments(
                [
                    "preflight",
                    "--repository-root",
                    str(repository),
                    "--expected-commit",
                    expected_commit,
                    "--bundle-directory",
                    str(bundle_root),
                    "--bundle-schema",
                    str(BUNDLE_SCHEMA_PATH),
                    "--campaign-schema",
                    str(
                        REPOSITORY_ROOT
                        / "schemas/target0-qualification-campaign-v1.schema.json"
                    ),
                    "--process-schema",
                    str(
                        REPOSITORY_ROOT
                        / "schemas/target0-host-qualification-v1.schema.json"
                    ),
                    "--toolchain-lock",
                    str(toolchain_lock),
                    "--campaign-id",
                    "target0-campaign-01",
                    "--campaign-number",
                    "1",
                    "--target-user",
                    "target-user",
                    "--output-directory",
                    str(campaign_root),
                    "--exclusive-use-confirmed",
                ]
            )
            command_runner = PreflightCommandRunner(
                identity_runner,
                capture_test.FakeCommandRunner(),
                expected_commit,
            )

            def finish_core_observation(seconds: int) -> None:
                self.assertEqual(seconds, 60)
                write_text(
                    source_root,
                    "proc/interrupts",
                    (
                        "           CPU0 CPU1 CPU2 CPU3\n"
                        "  0: 15 22 30 40 IO-APIC timer\n"
                    ),
                )

            timestamps = iter((0, 60_000_000_000))
            runner.execute_preflight(
                options,
                source_root=source_root,
                allowed_root=allowed_root,
                install_prefix=install_prefix,
                home_directory=home_directory,
                command_runner=command_runner,
                sleep=finish_core_observation,
                monotonic_ns=lambda: next(timestamps),
                captured_at_utc="2026-08-29T00:00:00Z",
            )
            preflight_template = fixture_root / "preflight-template"
            shutil.copytree(campaign_root, preflight_template)
            session_runner = PrimarySessionRunner()
            pmu_runner = PmuSessionRunner(
                {
                    "branches",
                    "branch-misses",
                    "cache-references",
                    "cache-misses",
                    "msr/aperf/",
                    "msr/mperf/",
                    "msr/tsc/",
                    "power/energy-pkg/",
                },
                unsupported_exit_statuses={"branches": 0},
            )

            def dispatch_session(
                command: tuple[str, ...],
                working_directory: Path | None = None,
                *,
                environment: dict[str, str] | None = None,
                timeout: int = 30,
            ) -> SimpleNamespace:
                """Route the exact public run loop to its two session fixtures."""
                selected = (
                    pmu_runner
                    if "--execution-mode" in command
                    else session_runner
                )
                return selected(
                    command,
                    working_directory,
                    environment=environment,
                    timeout=timeout,
                )

            run_options = runner.parse_arguments(
                [
                    "run",
                    "--repository-root",
                    str(repository),
                    "--campaign-directory",
                    str(campaign_root),
                    "--target-user",
                    "target-user",
                ]
            )
            outcome = runner.execute_run(
                run_options,
                source_root=source_root,
                command_runner=command_runner,
                session_runner=dispatch_session,
                captured_at_utc=lambda: "2026-08-29T00:02:00Z",
                effective_uid=0,
                user_lookup=lambda name: SimpleNamespace(pw_uid=1000),
            )
            processes = outcome["processes"]
            pmu = outcome["pmu"]

            self.assertEqual(
                [record["process_index"] for record in processes],
                [1, 2, 3, 4, 5],
            )
            self.assertEqual(len({record["seed"] for record in processes}), 5)
            self.assertTrue(
                all(
                    record["statistics"]["sample_count"] == 30
                    for record in processes
                )
            )
            self.assertEqual(len(session_runner.calls), 5)
            self.assertTrue(
                all(
                    stat.S_IMODE(
                        (campaign_root / f"process-{index:02d}").stat().st_mode
                    )
                    == 0o700
                    for index in range(1, 6)
                )
            )
            retained_probe = str(
                campaign_root / "inputs/xoas-target0-qualification-probe"
            )
            self.assertTrue(
                all(retained_probe in command for command in session_runner.calls)
            )
            self.assertEqual(
                [
                    command[command.index("--perf-events") + 1]
                    for command in pmu_runner.calls
                ],
                [
                    "cycles,instructions",
                    "branches",
                    "branch-misses",
                    "cache-references",
                    "cache-misses",
                    "msr/aperf/",
                    "msr/mperf/",
                    "msr/tsc/",
                    "power/energy-pkg/",
                ],
            )
            self.assertEqual(pmu["required"]["status"], "passed")
            self.assertEqual(len(pmu["optional"]), 8)
            self.assertTrue(
                all(
                    outcome["status"] == "unsupported"
                    for outcome in pmu["optional"]
                )
            )
            self.assertTrue(
                all(
                    stat.S_IMODE(path.stat().st_mode) == 0o700
                    for path in (campaign_root / "pmu").iterdir()
                )
            )
            self.assertFalse((campaign_root / "rejection.json").exists())
            self.assertTrue((campaign_root / "acceptance.json").is_file())
            verified = runner.verify_finalized_campaign(
                campaign_root,
                campaign_schema=(
                    REPOSITORY_ROOT
                    / "schemas/target0-qualification-campaign-v1.schema.json"
                ),
                process_schema=(
                    REPOSITORY_ROOT
                    / "schemas/target0-host-qualification-v1.schema.json"
                ),
                bundle_schema=BUNDLE_SCHEMA_PATH,
            )
            self.assertEqual(verified["status"], "accepted")
            retained_paths_before = sorted(
                path.relative_to(campaign_root).as_posix()
                for path in campaign_root.rglob("*")
            )
            verification = subprocess.run(
                (
                    sys.executable,
                    CAMPAIGN_VERIFIER_PATH,
                    "--campaign-directory",
                    campaign_root,
                    "--campaign-schema",
                    REPOSITORY_ROOT
                    / "schemas/target0-qualification-campaign-v1.schema.json",
                    "--process-schema",
                    REPOSITORY_ROOT
                    / "schemas/target0-host-qualification-v1.schema.json",
                    "--bundle-schema",
                    BUNDLE_SCHEMA_PATH,
                ),
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(verification.returncode, 0, verification.stderr)
            self.assertEqual(json.loads(verification.stdout), verified)
            self.assertEqual(verification.stderr, "")
            self.assertEqual(
                sorted(
                    path.relative_to(campaign_root).as_posix()
                    for path in campaign_root.rglob("*")
                ),
                retained_paths_before,
            )
            inventory = json.loads(
                (campaign_root / "inventory.json").read_text(encoding="utf-8")
            )
            inventory_paths = [record["path"] for record in inventory["files"]]
            self.assertEqual(
                inventory_paths,
                sorted(inventory_paths, key=lambda path: path.encode("utf-8")),
            )
            with self.assertRaises(RuntimeError):
                runner.execute_run(
                    run_options,
                    source_root=source_root,
                    command_runner=command_runner,
                    session_runner=dispatch_session,
                    captured_at_utc=lambda: "2026-08-29T00:08:00Z",
                    effective_uid=0,
                    user_lookup=lambda name: SimpleNamespace(pw_uid=1000),
                )

            def write_canonical_json(
                path: Path,
                record: dict[str, object],
            ) -> None:
                """Overwrite one disposable terminal record canonically."""
                path.write_bytes(runner.canonical_json_bytes(record))

            def rebind_disposable_terminal(attempt: Path) -> None:
                """Rebind outer digests so semantic tampering reaches replay."""
                inventory_record = runner.build_raw_inventory(attempt)
                inventory_path = attempt / "inventory.json"
                write_canonical_json(inventory_path, inventory_record)
                campaign_path = attempt / "campaign.json"
                campaign_record = json.loads(
                    campaign_path.read_text(encoding="utf-8")
                )
                campaign_record["evidence_inventory_sha256"] = hashlib.sha256(
                    inventory_path.read_bytes()
                ).hexdigest()
                write_canonical_json(campaign_path, campaign_record)
                acceptance_path = attempt / "acceptance.json"
                acceptance_record = json.loads(
                    acceptance_path.read_text(encoding="utf-8")
                )
                acceptance_record["inventory_sha256"] = hashlib.sha256(
                    inventory_path.read_bytes()
                ).hexdigest()
                acceptance_record["campaign_sha256"] = hashlib.sha256(
                    campaign_path.read_bytes()
                ).hexdigest()
                write_canonical_json(acceptance_path, acceptance_record)

            tamper_names = (
                "raw-process-byte",
                "noncanonical-process",
                "noncanonical-restoration",
                *(f"nonfinite-process-{name}" for name in NONFINITE_JSON_TOKENS),
                *(
                    f"nonfinite-restoration-{name}"
                    for name in NONFINITE_JSON_TOKENS
                ),
                "core-selection",
                "preflight-load",
                "preflight-session-decision",
                "thermal-decision",
                "session-host-identity",
                "pmu-restoration-core",
                "added-file",
                "removed-file",
                "retained-executable",
                "retained-bundle-record",
                "campaign-statistic",
                "inventory-record",
                "acceptance-record",
            )
            for tamper_name in tamper_names:
                with self.subTest(tamper=tamper_name):
                    attempt = fixture_root / f"tamper-{tamper_name}"
                    shutil.copytree(campaign_root, attempt)
                    if tamper_name == "raw-process-byte":
                        process_path = attempt / "process-01/process.json"
                        process_path.write_bytes(process_path.read_bytes() + b" ")
                        rebind_disposable_terminal(attempt)
                    elif tamper_name in {
                        "noncanonical-process",
                        "noncanonical-restoration",
                    }:
                        evidence_name = (
                            "process.json"
                            if tamper_name == "noncanonical-process"
                            else "restoration.json"
                        )
                        evidence_path = attempt / "process-01" / evidence_name
                        evidence_record = json.loads(
                            evidence_path.read_text(encoding="utf-8")
                        )
                        evidence_path.write_text(
                            json.dumps(evidence_record, indent=2) + "\n",
                            encoding="utf-8",
                        )
                        campaign_path = attempt / "campaign.json"
                        campaign_record = json.loads(
                            campaign_path.read_text(encoding="utf-8")
                        )
                        digest_field = (
                            "process_sha256"
                            if tamper_name == "noncanonical-process"
                            else "restoration_sha256"
                        )
                        campaign_record["processes"][0]["evidence"][
                            digest_field
                        ] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
                        write_canonical_json(campaign_path, campaign_record)
                        rebind_disposable_terminal(attempt)
                    elif tamper_name.startswith("nonfinite-"):
                        _, evidence_kind, token_name = tamper_name.split("-", 2)
                        evidence_name = f"{evidence_kind}.json"
                        evidence_path = attempt / "process-01" / evidence_name
                        numeric_key = (
                            "iterations"
                            if evidence_kind == "process"
                            else "cpu"
                        )
                        evidence_path.write_bytes(
                            replace_json_number(
                                evidence_path.read_bytes(),
                                numeric_key,
                                NONFINITE_JSON_TOKENS[token_name],
                            )
                        )
                        campaign_path = attempt / "campaign.json"
                        campaign_record = json.loads(
                            campaign_path.read_text(encoding="utf-8")
                        )
                        digest_field = f"{evidence_kind}_sha256"
                        campaign_record["processes"][0]["evidence"][
                            digest_field
                        ] = hashlib.sha256(
                            evidence_path.read_bytes()
                        ).hexdigest()
                        write_canonical_json(campaign_path, campaign_record)
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "core-selection":
                        selection_path = attempt / "core-selection.json"
                        selection_record = json.loads(
                            selection_path.read_text(encoding="utf-8")
                        )
                        selected_cpu = str(selection_record["cpu"])
                        selection_record["interrupts_after"][selected_cpu] += 1
                        write_canonical_json(selection_path, selection_record)
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "preflight-load":
                        preflight_path = attempt / "preflight.json"
                        preflight_record = json.loads(
                            preflight_path.read_text(encoding="utf-8")
                        )
                        preflight_record["host_capture"]["host"]["load"][
                            "load_average"
                        ][0] = 0.75
                        write_canonical_json(preflight_path, preflight_record)
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "preflight-session-decision":
                        preflight_path = attempt / "preflight.json"
                        preflight_record = json.loads(
                            preflight_path.read_text(encoding="utf-8")
                        )
                        sessions = preflight_record["interactive_sessions"]
                        sessions["expected"] += 1
                        sessions["total"] += 1
                        write_canonical_json(preflight_path, preflight_record)
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "thermal-decision":
                        thermal_path = (
                            attempt / "process-01/thermal-before.json"
                        )
                        thermal_record = json.loads(
                            thermal_path.read_text(encoding="utf-8")
                        )
                        sensor = thermal_record["sensors"][0]
                        sensor["critical_millidegrees_c"] = sensor[
                            "input_millidegrees_c"
                        ]
                        write_canonical_json(thermal_path, thermal_record)
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "session-host-identity":
                        for host_name in ("host-before.json", "host-after.json"):
                            host_path = attempt / "process-01" / host_name
                            host_record = json.loads(
                                host_path.read_text(encoding="utf-8")
                            )
                            host_record["repository"]["commit"] = "2" * 40
                            write_canonical_json(host_path, host_record)
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "pmu-restoration-core":
                        restoration_path = (
                            attempt / "pmu/required/restoration.json"
                        )
                        restoration_record = json.loads(
                            restoration_path.read_text(encoding="utf-8")
                        )
                        restoration_record["cpu"] += 1000
                        write_canonical_json(
                            restoration_path,
                            restoration_record,
                        )
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "added-file":
                        (attempt / "unexpected.bin").write_bytes(b"unexpected")
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "removed-file":
                        (attempt / "process-01/thermal-after.json").unlink()
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "retained-executable":
                        executable = (
                            attempt
                            / "inputs/xoas-target0-qualification-probe"
                        )
                        executable.write_bytes(executable.read_bytes() + b"drift")
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "retained-bundle-record":
                        bundle_record = attempt / "inputs/bundle.json"
                        bundle_record.write_bytes(bundle_record.read_bytes() + b" ")
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "campaign-statistic":
                        campaign_path = attempt / "campaign.json"
                        campaign_record = json.loads(
                            campaign_path.read_text(encoding="utf-8")
                        )
                        campaign_record["processes"][0]["statistics"][
                            "minimum_ns"
                        ] = 99_000_000
                        write_canonical_json(campaign_path, campaign_record)
                        rebind_disposable_terminal(attempt)
                    elif tamper_name == "inventory-record":
                        inventory_path = attempt / "inventory.json"
                        inventory_record = json.loads(
                            inventory_path.read_text(encoding="utf-8")
                        )
                        inventory_record["files"][0]["sha256"] = "0" * 64
                        write_canonical_json(inventory_path, inventory_record)
                        campaign_path = attempt / "campaign.json"
                        campaign_record = json.loads(
                            campaign_path.read_text(encoding="utf-8")
                        )
                        campaign_record["evidence_inventory_sha256"] = (
                            hashlib.sha256(inventory_path.read_bytes()).hexdigest()
                        )
                        write_canonical_json(campaign_path, campaign_record)
                        acceptance_path = attempt / "acceptance.json"
                        acceptance_record = json.loads(
                            acceptance_path.read_text(encoding="utf-8")
                        )
                        acceptance_record["inventory_sha256"] = hashlib.sha256(
                            inventory_path.read_bytes()
                        ).hexdigest()
                        acceptance_record["campaign_sha256"] = hashlib.sha256(
                            campaign_path.read_bytes()
                        ).hexdigest()
                        write_canonical_json(acceptance_path, acceptance_record)
                    else:
                        acceptance_path = attempt / "acceptance.json"
                        acceptance_record = json.loads(
                            acceptance_path.read_text(encoding="utf-8")
                        )
                        acceptance_record["process_count"] = 4
                        write_canonical_json(acceptance_path, acceptance_record)
                    with self.assertRaises(RuntimeError):
                        runner.verify_finalized_campaign(
                            attempt,
                            campaign_schema=(
                                REPOSITORY_ROOT
                                / "schemas"
                                / "target0-qualification-campaign-v1.schema.json"
                            ),
                            process_schema=(
                                REPOSITORY_ROOT
                                / "schemas/target0-host-qualification-v1.schema.json"
                            ),
                            bundle_schema=BUNDLE_SCHEMA_PATH,
                        )
            primary_template = fixture_root / "primary-template"
            shutil.copytree(campaign_root, primary_template)
            shutil.rmtree(primary_template / "pmu")
            for terminal_name in (
                "acceptance.json",
                "campaign.json",
                "inventory.json",
            ):
                (primary_template / terminal_name).unlink()

            failure_cases = (
                ("process_execution", "process_execution_failure"),
                ("invalid_schema", "process_schema_failure"),
                ("noncanonical_process", "process_schema_failure"),
                ("noncanonical_restoration", "restoration_failure"),
                *(
                    (f"nonfinite_process_{name}", "process_schema_failure")
                    for name in NONFINITE_JSON_TOKENS
                ),
                *(
                    (f"nonfinite_restoration_{name}", "restoration_failure")
                    for name in NONFINITE_JSON_TOKENS
                ),
                ("duration_low", "sample_bound_or_migration_failure"),
                ("duration_high", "sample_bound_or_migration_failure"),
                ("migration", "sample_bound_or_migration_failure"),
                ("thread", "sample_bound_or_migration_failure"),
                ("checksum", "sample_bound_or_migration_failure"),
                ("thermal_alarm", "thermal_precondition_failure"),
                ("thermal_threshold", "thermal_precondition_failure"),
                ("restoration", "restoration_failure"),
            )
            for mutation, expected_code in failure_cases:
                with self.subTest(mutation=mutation):
                    (source_root / "sys/class/hwmon/hwmon0/temp1_crit_alarm").unlink(
                        missing_ok=True
                    )
                    (source_root / "sys/class/hwmon/hwmon0/temp1_crit").unlink(
                        missing_ok=True
                    )
                    attempt = (
                        allowed_root
                        / f"xoas-target0-qualification-campaign.{mutation}"
                    )
                    shutil.copytree(preflight_template, attempt)
                    failing_session = PrimarySessionRunner(
                        mutation=mutation,
                        source_root=source_root,
                    )
                    with self.assertRaises(runner.CampaignPhaseError) as caught:
                        runner.execute_primary_processes(
                            campaign_root=attempt,
                            repository_root=repository,
                            target_user="target-user",
                            source_root=source_root,
                            command_runner=command_runner,
                            session_runner=failing_session,
                            captured_at_utc=lambda: "2026-08-29T00:04:00Z",
                        )
                    self.assertEqual(caught.exception.code, expected_code)
                    self.assertEqual(len(failing_session.calls), 1)
                    self.assertFalse((attempt / "acceptance.json").exists())
                    rejection = json.loads(
                        (attempt / "rejection.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(rejection["reason_code"], expected_code)
                    self.assertEqual(rejection["phase"], "primary")
                    expected_status = {
                        "process_execution": 9,
                        "restoration": 70,
                    }.get(mutation, 0)
                    self.assertEqual(
                        rejection["command_exit_status"],
                        expected_status,
                    )
                    self.assertTrue((attempt / "process-01/host-before.json").is_file())

            source_to_drift = repository / manifest["sources"][0]["path"]
            source_bytes = source_to_drift.read_bytes()
            remote_validation_count = 0

            def drift_on_second_process(command: tuple[str, ...]) -> None:
                nonlocal remote_validation_count
                if command == (
                    "/usr/bin/git",
                    "remote",
                    "get-url",
                    "origin",
                ):
                    remote_validation_count += 1
                    if remote_validation_count == 2:
                        source_to_drift.write_bytes(source_bytes + b"drift")

            drift_identity_runner = IdentityCommandRunner(
                lock,
                after_command=drift_on_second_process,
            )
            drift_command_runner = PreflightCommandRunner(
                drift_identity_runner,
                capture_test.FakeCommandRunner(),
                expected_commit,
            )
            drift_attempt = (
                allowed_root / "xoas-target0-qualification-campaign.identity-drift"
            )
            shutil.copytree(preflight_template, drift_attempt)
            drift_session = PrimarySessionRunner()
            with self.assertRaises(runner.CampaignPhaseError) as caught:
                runner.execute_primary_processes(
                    campaign_root=drift_attempt,
                    repository_root=repository,
                    target_user="target-user",
                    source_root=source_root,
                    command_runner=drift_command_runner,
                    session_runner=drift_session,
                    captured_at_utc=lambda: "2026-08-29T00:05:00Z",
                )
            source_to_drift.write_bytes(source_bytes)
            self.assertEqual(caught.exception.code, "per_process_identity_drift")
            self.assertEqual(len(drift_session.calls), 1)
            self.assertTrue((drift_attempt / "process-01/process.json").is_file())
            self.assertFalse((drift_attempt / "acceptance.json").exists())
            drift_rejection = json.loads(
                (drift_attempt / "rejection.json").read_text(encoding="utf-8")
            )
            self.assertEqual(drift_rejection["phase"], "primary")

            required_pmu_attempt = (
                allowed_root / "xoas-target0-qualification-campaign.required-pmu"
            )
            shutil.copytree(primary_template, required_pmu_attempt)
            with self.assertRaises(runner.CampaignPhaseError) as caught:
                runner.execute_pmu_sessions(
                    campaign_root=required_pmu_attempt,
                    repository_root=repository,
                    target_user="target-user",
                    source_root=source_root,
                    command_runner=command_runner,
                    session_runner=PmuSessionRunner({"cycles"}),
                    captured_at_utc=lambda: "2026-08-29T00:06:00Z",
                )
            self.assertEqual(caught.exception.code, "required_pmu_failure")
            self.assertFalse((required_pmu_attempt / "acceptance.json").exists())
            required_rejection = json.loads(
                (required_pmu_attempt / "rejection.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                required_rejection["reason_code"],
                "required_pmu_failure",
            )
            self.assertEqual(required_rejection["phase"], "pmu")
            self.assertEqual(required_rejection["command_exit_status"], 129)

            scaled_pmu_attempt = (
                allowed_root / "xoas-target0-qualification-campaign.scaled-pmu"
            )
            shutil.copytree(primary_template, scaled_pmu_attempt)
            scaled_runner = PmuSessionRunner(
                running_percentages={"cycles": "99.99"}
            )
            with self.assertRaises(runner.CampaignPhaseError) as caught:
                runner.execute_pmu_sessions(
                    campaign_root=scaled_pmu_attempt,
                    repository_root=repository,
                    target_user="target-user",
                    source_root=source_root,
                    command_runner=command_runner,
                    session_runner=scaled_runner,
                    captured_at_utc=lambda: "2026-08-29T00:07:00Z",
                )
            self.assertEqual(caught.exception.code, "required_pmu_failure")
            self.assertEqual(len(scaled_runner.calls), 1)
            scaled_rejection = json.loads(
                (scaled_pmu_attempt / "rejection.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                scaled_rejection["reason_code"],
                "required_pmu_failure",
            )
            self.assertEqual(scaled_rejection["phase"], "pmu")
            self.assertEqual(scaled_rejection["command_exit_status"], 0)


if __name__ == "__main__":
    unittest.main()
