#!/usr/bin/env python3
"""Define closed evidence contracts for Target 0 qualification campaigns."""

from __future__ import annotations

from collections.abc import Sequence
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
        elif re.fullmatch(r"[0-9]+", value_text) is not None:
            value = int(value_text)
            status = "supported"
        elif re.fullmatch(r"[0-9]+\.[0-9]+", value_text) is not None:
            value = value_text
            status = "supported"
        else:
            raise CampaignError("perf-stat value is invalid")
        if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", running_percentage) is None:
            raise CampaignError("perf-stat running percentage is invalid")
        records.append(
            {
                "event": event,
                "running_percentage": running_percentage,
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
    if any(not isinstance(package[field], str) or not package[field] for field in package):
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
    elif record["status"] != "unsupported" or command_exit_status == 0:
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
