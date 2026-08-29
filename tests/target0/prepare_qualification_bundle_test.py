#!/usr/bin/env python3
"""Behavioral tests for Target 0 qualification-tool deployment bundles."""

from __future__ import annotations

import argparse
import copy
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import ModuleType
import unittest

from jsonschema import Draft202012Validator


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPOSITORY_ROOT / "tools/target0/prepare_qualification_bundle.py"
TARGET_LOCK_PATH = (
    REPOSITORY_ROOT / "toolchains/target0-amd-ryzen9-7900x-v1.lock.json"
)
TARGET_LOCK_SCHEMA_PATH = (
    REPOSITORY_ROOT / "schemas/target0-toolchain-lock-v1.schema.json"
)


def parse_arguments() -> argparse.Namespace:
    """Parse explicit fixture paths without consuming unittest options."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--example", required=True, type=Path)
    arguments, unittest_arguments = parser.parse_known_args()
    unittest.main_argv = [__file__, *unittest_arguments]
    return arguments


def load_preparation_module() -> ModuleType:
    """Load the real preparation module after asserting its ownership path."""
    if not MODULE_PATH.is_file():
        raise AssertionError("preparation tool is missing")
    specification = importlib.util.spec_from_file_location(
        "xoas_prepare_qualification_bundle",
        MODULE_PATH,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("preparation tool cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def run_git(repository: Path, *arguments: str) -> str:
    """Run one local fixture Git command and return stripped stdout."""
    completed = subprocess.run(
        ("git", "-C", repository, *arguments),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def make_git_repository(root: Path) -> tuple[Path, str, str]:
    """Create one real clean repository with a public origin."""
    repository = root / "XOAS"
    repository.mkdir()
    run_git(repository, "init", "--quiet")
    run_git(repository, "config", "user.name", "XOAS Test")
    run_git(repository, "config", "user.email", "test@xoas.invalid")
    (repository / "contract.txt").write_text("fixture\n", encoding="utf-8")
    run_git(repository, "add", "contract.txt")
    run_git(repository, "commit", "--quiet", "-m", "fixture")
    run_git(
        repository,
        "remote",
        "add",
        "origin",
        "https://github.com/ShaiKKO/XOAS.git",
    )
    return (
        repository,
        run_git(repository, "rev-parse", "HEAD"),
        run_git(repository, "rev-parse", "HEAD^{tree}"),
    )


def write_fixture_text(root: Path, relative_path: str, content: str) -> None:
    """Write one controlled preflight host fact."""
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class PrepareQualificationBundleSchemaTest(unittest.TestCase):
    """Verify the closed retained bundle evidence contract."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load the real schema and its hand-authored positive instance."""
        if not ARGUMENTS.schema.is_file():
            raise AssertionError("bundle schema is missing")
        if not ARGUMENTS.example.is_file():
            raise AssertionError("bundle example is missing")
        cls.schema = json.loads(ARGUMENTS.schema.read_text(encoding="utf-8"))
        cls.example = json.loads(ARGUMENTS.example.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def test_schema_and_example_are_present(self) -> None:
        """Deployment evidence must have a schema and positive instance."""
        self.assertTrue(ARGUMENTS.schema.is_file(), "bundle schema is missing")
        self.assertTrue(ARGUMENTS.example.is_file(), "bundle example is missing")

    def test_example_is_a_valid_nonclaiming_passed_bundle(self) -> None:
        """The positive instance must demonstrate the complete passed shape."""
        self.validator.validate(self.example)
        self.assertEqual(
            self.example.get("manifest_version"),
            "xoas.target0-qualification-tool-bundle.v1",
        )
        self.assertIs(self.example.get("performance_claim"), False)
        self.assertEqual(self.example.get("status"), "passed")

    def test_example_retains_every_provenance_section(self) -> None:
        """A passed receipt cannot omit a load-bearing provenance category."""
        self.assertEqual(
            set(self.example),
            {
                "build",
                "bundle_id",
                "compatibility_tests",
                "created_at_utc",
                "elf",
                "manifest_version",
                "performance_claim",
                "provisioning_lock",
                "rejection_reasons",
                "repository",
                "runtime_dependencies",
                "sources",
                "status",
                "target_id",
                "toolchain",
            },
        )

    def test_schema_rejects_claims_and_unknown_fields(self) -> None:
        """A bundle cannot inflate its authority or extend the closed record."""
        claiming = copy.deepcopy(self.example)
        claiming["performance_claim"] = True
        extended = copy.deepcopy(self.example)
        extended["unreviewed_field"] = "not allowed"

        self.assertFalse(self.validator.is_valid(claiming))
        self.assertFalse(self.validator.is_valid(extended))

    def test_schema_rejects_malformed_digests(self) -> None:
        """Every retained SHA-256 must use one canonical lowercase spelling."""
        short_digest = copy.deepcopy(self.example)
        short_digest["sources"][0]["sha256"] = "abcd"
        uppercase_digest = copy.deepcopy(self.example)
        uppercase_digest["build"]["executable_sha256"] = "A" * 64

        self.assertFalse(self.validator.is_valid(short_digest))
        self.assertFalse(self.validator.is_valid(uppercase_digest))

    def test_schema_rejects_dirty_or_unconfirmed_builds(self) -> None:
        """Passed evidence requires a clean checkout and confirmed dual build."""
        dirty = copy.deepcopy(self.example)
        dirty["repository"]["tree_state"] = "dirty"
        unconfirmed = copy.deepcopy(self.example)
        unconfirmed["build"]["identical"] = False

        self.assertFalse(self.validator.is_valid(dirty))
        self.assertFalse(self.validator.is_valid(unconfirmed))

    def test_schema_rejects_passed_bundles_with_rejections(self) -> None:
        """A passed bundle cannot retain a contradictory rejection reason."""
        contradictory = copy.deepcopy(self.example)
        contradictory["rejection_reasons"] = ["build_failed"]

        self.assertFalse(self.validator.is_valid(contradictory))

    def test_schema_requires_dependency_hashes(self) -> None:
        """Every resolved runtime dependency must remain byte-authenticated."""
        unbound_dependency = copy.deepcopy(self.example)
        del unbound_dependency["runtime_dependencies"][0]["sha256"]

        self.assertFalse(self.validator.is_valid(unbound_dependency))

    def test_schema_rejects_unclosed_compatibility_results(self) -> None:
        """Compatibility checks cannot add an unreviewed outcome or field."""
        unclosed_status = copy.deepcopy(self.example)
        unclosed_status["compatibility_tests"][0]["status"] = "warning"
        unclosed_field = copy.deepcopy(self.example)
        unclosed_field["compatibility_tests"][0]["duration_ns"] = 1

        self.assertFalse(self.validator.is_valid(unclosed_status))
        self.assertFalse(self.validator.is_valid(unclosed_field))


class PrepareQualificationBundlePreflightTest(unittest.TestCase):
    """Verify preparation fails before trusting unsafe host inputs."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load the production module once for preflight behavior tests."""
        cls.module = load_preparation_module()

    def test_preparation_module_is_present(self) -> None:
        """The approved deployment surface must be a repository-owned tool."""
        self.assertTrue(MODULE_PATH.is_file(), "preparation tool is missing")

    def test_canonical_json_has_stable_bytes(self) -> None:
        """Input key order cannot change retained JSON identity."""
        self.assertTrue(
            hasattr(self.module, "canonical_json_bytes"),
            "canonical serializer is missing",
        )
        self.assertEqual(
            self.module.canonical_json_bytes({"z": 1, "a": [True, None]}),
            b'{"a":[true,null],"z":1}\n',
        )

    def test_cli_requires_all_explicit_inputs_and_full_commit(self) -> None:
        """Deployment cannot infer a checkout, lock, output, or commit."""
        self.assertTrue(
            hasattr(self.module, "parse_arguments"),
            "closed CLI parser is missing",
        )
        complete_arguments = [
            "--repository-root",
            "/work/XOAS",
            "--expected-commit",
            "1" * 40,
            "--toolchain-lock",
            "/work/XOAS/toolchains/target0.lock.json",
            "--output-directory",
            "/var/tmp/xoas-target0-qualification-tools.fixture",
        ]
        parsed = self.module.parse_arguments(complete_arguments)
        self.assertEqual(parsed.expected_commit, "1" * 40)
        self.assertEqual(parsed.repository_root, Path("/work/XOAS"))

        invalid_argument_sets = [
            complete_arguments[index : index + 2]
            for index in range(0, len(complete_arguments), 2)
        ]
        invalid_argument_sets.append(
            [
                *complete_arguments[:2],
                "--expected-commit",
                "1" * 12,
                *complete_arguments[4:],
            ]
        )
        invalid_argument_sets.append([*complete_arguments, "--unknown"])
        for arguments in invalid_argument_sets:
            with self.subTest(arguments=arguments):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        self.module.parse_arguments(arguments)
                self.assertEqual(raised.exception.code, 2)

    def test_staging_root_is_new_private_and_bounded(self) -> None:
        """Preparation cannot replace or escape its exact evidence directory."""
        self.assertTrue(
            hasattr(self.module, "create_staging_root"),
            "staging-root validator is missing",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            allowed_root = fixture_root / "var/tmp"
            repository_root = fixture_root / "work/XOAS"
            install_prefix = fixture_root / "opt/xoas/target0-v1"
            home_directory = fixture_root / "home/operator"
            for directory in (
                allowed_root,
                repository_root,
                install_prefix,
                home_directory,
            ):
                directory.mkdir(parents=True)

            accepted = allowed_root / "xoas-target0-qualification-tools.accepted"
            created = self.module.create_staging_root(
                accepted,
                allowed_root=allowed_root,
                repository_root=repository_root,
                install_prefix=install_prefix,
                home_directory=home_directory,
            )
            self.assertEqual(created, accepted)
            self.assertTrue(created.is_dir())
            self.assertEqual(os.stat(created).st_mode & 0o777, 0o700)

            existing = allowed_root / "xoas-target0-qualification-tools.existing"
            existing.mkdir()
            symlink = allowed_root / "xoas-target0-qualification-tools.symlink"
            symlink.symlink_to(repository_root, target_is_directory=True)
            invalid_paths = [
                existing,
                symlink,
                allowed_root,
                allowed_root / "xoas-target0-qualification-tools.",
                allowed_root / "unapproved-name",
                allowed_root / "nested/xoas-target0-qualification-tools.child",
                allowed_root
                / "../tmp/xoas-target0-qualification-tools.traversal",
                repository_root,
                install_prefix,
                home_directory,
            ]
            for invalid_path in invalid_paths:
                with self.subTest(path=invalid_path):
                    with self.assertRaises(self.module.PreparationError):
                        self.module.create_staging_root(
                            invalid_path,
                            allowed_root=allowed_root,
                            repository_root=repository_root,
                            install_prefix=install_prefix,
                            home_directory=home_directory,
                        )

    def test_repository_identity_requires_exact_clean_public_checkout(self) -> None:
        """The retained repository identity must come from one real checkout."""
        self.assertTrue(
            hasattr(self.module, "validate_repository"),
            "repository validator is missing",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository, commit, tree = make_git_repository(
                Path(temporary_directory)
            )
            identity = self.module.validate_repository(
                repository,
                commit,
                self.module.run_command,
            )

        self.assertEqual(
            identity,
            {
                "actual_commit": commit,
                "expected_commit": commit,
                "public_remote": "https://github.com/ShaiKKO/XOAS.git",
                "tree": tree,
                "tree_state": "clean",
            },
        )

    def test_repository_rejects_dirty_mismatched_and_missing_identity(self) -> None:
        """No dirty, wrong-commit, or originless checkout can be prepared."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository, commit, _ = make_git_repository(Path(temporary_directory))
            untracked = repository / "untracked.txt"
            untracked.write_text("dirty\n", encoding="utf-8")
            with self.assertRaises(self.module.PreparationError):
                self.module.validate_repository(
                    repository,
                    commit,
                    self.module.run_command,
                )

            untracked.unlink()
            with self.assertRaises(self.module.PreparationError):
                self.module.validate_repository(
                    repository,
                    "f" * 40,
                    self.module.run_command,
                )

            run_git(repository, "remote", "remove", "origin")
            with self.assertRaises(self.module.PreparationError):
                self.module.validate_repository(
                    repository,
                    commit,
                    self.module.run_command,
                )

    def test_repository_rejects_credential_remote_without_echo(self) -> None:
        """An authenticated remote must fail without leaking its credential."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository, commit, _ = make_git_repository(Path(temporary_directory))
            secret = "deployment-secret"
            run_git(
                repository,
                "remote",
                "set-url",
                "origin",
                f"https://{secret}@github.com/ShaiKKO/XOAS.git",
            )
            with self.assertRaises(self.module.PreparationError) as raised:
                self.module.validate_repository(
                    repository,
                    commit,
                    self.module.run_command,
                )

        self.assertNotIn(secret, str(raised.exception))

    def test_toolchain_lock_requires_schema_state_and_stable_digest(self) -> None:
        """Preparation must authenticate the installed lock as structured data."""
        self.assertTrue(
            hasattr(self.module, "validate_toolchain_lock"),
            "toolchain-lock validator is missing",
        )
        lock = json.loads(TARGET_LOCK_PATH.read_text(encoding="utf-8"))
        identity = self.module.validate_toolchain_lock(
            TARGET_LOCK_PATH,
            TARGET_LOCK_SCHEMA_PATH,
        )
        expected_lock_bytes = TARGET_LOCK_PATH.read_bytes()
        expected_configuration = copy.deepcopy(lock)
        expected_configuration_digest = expected_configuration.pop(
            "configuration_sha256"
        )
        expected_configuration_bytes = json.dumps(
            expected_configuration,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(
            identity,
            {
                "configuration_sha256": expected_configuration_digest,
                "execution_subject": lock["execution_subject"],
                "file_sha256": hashlib.sha256(expected_lock_bytes).hexdigest(),
                "lock_id": lock["lock_id"],
            },
        )
        self.assertEqual(
            hashlib.sha256(expected_configuration_bytes).hexdigest(),
            expected_configuration_digest,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            invalid_state = copy.deepcopy(lock)
            invalid_state["state"] = "candidate"
            invalid_state_path = fixture_root / "invalid-state.json"
            invalid_state_path.write_text(
                json.dumps(invalid_state), encoding="utf-8"
            )
            wrong_digest = copy.deepcopy(lock)
            wrong_digest["configuration_sha256"] = "0" * 64
            wrong_digest_path = fixture_root / "wrong-digest.json"
            wrong_digest_path.write_text(
                json.dumps(wrong_digest), encoding="utf-8"
            )
            permissive_schema_path = fixture_root / "permissive.schema.json"
            permissive_schema_path.write_text("{}\n", encoding="utf-8")

            for lock_path, schema_path in (
                (invalid_state_path, TARGET_LOCK_SCHEMA_PATH),
                (wrong_digest_path, TARGET_LOCK_SCHEMA_PATH),
                (TARGET_LOCK_PATH, permissive_schema_path),
            ):
                with self.subTest(lock_path=lock_path, schema_path=schema_path):
                    with self.assertRaises(self.module.PreparationError):
                        self.module.validate_toolchain_lock(lock_path, schema_path)

    def test_target_identity_matches_locked_cpu_os_and_architecture(self) -> None:
        """A valid lock cannot be replayed on a different physical target."""
        self.assertTrue(
            hasattr(self.module, "validate_target_identity"),
            "target identity validator is missing",
        )
        lock = json.loads(TARGET_LOCK_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_root = Path(temporary_directory)
            write_fixture_text(
                source_root,
                "etc/os-release",
                "ID=ubuntu\nVERSION_ID=26.04\nVERSION_CODENAME=resolute\n",
            )
            write_fixture_text(
                source_root,
                "proc/cpuinfo",
                "processor : 0\n"
                "vendor_id : AuthenticAMD\n"
                "cpu family : 25\n"
                "model : 97\n"
                "model name : AMD Ryzen 9 7900X 12-Core Processor\n"
                "stepping : 2\n",
            )
            identity = self.module.validate_target_identity(
                lock,
                source_root=source_root,
                architecture="x86_64",
            )
            self.assertEqual(identity, lock["target"])

            wrong_cpu = copy.deepcopy(lock)
            wrong_cpu["target"]["cpu"]["model"] = 98
            wrong_os = copy.deepcopy(lock)
            wrong_os["target"]["version_id"] = "24.04"
            wrong_architecture = copy.deepcopy(lock)
            wrong_architecture["target"]["architecture"] = "aarch64"
            incomplete_cpu = copy.deepcopy(lock)
            del incomplete_cpu["target"]["cpu"]["model_name"]
            for mutation in (
                wrong_cpu,
                wrong_os,
                wrong_architecture,
                incomplete_cpu,
            ):
                with self.subTest(target=mutation["target"]):
                    with self.assertRaises(self.module.PreparationError):
                        self.module.validate_target_identity(
                            mutation,
                            source_root=source_root,
                            architecture="x86_64",
                        )


ARGUMENTS = parse_arguments()


if __name__ == "__main__":
    unittest.main(argv=unittest.main_argv)
