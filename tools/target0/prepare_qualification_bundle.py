#!/usr/bin/env python3
"""Prepare a closed native Target 0 qualification-tool evidence bundle."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
from typing import Protocol

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError


class PreparationError(RuntimeError):
    """Report a condition that makes a deployment bundle inadmissible."""


class CommandRunner(Protocol):
    """Run one fixed argument array in an explicit working directory."""

    def __call__(
        self,
        command: tuple[str, ...],
        working_directory: Path | None = None,
        *,
        environment: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> SimpleNamespace:
        """Return status and captured output for one bounded command."""


def canonical_json_bytes(record: object) -> bytes:
    """Serialize one retained record with stable UTF-8 JSON bytes."""
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


def _full_git_object(value: str) -> str:
    """Accept one canonical full SHA-1 Git object identity."""
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise argparse.ArgumentTypeError(
            "expected commit must be 40 lowercase hex digits"
        )
    return value


def parse_arguments(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the closed qualification-bundle preparation interface."""
    parser = argparse.ArgumentParser(
        description="Prepare a native XOAS Target 0 qualification-tool bundle."
    )
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--expected-commit", required=True, type=_full_git_object)
    parser.add_argument("--toolchain-lock", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    return parser.parse_args(arguments)


def run_command(
    command: tuple[str, ...],
    working_directory: Path | None = None,
    *,
    environment: dict[str, str] | None = None,
    timeout: int = 30,
) -> SimpleNamespace:
    """Run one bounded command without shell evaluation."""
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        cwd=working_directory,
        env=environment,
        shell=False,
        text=True,
        timeout=timeout,
    )
    return SimpleNamespace(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _require_success(result: SimpleNamespace, operation: str) -> str:
    """Return stripped stdout without exposing a failed command's output."""
    if result.returncode != 0:
        raise PreparationError(f"{operation} failed")
    return result.stdout.strip()


def validate_repository(
    repository_root: Path,
    expected_commit: str,
    command_runner: CommandRunner,
) -> dict[str, object]:
    """Return a closed clean-checkout identity or fail without path leakage."""
    if re.fullmatch(r"[0-9a-f]{40}", expected_commit) is None:
        raise PreparationError("expected commit is not a full Git identity")
    try:
        resolved_root = repository_root.resolve(strict=True)
    except OSError as error:
        raise PreparationError("repository root is unavailable") from error
    if not resolved_root.is_dir():
        raise PreparationError("repository root is not a directory")

    top_level = _require_success(
        command_runner(
            ("/usr/bin/git", "rev-parse", "--show-toplevel"),
            resolved_root,
        ),
        "repository root inspection",
    )
    try:
        observed_top_level = Path(top_level).resolve(strict=True)
    except OSError as error:
        raise PreparationError("repository root identity is invalid") from error
    if observed_top_level != resolved_root:
        raise PreparationError("repository root identity differs")

    actual_commit = _require_success(
        command_runner(("/usr/bin/git", "rev-parse", "HEAD"), resolved_root),
        "repository commit inspection",
    )
    tree = _require_success(
        command_runner(
            ("/usr/bin/git", "rev-parse", "HEAD^{tree}"),
            resolved_root,
        ),
        "repository tree inspection",
    )
    status = _require_success(
        command_runner(
            (
                "/usr/bin/git",
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            ),
            resolved_root,
        ),
        "repository status inspection",
    )
    public_remote = _require_success(
        command_runner(
            ("/usr/bin/git", "remote", "get-url", "origin"),
            resolved_root,
        ),
        "repository remote inspection",
    )

    if actual_commit != expected_commit:
        raise PreparationError("repository commit differs from expected identity")
    if re.fullmatch(r"[0-9a-f]{40}", tree) is None:
        raise PreparationError("repository tree identity is invalid")
    if status:
        raise PreparationError("repository is dirty")
    if public_remote != "https://github.com/ShaiKKO/XOAS.git":
        raise PreparationError("repository public remote differs")
    return {
        "actual_commit": actual_commit,
        "expected_commit": expected_commit,
        "public_remote": public_remote,
        "tree": tree,
        "tree_state": "clean",
    }


def validate_toolchain_lock(
    lock_path: Path,
    schema_path: Path,
) -> dict[str, object]:
    """Validate the installed Target 0 lock and its stable configuration."""
    try:
        if lock_path.is_symlink() or schema_path.is_symlink():
            raise PreparationError("toolchain lock input is a symlink")
        lock_bytes = lock_path.read_bytes()
        schema_bytes = schema_path.read_bytes()
        lock = json.loads(lock_bytes.decode("utf-8"))
        schema = json.loads(schema_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PreparationError("toolchain lock input is unreadable") from error
    if not isinstance(lock, dict) or not isinstance(schema, dict):
        raise PreparationError("toolchain lock input is not an object")
    if schema.get("$id") != (
        "https://xoas.dev/schemas/target0-toolchain-lock-v1.schema.json"
    ):
        raise PreparationError("toolchain lock schema identity differs")
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(lock)
    except (SchemaError, ValidationError) as error:
        raise PreparationError("toolchain lock validation failed") from error
    if lock.get("state") != "installed_verified":
        raise PreparationError("toolchain lock is not installed and verified")
    if lock.get("baseline_stack_verified") is not True:
        raise PreparationError("toolchain lock baseline stack is not verified")
    if lock.get("target0_measurement_qualified") is not False:
        raise PreparationError("toolchain lock improperly claims qualification")
    if lock.get("performance_claim") is not False:
        raise PreparationError("toolchain lock contains a performance claim")

    configuration = dict(lock)
    configuration_digest = configuration.pop("configuration_sha256", None)
    configuration_bytes = json.dumps(
        configuration,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if (
        not isinstance(configuration_digest, str)
        or hashlib.sha256(configuration_bytes).hexdigest()
        != configuration_digest
    ):
        raise PreparationError("toolchain lock configuration digest differs")
    return {
        "configuration_sha256": configuration_digest,
        "execution_subject": lock["execution_subject"],
        "file_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "lock_id": lock["lock_id"],
    }


def _read_required_text(source_root: Path, absolute_path: str) -> str:
    """Read one required target fact below a real or fixture root."""
    path = source_root / absolute_path.removeprefix("/")
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise PreparationError("required target identity is unavailable") from error


def _parse_key_values(text: str, separator: str) -> dict[str, str]:
    """Parse one bounded Linux key-value identity record."""
    values: dict[str, str] = {}
    for line in text.splitlines():
        if separator not in line:
            continue
        key, value = line.split(separator, maxsplit=1)
        values[key.strip()] = value.strip().strip('"')
    return values


def validate_target_identity(
    lock: dict[str, object],
    *,
    source_root: Path,
    architecture: str,
) -> dict[str, object]:
    """Match unprivileged CPU, OS, and architecture facts to the lock."""
    try:
        target = lock["target"]
        if not isinstance(target, dict):
            raise TypeError
        expected_cpu = target["cpu"]
        if not isinstance(expected_cpu, dict):
            raise TypeError
        release = _parse_key_values(
            _read_required_text(source_root, "/etc/os-release"),
            "=",
        )
        first_cpu_block = _read_required_text(
            source_root,
            "/proc/cpuinfo",
        ).split("\n\n", maxsplit=1)[0]
        observed_cpu = _parse_key_values(first_cpu_block, ":")
        cpu_identity = {
            "vendor_id": observed_cpu["vendor_id"],
            "family": int(observed_cpu["cpu family"]),
            "model": int(observed_cpu["model"]),
            "stepping": int(observed_cpu["stepping"]),
            "model_name": observed_cpu["model name"],
        }
        os_identity = {
            "operating_system": release["ID"],
            "version_id": release["VERSION_ID"],
            "codename": release["VERSION_CODENAME"],
            "architecture": architecture,
        }
        expected_cpu_identity = {
            key: expected_cpu[key]
            for key in (
                "vendor_id",
                "family",
                "model",
                "stepping",
                "model_name",
            )
        }
        expected_os_identity = {
            key: target[key]
            for key in (
                "operating_system",
                "version_id",
                "codename",
                "architecture",
            )
        }
    except (KeyError, TypeError, ValueError) as error:
        raise PreparationError("target identity record is incomplete") from error
    if cpu_identity != expected_cpu_identity:
        raise PreparationError("target CPU identity differs from the lock")
    if os_identity != expected_os_identity:
        raise PreparationError("target OS identity differs from the lock")
    return copy.deepcopy(target)


def create_staging_root(
    output_directory: Path,
    *,
    allowed_root: Path,
    repository_root: Path,
    install_prefix: Path,
    home_directory: Path,
) -> Path:
    """Create one new private evidence root within the approved boundary."""
    if not output_directory.is_absolute():
        raise PreparationError("output directory must be absolute")
    if re.fullmatch(
        r"xoas-target0-qualification-tools\."
        r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?",
        output_directory.name,
    ) is None:
        raise PreparationError("output directory name is outside the contract")
    try:
        resolved_allowed_root = allowed_root.resolve(strict=True)
        resolved_parent = output_directory.parent.resolve(strict=True)
        resolved_output = output_directory.resolve(strict=False)
        protected_paths = tuple(
            path.resolve(strict=True)
            for path in (repository_root, install_prefix, home_directory)
        )
    except OSError as error:
        raise PreparationError("output boundary cannot be resolved") from error
    if resolved_output != output_directory:
        raise PreparationError("output directory path is not canonical")
    if resolved_parent != resolved_allowed_root:
        raise PreparationError("output directory is outside the evidence root")
    if os.path.lexists(output_directory):
        raise PreparationError("output directory already exists")
    if any(
        output_directory == protected
        or output_directory in protected.parents
        or protected in output_directory.parents
        for protected in protected_paths
    ):
        raise PreparationError("output directory overlaps a protected path")
    try:
        output_directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    except OSError as error:
        raise PreparationError("output directory cannot be created") from error
    if output_directory.is_symlink() or not output_directory.is_dir():
        raise PreparationError("output directory has an unsafe file type")
    return output_directory
