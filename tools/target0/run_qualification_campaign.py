#!/usr/bin/env python3
"""Orchestrate one closed Target 0 host qualification campaign."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
from types import SimpleNamespace
from typing import Protocol

from capture_host import (
    CaptureError,
    build_capture,
    read_interrupt_totals,
    select_core,
)
from prepare_qualification_bundle import (
    PreparationError,
    canonical_json_bytes,
    collect_source_records,
    run_command,
    validate_compiler,
    validate_linker,
    validate_repository,
    validate_toolchain_lock,
    verify_finalized_bundle,
)
from qualification_campaign import (
    CampaignError,
    build_identity_record,
    build_raw_inventory,
)


_PREFLIGHT_REJECTION_CODES = frozenset(
    {
        "bundle_verification_failure",
        "core_selection_failure",
        "evidence_inventory_failure",
        "exclusive_use_failure",
        "load_failure",
        "preflight_identity_mismatch",
        "thermal_precondition_failure",
        "unexpected_internal_failure",
        "unexpected_session_failure",
    }
)


class CommandRunner(Protocol):
    """Run one fixed read-only command and return captured output."""

    def __call__(
        self,
        command: tuple[str, ...],
        working_directory: Path | None = None,
        *,
        environment: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> SimpleNamespace:
        """Return the command status and captured output."""


class CampaignPhaseError(CampaignError):
    """Expose one closed operator-visible campaign rejection code."""

    def __init__(self, code: str) -> None:
        """Retain only the approved code without arbitrary diagnostics."""
        self.code = code
        super().__init__(code)


def parse_arguments(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the closed Target 0 qualification campaign operator interface."""
    parser = argparse.ArgumentParser(
        description="Run one bounded XOAS Target 0 qualification campaign."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight = subparsers.add_parser("preflight")
    for option in (
        "repository-root",
        "bundle-directory",
        "bundle-schema",
        "campaign-schema",
        "process-schema",
        "toolchain-lock",
        "output-directory",
    ):
        preflight.add_argument(f"--{option}", required=True, type=Path)
    preflight.add_argument("--expected-commit", required=True)
    preflight.add_argument("--campaign-id", required=True)
    preflight.add_argument(
        "--campaign-number",
        required=True,
        type=int,
        choices=(1, 2),
    )
    preflight.add_argument("--target-user", required=True)
    preflight.add_argument(
        "--exclusive-use-confirmed",
        action="store_true",
        required=True,
    )
    return parser.parse_args(arguments)


def _schema_identity(path: Path, expected_id: str) -> dict[str, object]:
    """Meta-validate one exact schema and return its non-secret byte identity."""
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError

        content = _read_regular_bytes(path)
        schema = json.loads(content.decode("utf-8"))
        if not isinstance(schema, dict) or schema.get("$id") != expected_id:
            raise CampaignError("schema identity differs")
        Draft202012Validator.check_schema(schema)
    except CampaignError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, SchemaError) as error:
        raise CampaignError("schema validation failed") from error
    return {
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
    }


def _publish_new_json(path: Path, record: dict[str, object]) -> None:
    """Publish one canonical retained JSON record without replacement."""
    _publish_new_bytes(path, canonical_json_bytes(record), 0o600)


def _write_preflight_rejection(
    campaign_root: Path,
    reason_code: str,
) -> None:
    """Publish one closed rejection after retaining all prior diagnostics."""
    if reason_code not in _PREFLIGHT_REJECTION_CODES:
        reason_code = "unexpected_internal_failure"
    inventory = build_raw_inventory(campaign_root)
    rejection = {
        "command_exit_status": None,
        "diagnostics": inventory["files"],
        "manifest_version": "xoas.target0-campaign-rejection.v1",
        "performance_claim": False,
        "phase": "preflight",
        "reason_code": reason_code,
        "status": "rejected",
    }
    _publish_new_json(campaign_root / "rejection.json", rejection)


def _preflight_rejection_code(failure_reasons: list[str]) -> str:
    """Map the first deterministic eligibility failure to a closed code."""
    mapping = {
        "exclusive_use_unconfirmed": "exclusive_use_failure",
        "load_average_too_high": "load_failure",
        "interactive_sessions_ineligible": "unexpected_session_failure",
        "thermal_state_ineligible": "thermal_precondition_failure",
        "virtualization_detected": "preflight_identity_mismatch",
        "clocksource_ineligible": "preflight_identity_mismatch",
        "required_pmu_unavailable": "preflight_identity_mismatch",
        "repository_dirty": "preflight_identity_mismatch",
    }
    if not failure_reasons:
        raise CampaignError("preflight failure has no reason")
    return mapping.get(failure_reasons[0], "unexpected_internal_failure")


def execute_preflight(
    options: argparse.Namespace,
    *,
    source_root: Path,
    allowed_root: Path,
    install_prefix: Path,
    home_directory: Path,
    command_runner: CommandRunner,
    sleep: Callable[[float], None] = time.sleep,
    monotonic_ns: Callable[[], int] = time.monotonic_ns,
    captured_at_utc: str,
) -> dict[str, object]:
    """Execute one read-only preflight and retain its accepted evidence."""
    if options.command != "preflight":
        raise CampaignError("operator command is not preflight")
    if re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,95}", options.campaign_id) is None:
        raise CampaignError("campaign identity is invalid")
    campaign_schema_identity = _schema_identity(
        options.campaign_schema,
        "https://xoas.dev/schemas/target0-qualification-campaign-v1.schema.json",
    )
    process_schema_identity = _schema_identity(
        options.process_schema,
        "https://xoas.dev/schemas/target0-host-qualification-v1.schema.json",
    )
    try:
        validate_repository(
            options.repository_root,
            options.expected_commit,
            command_runner,
        )
    except PreparationError as error:
        raise CampaignPhaseError("preflight_identity_mismatch") from error
    try:
        verify_finalized_bundle(
            options.bundle_directory,
            options.bundle_schema,
        )
    except PreparationError as error:
        raise CampaignPhaseError("bundle_verification_failure") from error
    campaign_root = create_campaign_root(
        options.output_directory,
        allowed_root=allowed_root,
        repository_root=options.repository_root,
        bundle_root=options.bundle_directory,
        install_prefix=install_prefix,
        home_directory=home_directory,
    )
    try:
        inputs = retain_verified_bundle_inputs(
            campaign_root=campaign_root,
            bundle_directory=options.bundle_directory,
            bundle_schema=options.bundle_schema,
        )
        try:
            host_capture = build_capture(
                phase="campaign",
                source_root=source_root,
                command_runner=command_runner,
                captured_at_utc=captured_at_utc,
                repository_root=options.repository_root,
            )
        except CaptureError as error:
            raise CampaignPhaseError("preflight_identity_mismatch") from error
        try:
            thermal = capture_thermal_state(source_root)
        except CampaignError as error:
            raise CampaignPhaseError("thermal_precondition_failure") from error
        try:
            sessions = capture_interactive_sessions(
                command_runner,
                options.target_user,
            )
        except CampaignError as error:
            raise CampaignPhaseError("unexpected_session_failure") from error
        eligibility = evaluate_preflight(
            host_capture=host_capture,
            thermal=thermal,
            sessions=sessions,
            exclusive_use_confirmed=options.exclusive_use_confirmed,
        )
        if eligibility["status"] != "passed":
            raise CampaignPhaseError(
                _preflight_rejection_code(eligibility["failure_reasons"])
            )
        selection = observe_core_selection(
            host_capture,
            source_root=source_root,
            sleep=sleep,
            monotonic_ns=monotonic_ns,
        )
        identity = collect_live_identity(
            repository_root=options.repository_root,
            expected_commit=options.expected_commit,
            bundle_directory=options.bundle_directory,
            bundle_schema=options.bundle_schema,
            toolchain_lock=options.toolchain_lock,
            selected_cpu=selection["cpu"],
            sibling=selection["sibling"],
            boot_id_sha256=host_capture["host"]["boot_id_sha256"],
            command_runner=command_runner,
        )
        record = {
            "campaign_id": options.campaign_id,
            "campaign_number": options.campaign_number,
            "captured_at_utc": captured_at_utc,
            "eligibility": eligibility,
            "host_capture": host_capture,
            "identity": identity,
            "inputs": inputs,
            "interactive_sessions": sessions,
            "manifest_version": "xoas.target0-campaign-preflight-evidence.v1",
            "performance_claim": False,
            "schemas": {
                "campaign": campaign_schema_identity,
                "process": process_schema_identity,
            },
            "status": "accepted",
            "target_id": "target0-amd-ryzen9-7900x-v1",
            "thermal": thermal,
        }
        _publish_new_json(campaign_root / "core-selection.json", selection)
        _publish_new_json(campaign_root / "preflight.json", record)
        return record
    except CampaignPhaseError as error:
        _write_preflight_rejection(campaign_root, error.code)
        raise
    except Exception as error:
        _write_preflight_rejection(
            campaign_root,
            "unexpected_internal_failure",
        )
        raise CampaignPhaseError("unexpected_internal_failure") from error


def observe_core_selection(
    host_capture: dict[str, object],
    *,
    source_root: Path,
    sleep: Callable[[float], None] = time.sleep,
    monotonic_ns: Callable[[], int] = time.monotonic_ns,
) -> dict[str, object]:
    """Observe interrupts for 60 seconds and apply the locked core selector."""
    try:
        before_interrupts = read_interrupt_totals(source_root)
        started_at_ns = monotonic_ns()
        sleep(60)
        after_interrupts = read_interrupt_totals(source_root)
        observed_window_ns = monotonic_ns() - started_at_ns
        if observed_window_ns < 60_000_000_000:
            raise CaptureError("core observation window was shorter than 60 seconds")
        selection = select_core(
            host_capture,
            before_interrupts=before_interrupts,
            after_interrupts=after_interrupts,
            window_seconds=60,
        )
        selection["observed_window_ns"] = observed_window_ns
        return selection
    except (CaptureError, OSError) as error:
        raise CampaignPhaseError("core_selection_failure") from error


def _load_canonical_json_object(
    path: Path,
    *,
    canonicalizer: object,
) -> dict[str, object]:
    """Load one regular canonical JSON object after evidence verification."""
    try:
        if path.is_symlink() or not path.is_file():
            raise CampaignError("retained JSON input is unavailable")
        content = path.read_bytes()
        record = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CampaignError("retained JSON input is unreadable") from error
    if (
        not isinstance(record, dict)
        or not callable(canonicalizer)
        or canonicalizer(record) != content
    ):
        raise CampaignError("retained JSON input is not canonical")
    return record


def _load_digest_bound_json_object(
    path: Path,
    expected_sha256: str,
) -> dict[str, object]:
    """Load one regular JSON object whose exact bytes have a trusted digest."""
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        chunks: list[bytes] = []
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
            digest.update(chunk)
        record = json.loads(b"".join(chunks).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CampaignError("digest-bound JSON input is unreadable") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if digest.hexdigest() != expected_sha256 or not isinstance(record, dict):
        raise CampaignError("digest-bound JSON input differs")
    return record


def collect_live_identity(
    *,
    repository_root: Path,
    expected_commit: str,
    bundle_directory: Path,
    bundle_schema: Path,
    toolchain_lock: Path,
    selected_cpu: int,
    sibling: int,
    boot_id_sha256: str,
    command_runner: CommandRunner,
) -> dict[str, object]:
    """Recompute every identity required before one campaign process."""
    try:
        try:
            bundle_acceptance = verify_finalized_bundle(
                bundle_directory,
                bundle_schema,
            )
        except PreparationError as error:
            raise CampaignPhaseError("bundle_verification_failure") from error
        bundle_manifest = _load_canonical_json_object(
            bundle_directory / "bundle.json",
            canonicalizer=canonical_json_bytes,
        )
        if hashlib.sha256(canonical_json_bytes(bundle_manifest)).hexdigest() != (
            bundle_acceptance["bundle_manifest_sha256"]
        ):
            raise CampaignPhaseError("bundle_verification_failure")
        repository = validate_repository(
            repository_root,
            expected_commit,
            command_runner,
        )
        lock_schema = (
            repository_root / "schemas/target0-toolchain-lock-v1.schema.json"
        )
        provisioning_lock = validate_toolchain_lock(
            toolchain_lock,
            lock_schema,
        )
        lock = _load_digest_bound_json_object(
            toolchain_lock,
            str(provisioning_lock["file_sha256"]),
        )
        compiler = validate_compiler(lock, command_runner)
        linker = validate_linker(lock, command_runner)
        sources = collect_source_records(repository_root)
        return build_identity_record(
            bundle_manifest=bundle_manifest,
            bundle_acceptance=bundle_acceptance,
            repository=repository,
            provisioning_lock=provisioning_lock,
            compiler=compiler,
            linker=linker,
            sources=sources,
            boot_id_sha256=boot_id_sha256,
            selected_cpu=selected_cpu,
            sibling=sibling,
        )
    except CampaignPhaseError:
        raise
    except (CampaignError, PreparationError) as error:
        raise CampaignPhaseError("preflight_identity_mismatch") from error


def _read_regular_bytes(path: Path) -> bytes:
    """Read one regular file without following a symbolic link."""
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise CampaignError("retained input is not a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    except CampaignError:
        raise
    except OSError as error:
        raise CampaignError("retained input is unavailable") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _publish_new_bytes(path: Path, content: bytes, mode: int) -> None:
    """Publish one flushed write-once file through a private hard link."""
    temporary_path = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    descriptor: int | None = None
    temporary_owned = False
    try:
        if os.path.lexists(path) or os.path.lexists(temporary_path):
            raise CampaignError("campaign evidence path already exists")
        descriptor = os.open(
            temporary_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            mode,
        )
        temporary_owned = True
        with os.fdopen(descriptor, "wb", closefd=True) as output:
            descriptor = None
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary_path, path, follow_symlinks=False)
        temporary_path.unlink()
        temporary_owned = False
        _fsync_directory(path.parent)
    except CampaignError:
        raise
    except OSError as error:
        raise CampaignError("campaign evidence publication failed") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_owned and os.path.lexists(temporary_path):
            temporary_path.unlink()


def _fsync_directory(path: Path) -> None:
    """Flush one retained directory entry boundary without following a link."""
    descriptor = os.open(
        path,
        os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def retain_verified_bundle_inputs(
    *,
    campaign_root: Path,
    bundle_directory: Path,
    bundle_schema: Path,
) -> dict[str, dict[str, object]]:
    """Copy the verified bundle contract and executable into campaign inputs."""
    try:
        try:
            acceptance = verify_finalized_bundle(
                bundle_directory,
                bundle_schema,
            )
        except PreparationError as error:
            raise CampaignPhaseError("bundle_verification_failure") from error
        manifest = _load_canonical_json_object(
            bundle_directory / "bundle.json",
            canonicalizer=canonical_json_bytes,
        )
        try:
            resolved_campaign_root = campaign_root.resolve(strict=True)
            executable = manifest["build"]["accepted_executable"]
            executable_relative_path = executable["path"]
        except (KeyError, OSError, TypeError) as error:
            raise CampaignError("verified bundle input is incomplete") from error
        if campaign_root.is_symlink() or not resolved_campaign_root.is_dir():
            raise CampaignError("campaign root is invalid")
        if executable_relative_path != "bin/xoas-target0-qualification-probe":
            raise CampaignError("verified executable path differs")
        source_paths = {
            "bundle_manifest": bundle_directory / "bundle.json",
            "bundle_inventory": bundle_directory / "inventory.json",
            "bundle_acceptance": bundle_directory / "acceptance.json",
            "executable": bundle_directory / executable_relative_path,
        }
        destination_names = {
            "bundle_manifest": "bundle.json",
            "bundle_inventory": "bundle-inventory.json",
            "bundle_acceptance": "bundle-acceptance.json",
            "executable": "xoas-target0-qualification-probe",
        }
        content = {
            name: _read_regular_bytes(source_path)
            for name, source_path in source_paths.items()
        }
        if hashlib.sha256(content["bundle_manifest"]).hexdigest() != acceptance[
            "bundle_manifest_sha256"
        ]:
            raise CampaignError("retained bundle manifest digest differs")
        if hashlib.sha256(content["bundle_inventory"]).hexdigest() != acceptance[
            "inventory_sha256"
        ]:
            raise CampaignError("retained bundle inventory digest differs")
        if hashlib.sha256(content["executable"]).hexdigest() != acceptance[
            "executable_sha256"
        ]:
            raise CampaignError("retained executable digest differs")
        inputs_directory = resolved_campaign_root / "inputs"
        inputs_directory.mkdir(mode=0o700, parents=False, exist_ok=False)
        _fsync_directory(resolved_campaign_root)
        records: dict[str, dict[str, object]] = {}
        for name in (
            "bundle_acceptance",
            "bundle_inventory",
            "bundle_manifest",
            "executable",
        ):
            destination = inputs_directory / destination_names[name]
            _publish_new_bytes(
                destination,
                content[name],
                0o700 if name == "executable" else 0o600,
            )
            records[name] = {
                "path": destination.relative_to(resolved_campaign_root).as_posix(),
                "sha256": hashlib.sha256(content[name]).hexdigest(),
                "size_bytes": len(content[name]),
            }
        return records
    except CampaignPhaseError:
        raise
    except (CampaignError, OSError) as error:
        raise CampaignPhaseError("evidence_inventory_failure") from error


def _read_required_text(path: Path, description: str) -> str:
    """Read one required fixture or live sysfs text value."""
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise CampaignError(f"{description} is unavailable") from error
    if not value:
        raise CampaignError(f"{description} is empty")
    return value


def _read_optional_integer(path: Path, description: str) -> int | None:
    """Read one optional decimal sysfs value without treating absence as zero."""
    if not path.exists():
        return None
    value = _read_required_text(path, description)
    if re.fullmatch(r"-?[0-9]+", value) is None:
        raise CampaignError(f"{description} is malformed")
    return int(value)


def _sensor_index(path: Path) -> int:
    """Return the numeric index from one tempN_input sysfs filename."""
    match = re.fullmatch(r"temp([0-9]+)_input", path.name)
    if match is None:
        raise CampaignError("thermal sensor filename is malformed")
    return int(match.group(1))


def capture_thermal_state(source_root: Path) -> dict[str, object]:
    """Capture objective hwmon inputs, thresholds, alarms, and faults."""
    hwmon_root = source_root / "sys/class/hwmon"
    try:
        device_roots = sorted(
            hwmon_root.glob("hwmon*"),
            key=lambda path: int(path.name.removeprefix("hwmon")),
        )
    except (OSError, ValueError) as error:
        raise CampaignError("thermal device inventory is invalid") from error

    sensors: list[dict[str, object]] = []
    for device_root in device_roots:
        if re.fullmatch(r"hwmon[0-9]+", device_root.name) is None:
            raise CampaignError("thermal device identity is malformed")
        device_index = int(device_root.name.removeprefix("hwmon"))
        device_name = _read_required_text(
            device_root / "name",
            "thermal device name",
        )
        if re.fullmatch(r"[A-Za-z0-9_.-]+", device_name) is None:
            raise CampaignError("thermal device name is malformed")
        input_paths = sorted(
            device_root.glob("temp*_input"),
            key=_sensor_index,
        )
        for input_path in input_paths:
            sensor_index = _sensor_index(input_path)
            sensor = f"temp{sensor_index}"
            input_temperature = _read_optional_integer(
                input_path,
                "thermal input",
            )
            if input_temperature is None:
                raise CampaignError("thermal input disappeared")
            label_path = device_root / f"{sensor}_label"
            label = (
                _read_required_text(label_path, "thermal label")
                if label_path.exists()
                else "unavailable"
            )
            maximum = _read_optional_integer(
                device_root / f"{sensor}_max",
                "thermal maximum",
            )
            critical = _read_optional_integer(
                device_root / f"{sensor}_crit",
                "thermal critical threshold",
            )
            emergency = _read_optional_integer(
                device_root / f"{sensor}_emergency",
                "thermal emergency threshold",
            )
            critical_alarm = _read_optional_integer(
                device_root / f"{sensor}_crit_alarm",
                "thermal critical alarm",
            )
            emergency_alarm = _read_optional_integer(
                device_root / f"{sensor}_emergency_alarm",
                "thermal emergency alarm",
            )
            fault = _read_optional_integer(
                device_root / f"{sensor}_fault",
                "thermal sensor fault",
            )
            for state in (critical_alarm, emergency_alarm, fault):
                if state is not None and state not in {0, 1}:
                    raise CampaignError("thermal alarm or fault state is invalid")
            thresholds = [
                threshold
                for threshold in (critical, emergency)
                if threshold is not None
            ]
            if not thresholds:
                threshold_status = "threshold_unavailable"
            elif any(input_temperature >= threshold for threshold in thresholds):
                threshold_status = "threshold_violation"
            else:
                threshold_status = "below_threshold"
            sensors.append(
                {
                    "critical_millidegrees_c": critical,
                    "critical_alarm": critical_alarm,
                    "device_index": device_index,
                    "device_name": device_name,
                    "emergency_alarm": emergency_alarm,
                    "emergency_millidegrees_c": emergency,
                    "fault": fault,
                    "input_millidegrees_c": input_temperature,
                    "label": label,
                    "maximum_millidegrees_c": maximum,
                    "sensor": sensor,
                    "threshold_status": threshold_status,
                }
            )

    alarm_count = sum(
        int(sensor[field] == 1)
        for sensor in sensors
        for field in ("critical_alarm", "emergency_alarm")
    )
    fault_count = sum(int(sensor["fault"] == 1) for sensor in sensors)
    threshold_violation_count = sum(
        int(sensor["threshold_status"] == "threshold_violation")
        for sensor in sensors
    )
    threshold_unavailable_count = sum(
        int(sensor["threshold_status"] == "threshold_unavailable")
        for sensor in sensors
    )
    failure_reasons: list[str] = []
    if not sensors:
        failure_reasons.append("no_temperature_sensor")
    if alarm_count:
        failure_reasons.append("thermal_alarm")
    if fault_count:
        failure_reasons.append("thermal_sensor_fault")
    if threshold_violation_count:
        failure_reasons.append("thermal_threshold_violation")
    return {
        "failure_reasons": failure_reasons,
        "manifest_version": "xoas.target0-thermal-state.v1",
        "performance_claim": False,
        "sensors": sensors,
        "status": "passed" if not failure_reasons else "failed",
        "summary": {
            "alarm_count": alarm_count,
            "fault_count": fault_count,
            "sensor_count": len(sensors),
            "threshold_unavailable_count": threshold_unavailable_count,
            "threshold_violation_count": threshold_violation_count,
        },
    }


def capture_interactive_sessions(
    command_runner: CommandRunner,
    target_user: str,
) -> dict[str, object]:
    """Retain only aggregate eligibility for live interactive sessions."""
    if target_user == "root" or re.fullmatch(
        r"[a-z_][a-z0-9_-]*",
        target_user,
    ) is None:
        raise CampaignError("target user is invalid")
    result = command_runner(
        (
            "/usr/bin/loginctl",
            "list-sessions",
            "--no-legend",
            "--no-pager",
        )
    )
    if result.returncode != 0:
        raise CampaignError("interactive session inventory failed")
    total = 0
    expected = 0
    root = 0
    unexpected = 0
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) < 3 or re.fullmatch(r"[0-9]+", fields[1]) is None:
            raise CampaignError("interactive session record is malformed")
        user_id = int(fields[1])
        session_user = fields[2]
        total += 1
        if user_id == 0 or session_user == "root":
            root += 1
        elif session_user == target_user:
            expected += 1
        else:
            unexpected += 1
    status = (
        "passed"
        if expected >= 1 and root == 0 and unexpected == 0
        else "failed"
    )
    return {
        "expected": expected,
        "manifest_version": "xoas.target0-interactive-sessions.v1",
        "performance_claim": False,
        "root": root,
        "status": status,
        "total": total,
        "unexpected": unexpected,
    }


def evaluate_preflight(
    *,
    host_capture: dict[str, object],
    thermal: dict[str, object],
    sessions: dict[str, object],
    exclusive_use_confirmed: bool,
) -> dict[str, object]:
    """Evaluate every independent read-only campaign preflight predicate."""
    try:
        host = host_capture["host"]
        load_average = host["load"]["load_average"]
        load_average_1m = load_average[0]
        virtualization_kind = host["virtualization"]["kind"]
        clocksource = host["clocksource"]["current"]
        perf = host["perf"]
        repository_clean = (
            host_capture["repository"]["tree_state"] == "clean"
        )
        thermal_summary = thermal["summary"]
        session_summary = {
            field: sessions[field]
            for field in ("total", "expected", "root", "unexpected")
        }
    except (AttributeError, KeyError, IndexError, TypeError) as error:
        raise CampaignError("preflight input is incomplete") from error
    if (
        isinstance(load_average_1m, bool)
        or not isinstance(load_average_1m, (int, float))
        or load_average_1m < 0
    ):
        raise CampaignError("preflight load average is invalid")
    failure_reasons: list[str] = []
    if exclusive_use_confirmed is not True:
        failure_reasons.append("exclusive_use_unconfirmed")
    if load_average_1m >= 0.5:
        failure_reasons.append("load_average_too_high")
    if sessions.get("status") != "passed":
        failure_reasons.append("interactive_sessions_ineligible")
    if thermal.get("status") != "passed":
        failure_reasons.append("thermal_state_ineligible")
    bare_metal = virtualization_kind == "none"
    if not bare_metal:
        failure_reasons.append("virtualization_detected")
    if clocksource != "tsc":
        failure_reasons.append("clocksource_ineligible")
    required_pmu_available = (
        perf.get("cycles_available") is True
        and perf.get("instructions_available") is True
    )
    if not required_pmu_available:
        failure_reasons.append("required_pmu_unavailable")
    if not repository_clean:
        failure_reasons.append("repository_dirty")
    return {
        "bare_metal": bare_metal,
        "clocksource": clocksource,
        "exclusive_use_confirmed": exclusive_use_confirmed,
        "failure_reasons": failure_reasons,
        "interactive_sessions": session_summary,
        "load_average_1m": load_average_1m,
        "manifest_version": "xoas.target0-campaign-preflight.v1",
        "performance_claim": False,
        "repository_clean": repository_clean,
        "required_pmu_available": required_pmu_available,
        "status": "passed" if not failure_reasons else "failed",
        "thermal": dict(thermal_summary),
    }


def create_campaign_root(
    output_directory: Path,
    *,
    allowed_root: Path,
    repository_root: Path,
    bundle_root: Path,
    install_prefix: Path,
    home_directory: Path,
) -> Path:
    """Create one new private campaign root within the approved boundary."""
    if not output_directory.is_absolute():
        raise CampaignError("campaign output directory must be absolute")
    if re.fullmatch(
        r"xoas-target0-qualification-campaign\."
        r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?",
        output_directory.name,
    ) is None:
        raise CampaignError("campaign output name is outside the contract")
    try:
        resolved_allowed_root = allowed_root.resolve(strict=True)
        resolved_parent = output_directory.parent.resolve(strict=True)
        protected_paths = tuple(
            path.resolve(strict=True)
            for path in (
                repository_root,
                bundle_root,
                install_prefix,
                home_directory,
            )
        )
    except OSError as error:
        raise CampaignError("campaign output boundary cannot be resolved") from error
    if Path(os.path.abspath(output_directory)) != output_directory:
        raise CampaignError("campaign output path is not canonical")
    if resolved_parent != resolved_allowed_root:
        raise CampaignError("campaign output is outside the evidence root")
    resolved_output = resolved_parent / output_directory.name
    if os.path.lexists(output_directory):
        raise CampaignError("campaign output already exists")
    if any(
        resolved_output == protected
        or resolved_output in protected.parents
        or protected in resolved_output.parents
        for protected in protected_paths
    ):
        raise CampaignError("campaign output overlaps a protected path")
    try:
        output_directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    except OSError as error:
        raise CampaignError("campaign output cannot be created") from error
    if output_directory.is_symlink() or not output_directory.is_dir():
        raise CampaignError("campaign output has an unsafe file type")
    _fsync_directory(resolved_parent)
    return output_directory


def _utc_now() -> str:
    """Return one whole-second UTC timestamp for retained attempt evidence."""
    return (
        datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def main(arguments: Sequence[str] | None = None) -> int:
    """Run one closed operator command and return a stable public status."""
    options = parse_arguments(arguments)
    try:
        execute_preflight(
            options,
            source_root=Path("/"),
            allowed_root=Path("/var/tmp"),
            install_prefix=Path("/opt/xoas/target0-v1"),
            home_directory=Path.home(),
            command_runner=run_command,
            captured_at_utc=_utc_now(),
        )
        return 0
    except CampaignPhaseError as error:
        print(
            f"qualification campaign preflight failed: {error.code}",
            file=sys.stderr,
        )
        return 2
    except (CampaignError, CaptureError, PreparationError, OSError):
        print("qualification campaign preflight failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
