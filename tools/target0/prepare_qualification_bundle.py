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
_RUNTIME_PACKAGE_BY_SONAME = {
    "libstdc++.so.6": "libstdc++6:amd64",
    "libm.so.6": "libc6:amd64",
    "libgcc_s.so.1": "libgcc-s1:amd64",
    "libc.so.6": "libc6:amd64",
    "ld-linux-x86-64.so.2": "libc6:amd64",
}


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
    *,
    environment: dict[str, str] | None = None,
) -> str:
    """Read one canonical SHA-256 from the fixed system utility."""
    output = _require_success(
        command_runner(
            ("/usr/bin/sha256sum", path),
            environment=environment,
        ),
        operation,
    )
    return _parse_sha256_output(output, path, operation)


def _parse_sha256_output(output: str, path: str, operation: str) -> str:
    """Parse one canonical SHA-256 utility result for an exact path."""
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
            raise PreparationError(
                "private build directory cannot be created"
            ) from error
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


def _is_approved_system_path(path: str) -> bool:
    """Return whether a canonical absolute path is in a system runtime root."""
    candidate = Path(path)
    if not candidate.is_absolute() or candidate != Path(os.path.normpath(path)):
        return False
    return path.startswith(("/lib/", "/lib64/", "/usr/lib/"))


def parse_file_identity(output: str) -> str:
    """Validate `file` output and return the absolute ELF interpreter."""
    lines = output.splitlines()
    if len(lines) != 1:
        raise PreparationError("file identity output is malformed")
    identity = lines[0]
    required_fragments = (
        "ELF 64-bit LSB",
        "x86-64",
        "dynamically linked",
    )
    if any(fragment not in identity for fragment in required_fragments):
        raise PreparationError("file identity differs from Target 0")
    interpreter_match = re.search(r"(?:^|, )interpreter ([^,]+)(?:,|$)", identity)
    if interpreter_match is None:
        raise PreparationError("ELF interpreter is absent")
    interpreter = interpreter_match.group(1)
    if not _is_approved_system_path(interpreter):
        raise PreparationError("ELF interpreter path is unapproved")
    return interpreter


def parse_readelf_header(output: str) -> dict[str, str]:
    """Parse and validate the closed ELF64 x86-64 header identity."""
    observed: dict[str, str] = {}
    for line in output.splitlines():
        match = re.match(r"^\s+(Class|Data|Type|Machine):\s+(.+?)\s*$", line)
        if match is None:
            continue
        field, value = match.groups()
        if field in observed:
            raise PreparationError("ELF header contains duplicate identity fields")
        observed[field] = value
    if observed.get("Class") != "ELF64":
        raise PreparationError("ELF class differs from Target 0")
    if observed.get("Data") != "2's complement, little endian":
        raise PreparationError("ELF endianness differs from Target 0")
    if observed.get("Machine") != "Advanced Micro Devices X86-64":
        raise PreparationError("ELF machine differs from Target 0")
    elf_type = observed.get("Type", "").split(maxsplit=1)[0]
    if elf_type not in {"DYN", "EXEC"}:
        raise PreparationError("ELF type is unsupported")
    return {
        "class": "ELF64",
        "endianness": "little",
        "machine": observed["Machine"],
        "type": elf_type,
    }


def parse_readelf_notes(output: str) -> str | None:
    """Return one optional canonical GNU build ID without inventing one."""
    build_ids = re.findall(r"\bBuild ID:\s*([0-9A-Fa-f]+)\s*$", output, re.MULTILINE)
    if not build_ids:
        return None
    if (
        len(build_ids) != 1
        or re.fullmatch(r"[0-9a-f]{32,64}", build_ids[0]) is None
    ):
        raise PreparationError("ELF build ID is malformed or ambiguous")
    return build_ids[0]


def parse_readelf_dynamic(output: str) -> tuple[str, ...]:
    """Return one ordered duplicate-free direct dependency set."""
    needed_lines = [line for line in output.splitlines() if "(NEEDED)" in line]
    needed = tuple(
        match.group(1)
        for line in needed_lines
        if (
            match := re.search(
                r"\(NEEDED\)\s+Shared library: \[([^]]+)\]\s*$",
                line,
            )
        )
    )
    if not needed or len(needed) != len(needed_lines):
        raise PreparationError("ELF dynamic dependency output is malformed")
    if len(set(needed)) != len(needed):
        raise PreparationError("ELF dynamic dependencies contain duplicates")
    if any(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9+_.-]*", name) is None
        for name in needed
    ):
        raise PreparationError("ELF dynamic dependency name is invalid")
    return needed


def parse_ldd_dependencies(
    output: str,
    needed: tuple[str, ...],
    interpreter: str,
) -> tuple[tuple[str, str], ...]:
    """Resolve one exact direct dependency and interpreter mapping."""
    expected = (*needed, Path(interpreter).name)
    if len(set(expected)) != len(expected):
        raise PreparationError("runtime dependency identity is ambiguous")
    observed: dict[str, str] = {}
    virtual_dynamic_shared_object_seen = False
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.fullmatch(r"linux-vdso\.so\.1 \(0x[0-9a-fA-F]+\)", line):
            if virtual_dynamic_shared_object_seen:
                raise PreparationError(
                    "loader output contains duplicate virtual objects"
                )
            virtual_dynamic_shared_object_seen = True
            continue
        arrow_match = re.fullmatch(
            r"([A-Za-z0-9][A-Za-z0-9+_.-]*) => (\S+) \(0x[0-9a-fA-F]+\)",
            line,
        )
        direct_match = re.fullmatch(r"(\S+) \(0x[0-9a-fA-F]+\)", line)
        if arrow_match is not None:
            soname, loader_path = arrow_match.groups()
        elif direct_match is not None:
            loader_path = direct_match.group(1)
            soname = Path(loader_path).name
        else:
            raise PreparationError("loader output is unresolved or malformed")
        if soname in observed:
            raise PreparationError("loader output contains duplicate dependencies")
        if not _is_approved_system_path(loader_path):
            raise PreparationError("loader dependency path is unapproved")
        observed[soname] = loader_path
    if set(observed) != set(expected):
        raise PreparationError("loader output differs from ELF dependencies")
    if observed[Path(interpreter).name] != interpreter:
        raise PreparationError("loader interpreter differs from the ELF identity")
    return tuple((soname, observed[soname]) for soname in expected)


def _inspection_environment() -> dict[str, str]:
    """Return the complete environment allowed for read-only inspection."""
    return {
        "HOME": "/nonexistent",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin:/usr/sbin",
    }


def _run_retained_command(
    name: str,
    command: tuple[str, ...],
    working_directory: Path,
    log_directory: Path,
    command_runner: CommandRunner,
    environment: dict[str, str],
    *,
    fail_on_nonzero: bool = True,
) -> tuple[SimpleNamespace, dict[str, str]]:
    """Run one fixed command and retain its closed status and raw output."""
    if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", name) is None:
        raise PreparationError("retained command name is invalid")
    result = command_runner(
        command,
        working_directory,
        environment=environment,
        timeout=180,
    )
    stdout_bytes = result.stdout.encode("utf-8")
    stderr_bytes = result.stderr.encode("utf-8")
    stdout_path = log_directory / f"{name}.stdout.log"
    stderr_path = log_directory / f"{name}.stderr.log"
    status_path = log_directory / f"{name}.json"
    stdout_path.write_bytes(stdout_bytes)
    stderr_path.write_bytes(stderr_bytes)
    status_record = {
        "command": list(command),
        "exit_status": result.returncode,
        "name": name,
        "status": "passed" if result.returncode == 0 else "failed",
        "stderr_sha256": hashlib.sha256(stderr_bytes).hexdigest(),
        "stdout_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
    }
    status_bytes = canonical_json_bytes(status_record)
    status_path.write_bytes(status_bytes)
    for path in (stdout_path, stderr_path, status_path):
        path.chmod(0o600)
    log_record = {
        "name": name,
        "sha256": hashlib.sha256(status_bytes).hexdigest(),
    }
    if fail_on_nonzero and result.returncode != 0:
        raise PreparationError(f"{name} command failed")
    return result, log_record


def inspect_elf_runtime(
    executable: Path,
    staging_root: Path,
    lock: dict[str, object],
    command_runner: CommandRunner,
) -> dict[str, object]:
    """Authenticate ELF identity and every resolved Target 0 dependency."""
    try:
        resolved_staging_root = staging_root.resolve(strict=True)
        resolved_executable = executable.resolve(strict=True)
    except OSError as error:
        raise PreparationError("runtime inspection input is unavailable") from error
    expected_executable = (
        resolved_staging_root / "bin/xoas-target0-qualification-probe"
    )
    if (
        staging_root.is_symlink()
        or executable.is_symlink()
        or not executable.is_file()
        or resolved_executable != expected_executable
    ):
        raise PreparationError("runtime inspection executable is invalid")
    log_directory = resolved_staging_root / "inspection"
    try:
        log_directory.mkdir(mode=0o700, exist_ok=False)
    except OSError as error:
        raise PreparationError("inspection log directory cannot be created") from error

    environment = _inspection_environment()
    executable_path = str(resolved_executable)
    inspection_commands = (
        (
            "file",
            (
                "/usr/bin/file",
                "--brief",
                "--dereference",
                executable_path,
            ),
        ),
        (
            "readelf-header",
            ("/usr/bin/readelf", "-h", "-W", executable_path),
        ),
        (
            "readelf-notes",
            ("/usr/bin/readelf", "-n", "-W", executable_path),
        ),
        (
            "readelf-dynamic",
            ("/usr/bin/readelf", "-d", "-W", executable_path),
        ),
        ("ldd", ("/usr/bin/ldd", executable_path)),
    )
    outputs: dict[str, str] = {}
    inspection_logs: list[dict[str, str]] = []
    for name, command in inspection_commands:
        result, log_record = _run_retained_command(
            name,
            command,
            resolved_staging_root,
            log_directory,
            command_runner,
            environment,
        )
        outputs[name] = result.stdout
        inspection_logs.append(log_record)

    interpreter = parse_file_identity(outputs["file"])
    header = parse_readelf_header(outputs["readelf-header"])
    build_id = parse_readelf_notes(outputs["readelf-notes"])
    needed = parse_readelf_dynamic(outputs["readelf-dynamic"])
    dependency_paths = parse_ldd_dependencies(outputs["ldd"], needed, interpreter)
    runtime_dependencies: list[dict[str, object]] = []
    for dependency_index, (soname, loader_path) in enumerate(
        dependency_paths,
        start=1,
    ):
        expected_package_name = _RUNTIME_PACKAGE_BY_SONAME.get(soname)
        if expected_package_name is None:
            raise PreparationError("runtime dependency is outside the contract")
        expected_package = _locked_package(lock, expected_package_name)
        command_prefix = f"dependency-{dependency_index:02d}"
        realpath_result, realpath_log = _run_retained_command(
            f"{command_prefix}-realpath",
            ("/usr/bin/readlink", "-f", loader_path),
            resolved_staging_root,
            log_directory,
            command_runner,
            environment,
        )
        inspection_logs.append(realpath_log)
        realpath = realpath_result.stdout.strip()
        if not _is_approved_system_path(realpath):
            raise PreparationError("runtime dependency realpath is unapproved")

        size_result, size_log = _run_retained_command(
            f"{command_prefix}-size",
            ("/usr/bin/stat", "--format=%s", realpath),
            resolved_staging_root,
            log_directory,
            command_runner,
            environment,
        )
        inspection_logs.append(size_log)
        try:
            size_bytes = int(size_result.stdout.strip())
        except ValueError as error:
            raise PreparationError("runtime dependency size is invalid") from error
        if size_bytes <= 0 or str(size_bytes) != size_result.stdout.strip():
            raise PreparationError("runtime dependency size is invalid")

        digest_result, digest_log = _run_retained_command(
            f"{command_prefix}-digest",
            ("/usr/bin/sha256sum", realpath),
            resolved_staging_root,
            log_directory,
            command_runner,
            environment,
        )
        inspection_logs.append(digest_log)
        digest = _parse_sha256_output(
            digest_result.stdout,
            realpath,
            "runtime dependency digest inspection",
        )

        owner_result, owner_log = _run_retained_command(
            f"{command_prefix}-owner",
            ("/usr/bin/dpkg-query", "-S", realpath),
            resolved_staging_root,
            log_directory,
            command_runner,
            environment,
        )
        inspection_logs.append(owner_log)
        if owner_result.stdout.strip() != f"{expected_package_name}: {realpath}":
            raise PreparationError("runtime dependency package owner differs")

        version_result, version_log = _run_retained_command(
            f"{command_prefix}-version",
            (
                "/usr/bin/dpkg-query",
                "-W",
                "-f=${Version}\\n",
                expected_package_name,
            ),
            resolved_staging_root,
            log_directory,
            command_runner,
            environment,
        )
        inspection_logs.append(version_log)
        if version_result.stdout.strip() != expected_package["version"]:
            raise PreparationError("runtime dependency package version differs")
        runtime_dependencies.append(
            {
                "soname": soname,
                "loader_path": loader_path,
                "realpath": realpath,
                "size_bytes": size_bytes,
                "sha256": digest,
                "package": expected_package,
            }
        )

    return {
        "elf": {
            **header,
            "interpreter": interpreter,
            "build_id": build_id,
            "needed": list(needed),
            "inspection_logs": inspection_logs,
        },
        "runtime_dependencies": runtime_dependencies,
    }


def validate_schema_instance(schema_path: Path, instance: object) -> None:
    """Meta-validate one draft-2020-12 schema and validate its instance."""
    try:
        if schema_path.is_symlink():
            raise PreparationError("schema input is a symlink")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PreparationError("schema input is unreadable") from error
    if not isinstance(schema, dict):
        raise PreparationError("schema input is not an object")
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(instance)
    except (SchemaError, ValidationError) as error:
        raise PreparationError("schema or instance validation failed") from error


def run_compatibility_tests(
    repository_root: Path,
    accepted_probe: Path,
    staging_root: Path,
    command_runner: CommandRunner,
) -> list[dict[str, object]]:
    """Run the closed physical compatibility suite and retain every result."""
    try:
        resolved_repository_root = repository_root.resolve(strict=True)
        resolved_staging_root = staging_root.resolve(strict=True)
        resolved_probe = accepted_probe.resolve(strict=True)
    except OSError as error:
        raise PreparationError("compatibility-test input is unavailable") from error
    if (
        repository_root.is_symlink()
        or not resolved_repository_root.is_dir()
        or staging_root.is_symlink()
        or not resolved_staging_root.is_dir()
        or accepted_probe.is_symlink()
        or not resolved_probe.is_file()
        or resolved_probe
        != resolved_staging_root / "bin/xoas-target0-qualification-probe"
    ):
        raise PreparationError("compatibility-test input is invalid")

    required_repository_paths = (
        "tools/target0/prepare_qualification_bundle.py",
        "tools/target0/capture_host.py",
        "tools/target0/measurement_session.sh",
        "tests/target0/capture_host_test.py",
        "tests/target0/measurement_session_test.py",
        "tests/target0/qualification_probe_test.py",
        "schemas/target0-host-qualification-v1.schema.json",
        "schemas/target0-qualification-tool-bundle-v1.schema.json",
    )
    for relative_path in required_repository_paths:
        path = resolved_repository_root / relative_path
        if path.is_symlink() or not path.is_file():
            raise PreparationError("compatibility-test source is unavailable")

    compatibility_directory = resolved_staging_root / "compatibility"
    try:
        compatibility_directory.mkdir(mode=0o700, exist_ok=False)
        temporary_directory = compatibility_directory / "tmp"
        temporary_directory.mkdir(mode=0o700, exist_ok=False)
        python_cache = compatibility_directory / "python-cache"
        python_cache.mkdir(mode=0o700, exist_ok=False)
    except OSError as error:
        raise PreparationError(
            "compatibility log directory cannot be created"
        ) from error
    environment = {
        "HOME": "/nonexistent",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin:/usr/sbin",
        "PYTHONPYCACHEPREFIX": str(python_cache),
        "TMPDIR": str(temporary_directory),
    }
    commands = (
        (
            "python-byte-compilation",
            (
                "/usr/bin/python3",
                "-m",
                "py_compile",
                "tools/target0/prepare_qualification_bundle.py",
                "tools/target0/capture_host.py",
            ),
        ),
        (
            "bash-syntax",
            (
                "/usr/bin/bash",
                "-n",
                "tools/target0/measurement_session.sh",
            ),
        ),
        (
            "capture-host-fixtures",
            ("/usr/bin/python3", "tests/target0/capture_host_test.py"),
        ),
        (
            "measurement-session-fixtures",
            (
                "/usr/bin/python3",
                "tests/target0/measurement_session_test.py",
            ),
        ),
        (
            "qualification-probe-behavior",
            (
                "/usr/bin/python3",
                "tests/target0/qualification_probe_test.py",
                "--probe",
                str(resolved_probe),
                "--schema",
                "schemas/target0-host-qualification-v1.schema.json",
            ),
        ),
    )
    records: list[dict[str, object]] = []
    for name, command in commands:
        result, _ = _run_retained_command(
            name,
            command,
            resolved_repository_root,
            compatibility_directory,
            command_runner,
            environment,
            fail_on_nonzero=False,
        )
        record = {
            "name": name,
            "command": list(command),
            "status": "passed" if result.returncode == 0 else "failed",
            "exit_status": result.returncode,
            "stdout_sha256": hashlib.sha256(
                result.stdout.encode("utf-8")
            ).hexdigest(),
            "stderr_sha256": hashlib.sha256(
                result.stderr.encode("utf-8")
            ).hexdigest(),
        }
        records.append(record)
        if result.returncode != 0:
            raise PreparationError(f"{name} compatibility test failed")
    return records


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
