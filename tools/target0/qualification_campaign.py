#!/usr/bin/env python3
"""Define closed evidence contracts for Target 0 qualification campaigns."""

from __future__ import annotations

from collections.abc import Sequence
import copy
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import stat


REQUIRED_PERF_EVENTS = ("cycles", "instructions")
OPTIONAL_PERF_EVENTS = (
    "branches",
    "branch-misses",
    "cache-references",
    "cache-misses",
    "msr/aperf/",
    "msr/mperf/",
    "msr/tsc/",
    "power/energy-pkg/",
)


class CampaignError(RuntimeError):
    """Report a condition that makes a qualification campaign inadmissible."""


class ProcessValidationError(CampaignError):
    """Report one closed primary-process rejection category."""

    def __init__(self, code: str) -> None:
        """Retain one operator-visible process rejection code."""
        self.code = code
        super().__init__(code)


def _fraction_record(value: Fraction) -> dict[str, int]:
    """Return one exact reduced rational record."""
    return {
        "denominator": value.denominator,
        "numerator": value.numerator,
    }


def _ratio_decimal(value: Fraction) -> str:
    """Render one exact ratio once with the approved decimal policy."""
    with localcontext() as context:
        context.prec = 50
        decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
        rounded = decimal_value.quantize(
            Decimal("0.000000000001"),
            rounding=ROUND_HALF_EVEN,
        )
    return format(rounded, "f")


def derive_process_seed(campaign_id: str, process_index: int) -> int:
    """Derive one deterministic unsigned 64-bit campaign-process seed."""
    if re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,95}", campaign_id) is None:
        raise CampaignError("campaign identity is invalid")
    if (
        isinstance(process_index, bool)
        or not isinstance(process_index, int)
        or not 1 <= process_index <= 5
    ):
        raise CampaignError("campaign process index is invalid")
    material = (
        b"xoas.target0-qualification-seed.v1\0"
        + campaign_id.encode("utf-8")
        + b"\0"
        + str(process_index).encode("ascii")
    )
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big")


def process_statistics(
    elapsed_nanoseconds: Sequence[int],
) -> dict[str, object]:
    """Return exact median, MAD, and conservative nearest-rank p99 records."""
    if len(elapsed_nanoseconds) != 30:
        raise CampaignError("process statistics require exactly 30 samples")
    if any(
        isinstance(sample, bool)
        or not isinstance(sample, int)
        or sample <= 0
        for sample in elapsed_nanoseconds
    ):
        raise CampaignError("process statistics contain an invalid sample")
    ordered = sorted(elapsed_nanoseconds)
    sample_count = len(ordered)
    central_index = sample_count // 2
    median = Fraction(
        ordered[central_index - 1] + ordered[central_index],
        2,
    )
    deviations = sorted(abs(Fraction(sample) - median) for sample in ordered)
    mad = (deviations[central_index - 1] + deviations[central_index]) / 2
    nearest_rank_index = (99 * sample_count + 99) // 100 - 1
    p99 = ordered[nearest_rank_index]
    return {
        "mad_ns": _fraction_record(mad),
        "mad_ratio": _ratio_decimal(mad / median),
        "maximum_ns": ordered[-1],
        "median_ns": _fraction_record(median),
        "minimum_ns": ordered[0],
        "p99_ns": p99,
        "p99_ratio": _ratio_decimal(Fraction(p99) / median),
        "sample_count": sample_count,
    }


def validate_process_record(
    record: dict[str, object],
    schema_path: Path,
    *,
    expected_cpu: int,
    expected_seed: int,
) -> dict[str, object]:
    """Validate one primary process and return its exact statistics."""
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError, ValidationError

        if schema_path.is_symlink():
            raise ProcessValidationError("process_schema_failure")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if not isinstance(schema, dict) or schema.get("$id") != (
            "https://xoas.dev/schemas/target0-host-qualification-v1.schema.json"
        ):
            raise ProcessValidationError("process_schema_failure")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(record)
    except ProcessValidationError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProcessValidationError("process_schema_failure") from error
    except (SchemaError, ValidationError) as error:
        raise ProcessValidationError("process_schema_failure") from error
    if (
        isinstance(expected_cpu, bool)
        or not isinstance(expected_cpu, int)
        or expected_cpu < 0
        or isinstance(expected_seed, bool)
        or not isinstance(expected_seed, int)
        or not 0 <= expected_seed <= (1 << 64) - 1
    ):
        raise ProcessValidationError("process_schema_failure")
    if record["requested_cpu"] != expected_cpu or record["affinity_cpus"] != [
        expected_cpu
    ]:
        raise ProcessValidationError("sample_bound_or_migration_failure")
    if record["seed"] != expected_seed:
        raise ProcessValidationError("sample_bound_or_migration_failure")
    if (
        record["status"] != "passed"
        or record["failure_reasons"] != []
        or record["max_observed_threads"] != 1
    ):
        raise ProcessValidationError("sample_bound_or_migration_failure")
    samples = record["samples"]
    elapsed_nanoseconds: list[int] = []
    aggregate_checksum = 0
    for round_index, sample in enumerate(samples):
        if (
            sample["round"] != round_index
            or sample["observed_cpu_start"] != expected_cpu
            or sample["observed_cpu_end"] != expected_cpu
        ):
            raise ProcessValidationError("sample_bound_or_migration_failure")
        elapsed_ns = sample["elapsed_ns"]
        if not 20_000_000 <= elapsed_ns <= 200_000_000:
            raise ProcessValidationError("sample_bound_or_migration_failure")
        elapsed_nanoseconds.append(elapsed_ns)
        aggregate_checksum = (
            aggregate_checksum + int(sample["checksum"], 16)
        ) & ((1 << 64) - 1)
    if int(record["checksum"], 16) != aggregate_checksum:
        raise ProcessValidationError("sample_bound_or_migration_failure")
    return {
        "sample_count": len(elapsed_nanoseconds),
        "statistics": process_statistics(elapsed_nanoseconds),
    }


def parse_perf_stat(
    raw_text: str,
    expected_events: Sequence[str],
) -> list[dict[str, object]]:
    """Parse one closed semicolon-delimited Linux perf-stat record."""
    requested_events = tuple(expected_events)
    if requested_events != REQUIRED_PERF_EVENTS and not (
        len(requested_events) == 1
        and requested_events[0] in OPTIONAL_PERF_EVENTS
    ):
        raise CampaignError("perf-stat event request is outside the allowlist")
    records: list[dict[str, object]] = []
    for line in raw_text.splitlines():
        if not line:
            continue
        fields = [field.strip() for field in line.split(";")]
        if len(fields) < 5 or fields[2] not in requested_events:
            continue
        value_text, event, running_percentage = fields[0], fields[2], fields[4]
        if value_text == "<not supported>":
            value: int | str | None = None
            status = "unsupported"
            retained_running_percentage: str | None = None
        elif re.fullmatch(r"[0-9]+", value_text) is not None:
            value = int(value_text)
            status = "supported"
            retained_running_percentage = running_percentage
        elif re.fullmatch(r"[0-9]+\.[0-9]+", value_text) is not None:
            value = value_text
            status = "supported"
            retained_running_percentage = running_percentage
        else:
            raise CampaignError("perf-stat value is invalid")
        if status == "supported" and re.fullmatch(
            r"[0-9]+(?:\.[0-9]+)?",
            running_percentage,
        ) is None:
            raise CampaignError("perf-stat running percentage is invalid")
        records.append(
            {
                "event": event,
                "running_percentage": retained_running_percentage,
                "status": status,
                "value": value,
            }
        )
    if [record["event"] for record in records] != list(requested_events):
        raise CampaignError("perf-stat event set or order differs")
    return records


def _record_fraction(record: object, description: str) -> Fraction:
    """Load one reduced, nonnegative rational evidence value."""
    if not isinstance(record, dict) or set(record) != {
        "denominator",
        "numerator",
    }:
        raise CampaignError(f"{description} shape is invalid")
    numerator = record["numerator"]
    denominator = record["denominator"]
    if (
        isinstance(numerator, bool)
        or not isinstance(numerator, int)
        or numerator < 0
        or isinstance(denominator, bool)
        or not isinstance(denominator, int)
        or denominator <= 0
    ):
        raise CampaignError(f"{description} value is invalid")
    value = Fraction(numerator, denominator)
    if value.numerator != numerator or value.denominator != denominator:
        raise CampaignError(f"{description} is not reduced")
    return value


def _validate_retained_fields(value: object) -> None:
    """Reject access, credential, command, and private-path fields recursively."""
    prohibited_keys = {
        "address",
        "command",
        "command_line",
        "credential",
        "environment",
        "home",
        "home_directory",
        "hostname",
        "ip",
        "ip_address",
        "login",
        "operator",
        "private_key",
        "ssh",
        "user",
        "username",
    }
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str) or key.lower() in prohibited_keys:
                raise CampaignError("campaign contains a prohibited field")
            _validate_retained_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            _validate_retained_fields(nested)
    elif isinstance(value, str) and value.startswith(
        ("/home/", "/Users/", "/private/", "/tmp/", "/var/tmp/")
    ):
        raise CampaignError("campaign contains a private filesystem path")


def _require_exact_keys(
    record: object,
    expected_keys: set[str],
    description: str,
) -> dict[str, object]:
    """Require one record with exactly the approved field names."""
    if not isinstance(record, dict) or set(record) != expected_keys:
        raise CampaignError(f"{description} shape is invalid")
    return record


def _require_sha256(value: object, description: str) -> str:
    """Require one canonical lowercase SHA-256 identity."""
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise CampaignError(f"{description} digest is invalid")
    return value


def _require_git_object(value: object, description: str) -> str:
    """Require one canonical full SHA-1 Git object identity."""
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise CampaignError(f"{description} Git identity is invalid")
    return value


def _validate_package_record(record: object, description: str) -> None:
    """Validate one nonempty package name and exact-version record."""
    package = _require_exact_keys(record, {"name", "version"}, description)
    if any(
        not isinstance(package[field], str) or not package[field]
        for field in package
    ):
        raise CampaignError(f"{description} value is invalid")


def validate_identity_record(record: dict[str, object]) -> None:
    """Validate one closed, exact, non-secret campaign identity snapshot."""
    _require_exact_keys(
        record,
        {
            "boot_id_sha256",
            "bundle",
            "manifest_version",
            "performance_claim",
            "provisioning_lock",
            "repository",
            "selected_core",
            "sources",
            "status",
            "toolchain",
        },
        "identity record",
    )
    _validate_retained_fields(record)
    if (
        record["manifest_version"] != "xoas.target0-campaign-identity.v1"
        or record["performance_claim"] is not False
        or record["status"] != "accepted"
    ):
        raise CampaignError("identity record status is invalid")
    _require_sha256(record["boot_id_sha256"], "boot ID")

    bundle = _require_exact_keys(
        record["bundle"],
        {
            "bundle_id",
            "bundle_inventory_sha256",
            "bundle_manifest_sha256",
            "executable_identity_sha256",
            "executable_sha256",
        },
        "identity bundle",
    )
    if not isinstance(bundle["bundle_id"], str) or re.fullmatch(
        r"[A-Za-z0-9._-]{1,128}",
        bundle["bundle_id"],
    ) is None:
        raise CampaignError("identity bundle name is invalid")
    for field in set(bundle) - {"bundle_id"}:
        _require_sha256(bundle[field], f"identity bundle {field}")

    lock = _require_exact_keys(
        record["provisioning_lock"],
        {"configuration_sha256", "file_sha256", "lock_id"},
        "identity provisioning lock",
    )
    if not isinstance(lock["lock_id"], str) or re.fullmatch(
        r"[A-Za-z0-9._-]{1,128}",
        lock["lock_id"],
    ) is None:
        raise CampaignError("identity provisioning lock name is invalid")
    _require_sha256(lock["configuration_sha256"], "lock configuration")
    _require_sha256(lock["file_sha256"], "lock file")

    repository = _require_exact_keys(
        record["repository"],
        {"actual_commit", "expected_commit", "tree", "tree_state"},
        "identity repository",
    )
    actual_commit = _require_git_object(
        repository["actual_commit"],
        "actual commit",
    )
    expected_commit = _require_git_object(
        repository["expected_commit"],
        "expected commit",
    )
    _require_git_object(repository["tree"], "repository tree")
    if actual_commit != expected_commit or repository["tree_state"] != "clean":
        raise CampaignError("identity repository state differs")

    selected_core = _require_exact_keys(
        record["selected_core"],
        {"cpu", "sibling"},
        "identity selected core",
    )
    cpu = selected_core["cpu"]
    sibling = selected_core["sibling"]
    if (
        isinstance(cpu, bool)
        or not isinstance(cpu, int)
        or cpu < 0
        or isinstance(sibling, bool)
        or not isinstance(sibling, int)
        or sibling < 0
        or cpu == sibling
    ):
        raise CampaignError("identity selected core is invalid")

    sources = record["sources"]
    if not isinstance(sources, list) or not sources:
        raise CampaignError("identity source set is empty")
    source_paths: list[str] = []
    for source in sources:
        source_record = _require_exact_keys(
            source,
            {"path", "sha256"},
            "identity source",
        )
        relative_path = source_record["path"]
        if (
            not isinstance(relative_path, str)
            or not relative_path
            or relative_path.startswith("/")
            or ".." in Path(relative_path).parts
            or Path(relative_path).as_posix() != relative_path
        ):
            raise CampaignError("identity source path is invalid")
        _require_sha256(source_record["sha256"], "identity source")
        source_paths.append(relative_path)
    if source_paths != sorted(source_paths, key=lambda path: path.encode("utf-8")):
        raise CampaignError("identity source set is not bytewise sorted")
    if len(source_paths) != len(set(source_paths)):
        raise CampaignError("identity source set contains a duplicate")

    toolchain = _require_exact_keys(
        record["toolchain"],
        {"compiler", "linker"},
        "identity toolchain",
    )
    compiler = _require_exact_keys(
        toolchain["compiler"],
        {
            "driver_path",
            "package",
            "resolved_path",
            "sha256",
            "target_triple",
            "version",
        },
        "identity compiler",
    )
    linker = _require_exact_keys(
        toolchain["linker"],
        {"driver_path", "package", "resolved_path", "sha256", "version"},
        "identity linker",
    )
    if (
        compiler["driver_path"] != "/usr/bin/clang++-21"
        or compiler["resolved_path"] != "/usr/lib/llvm-21/bin/clang"
        or compiler["target_triple"] != "x86_64-pc-linux-gnu"
        or linker["driver_path"] != "/usr/bin/ld.lld-21"
        or linker["resolved_path"] != "/usr/lib/llvm-21/bin/lld"
    ):
        raise CampaignError("identity toolchain path or target differs")
    for tool, description in ((compiler, "compiler"), (linker, "linker")):
        if not isinstance(tool["version"], str) or not tool["version"]:
            raise CampaignError(f"identity {description} version is invalid")
        _require_sha256(tool["sha256"], f"identity {description}")
        _validate_package_record(tool["package"], f"identity {description} package")


def build_identity_record(
    *,
    bundle_manifest: dict[str, object],
    bundle_acceptance: dict[str, object],
    repository: dict[str, object],
    provisioning_lock: dict[str, object],
    compiler: dict[str, object],
    linker: dict[str, object],
    sources: list[dict[str, str]],
    boot_id_sha256: str,
    selected_cpu: int,
    sibling: int,
) -> dict[str, object]:
    """Bind independently recomputed live inputs to one accepted bundle."""
    acceptance = _require_exact_keys(
        bundle_acceptance,
        {
            "bundle_id",
            "bundle_manifest_sha256",
            "executable_identity_sha256",
            "executable_sha256",
            "inventory_sha256",
            "manifest_version",
            "performance_claim",
            "status",
        },
        "bundle acceptance",
    )
    if (
        acceptance["manifest_version"]
        != "xoas.target0-qualification-tool-acceptance.v1"
        or acceptance["performance_claim"] is not False
        or acceptance["status"] != "accepted"
    ):
        raise CampaignError("bundle acceptance status is invalid")
    required_manifest_keys = {
        "build",
        "bundle_id",
        "provisioning_lock",
        "repository",
        "sources",
        "toolchain",
    }
    if not required_manifest_keys.issubset(bundle_manifest):
        raise CampaignError("bundle manifest identity is incomplete")
    if acceptance["bundle_id"] != bundle_manifest["bundle_id"]:
        raise CampaignError("bundle identity differs")
    if (
        not isinstance(bundle_manifest["build"], dict)
        or bundle_manifest["build"].get("executable_sha256")
        != acceptance["executable_sha256"]
    ):
        raise CampaignError("bundle executable identity differs")
    if bundle_manifest["repository"] != repository:
        raise CampaignError("live repository identity differs from bundle")
    try:
        campaign_repository = {
            field: repository[field]
            for field in (
                "actual_commit",
                "expected_commit",
                "tree",
                "tree_state",
            )
        }
    except KeyError as error:
        raise CampaignError("live repository identity is incomplete") from error
    if bundle_manifest["provisioning_lock"] != provisioning_lock:
        raise CampaignError("live provisioning lock differs from bundle")
    try:
        campaign_lock = {
            field: provisioning_lock[field]
            for field in (
                "configuration_sha256",
                "file_sha256",
                "lock_id",
            )
        }
    except KeyError as error:
        raise CampaignError("live provisioning lock is incomplete") from error
    if bundle_manifest["sources"] != sources:
        raise CampaignError("live source set differs from bundle")
    if not isinstance(bundle_manifest["toolchain"], dict) or (
        bundle_manifest["toolchain"].get("compiler") != compiler
        or bundle_manifest["toolchain"].get("linker") != linker
    ):
        raise CampaignError("live toolchain differs from bundle")
    identity = {
        "boot_id_sha256": boot_id_sha256,
        "bundle": {
            "bundle_id": acceptance["bundle_id"],
            "bundle_inventory_sha256": acceptance["inventory_sha256"],
            "bundle_manifest_sha256": acceptance["bundle_manifest_sha256"],
            "executable_identity_sha256": acceptance[
                "executable_identity_sha256"
            ],
            "executable_sha256": acceptance["executable_sha256"],
        },
        "manifest_version": "xoas.target0-campaign-identity.v1",
        "performance_claim": False,
        "provisioning_lock": copy.deepcopy(campaign_lock),
        "repository": copy.deepcopy(campaign_repository),
        "selected_core": {"cpu": selected_cpu, "sibling": sibling},
        "sources": copy.deepcopy(sources),
        "status": "accepted",
        "toolchain": {
            "compiler": copy.deepcopy(compiler),
            "linker": copy.deepcopy(linker),
        },
    }
    validate_identity_record(identity)
    return identity


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


def _validate_perf_event_record(
    record: dict[str, object],
    expected_event: str,
    *,
    required: bool,
) -> None:
    """Validate one supported or explicitly unsupported PMU event."""
    if record.get("event") != expected_event:
        raise CampaignError("PMU event identity or order differs")
    status = record.get("status")
    value = record.get("value")
    running_percentage = record.get("running_percentage")
    if status == "supported":
        if value is None or running_percentage is None:
            raise CampaignError("supported PMU event has no value or scale")
        try:
            percentage = Decimal(str(running_percentage))
        except Exception as error:
            raise CampaignError("PMU running percentage is invalid") from error
        if percentage != Decimal("100"):
            raise CampaignError("PMU event has non-unit multiplex scaling")
    elif status == "unsupported" and not required:
        if value is not None or running_percentage is not None:
            raise CampaignError("unsupported PMU event contains an estimate")
    else:
        raise CampaignError("required PMU event is unsupported")


def validate_restoration_record(
    record: dict[str, object],
    *,
    expected_command_status: int,
) -> None:
    """Require one closed, exactly restored measurement-session record."""
    expected_keys = {
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
    }
    if set(record) != expected_keys:
        raise CampaignError("restoration record shape is invalid")
    _validate_retained_fields(record)
    if (
        record["manifest_version"]
        != "xoas.target0-measurement-session-restoration.v1"
        or record["performance_claim"] is not False
        or record["status"] != "restored"
        or record["restored"] is not True
        or record["boost_unchanged"] is not True
        or record["failure_reasons"] != []
    ):
        raise CampaignError("restoration record is not accepted")
    if (
        isinstance(expected_command_status, bool)
        or not isinstance(expected_command_status, int)
        or not 0 <= expected_command_status <= 255
        or record["command_exit_status"] != expected_command_status
    ):
        raise CampaignError("restoration command status differs")
    cpu = record["cpu"]
    sibling = record["sibling"]
    if (
        isinstance(cpu, bool)
        or not isinstance(cpu, int)
        or cpu < 0
        or isinstance(sibling, bool)
        or not isinstance(sibling, int)
        or sibling < 0
        or cpu == sibling
    ):
        raise CampaignError("restoration CPU pair is invalid")
    state_keys = {
        "boost",
        "energy_performance_preference",
        "governor",
        "selected_cpu_interrupts",
        "sibling_online",
    }
    pre_state = record["pre_state"]
    post_state = record["post_state"]
    if (
        not isinstance(pre_state, dict)
        or not isinstance(post_state, dict)
        or set(pre_state) != state_keys
        or set(post_state) != state_keys
    ):
        raise CampaignError("restoration state shape is invalid")
    for field in (
        "boost",
        "energy_performance_preference",
        "governor",
        "sibling_online",
    ):
        if post_state[field] != pre_state[field]:
            raise CampaignError("restoration control state differs")
    pre_interrupts = pre_state["selected_cpu_interrupts"]
    post_interrupts = post_state["selected_cpu_interrupts"]
    if (
        isinstance(pre_interrupts, bool)
        or not isinstance(pre_interrupts, int)
        or pre_interrupts < 0
        or isinstance(post_interrupts, bool)
        or not isinstance(post_interrupts, int)
        or post_interrupts < pre_interrupts
    ):
        raise CampaignError("restoration interrupt state differs")


def validate_pmu_record(
    record: dict[str, object],
    *,
    required: bool,
) -> None:
    """Validate one supported or explicitly unsupported PMU session record."""
    _require_exact_keys(
        record,
        {
            "command_exit_status",
            "events",
            "failure_reasons",
            "manifest_version",
            "performance_claim",
            "required",
            "restored",
            "status",
        },
        "PMU record",
    )
    _validate_retained_fields(record)
    if (
        record["manifest_version"] != "xoas.target0-pmu-session.v1"
        or record["performance_claim"] is not False
        or record["required"] is not required
        or record["restored"] is not True
        or record["failure_reasons"] != []
    ):
        raise CampaignError("PMU record status is invalid")
    command_exit_status = record["command_exit_status"]
    if (
        isinstance(command_exit_status, bool)
        or not isinstance(command_exit_status, int)
        or not 0 <= command_exit_status <= 255
    ):
        raise CampaignError("PMU command status is invalid")
    events = record["events"]
    if not isinstance(events, list):
        raise CampaignError("PMU event set is invalid")
    if required:
        if (
            record["status"] != "passed"
            or command_exit_status != 0
            or len(events) != len(REQUIRED_PERF_EVENTS)
        ):
            raise CampaignError("required PMU record is not accepted")
        for event_record, expected_event in zip(
            events,
            REQUIRED_PERF_EVENTS,
            strict=True,
        ):
            if not isinstance(event_record, dict):
                raise CampaignError("required PMU event is invalid")
            _validate_perf_event_record(
                event_record,
                expected_event,
                required=True,
            )
        return

    if len(events) != 1 or not isinstance(events[0], dict):
        raise CampaignError("optional PMU event set is invalid")
    event_record = events[0]
    expected_event = event_record.get("event")
    if expected_event not in OPTIONAL_PERF_EVENTS:
        raise CampaignError("optional PMU event is outside the allowlist")
    _validate_perf_event_record(
        event_record,
        str(expected_event),
        required=False,
    )
    if event_record["status"] == "supported":
        if record["status"] != "passed" or command_exit_status != 0:
            raise CampaignError("supported optional PMU record differs")
    elif record["status"] != "unsupported":
        raise CampaignError("unsupported optional PMU status differs")


def _regular_file_identity(path: Path) -> tuple[int, str]:
    """Return size and SHA-256 without following a replaced symbolic link."""
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise CampaignError("campaign evidence entry is not a regular file")
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        return metadata.st_size, digest.hexdigest()
    except CampaignError:
        raise
    except OSError as error:
        raise CampaignError("campaign evidence file is unavailable") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def build_raw_inventory(campaign_root: Path) -> dict[str, object]:
    """Hash every raw retained regular file in bytewise relative-path order."""
    try:
        resolved_root = campaign_root.resolve(strict=True)
    except OSError as error:
        raise CampaignError("campaign root is unavailable") from error
    if campaign_root.is_symlink() or not resolved_root.is_dir():
        raise CampaignError("campaign root is invalid")
    excluded_paths = {
        "acceptance.json",
        "campaign.json",
        "inventory.json",
        "rejection.json",
    }
    candidate_paths: list[tuple[bytes, str, Path]] = []
    for path in resolved_root.rglob("*"):
        relative_path = path.relative_to(resolved_root).as_posix()
        if path.is_symlink():
            raise CampaignError("campaign evidence contains a symbolic link")
        if path.is_dir():
            continue
        if relative_path in excluded_paths:
            continue
        candidate_paths.append(
            (relative_path.encode("utf-8"), relative_path, path)
        )
    candidate_paths.sort(key=lambda record: record[0])
    files: list[dict[str, object]] = []
    for _, relative_path, path in candidate_paths:
        size_bytes, digest = _regular_file_identity(path)
        files.append(
            {
                "path": relative_path,
                "sha256": digest,
                "size_bytes": size_bytes,
            }
        )
    return {
        "file_count": len(files),
        "files": files,
        "manifest_version": "xoas.target0-campaign-raw-inventory.v1",
        "performance_claim": False,
    }


def validate_campaign_manifest(
    record: dict[str, object],
    schema_path: Path,
) -> None:
    """Validate schema closure and every cross-field campaign decision."""
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError, ValidationError

        if schema_path.is_symlink():
            raise CampaignError("campaign schema is a symlink")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(record)
    except CampaignError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CampaignError("campaign schema is unreadable") from error
    except (SchemaError, ValidationError) as error:
        raise CampaignError("campaign schema validation failed") from error

    _validate_retained_fields(record)
    repository = record["repository"]
    if repository["actual_commit"] != repository["expected_commit"]:
        raise CampaignError("campaign repository commit differs")
    if record["completed_at_utc"] < record["created_at_utc"]:
        raise CampaignError("campaign completion precedes creation")
    campaign_number = record["campaign_number"]
    if bool(record["controlled_reboot_preceded_campaign"]) != (
        campaign_number == 2
    ):
        raise CampaignError("campaign reboot boundary differs")
    sessions = record["preflight"]["interactive_sessions"]
    if sessions["expected"] < 1 or sessions["total"] != (
        sessions["expected"] + sessions["root"] + sessions["unexpected"]
    ):
        raise CampaignError("campaign interactive session totals differ")

    processes = record["processes"]
    expected_indexes = list(range(1, 6))
    if [process["process_index"] for process in processes] != expected_indexes:
        raise CampaignError("campaign process order differs")

    strict_mad_process_count = 0
    for process in processes:
        process_index = process["process_index"]
        if process["seed"] != derive_process_seed(
            record["campaign_id"],
            process_index,
        ):
            raise CampaignError("campaign process seed differs")
        statistics = process["statistics"]
        median = _record_fraction(statistics["median_ns"], "median")
        mad = _record_fraction(statistics["mad_ns"], "MAD")
        if median <= 0:
            raise CampaignError("campaign median is not positive")
        mad_ratio = mad / median
        p99_ratio = Fraction(statistics["p99_ns"]) / median
        if statistics["mad_ratio"] != _ratio_decimal(mad_ratio):
            raise CampaignError("campaign MAD ratio differs")
        if statistics["p99_ratio"] != _ratio_decimal(p99_ratio):
            raise CampaignError("campaign p99 ratio differs")
        minimum = Fraction(statistics["minimum_ns"])
        maximum = Fraction(statistics["maximum_ns"])
        p99 = Fraction(statistics["p99_ns"])
        if not minimum <= median <= p99 <= maximum:
            raise CampaignError("campaign process order statistics differ")
        if mad_ratio > Fraction(1, 100):
            raise CampaignError("campaign MAD ratio exceeds 0.010")
        if mad_ratio <= Fraction(1, 200):
            strict_mad_process_count += 1
        if p99_ratio > Fraction(51, 50):
            raise CampaignError("campaign p99 ratio exceeds 1.02")

    acceptance = record["acceptance"]
    if acceptance["strict_mad_process_count"] != strict_mad_process_count:
        raise CampaignError("campaign strict MAD process count differs")
    if strict_mad_process_count < 4:
        raise CampaignError("campaign has fewer than four strict MAD processes")

    required_events = record["pmu"]["required"]["events"]
    if len(required_events) != len(REQUIRED_PERF_EVENTS):
        raise CampaignError("required PMU event count differs")
    for event_record, expected_event in zip(
        required_events,
        REQUIRED_PERF_EVENTS,
        strict=True,
    ):
        _validate_perf_event_record(
            event_record,
            expected_event,
            required=True,
        )

    optional_records = record["pmu"]["optional"]
    if [item["event"] for item in optional_records] != list(
        OPTIONAL_PERF_EVENTS
    ):
        raise CampaignError("optional PMU event order differs")
    for item, expected_event in zip(
        optional_records,
        OPTIONAL_PERF_EVENTS,
        strict=True,
    ):
        if item["status"] != item["record"]["status"]:
            raise CampaignError("optional PMU summary status differs")
        _validate_perf_event_record(
            item["record"],
            expected_event,
            required=False,
        )


def _canonical_campaign_json(record: object) -> bytes:
    """Serialize one campaign record to its stable retained bytes."""
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


def _read_campaign_bytes(path: Path) -> bytes:
    """Read one regular retained file without following a symbolic link."""
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise CampaignError("campaign evidence is not a regular file")
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
        raise CampaignError("campaign evidence is unavailable") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _load_campaign_json(
    path: Path,
    *,
    canonical: bool,
) -> dict[str, object]:
    """Load one retained JSON object with optional canonical-byte checking."""
    try:
        content = _read_campaign_bytes(path)
        record = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CampaignError("campaign JSON evidence is unreadable") from error
    if not isinstance(record, dict):
        raise CampaignError("campaign JSON evidence is not an object")
    if canonical and _canonical_campaign_json(record) != content:
        raise CampaignError("campaign JSON evidence is not canonical")
    return record


def _publish_campaign_json(path: Path, record: dict[str, object]) -> bytes:
    """Publish one flushed canonical campaign record without replacement."""
    content = _canonical_campaign_json(record)
    temporary_path = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    descriptor: int | None = None
    temporary_owned = False
    try:
        if os.path.lexists(path) or os.path.lexists(temporary_path):
            raise CampaignError("campaign terminal evidence already exists")
        descriptor = os.open(
            temporary_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
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
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return content
    except CampaignError:
        raise
    except OSError as error:
        raise CampaignError("campaign terminal publication failed") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_owned and os.path.lexists(temporary_path):
            temporary_path.unlink()


def _sha256_file(path: Path) -> str:
    """Return the exact SHA-256 of one retained regular file."""
    return hashlib.sha256(_read_campaign_bytes(path)).hexdigest()


def _validate_thermal_record(record: dict[str, object]) -> None:
    """Recompute the accepted aggregate thermal decision from its sensors."""
    thermal = _require_exact_keys(
        record,
        {
            "failure_reasons",
            "manifest_version",
            "performance_claim",
            "sensors",
            "status",
            "summary",
        },
        "thermal record",
    )
    if not isinstance(thermal["sensors"], list):
        raise CampaignError("thermal sensor set is invalid")
    sensors = thermal["sensors"]
    expected_sensor_keys = {
        "critical_alarm",
        "critical_millidegrees_c",
        "device_index",
        "device_name",
        "emergency_alarm",
        "emergency_millidegrees_c",
        "fault",
        "input_millidegrees_c",
        "label",
        "maximum_millidegrees_c",
        "sensor",
        "threshold_status",
    }
    sensor_identities: list[tuple[int, int]] = []
    for sensor in sensors:
        if not isinstance(sensor, dict) or set(sensor) != expected_sensor_keys:
            raise CampaignError("thermal sensor record is invalid")
        device_index = sensor["device_index"]
        sensor_name = sensor["sensor"]
        if (
            isinstance(device_index, bool)
            or not isinstance(device_index, int)
            or device_index < 0
            or not isinstance(sensor["device_name"], str)
            or re.fullmatch(r"[A-Za-z0-9_.-]+", sensor["device_name"])
            is None
            or not isinstance(sensor_name, str)
            or re.fullmatch(r"temp([0-9]+)", sensor_name) is None
            or not isinstance(sensor["label"], str)
            or not sensor["label"]
        ):
            raise CampaignError("thermal sensor identity is invalid")
        sensor_index = int(sensor_name.removeprefix("temp"))
        if sensor_name != f"temp{sensor_index}":
            raise CampaignError("thermal sensor identity is not canonical")
        sensor_identities.append((device_index, sensor_index))
        for field in (
            "critical_millidegrees_c",
            "emergency_millidegrees_c",
            "maximum_millidegrees_c",
        ):
            value = sensor[field]
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int)
            ):
                raise CampaignError("thermal threshold is invalid")
        input_temperature = sensor["input_millidegrees_c"]
        if isinstance(input_temperature, bool) or not isinstance(
            input_temperature,
            int,
        ):
            raise CampaignError("thermal input is invalid")
        for field in ("critical_alarm", "emergency_alarm", "fault"):
            state = sensor[field]
            if state is not None and (
                isinstance(state, bool)
                or not isinstance(state, int)
                or state not in {0, 1}
            ):
                raise CampaignError("thermal alarm or fault is invalid")
        thresholds = [
            value
            for value in (
                sensor["critical_millidegrees_c"],
                sensor["emergency_millidegrees_c"],
            )
            if value is not None
        ]
        if not thresholds:
            expected_status = "threshold_unavailable"
        elif any(input_temperature >= threshold for threshold in thresholds):
            expected_status = "threshold_violation"
        else:
            expected_status = "below_threshold"
        if sensor["threshold_status"] != expected_status:
            raise CampaignError("thermal threshold decision differs")
    if sensor_identities != sorted(sensor_identities) or len(
        set(sensor_identities)
    ) != len(sensor_identities):
        raise CampaignError("thermal sensor order differs")
    alarm_count = sum(
        int(sensor.get(field) == 1)
        for sensor in sensors
        for field in ("critical_alarm", "emergency_alarm")
    )
    fault_count = sum(int(sensor.get("fault") == 1) for sensor in sensors)
    violation_count = sum(
        int(sensor.get("threshold_status") == "threshold_violation")
        for sensor in sensors
    )
    unavailable_count = sum(
        int(sensor.get("threshold_status") == "threshold_unavailable")
        for sensor in sensors
    )
    expected_summary = {
        "alarm_count": alarm_count,
        "fault_count": fault_count,
        "sensor_count": len(sensors),
        "threshold_unavailable_count": unavailable_count,
        "threshold_violation_count": violation_count,
    }
    failure_reasons: list[str] = []
    if not sensors:
        failure_reasons.append("no_temperature_sensor")
    if alarm_count:
        failure_reasons.append("thermal_alarm")
    if fault_count:
        failure_reasons.append("thermal_sensor_fault")
    if violation_count:
        failure_reasons.append("thermal_threshold_violation")
    expected_status = "passed" if not failure_reasons else "failed"
    if (
        thermal["manifest_version"] != "xoas.target0-thermal-state.v1"
        or thermal["performance_claim"] is not False
        or thermal["status"] != expected_status
        or thermal["failure_reasons"] != failure_reasons
        or thermal["summary"] != expected_summary
    ):
        raise CampaignError("thermal summary differs from sensor evidence")
    if expected_status != "passed":
        raise CampaignError("thermal evidence contains an objective failure")


def _validate_interactive_sessions(record: object) -> None:
    """Recompute one retained aggregate interactive-session decision."""
    sessions = _require_exact_keys(
        record,
        {
            "expected",
            "manifest_version",
            "performance_claim",
            "root",
            "status",
            "total",
            "unexpected",
        },
        "interactive sessions",
    )
    for field in ("expected", "root", "total", "unexpected"):
        value = sessions[field]
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            raise CampaignError("interactive session count is invalid")
    expected_status = (
        "passed"
        if sessions["expected"] >= 1
        and sessions["root"] == 0
        and sessions["unexpected"] == 0
        else "failed"
    )
    if (
        sessions["manifest_version"]
        != "xoas.target0-interactive-sessions.v1"
        or sessions["performance_claim"] is not False
        or sessions["total"]
        != sessions["expected"] + sessions["root"] + sessions["unexpected"]
        or sessions["status"] != expected_status
    ):
        raise CampaignError("interactive session decision differs")


def _stable_host_projection(capture: dict[str, object]) -> dict[str, object]:
    """Project one capture to the stable facts required across a session."""
    host = capture["host"]
    frequency = host["frequency"]
    return {
        "frequency": {
            "boost": frequency["boost"],
            "cpus": [
                {
                    key: value
                    for key, value in record.items()
                    if key != "current_khz"
                }
                for record in frequency["cpus"]
            ],
        },
        "host": {
            field: host[field]
            for field in (
                "boot_id_sha256",
                "clocksource",
                "cpu",
                "kernel_controls",
                "memory",
                "os",
                "packages",
                "powercap",
                "tools",
                "topology",
                "virtualization",
            )
        },
        "repository": capture["repository"],
    }


def _require_file_digest(path: Path, expected_digest: object) -> None:
    """Require one retained regular file to match its manifest digest."""
    if not isinstance(expected_digest, str) or _sha256_file(path) != expected_digest:
        raise CampaignError("campaign evidence digest differs")


def _validate_session_evidence(
    session_directory: Path,
    *,
    expected_identity: dict[str, object],
    expected_boot_id: str,
    expected_cpu: int,
    expected_sibling: int,
) -> tuple[dict[str, object], dict[str, object]]:
    """Validate common identity, host, and thermal session evidence."""
    from capture_host import CaptureError, validate_capture

    identity = _load_campaign_json(
        session_directory / "identity-before.json",
        canonical=True,
    )
    validate_identity_record(identity)
    if identity != expected_identity:
        raise CampaignError("session identity differs from preflight")
    host_before = _load_campaign_json(
        session_directory / "host-before.json",
        canonical=True,
    )
    host_after = _load_campaign_json(
        session_directory / "host-after.json",
        canonical=True,
    )
    try:
        validate_capture(host_before)
        validate_capture(host_after)
    except CaptureError as error:
        raise CampaignError("session host capture is invalid") from error
    if (
        host_before.get("phase") != "campaign"
        or host_after.get("phase") != "campaign"
        or host_before["host"].get("boot_id_sha256") != expected_boot_id
        or host_after["host"].get("boot_id_sha256") != expected_boot_id
        or _stable_host_projection(host_before)
        != _stable_host_projection(host_after)
    ):
        raise CampaignError("session host identity differs")
    for capture in (host_before, host_after):
        if (
            capture["repository"].get("commit")
            != expected_identity["repository"]["actual_commit"]
            or capture["repository"].get("tree_state") != "clean"
        ):
            raise CampaignError("session host repository identity differs")
    for name in ("thermal-before.json", "thermal-after.json"):
        _validate_thermal_record(
            _load_campaign_json(session_directory / name, canonical=True)
        )
    if identity["selected_core"] != {
        "cpu": expected_cpu,
        "sibling": expected_sibling,
    }:
        raise CampaignError("session selected core differs")
    return host_before, host_after


def _validate_retained_bundle(
    campaign_root: Path,
    preflight: dict[str, object],
    bundle_schema: Path,
) -> None:
    """Revalidate the retained bundle subset and its accepted digest binding."""
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError, ValidationError
    from prepare_qualification_bundle import normalized_executable_identity

    expected_paths = {
        "bundle_acceptance": "inputs/bundle-acceptance.json",
        "bundle_inventory": "inputs/bundle-inventory.json",
        "bundle_manifest": "inputs/bundle.json",
        "executable": "inputs/xoas-target0-qualification-probe",
    }
    inputs = preflight.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != set(expected_paths):
        raise CampaignError("retained bundle input set differs")
    for name, relative_path in expected_paths.items():
        record = inputs[name]
        if (
            not isinstance(record, dict)
            or set(record) != {"path", "sha256", "size_bytes"}
            or record.get("path") != relative_path
        ):
            raise CampaignError("retained bundle input path differs")
        content = _read_campaign_bytes(campaign_root / relative_path)
        if (
            record.get("size_bytes") != len(content)
            or record.get("sha256") != hashlib.sha256(content).hexdigest()
        ):
            raise CampaignError("retained bundle input digest differs")
    manifest = _load_campaign_json(
        campaign_root / expected_paths["bundle_manifest"],
        canonical=True,
    )
    inventory_bytes = _read_campaign_bytes(
        campaign_root / expected_paths["bundle_inventory"]
    )
    _load_campaign_json(
        campaign_root / expected_paths["bundle_inventory"],
        canonical=True,
    )
    acceptance = _load_campaign_json(
        campaign_root / expected_paths["bundle_acceptance"],
        canonical=True,
    )
    try:
        schema = json.loads(_read_campaign_bytes(bundle_schema).decode("utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(manifest)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        SchemaError,
        ValidationError,
    ) as error:
        raise CampaignError("retained bundle schema validation failed") from error
    expected_acceptance_keys = {
        "bundle_id",
        "bundle_manifest_sha256",
        "executable_identity_sha256",
        "executable_sha256",
        "inventory_sha256",
        "manifest_version",
        "performance_claim",
        "status",
    }
    if (
        set(acceptance) != expected_acceptance_keys
        or acceptance.get("manifest_version")
        != "xoas.target0-qualification-tool-acceptance.v1"
        or acceptance.get("performance_claim") is not False
        or acceptance.get("status") != "accepted"
        or acceptance.get("bundle_id") != manifest.get("bundle_id")
        or acceptance.get("bundle_manifest_sha256")
        != _sha256_file(campaign_root / expected_paths["bundle_manifest"])
        or acceptance.get("inventory_sha256")
        != hashlib.sha256(inventory_bytes).hexdigest()
        or acceptance.get("executable_sha256")
        != _sha256_file(campaign_root / expected_paths["executable"])
        or acceptance.get("executable_sha256")
        != manifest.get("build", {}).get("executable_sha256")
        or acceptance.get("executable_identity_sha256")
        != normalized_executable_identity(manifest)
    ):
        raise CampaignError("retained bundle acceptance differs")
    identity = preflight.get("identity")
    if not isinstance(identity, dict):
        raise CampaignError("retained bundle campaign identity is invalid")
    repository = manifest.get("repository")
    provisioning_lock = manifest.get("provisioning_lock")
    if not isinstance(repository, dict) or not isinstance(
        provisioning_lock,
        dict,
    ):
        raise CampaignError("retained bundle semantic identity is invalid")
    expected_repository = {
        field: repository[field]
        for field in (
            "actual_commit",
            "expected_commit",
            "tree",
            "tree_state",
        )
    }
    expected_lock = {
        field: provisioning_lock[field]
        for field in (
            "configuration_sha256",
            "file_sha256",
            "lock_id",
        )
    }
    expected_bundle = {
        "bundle_id": acceptance["bundle_id"],
        "bundle_inventory_sha256": acceptance["inventory_sha256"],
        "bundle_manifest_sha256": acceptance["bundle_manifest_sha256"],
        "executable_identity_sha256": acceptance[
            "executable_identity_sha256"
        ],
        "executable_sha256": acceptance["executable_sha256"],
    }
    if (
        identity.get("bundle") != expected_bundle
        or identity.get("repository") != expected_repository
        or identity.get("provisioning_lock") != expected_lock
        or identity.get("sources") != manifest.get("sources")
        or identity.get("toolchain") != manifest.get("toolchain")
    ):
        raise CampaignError("retained bundle and campaign identities differ")


def _validate_raw_campaign(
    campaign_root: Path,
    campaign_manifest: dict[str, object],
    *,
    campaign_schema: Path,
    process_schema: Path,
    bundle_schema: Path,
) -> None:
    """Recompute every raw campaign decision before trusting final records."""
    from capture_host import CaptureError, select_core, validate_capture

    primary_files = (
        "host-after.json",
        "host-before.json",
        "identity-before.json",
        "process.json",
        "restoration.json",
        "thermal-after.json",
        "thermal-before.json",
    )
    pmu_files = (*primary_files, "perf-stat.txt", "pmu.json")
    pmu_directories = (
        "required",
        *(
            f"optional-{event.strip('/').replace('/', '-')}"
            for event in OPTIONAL_PERF_EVENTS
        ),
    )
    expected_raw_paths = {
        "core-selection.json",
        "inputs/bundle-acceptance.json",
        "inputs/bundle-inventory.json",
        "inputs/bundle.json",
        "inputs/xoas-target0-qualification-probe",
        "preflight.json",
        *(
            f"process-{index:02d}/{name}"
            for index in range(1, 6)
            for name in primary_files
        ),
        *(
            f"pmu/{directory}/{name}"
            for directory in pmu_directories
            for name in pmu_files
        ),
    }
    raw_inventory = build_raw_inventory(campaign_root)
    observed_raw_paths = {record["path"] for record in raw_inventory["files"]}
    if observed_raw_paths != expected_raw_paths:
        raise CampaignError("campaign raw evidence path set differs")
    validate_campaign_manifest(campaign_manifest, campaign_schema)
    preflight = _load_campaign_json(
        campaign_root / "preflight.json",
        canonical=True,
    )
    selection = _load_campaign_json(
        campaign_root / "core-selection.json",
        canonical=True,
    )
    expected_preflight_keys = {
        "campaign_id",
        "campaign_number",
        "captured_at_utc",
        "eligibility",
        "host_capture",
        "identity",
        "inputs",
        "interactive_sessions",
        "manifest_version",
        "performance_claim",
        "schemas",
        "status",
        "target_id",
        "thermal",
    }
    if set(preflight) != expected_preflight_keys:
        raise CampaignError("campaign preflight shape differs")
    _validate_retained_fields(preflight)
    if (
        preflight["manifest_version"]
        != "xoas.target0-campaign-preflight-evidence.v1"
        or preflight["performance_claim"] is not False
        or preflight["status"] != "accepted"
        or preflight["campaign_id"] != campaign_manifest["campaign_id"]
        or preflight["campaign_number"] != campaign_manifest["campaign_number"]
        or preflight["target_id"] != campaign_manifest["target_id"]
    ):
        raise CampaignError("campaign preflight identity differs")
    try:
        validate_capture(preflight["host_capture"])
    except (CaptureError, KeyError, TypeError) as error:
        raise CampaignError("campaign preflight host capture is invalid") from error
    thermal = preflight["thermal"]
    if not isinstance(thermal, dict):
        raise CampaignError("campaign preflight thermal evidence is invalid")
    _validate_thermal_record(thermal)
    sessions = preflight["interactive_sessions"]
    _validate_interactive_sessions(sessions)
    eligibility = preflight["eligibility"]
    if not isinstance(eligibility, dict) or eligibility != evaluate_preflight(
        host_capture=preflight["host_capture"],
        thermal=thermal,
        sessions=sessions,
        exclusive_use_confirmed=True,
    ):
        raise CampaignError("campaign preflight decision does not replay")
    identity = preflight.get("identity")
    if not isinstance(identity, dict):
        raise CampaignError("campaign preflight identity is invalid")
    validate_identity_record(identity)
    preflight_capture = preflight["host_capture"]
    if (
        preflight_capture["host"].get("boot_id_sha256")
        != identity["boot_id_sha256"]
        or preflight_capture["repository"].get("commit")
        != identity["repository"]["actual_commit"]
        or preflight_capture["repository"].get("tree_state") != "clean"
    ):
        raise CampaignError("campaign preflight capture identity differs")
    schema_records = preflight.get("schemas")
    if not isinstance(schema_records, dict) or set(schema_records) != {
        "campaign",
        "process",
    }:
        raise CampaignError("campaign preflight schema identity differs")
    for name, path in (
        ("campaign", campaign_schema),
        ("process", process_schema),
    ):
        content = _read_campaign_bytes(path)
        if schema_records[name] != {
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
        }:
            raise CampaignError("campaign schema bytes differ from preflight")
    _validate_retained_bundle(campaign_root, preflight, bundle_schema)
    expected_selection_keys = {
        "cpu",
        "interrupt_delta",
        "interrupts_after",
        "interrupts_before",
        "manifest_version",
        "observed_window_ns",
        "performance_claim",
        "preferred_core_ranking",
        "sibling",
        "window_seconds",
    }
    if set(selection) != expected_selection_keys:
        raise CampaignError("campaign core selection shape differs")
    observed_window_ns = selection["observed_window_ns"]
    if (
        isinstance(observed_window_ns, bool)
        or not isinstance(observed_window_ns, int)
        or observed_window_ns < 60_000_000_000
    ):
        raise CampaignError("campaign core observation window differs")

    interrupt_maps: dict[str, dict[int, int]] = {}
    topology_cpus = {
        record["cpu"]
        for record in preflight["host_capture"]["host"]["topology"]["cpus"]
    }
    for name in ("interrupts_before", "interrupts_after"):
        raw_interrupts = selection[name]
        if not isinstance(raw_interrupts, dict):
            raise CampaignError("campaign core interrupt evidence is invalid")
        interrupts: dict[int, int] = {}
        for cpu_text, total in raw_interrupts.items():
            if (
                not isinstance(cpu_text, str)
                or re.fullmatch(r"0|[1-9][0-9]*", cpu_text) is None
                or isinstance(total, bool)
                or not isinstance(total, int)
                or total < 0
            ):
                raise CampaignError("campaign core interrupt evidence is invalid")
            interrupts[int(cpu_text)] = total
        if set(interrupts) != topology_cpus:
            raise CampaignError("campaign core interrupt CPU set differs")
        interrupt_maps[name] = interrupts
    try:
        recomputed_selection = select_core(
            preflight["host_capture"],
            before_interrupts=interrupt_maps["interrupts_before"],
            after_interrupts=interrupt_maps["interrupts_after"],
            window_seconds=60,
        )
    except CaptureError as error:
        raise CampaignError("campaign core selection is invalid") from error
    if any(
        selection[key] != value
        for key, value in recomputed_selection.items()
    ):
        raise CampaignError("campaign core selection does not replay")

    selected_core = {
        key: selection[key]
        for key in (
            "cpu",
            "interrupt_delta",
            "preferred_core_ranking",
            "sibling",
            "window_seconds",
        )
    }
    if (
        selection.get("manifest_version") != "xoas.target0-core-selection.v1"
        or selection.get("performance_claim") is not False
        or selected_core != campaign_manifest["selected_core"]
        or identity["selected_core"]
        != {"cpu": selection["cpu"], "sibling": selection["sibling"]}
    ):
        raise CampaignError("campaign core selection differs")
    if (
        identity["repository"] != campaign_manifest["repository"]
        or identity["bundle"] != campaign_manifest["bundle"]
        or identity["provisioning_lock"] != campaign_manifest["provisioning_lock"]
        or preflight.get("captured_at_utc") != campaign_manifest["created_at_utc"]
    ):
        raise CampaignError("campaign manifest identity differs from preflight")
    expected_preflight_summary = {
        "bare_metal": eligibility.get("bare_metal"),
        "clocksource": eligibility.get("clocksource"),
        "exclusive_use_confirmed": eligibility.get("exclusive_use_confirmed"),
        "interactive_sessions": {
            key: eligibility.get("interactive_sessions", {}).get(key)
            for key in ("expected", "root", "total", "unexpected")
        },
        "load_average_1m": eligibility.get("load_average_1m"),
        "required_pmu_available": eligibility.get("required_pmu_available"),
        "thermal": eligibility.get("thermal"),
    }
    if expected_preflight_summary != campaign_manifest["preflight"]:
        raise CampaignError("campaign preflight summary differs")
    expected_boot_id = str(identity["boot_id_sha256"])
    expected_cpu = int(selection["cpu"])
    expected_sibling = int(selection["sibling"])

    recomputed_processes: list[dict[str, object]] = []
    for process_index in range(1, 6):
        directory = campaign_root / f"process-{process_index:02d}"
        _validate_session_evidence(
            directory,
            expected_identity=identity,
            expected_boot_id=expected_boot_id,
            expected_cpu=expected_cpu,
            expected_sibling=expected_sibling,
        )
        process_path = directory / "process.json"
        restoration_path = directory / "restoration.json"
        process = _load_campaign_json(process_path, canonical=False)
        seed = derive_process_seed(campaign_manifest["campaign_id"], process_index)
        summary = validate_process_record(
            process,
            process_schema,
            expected_cpu=expected_cpu,
            expected_seed=seed,
        )
        restoration = _load_campaign_json(restoration_path, canonical=False)
        validate_restoration_record(restoration, expected_command_status=0)
        if (
            restoration["cpu"] != expected_cpu
            or restoration["sibling"] != expected_sibling
        ):
            raise CampaignError("primary restoration core differs")
        manifest_process = campaign_manifest["processes"][process_index - 1]
        evidence = manifest_process["evidence"]
        for name, field in (
            ("host-after.json", "host_after_sha256"),
            ("host-before.json", "host_before_sha256"),
            ("identity-before.json", "identity_sha256"),
            ("process.json", "process_sha256"),
            ("restoration.json", "restoration_sha256"),
        ):
            _require_file_digest(directory / name, evidence[field])
        recomputed_processes.append(
            {
                "accepted": True,
                "evidence": evidence,
                "process_index": process_index,
                "restored": True,
                "seed": seed,
                "statistics": summary["statistics"],
            }
        )
    if recomputed_processes != campaign_manifest["processes"]:
        raise CampaignError("campaign process summaries differ from raw evidence")

    pmu_manifest = campaign_manifest["pmu"]
    pmu_requests = [
        ("required", tuple(REQUIRED_PERF_EVENTS), True),
        *(
            (f"optional-{event.strip('/').replace('/', '-')}", (event,), False)
            for event in OPTIONAL_PERF_EVENTS
        ),
    ]
    recomputed_required: dict[str, object] | None = None
    recomputed_optional: list[dict[str, object]] = []
    pmu_seed = derive_process_seed(campaign_manifest["campaign_id"], 1)
    for directory_name, expected_events, required in pmu_requests:
        directory = campaign_root / "pmu" / directory_name
        _validate_session_evidence(
            directory,
            expected_identity=identity,
            expected_boot_id=expected_boot_id,
            expected_cpu=expected_cpu,
            expected_sibling=expected_sibling,
        )
        process = _load_campaign_json(directory / "process.json", canonical=False)
        validate_process_record(
            process,
            process_schema,
            expected_cpu=expected_cpu,
            expected_seed=pmu_seed,
        )
        pmu_record = _load_campaign_json(directory / "pmu.json", canonical=True)
        validate_pmu_record(pmu_record, required=required)
        restoration = _load_campaign_json(
            directory / "restoration.json",
            canonical=False,
        )
        validate_restoration_record(
            restoration,
            expected_command_status=pmu_record["command_exit_status"],
        )
        if (
            restoration["cpu"] != expected_cpu
            or restoration["sibling"] != expected_sibling
        ):
            raise CampaignError("PMU restoration core differs")
        raw_events = parse_perf_stat(
            _read_campaign_bytes(directory / "perf-stat.txt").decode("utf-8"),
            expected_events,
        )
        if raw_events != pmu_record["events"]:
            raise CampaignError("PMU raw and structured events differ")
        pmu_digest = _sha256_file(directory / "pmu.json")
        if required:
            recomputed_required = {
                "events": raw_events,
                "evidence_sha256": pmu_digest,
                "restored": True,
                "status": "passed",
            }
        else:
            recomputed_optional.append(
                {
                    "event": expected_events[0],
                    "evidence_sha256": pmu_digest,
                    "record": raw_events[0],
                    "restored": True,
                    "status": raw_events[0]["status"],
                }
            )
    if {
        "optional": recomputed_optional,
        "required": recomputed_required,
    } != pmu_manifest:
        raise CampaignError("campaign PMU summary differs from raw evidence")


def _validate_campaign_acceptance(
    acceptance: dict[str, object],
    campaign: dict[str, object],
    *,
    campaign_sha256: str,
    inventory_sha256: str,
    boot_id_sha256: str,
) -> None:
    """Validate the compact terminal acceptance binding exactly."""
    expected_keys = {
        "boot_id_sha256",
        "campaign_id",
        "campaign_sha256",
        "expected_commit",
        "inventory_sha256",
        "manifest_version",
        "performance_claim",
        "process_count",
        "qualification_claim",
        "selected_cpu",
        "status",
    }
    if set(acceptance) != expected_keys:
        raise CampaignError("campaign acceptance shape differs")
    if acceptance != {
        "boot_id_sha256": boot_id_sha256,
        "campaign_id": campaign["campaign_id"],
        "campaign_sha256": campaign_sha256,
        "expected_commit": campaign["repository"]["expected_commit"],
        "inventory_sha256": inventory_sha256,
        "manifest_version": "xoas.target0-campaign-acceptance.v1",
        "performance_claim": False,
        "process_count": 5,
        "qualification_claim": False,
        "selected_cpu": campaign["selected_core"]["cpu"],
        "status": "accepted",
    }:
        raise CampaignError("campaign acceptance binding differs")


def finalize_campaign(
    campaign_root: Path,
    campaign_manifest: dict[str, object],
    campaign_schema: Path,
) -> dict[str, object]:
    """Publish inventory, campaign, and acceptance records without replacement."""
    resolved_root = campaign_root.resolve(strict=True)
    if campaign_root.is_symlink() or not resolved_root.is_dir():
        raise CampaignError("campaign root is invalid")
    if any(
        os.path.lexists(resolved_root / name)
        for name in (
            "acceptance.json",
            "campaign.json",
            "inventory.json",
            "rejection.json",
        )
    ):
        raise CampaignError("campaign root is already terminal")
    inventory = build_raw_inventory(resolved_root)
    inventory_bytes = _canonical_campaign_json(inventory)
    manifest = copy.deepcopy(campaign_manifest)
    manifest["evidence_inventory_sha256"] = hashlib.sha256(
        inventory_bytes
    ).hexdigest()
    _validate_raw_campaign(
        resolved_root,
        manifest,
        campaign_schema=campaign_schema,
        process_schema=campaign_schema.with_name(
            "target0-host-qualification-v1.schema.json"
        ),
        bundle_schema=campaign_schema.with_name(
            "target0-qualification-tool-bundle-v1.schema.json"
        ),
    )
    preflight = _load_campaign_json(
        resolved_root / "preflight.json",
        canonical=True,
    )
    campaign_bytes = _canonical_campaign_json(manifest)
    acceptance = {
        "boot_id_sha256": preflight["identity"]["boot_id_sha256"],
        "campaign_id": manifest["campaign_id"],
        "campaign_sha256": hashlib.sha256(campaign_bytes).hexdigest(),
        "expected_commit": manifest["repository"]["expected_commit"],
        "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "manifest_version": "xoas.target0-campaign-acceptance.v1",
        "performance_claim": False,
        "process_count": 5,
        "qualification_claim": False,
        "selected_cpu": manifest["selected_core"]["cpu"],
        "status": "accepted",
    }
    _validate_campaign_acceptance(
        acceptance,
        manifest,
        campaign_sha256=hashlib.sha256(campaign_bytes).hexdigest(),
        inventory_sha256=hashlib.sha256(inventory_bytes).hexdigest(),
        boot_id_sha256=preflight["identity"]["boot_id_sha256"],
    )
    _publish_campaign_json(resolved_root / "inventory.json", inventory)
    _publish_campaign_json(resolved_root / "campaign.json", manifest)
    _publish_campaign_json(resolved_root / "acceptance.json", acceptance)
    return acceptance


def _verify_finalized_campaign(
    campaign_root: Path,
    *,
    campaign_schema: Path,
    process_schema: Path,
    bundle_schema: Path,
) -> dict[str, object]:
    """Implement replay after the public boundary normalizes diagnostics."""
    resolved_root = campaign_root.resolve(strict=True)
    if campaign_root.is_symlink() or not resolved_root.is_dir():
        raise CampaignError("campaign root is invalid")
    if os.path.lexists(resolved_root / "rejection.json"):
        raise CampaignError("rejected campaign cannot be accepted")
    inventory_path = resolved_root / "inventory.json"
    campaign_path = resolved_root / "campaign.json"
    acceptance_path = resolved_root / "acceptance.json"
    inventory = _load_campaign_json(inventory_path, canonical=True)
    campaign = _load_campaign_json(campaign_path, canonical=True)
    acceptance = _load_campaign_json(acceptance_path, canonical=True)
    recomputed_inventory = build_raw_inventory(resolved_root)
    if inventory != recomputed_inventory:
        raise CampaignError("campaign raw inventory differs")
    inventory_sha256 = _sha256_file(inventory_path)
    campaign_sha256 = _sha256_file(campaign_path)
    if campaign.get("evidence_inventory_sha256") != inventory_sha256:
        raise CampaignError("campaign inventory binding differs")
    _validate_raw_campaign(
        resolved_root,
        campaign,
        campaign_schema=campaign_schema,
        process_schema=process_schema,
        bundle_schema=bundle_schema,
    )
    preflight = _load_campaign_json(
        resolved_root / "preflight.json",
        canonical=True,
    )
    _validate_campaign_acceptance(
        acceptance,
        campaign,
        campaign_sha256=campaign_sha256,
        inventory_sha256=inventory_sha256,
        boot_id_sha256=preflight["identity"]["boot_id_sha256"],
    )
    return acceptance


def verify_finalized_campaign(
    campaign_root: Path,
    *,
    campaign_schema: Path,
    process_schema: Path,
    bundle_schema: Path,
) -> dict[str, object]:
    """Recompute and validate one finalized campaign without trusting digests."""
    try:
        return _verify_finalized_campaign(
            campaign_root,
            campaign_schema=campaign_schema,
            process_schema=process_schema,
            bundle_schema=bundle_schema,
        )
    except CampaignError:
        raise
    except Exception as error:
        raise CampaignError("campaign verification failed") from error
