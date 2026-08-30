#!/usr/bin/env python3
"""Orchestrate one closed Target 0 host qualification campaign."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
import datetime
from decimal import Decimal
import functools
import hashlib
import json
import os
from pathlib import Path
import pwd
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
    validate_capture,
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
    OPTIONAL_PERF_EVENTS,
    ProcessValidationError,
    REQUIRED_PERF_EVENTS,
    build_identity_record,
    build_raw_inventory,
    derive_process_seed,
    evaluate_preflight,
    finalize_campaign,
    parse_perf_stat,
    validate_campaign_manifest,
    validate_pmu_record,
    validate_process_record,
    validate_restoration_record,
    verify_finalized_campaign,
)


_CAMPAIGN_REJECTION_CODES = frozenset(
    {
        "bundle_verification_failure",
        "campaign_threshold_failure",
        "core_selection_failure",
        "evidence_inventory_failure",
        "exclusive_use_failure",
        "load_failure",
        "per_process_identity_drift",
        "preflight_identity_mismatch",
        "process_execution_failure",
        "process_schema_failure",
        "required_pmu_failure",
        "restoration_failure",
        "sample_bound_or_migration_failure",
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


class UserRecord(Protocol):
    """Expose the resolved numeric identity needed by the run boundary."""

    pw_uid: int


class CampaignPhaseError(CampaignError):
    """Expose one closed operator-visible campaign rejection code."""

    def __init__(
        self,
        code: str,
        *,
        command_status: int | None = None,
    ) -> None:
        """Retain only approved structured evidence without diagnostics."""
        self.code = code
        self.command_status = command_status
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
    run = subparsers.add_parser("run")
    run.add_argument("--repository-root", required=True, type=Path)
    run.add_argument("--campaign-directory", required=True, type=Path)
    run.add_argument("--target-user", required=True)
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


def _write_rejection(
    campaign_root: Path,
    reason_code: str,
    *,
    phase: str,
    command_status: int | None = None,
) -> None:
    """Publish one closed rejection after retaining all prior diagnostics."""
    if reason_code not in _CAMPAIGN_REJECTION_CODES:
        reason_code = "unexpected_internal_failure"
    if phase not in {"finalization", "preflight", "primary", "pmu"}:
        phase = "preflight"
    inventory = build_raw_inventory(campaign_root)
    rejection = {
        "command_exit_status": command_status,
        "diagnostics": inventory["files"],
        "manifest_version": "xoas.target0-campaign-rejection.v1",
        "performance_claim": False,
        "phase": phase,
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
        _write_rejection(
            campaign_root,
            error.code,
            phase="preflight",
            command_status=error.command_status,
        )
        raise
    except Exception as error:
        _write_rejection(
            campaign_root,
            "unexpected_internal_failure",
            phase="preflight",
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
        selection["interrupts_after"] = {
            str(cpu): total for cpu, total in sorted(after_interrupts.items())
        }
        selection["interrupts_before"] = {
            str(cpu): total for cpu, total in sorted(before_interrupts.items())
        }
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


def _load_regular_json_object(path: Path) -> dict[str, object]:
    """Load one retained regular JSON object without requiring canonical bytes."""
    try:
        content = _read_regular_bytes(path)
        record = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CampaignError("retained JSON record is unreadable") from error
    if not isinstance(record, dict):
        raise CampaignError("retained JSON record is not an object")
    return record


def _retained_bundle_identity(
    campaign_root: Path,
    preflight: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    """Authenticate retained bundle inputs against the preflight record."""
    expected_paths = {
        "bundle_acceptance": "inputs/bundle-acceptance.json",
        "bundle_inventory": "inputs/bundle-inventory.json",
        "bundle_manifest": "inputs/bundle.json",
        "executable": "inputs/xoas-target0-qualification-probe",
    }
    inputs = preflight.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != set(expected_paths):
        raise CampaignError("retained preflight input set differs")
    contents: dict[str, bytes] = {}
    for name, relative_path in expected_paths.items():
        record = inputs[name]
        if not isinstance(record, dict) or set(record) != {
            "path",
            "sha256",
            "size_bytes",
        }:
            raise CampaignError("retained preflight input shape differs")
        if record["path"] != relative_path:
            raise CampaignError("retained preflight input path differs")
        content = _read_regular_bytes(campaign_root / relative_path)
        if (
            record["size_bytes"] != len(content)
            or record["sha256"] != hashlib.sha256(content).hexdigest()
        ):
            raise CampaignError("retained preflight input bytes differ")
        contents[name] = content
    try:
        manifest = json.loads(contents["bundle_manifest"].decode("utf-8"))
        acceptance = json.loads(contents["bundle_acceptance"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CampaignError("retained bundle identity is unreadable") from error
    if not isinstance(manifest, dict) or not isinstance(acceptance, dict):
        raise CampaignError("retained bundle identity is not an object")
    if canonical_json_bytes(manifest) != contents["bundle_manifest"]:
        raise CampaignError("retained bundle manifest is not canonical")
    if canonical_json_bytes(acceptance) != contents["bundle_acceptance"]:
        raise CampaignError("retained bundle acceptance is not canonical")
    if acceptance.get("bundle_manifest_sha256") != hashlib.sha256(
        contents["bundle_manifest"]
    ).hexdigest():
        raise CampaignError("retained bundle manifest digest differs")
    if acceptance.get("inventory_sha256") != hashlib.sha256(
        contents["bundle_inventory"]
    ).hexdigest():
        raise CampaignError("retained bundle inventory digest differs")
    if acceptance.get("executable_sha256") != hashlib.sha256(
        contents["executable"]
    ).hexdigest():
        raise CampaignError("retained executable digest differs")
    return manifest, acceptance


def collect_retained_live_identity(
    *,
    campaign_root: Path,
    repository_root: Path,
    expected_commit: str,
    selected_cpu: int,
    sibling: int,
    boot_id_sha256: str,
    command_runner: CommandRunner,
) -> dict[str, object]:
    """Recompute live identity using only retained accepted campaign inputs."""
    try:
        preflight = _load_canonical_json_object(
            campaign_root / "preflight.json",
            canonicalizer=canonical_json_bytes,
        )
        manifest, acceptance = _retained_bundle_identity(
            campaign_root,
            preflight,
        )
        repository = validate_repository(
            repository_root,
            expected_commit,
            command_runner,
        )
        toolchain_lock = (
            repository_root
            / "toolchains/target0-amd-ryzen9-7900x-v1.lock.json"
        )
        provisioning_lock = validate_toolchain_lock(
            toolchain_lock,
            repository_root / "schemas/target0-toolchain-lock-v1.schema.json",
        )
        lock = _load_digest_bound_json_object(
            toolchain_lock,
            str(provisioning_lock["file_sha256"]),
        )
        compiler = validate_compiler(lock, command_runner)
        linker = validate_linker(lock, command_runner)
        identity = build_identity_record(
            bundle_manifest=manifest,
            bundle_acceptance=acceptance,
            repository=repository,
            provisioning_lock=provisioning_lock,
            compiler=compiler,
            linker=linker,
            sources=collect_source_records(repository_root),
            boot_id_sha256=boot_id_sha256,
            selected_cpu=selected_cpu,
            sibling=sibling,
        )
        if canonical_json_bytes(identity) != canonical_json_bytes(
            preflight.get("identity")
        ):
            raise CampaignError("live identity differs from accepted preflight")
        return identity
    except (CampaignError, PreparationError) as error:
        raise CampaignPhaseError("per_process_identity_drift") from error


def _host_identity_projection(capture: dict[str, object]) -> dict[str, object]:
    """Project one host capture to facts that must not change in a session."""
    validate_capture(capture)
    host = capture["host"]
    frequency = host["frequency"]
    frequency_cpus = [
        {
            key: value
            for key, value in record.items()
            if key != "current_khz"
        }
        for record in frequency["cpus"]
    ]
    stable_host_fields = (
        "cpu",
        "topology",
        "memory",
        "os",
        "virtualization",
        "clocksource",
        "boot_id_sha256",
        "powercap",
        "kernel_controls",
        "tools",
        "packages",
    )
    return {
        "frequency": {
            "boost": frequency["boost"],
            "cpus": frequency_cpus,
        },
        "host": {field: host[field] for field in stable_host_fields},
        "repository": capture["repository"],
    }


def validate_host_transition(
    before: dict[str, object],
    after: dict[str, object],
    *,
    expected_boot_id_sha256: str,
) -> None:
    """Require stable boot, topology, ABI, controls, tools, and repository."""
    if (
        before.get("phase") != "campaign"
        or after.get("phase") != "campaign"
        or before.get("host", {}).get("boot_id_sha256")
        != expected_boot_id_sha256
        or after.get("host", {}).get("boot_id_sha256")
        != expected_boot_id_sha256
    ):
        raise CampaignError("session boot identity differs")
    if canonical_json_bytes(_host_identity_projection(before)) != (
        canonical_json_bytes(_host_identity_projection(after))
    ):
        raise CampaignError("session host identity differs")


def _file_sha256(path: Path) -> str:
    """Return the SHA-256 of one retained regular evidence file."""
    return hashlib.sha256(_read_regular_bytes(path)).hexdigest()


def _run_measurement_session(
    *,
    session_directory: Path,
    session_runner: CommandRunner,
    command: tuple[str, ...],
    repository_root: Path,
) -> SimpleNamespace:
    """Open only the child publication boundary while its session runs."""
    descriptor = os.open(
        session_directory,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    try:
        status = os.fstat(descriptor)
        if not stat.S_ISDIR(status.st_mode):
            raise CampaignError("session output boundary is invalid")
        os.fchmod(descriptor, 0o1733)
        return session_runner(command, repository_root, timeout=35)
    finally:
        try:
            os.fchmod(descriptor, 0o700)
        finally:
            os.close(descriptor)


def _primary_session_command(
    *,
    repository_root: Path,
    campaign_root: Path,
    target_user: str,
    cpu: int,
    sibling: int,
    seed: int,
    process_path: Path,
    restoration_path: Path,
) -> tuple[str, ...]:
    """Construct one exact ordinary measurement-session command."""
    return (
        "/usr/bin/timeout",
        "--foreground",
        "--kill-after=5s",
        "--preserve-status",
        "--signal=TERM",
        "20s",
        "/usr/bin/bash",
        str(repository_root / "tools/target0/measurement_session.sh"),
        "--cpu",
        str(cpu),
        "--sibling",
        str(sibling),
        "--target-user",
        target_user,
        "--restoration-record",
        str(restoration_path),
        "--",
        str(campaign_root / "inputs/xoas-target0-qualification-probe"),
        "--cpu",
        str(cpu),
        "--warmup-rounds",
        "5",
        "--rounds",
        "30",
        "--iterations",
        "16777216",
        "--seed",
        str(seed),
        "--output",
        str(process_path),
    )


def execute_primary_processes(
    *,
    campaign_root: Path,
    repository_root: Path,
    target_user: str,
    source_root: Path,
    command_runner: CommandRunner,
    session_runner: CommandRunner,
    captured_at_utc: Callable[[], str],
) -> list[dict[str, object]]:
    """Run and validate five ordered primary measurement processes once."""
    if target_user == "root" or re.fullmatch(
        r"[a-z_][a-z0-9_-]*",
        target_user,
    ) is None:
        raise CampaignError("target user is invalid")
    resolved_campaign_root = campaign_root.resolve(strict=True)
    if campaign_root.is_symlink() or not resolved_campaign_root.is_dir():
        raise CampaignError("campaign root is invalid")
    if any(
        os.path.lexists(resolved_campaign_root / name)
        for name in ("acceptance.json", "campaign.json", "rejection.json")
    ):
        raise CampaignError("campaign root is already terminal")
    preflight = _load_canonical_json_object(
        resolved_campaign_root / "preflight.json",
        canonicalizer=canonical_json_bytes,
    )
    selection = _load_canonical_json_object(
        resolved_campaign_root / "core-selection.json",
        canonicalizer=canonical_json_bytes,
    )
    if preflight.get("status") != "accepted":
        raise CampaignError("campaign preflight is not accepted")
    try:
        campaign_id = preflight["campaign_id"]
        expected_commit = preflight["identity"]["repository"]["expected_commit"]
        expected_boot_id = preflight["identity"]["boot_id_sha256"]
        cpu = selection["cpu"]
        sibling = selection["sibling"]
    except (KeyError, TypeError) as error:
        raise CampaignError("accepted preflight is incomplete") from error
    if preflight["identity"]["selected_core"] != {
        "cpu": cpu,
        "sibling": sibling,
    }:
        raise CampaignError("preflight core identity differs")
    summaries: list[dict[str, object]] = []
    try:
        for process_index in range(1, 6):
            process_directory = (
                resolved_campaign_root / f"process-{process_index:02d}"
            )
            process_directory.mkdir(mode=0o700, parents=False, exist_ok=False)
            _fsync_directory(resolved_campaign_root)
            host_before = build_capture(
                phase="campaign",
                source_root=source_root,
                command_runner=command_runner,
                captured_at_utc=captured_at_utc(),
                repository_root=repository_root,
            )
            thermal_before = capture_thermal_state(source_root)
            if thermal_before["status"] != "passed":
                raise CampaignPhaseError("thermal_precondition_failure")
            identity = collect_retained_live_identity(
                campaign_root=resolved_campaign_root,
                repository_root=repository_root,
                expected_commit=expected_commit,
                selected_cpu=cpu,
                sibling=sibling,
                boot_id_sha256=host_before["host"]["boot_id_sha256"],
                command_runner=command_runner,
            )
            identity_path = process_directory / "identity-before.json"
            host_before_path = process_directory / "host-before.json"
            thermal_before_path = process_directory / "thermal-before.json"
            _publish_new_json(identity_path, identity)
            _publish_new_json(host_before_path, host_before)
            _publish_new_json(thermal_before_path, thermal_before)
            seed = derive_process_seed(campaign_id, process_index)
            process_path = process_directory / "process.json"
            restoration_path = process_directory / "restoration.json"
            command = _primary_session_command(
                repository_root=repository_root,
                campaign_root=resolved_campaign_root,
                target_user=target_user,
                cpu=cpu,
                sibling=sibling,
                seed=seed,
                process_path=process_path,
                restoration_path=restoration_path,
            )
            result = _run_measurement_session(
                session_directory=process_directory,
                session_runner=session_runner,
                command=command,
                repository_root=repository_root,
            )
            try:
                restoration = _load_regular_json_object(restoration_path)
                validate_restoration_record(
                    restoration,
                    expected_command_status=result.returncode,
                )
            except CampaignError as error:
                raise CampaignPhaseError(
                    "restoration_failure",
                    command_status=result.returncode,
                ) from error
            host_after = build_capture(
                phase="campaign",
                source_root=source_root,
                command_runner=command_runner,
                captured_at_utc=captured_at_utc(),
                repository_root=repository_root,
            )
            thermal_after = capture_thermal_state(source_root)
            host_after_path = process_directory / "host-after.json"
            thermal_after_path = process_directory / "thermal-after.json"
            _publish_new_json(host_after_path, host_after)
            _publish_new_json(thermal_after_path, thermal_after)
            if result.returncode != 0:
                raise CampaignPhaseError(
                    "process_execution_failure",
                    command_status=result.returncode,
                )
            if thermal_after["status"] != "passed":
                raise CampaignPhaseError(
                    "thermal_precondition_failure",
                    command_status=result.returncode,
                )
            try:
                validate_host_transition(
                    host_before,
                    host_after,
                    expected_boot_id_sha256=expected_boot_id,
                )
            except CampaignError as error:
                raise CampaignPhaseError(
                    "per_process_identity_drift",
                    command_status=result.returncode,
                ) from error
            process_record = _load_regular_json_object(process_path)
            try:
                process_summary = validate_process_record(
                    process_record,
                    repository_root
                    / "schemas/target0-host-qualification-v1.schema.json",
                    expected_cpu=cpu,
                    expected_seed=seed,
                )
            except ProcessValidationError as error:
                raise CampaignPhaseError(
                    error.code,
                    command_status=result.returncode,
                ) from error
            summaries.append(
                {
                    "accepted": True,
                    "evidence": {
                        "host_after_sha256": _file_sha256(host_after_path),
                        "host_before_sha256": _file_sha256(host_before_path),
                        "identity_sha256": _file_sha256(identity_path),
                        "process_sha256": _file_sha256(process_path),
                        "restoration_sha256": _file_sha256(restoration_path),
                    },
                    "process_index": process_index,
                    "restored": True,
                    "seed": seed,
                    "statistics": process_summary["statistics"],
                }
            )
        return summaries
    except CampaignPhaseError as error:
        _write_rejection(
            resolved_campaign_root,
            error.code,
            phase="primary",
            command_status=error.command_status,
        )
        raise
    except Exception as error:
        _write_rejection(
            resolved_campaign_root,
            "unexpected_internal_failure",
            phase="primary",
        )
        raise CampaignPhaseError("unexpected_internal_failure") from error


def _pmu_directory_name(event_specification: str, required: bool) -> str:
    """Return one fixed safe evidence directory for a PMU event request."""
    if required:
        return "required"
    return "optional-" + event_specification.strip("/").replace("/", "-")


def _pmu_session_command(
    *,
    repository_root: Path,
    campaign_root: Path,
    target_user: str,
    cpu: int,
    sibling: int,
    seed: int,
    event_specification: str,
    process_path: Path,
    restoration_path: Path,
    perf_output_path: Path,
) -> tuple[str, ...]:
    """Construct one exact privileged-perf measurement-session command."""
    return (
        "/usr/bin/timeout",
        "--foreground",
        "--kill-after=5s",
        "--preserve-status",
        "--signal=TERM",
        "20s",
        "/usr/bin/bash",
        str(repository_root / "tools/target0/measurement_session.sh"),
        "--cpu",
        str(cpu),
        "--sibling",
        str(sibling),
        "--target-user",
        target_user,
        "--restoration-record",
        str(restoration_path),
        "--execution-mode",
        "privileged-perf",
        "--perf-output",
        str(perf_output_path),
        "--perf-events",
        event_specification,
        "--",
        str(campaign_root / "inputs/xoas-target0-qualification-probe"),
        "--cpu",
        str(cpu),
        "--warmup-rounds",
        "5",
        "--rounds",
        "30",
        "--iterations",
        "16777216",
        "--seed",
        str(seed),
        "--output",
        str(process_path),
    )


def execute_pmu_sessions(
    *,
    campaign_root: Path,
    repository_root: Path,
    target_user: str,
    source_root: Path,
    command_runner: CommandRunner,
    session_runner: CommandRunner,
    captured_at_utc: Callable[[], str],
) -> dict[str, object]:
    """Run one required and eight separate optional PMU sessions in order."""
    resolved_campaign_root = campaign_root.resolve(strict=True)
    if any(
        not (resolved_campaign_root / f"process-{index:02d}").is_dir()
        for index in range(1, 6)
    ):
        raise CampaignError("primary process evidence is incomplete")
    if os.path.lexists(resolved_campaign_root / "rejection.json"):
        raise CampaignError("rejected campaign cannot run PMU sessions")
    preflight = _load_canonical_json_object(
        resolved_campaign_root / "preflight.json",
        canonicalizer=canonical_json_bytes,
    )
    selection = _load_canonical_json_object(
        resolved_campaign_root / "core-selection.json",
        canonicalizer=canonical_json_bytes,
    )
    try:
        campaign_id = preflight["campaign_id"]
        expected_commit = preflight["identity"]["repository"]["expected_commit"]
        expected_boot_id = preflight["identity"]["boot_id_sha256"]
        cpu = selection["cpu"]
        sibling = selection["sibling"]
    except (KeyError, TypeError) as error:
        raise CampaignError("accepted preflight is incomplete") from error
    pmu_root = resolved_campaign_root / "pmu"
    pmu_root.mkdir(mode=0o700, parents=False, exist_ok=False)
    _fsync_directory(resolved_campaign_root)
    requests = [
        ("cycles,instructions", tuple(REQUIRED_PERF_EVENTS), True),
        *((event, (event,), False) for event in OPTIONAL_PERF_EVENTS),
    ]
    required_summary: dict[str, object] | None = None
    optional_summaries: list[dict[str, object]] = []
    seed = derive_process_seed(campaign_id, 1)
    try:
        for event_specification, expected_events, required in requests:
            session_directory = pmu_root / _pmu_directory_name(
                event_specification,
                required,
            )
            session_directory.mkdir(mode=0o700, parents=False, exist_ok=False)
            _fsync_directory(pmu_root)
            host_before = build_capture(
                phase="campaign",
                source_root=source_root,
                command_runner=command_runner,
                captured_at_utc=captured_at_utc(),
                repository_root=repository_root,
            )
            thermal_before = capture_thermal_state(source_root)
            if thermal_before["status"] != "passed":
                raise CampaignPhaseError("thermal_precondition_failure")
            identity = collect_retained_live_identity(
                campaign_root=resolved_campaign_root,
                repository_root=repository_root,
                expected_commit=expected_commit,
                selected_cpu=cpu,
                sibling=sibling,
                boot_id_sha256=host_before["host"]["boot_id_sha256"],
                command_runner=command_runner,
            )
            identity_path = session_directory / "identity-before.json"
            host_before_path = session_directory / "host-before.json"
            thermal_before_path = session_directory / "thermal-before.json"
            _publish_new_json(identity_path, identity)
            _publish_new_json(host_before_path, host_before)
            _publish_new_json(thermal_before_path, thermal_before)
            process_path = session_directory / "process.json"
            restoration_path = session_directory / "restoration.json"
            perf_output_path = session_directory / "perf-stat.txt"
            command = _pmu_session_command(
                repository_root=repository_root,
                campaign_root=resolved_campaign_root,
                target_user=target_user,
                cpu=cpu,
                sibling=sibling,
                seed=seed,
                event_specification=event_specification,
                process_path=process_path,
                restoration_path=restoration_path,
                perf_output_path=perf_output_path,
            )
            result = _run_measurement_session(
                session_directory=session_directory,
                session_runner=session_runner,
                command=command,
                repository_root=repository_root,
            )
            try:
                restoration = _load_regular_json_object(restoration_path)
                validate_restoration_record(
                    restoration,
                    expected_command_status=result.returncode,
                )
            except CampaignError as error:
                raise CampaignPhaseError(
                    "restoration_failure",
                    command_status=result.returncode,
                ) from error
            host_after = build_capture(
                phase="campaign",
                source_root=source_root,
                command_runner=command_runner,
                captured_at_utc=captured_at_utc(),
                repository_root=repository_root,
            )
            thermal_after = capture_thermal_state(source_root)
            _publish_new_json(session_directory / "host-after.json", host_after)
            _publish_new_json(
                session_directory / "thermal-after.json",
                thermal_after,
            )
            if thermal_after["status"] != "passed":
                raise CampaignPhaseError(
                    "thermal_precondition_failure",
                    command_status=result.returncode,
                )
            try:
                validate_host_transition(
                    host_before,
                    host_after,
                    expected_boot_id_sha256=expected_boot_id,
                )
            except CampaignError as error:
                raise CampaignPhaseError(
                    "per_process_identity_drift",
                    command_status=result.returncode,
                ) from error
            process_record = _load_regular_json_object(process_path)
            try:
                validate_process_record(
                    process_record,
                    repository_root
                    / "schemas/target0-host-qualification-v1.schema.json",
                    expected_cpu=cpu,
                    expected_seed=seed,
                )
            except ProcessValidationError as error:
                raise CampaignPhaseError(
                    error.code,
                    command_status=result.returncode,
                ) from error
            try:
                raw_perf = _read_regular_bytes(perf_output_path).decode("utf-8")
                events = parse_perf_stat(raw_perf, expected_events)
                status = (
                    "unsupported"
                    if events[0]["status"] == "unsupported"
                    else "passed"
                )
                pmu_record = {
                    "command_exit_status": result.returncode,
                    "events": events,
                    "failure_reasons": [],
                    "manifest_version": "xoas.target0-pmu-session.v1",
                    "performance_claim": False,
                    "required": required,
                    "restored": True,
                    "status": status,
                }
                validate_pmu_record(pmu_record, required=required)
            except (CampaignError, UnicodeDecodeError) as error:
                code = (
                    "required_pmu_failure"
                    if required
                    else "evidence_inventory_failure"
                )
                raise CampaignPhaseError(
                    code,
                    command_status=result.returncode,
                ) from error
            pmu_record_path = session_directory / "pmu.json"
            _publish_new_json(pmu_record_path, pmu_record)
            if required:
                required_summary = {
                    "events": events,
                    "evidence_sha256": _file_sha256(pmu_record_path),
                    "restored": True,
                    "status": "passed",
                }
            else:
                optional_summaries.append(
                    {
                        "event": event_specification,
                        "evidence_sha256": _file_sha256(pmu_record_path),
                        "record": events[0],
                        "restored": True,
                        "status": events[0]["status"],
                    }
                )
        if required_summary is None or len(optional_summaries) != 8:
            raise CampaignPhaseError("evidence_inventory_failure")
        return {
            "optional": optional_summaries,
            "required": required_summary,
        }
    except CampaignPhaseError as error:
        _write_rejection(
            resolved_campaign_root,
            error.code,
            phase="pmu",
            command_status=error.command_status,
        )
        raise
    except Exception as error:
        _write_rejection(
            resolved_campaign_root,
            "unexpected_internal_failure",
            phase="pmu",
        )
        raise CampaignPhaseError("unexpected_internal_failure") from error


def build_campaign_manifest(
    *,
    campaign_root: Path,
    processes: list[dict[str, object]],
    pmu: dict[str, object],
    completed_at_utc: str,
) -> dict[str, object]:
    """Assemble one compact campaign manifest from validated raw summaries."""
    preflight = _load_canonical_json_object(
        campaign_root / "preflight.json",
        canonicalizer=canonical_json_bytes,
    )
    selection = _load_canonical_json_object(
        campaign_root / "core-selection.json",
        canonicalizer=canonical_json_bytes,
    )
    identity = preflight["identity"]
    eligibility = preflight["eligibility"]
    interactive_sessions = eligibility["interactive_sessions"]
    strict_mad_process_count = sum(
        Decimal(process["statistics"]["mad_ratio"]) <= Decimal("0.005")
        for process in processes
    )
    return {
        "acceptance": {
            "all_mad_at_most_0_010": all(
                Decimal(process["statistics"]["mad_ratio"])
                <= Decimal("0.010")
                for process in processes
            ),
            "all_p99_at_most_1_02": all(
                Decimal(process["statistics"]["p99_ratio"])
                <= Decimal("1.02")
                for process in processes
            ),
            "all_restored": all(
                process["restored"] is True for process in processes
            ),
            "process_count": len(processes),
            "required_pmu_accepted": pmu["required"]["status"] == "passed",
            "retained_sample_count": sum(
                process["statistics"]["sample_count"]
                for process in processes
            ),
            "status": "passed",
            "strict_mad_process_count": strict_mad_process_count,
        },
        "bundle": identity["bundle"],
        "campaign_id": preflight["campaign_id"],
        "campaign_number": preflight["campaign_number"],
        "completed_at_utc": completed_at_utc,
        "controlled_reboot_preceded_campaign": (
            preflight["campaign_number"] == 2
        ),
        "created_at_utc": preflight["captured_at_utc"],
        "evidence_inventory_sha256": "0" * 64,
        "external_retention": "external_private_evidence_root",
        "manifest_version": "xoas.target0-qualification-campaign.v1",
        "performance_claim": False,
        "pmu": pmu,
        "preflight": {
            "bare_metal": eligibility["bare_metal"],
            "clocksource": eligibility["clocksource"],
            "exclusive_use_confirmed": eligibility[
                "exclusive_use_confirmed"
            ],
            "interactive_sessions": {
                field: interactive_sessions[field]
                for field in ("expected", "root", "total", "unexpected")
            },
            "load_average_1m": eligibility["load_average_1m"],
            "required_pmu_available": eligibility["required_pmu_available"],
            "thermal": eligibility["thermal"],
        },
        "processes": processes,
        "provisioning_lock": identity["provisioning_lock"],
        "qualification_claim": False,
        "repository": identity["repository"],
        "selected_core": {
            field: selection[field]
            for field in (
                "cpu",
                "interrupt_delta",
                "preferred_core_ranking",
                "sibling",
                "window_seconds",
            )
        },
        "status": "passed",
        "target_id": preflight["target_id"],
    }


def validate_run_authority(
    *,
    target_user: str,
    effective_uid: int,
    user_lookup: Callable[[str], UserRecord],
) -> None:
    """Require a root operator and one existing non-root execution user."""
    if effective_uid != 0:
        raise CampaignError("campaign run requires effective UID zero")
    if target_user == "root" or re.fullmatch(
        r"[a-z_][a-z0-9_-]*",
        target_user,
    ) is None:
        raise CampaignError("target user is invalid")
    try:
        user = user_lookup(target_user)
    except KeyError as error:
        raise CampaignError("target user does not exist") from error
    if user.pw_uid == 0:
        raise CampaignError("target user resolves to root")


def run_campaign_command(
    command: tuple[str, ...],
    working_directory: Path | None = None,
    *,
    environment: dict[str, str] | None = None,
    timeout: int = 30,
    repository_root: Path,
    delegate: CommandRunner = run_command,
) -> SimpleNamespace:
    """Run Git safely against only the exact root-owned campaign checkout."""
    if command and command[0] in {"git", "/usr/bin/git"} and (
        working_directory is not None
    ):
        try:
            resolved_repository = repository_root.resolve(strict=True)
            resolved_working_directory = working_directory.resolve(strict=True)
        except OSError as error:
            raise CampaignError("campaign Git boundary is unavailable") from error
        if (
            repository_root.is_symlink()
            or resolved_working_directory != resolved_repository
        ):
            raise CampaignError("campaign Git boundary differs")
        command = (
            command[0],
            "-c",
            f"safe.directory={resolved_repository}",
            *command[1:],
        )
    return delegate(
        command,
        working_directory,
        environment=environment,
        timeout=timeout,
    )


def execute_run(
    options: argparse.Namespace,
    *,
    source_root: Path,
    command_runner: CommandRunner,
    session_runner: CommandRunner,
    captured_at_utc: Callable[[], str],
    effective_uid: int,
    user_lookup: Callable[[str], UserRecord],
) -> dict[str, object]:
    """Execute the controlled primary and PMU phases exactly once."""
    if options.command != "run":
        raise CampaignError("operator command is not run")
    validate_run_authority(
        target_user=options.target_user,
        effective_uid=effective_uid,
        user_lookup=user_lookup,
    )
    campaign_root = options.campaign_directory.resolve(strict=True)
    if options.campaign_directory.is_symlink() or not campaign_root.is_dir():
        raise CampaignError("campaign root is invalid")
    if any(
        os.path.lexists(campaign_root / name)
        for name in (
            "acceptance.json",
            "campaign.json",
            "pmu",
            "process-01",
            "process-02",
            "process-03",
            "process-04",
            "process-05",
            "rejection.json",
        )
    ):
        raise CampaignError("campaign root is not pristine after preflight")
    processes = execute_primary_processes(
        campaign_root=campaign_root,
        repository_root=options.repository_root,
        target_user=options.target_user,
        source_root=source_root,
        command_runner=command_runner,
        session_runner=session_runner,
        captured_at_utc=captured_at_utc,
    )
    pmu = execute_pmu_sessions(
        campaign_root=campaign_root,
        repository_root=options.repository_root,
        target_user=options.target_user,
        source_root=source_root,
        command_runner=command_runner,
        session_runner=session_runner,
        captured_at_utc=captured_at_utc,
    )
    campaign_manifest = build_campaign_manifest(
        campaign_root=campaign_root,
        processes=processes,
        pmu=pmu,
        completed_at_utc=captured_at_utc(),
    )
    campaign_schema = (
        options.repository_root
        / "schemas/target0-qualification-campaign-v1.schema.json"
    )
    try:
        validate_campaign_manifest(campaign_manifest, campaign_schema)
    except CampaignError as error:
        _write_rejection(
            campaign_root,
            "campaign_threshold_failure",
            phase="finalization",
        )
        raise CampaignPhaseError("campaign_threshold_failure") from error
    try:
        acceptance = finalize_campaign(
            campaign_root,
            campaign_manifest,
            campaign_schema,
        )
    except CampaignError as error:
        _write_rejection(
            campaign_root,
            "evidence_inventory_failure",
            phase="finalization",
        )
        raise CampaignPhaseError("evidence_inventory_failure") from error
    return {
        "acceptance": acceptance,
        "pmu": pmu,
        "processes": processes,
    }


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
        if options.command == "preflight":
            execute_preflight(
                options,
                source_root=Path("/"),
                allowed_root=Path("/var/tmp"),
                install_prefix=Path("/opt/xoas/target0-v1"),
                home_directory=Path.home(),
                command_runner=run_command,
                captured_at_utc=_utc_now(),
            )
        else:
            campaign_command_runner = functools.partial(
                run_campaign_command,
                repository_root=options.repository_root,
            )
            execute_run(
                options,
                source_root=Path("/"),
                command_runner=campaign_command_runner,
                session_runner=run_command,
                captured_at_utc=_utc_now,
                effective_uid=os.geteuid(),
                user_lookup=pwd.getpwnam,
            )
        return 0
    except CampaignPhaseError as error:
        print(
            f"qualification campaign {options.command} failed: {error.code}",
            file=sys.stderr,
        )
        return 2
    except (CampaignError, CaptureError, PreparationError, OSError):
        print(
            f"qualification campaign {options.command} failed",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
