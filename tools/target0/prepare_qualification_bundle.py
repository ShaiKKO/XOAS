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


_COMPILER_DRIVER = "/usr/bin/clang++-21"
_LINKER_DRIVER = "/usr/bin/ld.lld-21"
_LINKER_RESOLVED_PATH = "/usr/lib/llvm-21/bin/lld"
_WARNING_FLAGS = (
    "-Wall",
    "-Wextra",
    "-Wpedantic",
    "-Werror",
    "-Wcast-align",
    "-Wconversion",
    "-Wdouble-promotion",
    "-Wextra-semi",
    "-Wformat=2",
    "-Wimplicit-fallthrough",
    "-Wnon-virtual-dtor",
    "-Wold-style-cast",
    "-Woverloaded-virtual",
    "-Wshadow",
    "-Wsign-conversion",
    "-Wundef",
    "-Wzero-as-null-pointer-constant",
)


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


def _locked_package(
    lock: dict[str, object],
    package_name: str,
) -> dict[str, str]:
    """Return one exact package identity from the provisioning prestate."""
    try:
        apt = lock["apt"]
        if not isinstance(apt, dict):
            raise TypeError
        prestate = apt["prestate"]
        if not isinstance(prestate, dict):
            raise TypeError
        packages = prestate["packages"]
        if not isinstance(packages, list):
            raise TypeError
        matches = [
            package
            for package in packages
            if isinstance(package, dict) and package.get("name") == package_name
        ]
        if len(matches) != 1 or not isinstance(matches[0].get("version"), str):
            raise TypeError
        return {
            "name": package_name,
            "version": matches[0]["version"],
        }
    except (KeyError, TypeError) as error:
        raise PreparationError("locked package identity is incomplete") from error


def _locked_executable(
    lock: dict[str, object],
    executable_name: str,
) -> dict[str, object]:
    """Return one exact executable identity from the provisioning lock."""
    try:
        executables = lock["existing_executables"]
        if not isinstance(executables, list):
            raise TypeError
        matches = [
            executable
            for executable in executables
            if isinstance(executable, dict)
            and executable.get("name") == executable_name
        ]
        if len(matches) != 1:
            raise TypeError
        executable = matches[0]
        if (
            executable.get("available") is not True
            or not isinstance(executable.get("path"), str)
            or not isinstance(executable.get("version_line"), str)
            or re.fullmatch(r"[0-9a-f]{64}", str(executable.get("sha256")))
            is None
        ):
            raise TypeError
        return copy.deepcopy(executable)
    except (KeyError, TypeError) as error:
        raise PreparationError("locked executable identity is incomplete") from error


def _first_output_line(output: str, operation: str) -> str:
    """Return a required first output line from an authenticated command."""
    lines = output.splitlines()
    if not lines or not lines[0]:
        raise PreparationError(f"{operation} returned no identity")
    return lines[0]


def _command_sha256(
    command_runner: CommandRunner,
    path: str,
    operation: str,
) -> str:
    """Read one canonical SHA-256 from the fixed system utility."""
    output = _require_success(
        command_runner(("/usr/bin/sha256sum", path)),
        operation,
    )
    fields = output.split(maxsplit=1)
    if (
        len(fields) != 2
        or re.fullmatch(r"[0-9a-f]{64}", fields[0]) is None
        or fields[1].lstrip("*").strip() != path
    ):
        raise PreparationError(f"{operation} returned an invalid digest")
    return fields[0]


def validate_compiler(
    lock: dict[str, object],
    command_runner: CommandRunner,
) -> dict[str, object]:
    """Authenticate the fixed Target 0 C++ driver against the lock."""
    locked_compiler = _locked_executable(lock, "clang++-21")
    clang_package = _locked_package(lock, "clang-21")
    resolved_path = _require_success(
        command_runner(("/usr/bin/readlink", "-f", _COMPILER_DRIVER)),
        "compiler path inspection",
    )
    if resolved_path != locked_compiler["path"]:
        raise PreparationError("compiler resolved path differs from the lock")
    version = _first_output_line(
        _require_success(
            command_runner((_COMPILER_DRIVER, "--version")),
            "compiler version inspection",
        ),
        "compiler version inspection",
    )
    target_triple = _require_success(
        command_runner((_COMPILER_DRIVER, "-dumpmachine")),
        "compiler target inspection",
    )
    digest = _command_sha256(
        command_runner,
        resolved_path,
        "compiler digest inspection",
    )
    if version != locked_compiler["version_line"]:
        raise PreparationError("compiler version differs from the lock")
    if digest != locked_compiler["sha256"]:
        raise PreparationError("compiler digest differs from the lock")
    try:
        target = lock["target"]
        if not isinstance(target, dict) or target["architecture"] != "x86_64":
            raise TypeError
    except (KeyError, TypeError) as error:
        raise PreparationError("compiler target lock is incomplete") from error
    if target_triple != "x86_64-pc-linux-gnu":
        raise PreparationError("compiler target triple differs from the lock")
    return {
        "driver_path": _COMPILER_DRIVER,
        "resolved_path": resolved_path,
        "version": version,
        "target_triple": target_triple,
        "sha256": digest,
        "package": clang_package,
    }


def validate_linker(
    lock: dict[str, object],
    command_runner: CommandRunner,
) -> dict[str, object]:
    """Authenticate LLD against the locked package closure and live bytes."""
    locked_package = _locked_package(lock, "lld-21")
    resolved_path = _require_success(
        command_runner(("/usr/bin/readlink", "-f", _LINKER_DRIVER)),
        "linker path inspection",
    )
    if resolved_path != _LINKER_RESOLVED_PATH:
        raise PreparationError("linker resolved path differs from the contract")
    installed_version = _require_success(
        command_runner(
            (
                "/usr/bin/dpkg-query",
                "-W",
                "-f=${Version}\\n",
                "lld-21",
            )
        ),
        "linker package version inspection",
    )
    if installed_version != locked_package["version"]:
        raise PreparationError("linker package version differs from the lock")
    verification = command_runner(("/usr/bin/dpkg", "-V", "lld-21"))
    if (
        verification.returncode != 0
        or verification.stdout.strip()
        or verification.stderr.strip()
    ):
        raise PreparationError("linker package verification failed")
    ownership = _require_success(
        command_runner(("/usr/bin/dpkg-query", "-S", resolved_path)),
        "linker package ownership inspection",
    )
    if ownership.strip() != f"lld-21: {resolved_path}":
        raise PreparationError("linker resolved path lacks locked ownership")
    version = _first_output_line(
        _require_success(
            command_runner((_LINKER_DRIVER, "--version")),
            "linker version inspection",
        ),
        "linker version inspection",
    )
    digest = _command_sha256(
        command_runner,
        resolved_path,
        "linker digest inspection",
    )
    return {
        "driver_path": _LINKER_DRIVER,
        "resolved_path": resolved_path,
        "version": version,
        "sha256": digest,
        "package": locked_package,
    }


def qualification_compile_arguments(
    source: Path,
    output: Path,
) -> tuple[str, ...]:
    """Return the closed native qualification-probe build contract."""
    if source != Path("qualification_probe.cpp"):
        raise PreparationError("qualification source path differs")
    if output != Path("xoas-target0-qualification-probe"):
        raise PreparationError("qualification output path differs")
    return (
        _COMPILER_DRIVER,
        "-std=c++23",
        "-O3",
        "-DNDEBUG",
        *_WARNING_FLAGS,
        f"-fuse-ld={_LINKER_DRIVER}",
        str(source),
        "-o",
        str(output),
    )


def _write_private_text(path: Path, content: str) -> None:
    """Write one retained diagnostic with owner-only permissions."""
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)


def _executable_record(path: Path, staging_root: Path) -> dict[str, object]:
    """Authenticate and describe one private regular executable."""
    if path.is_symlink() or not path.is_file():
        raise PreparationError("compiler output is not a regular file")
    size_bytes = path.stat().st_size
    if size_bytes <= 0:
        raise PreparationError("compiler output is empty")
    path.chmod(0o700)
    if not os.access(path, os.X_OK):
        raise PreparationError("compiler output is not executable")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "path": path.relative_to(staging_root).as_posix(),
        "sha256": digest,
        "size_bytes": size_bytes,
    }


def build_probe_twice(
    source: Path,
    expected_source_sha256: str,
    staging_root: Path,
    source_date_epoch: str,
    command_runner: CommandRunner,
) -> dict[str, object]:
    """Build independently and require byte-identical executables."""
    if (
        source.is_symlink()
        or not source.is_file()
        or re.fullmatch(r"[0-9a-f]{64}", expected_source_sha256) is None
    ):
        raise PreparationError("reviewed probe source is invalid")
    source_bytes = source.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != expected_source_sha256:
        raise PreparationError("reviewed probe source digest differs")
    if re.fullmatch(r"[0-9]{1,20}", source_date_epoch) is None:
        raise PreparationError("source date epoch is invalid")
    if staging_root.is_symlink() or not staging_root.is_dir():
        raise PreparationError("staging root is invalid")

    compile_arguments = qualification_compile_arguments(
        Path("qualification_probe.cpp"),
        Path("xoas-target0-qualification-probe"),
    )
    build_records: list[dict[str, object]] = []
    for build_name in ("build-01", "build-02"):
        build_directory = staging_root / build_name
        try:
            build_directory.mkdir(mode=0o700, exist_ok=False)
            temporary_directory = build_directory / "tmp"
            temporary_directory.mkdir(mode=0o700, exist_ok=False)
            copied_source = build_directory / "qualification_probe.cpp"
            copied_source.write_bytes(source_bytes)
            copied_source.chmod(0o600)
        except OSError as error:
            raise PreparationError("private build directory cannot be created") from error
        environment = {
            "HOME": "/nonexistent",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PATH": "/usr/bin:/usr/sbin",
            "SOURCE_DATE_EPOCH": source_date_epoch,
            "TMPDIR": str(temporary_directory),
        }
        result = command_runner(
            compile_arguments,
            build_directory,
            environment=environment,
            timeout=180,
        )
        _write_private_text(build_directory / "compiler.stdout.log", result.stdout)
        _write_private_text(build_directory / "compiler.stderr.log", result.stderr)
        if result.returncode != 0:
            raise PreparationError("qualification probe compilation failed")
        build_records.append(
            _executable_record(
                build_directory / "xoas-target0-qualification-probe",
                staging_root,
            )
        )

    first_digest = build_records[0]["sha256"]
    second_digest = build_records[1]["sha256"]
    if first_digest != second_digest:
        raise PreparationError("independent qualification builds differ")
    accepted_directory = staging_root / "bin"
    try:
        accepted_directory.mkdir(mode=0o700, exist_ok=False)
        accepted_path = accepted_directory / "xoas-target0-qualification-probe"
        with accepted_path.open("xb") as accepted_file:
            accepted_file.write(
                (staging_root / build_records[0]["path"]).read_bytes()
            )
        accepted_path.chmod(0o700)
    except OSError as error:
        raise PreparationError("accepted executable cannot be published") from error
    accepted_record = _executable_record(accepted_path, staging_root)
    if accepted_record["sha256"] != first_digest:
        raise PreparationError("accepted executable digest differs")
    return {
        "arguments": list(compile_arguments),
        "environment": {
            "HOME": "/nonexistent",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PATH": "/usr/bin:/usr/sbin",
            "SOURCE_DATE_EPOCH": source_date_epoch,
            "TMPDIR": "private-build-directory",
        },
        "builds": build_records,
        "identical": True,
        "executable_sha256": first_digest,
        "accepted_executable": accepted_record,
    }


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
