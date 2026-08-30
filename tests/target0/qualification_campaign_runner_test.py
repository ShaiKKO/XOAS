#!/usr/bin/env python3
"""Fixture-driven tests for Target 0 qualification campaign orchestration."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
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
        if relative_path == "schemas/target0-toolchain-lock-v1.schema.json":
            path.write_bytes(
                (
                    REPOSITORY_ROOT
                    / "schemas/target0-toolchain-lock-v1.schema.json"
                ).read_bytes()
            )
        else:
            path.write_text(f"fixture:{relative_path}\n", encoding="utf-8")
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
            self.assertFalse((rejection_root / "preflight.json").exists())
            self.assertFalse((rejection_root / "core-selection.json").exists())


if __name__ == "__main__":
    unittest.main()
