#!/usr/bin/env python3
"""Capture and validate non-secret Target 0 host qualification facts."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from types import SimpleNamespace
from typing import Any


CommandRunner = Callable[[tuple[str, ...]], SimpleNamespace]
QUALIFICATION_WINDOW_SECONDS = 60
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class CaptureError(RuntimeError):
    """Report a host fact that makes qualification capture invalid."""


def _source_path(source_root: Path, absolute_path: str) -> Path:
    """Resolve one absolute Linux path under a real or fixture root."""
    return source_root / absolute_path.removeprefix("/")


def _read_text(source_root: Path, absolute_path: str) -> str:
    """Read one required host file and strip its trailing whitespace."""
    path = _source_path(source_root, absolute_path)
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise CaptureError(f"required host fact is unavailable: {absolute_path}") from error


def _read_optional(source_root: Path, absolute_path: str) -> str | None:
    """Read one optional host file without converting absence into evidence."""
    path = _source_path(source_root, absolute_path)
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _parse_cpu_list(text: str) -> list[int]:
    """Parse the Linux comma/range CPU-list format into sorted identifiers."""
    cpus: set[int] = set()
    for component in text.split(","):
        component = component.strip()
        if not component:
            raise CaptureError("CPU list contains an empty component")
        if "-" in component:
            bounds = component.split("-", maxsplit=1)
            if len(bounds) != 2:
                raise CaptureError("CPU range is malformed")
            try:
                first, last = (int(bound) for bound in bounds)
            except ValueError as error:
                raise CaptureError("CPU range is not numeric") from error
            if first < 0 or last < first:
                raise CaptureError("CPU range is descending or negative")
            cpus.update(range(first, last + 1))
        else:
            try:
                cpu = int(component)
            except ValueError as error:
                raise CaptureError("CPU identifier is not numeric") from error
            if cpu < 0:
                raise CaptureError("CPU identifier is negative")
            cpus.add(cpu)
    if not cpus:
        raise CaptureError("CPU list is empty")
    return sorted(cpus)


def _parse_key_value_file(text: str, separator: str = "=") -> dict[str, str]:
    """Parse a simple Linux key-value record without shell evaluation."""
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.startswith("#") or separator not in line:
            continue
        key, value = line.split(separator, maxsplit=1)
        values[key.strip()] = value.strip().strip('"')
    return values


def _parse_cpuinfo(source_root: Path) -> tuple[dict[str, str], list[int]]:
    """Read the common processor identity and exact processor identifiers."""
    blocks = [
        _parse_key_value_file(block, separator=":")
        for block in _read_text(source_root, "/proc/cpuinfo").split("\n\n")
        if block.strip()
    ]
    if not blocks:
        raise CaptureError("/proc/cpuinfo contains no processors")
    required_fields = (
        "vendor_id",
        "cpu family",
        "model",
        "model name",
        "stepping",
        "microcode",
        "flags",
        "processor",
    )
    for block in blocks:
        missing = [field for field in required_fields if field not in block]
        if missing:
            raise CaptureError(f"CPU information is missing fields: {missing}")
    identity_fields = required_fields[:-1]
    for field in identity_fields:
        if any(block[field] != blocks[0][field] for block in blocks[1:]):
            raise CaptureError(f"CPU identity differs across processors: {field}")
    try:
        processors = sorted(int(block["processor"]) for block in blocks)
    except ValueError as error:
        raise CaptureError("processor identifier is not numeric") from error
    return blocks[0], processors


def _cache_records(source_root: Path, cpu: int) -> list[dict[str, Any]]:
    """Capture the cache hierarchy exposed for one logical CPU."""
    cache_root = _source_path(
        source_root, f"/sys/devices/system/cpu/cpu{cpu}/cache"
    )
    records: list[dict[str, Any]] = []
    for index_path in sorted(cache_root.glob("index*")):
        try:
            index = int(index_path.name.removeprefix("index"))
            level = int((index_path / "level").read_text(encoding="utf-8").strip())
            cache_type = (index_path / "type").read_text(encoding="utf-8").strip()
            size = (index_path / "size").read_text(encoding="utf-8").strip()
            shared = _parse_cpu_list(
                (index_path / "shared_cpu_list").read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as error:
            raise CaptureError(f"cache record is incomplete for CPU {cpu}") from error
        records.append(
            {
                "index": index,
                "level": level,
                "type": cache_type,
                "size": size,
                "shared_cpus": shared,
            }
        )
    if not records:
        raise CaptureError(f"CPU {cpu} exposes no cache records")
    return records


def _numa_node(source_root: Path, cpu: int) -> int:
    """Return the unique NUMA node linked from one CPU directory."""
    cpu_root = _source_path(source_root, f"/sys/devices/system/cpu/cpu{cpu}")
    nodes = sorted(cpu_root.glob("node[0-9]*"))
    if len(nodes) != 1:
        raise CaptureError(f"CPU {cpu} does not map to exactly one NUMA node")
    try:
        return int(nodes[0].name.removeprefix("node"))
    except ValueError as error:
        raise CaptureError(f"CPU {cpu} has a malformed NUMA node") from error


def _frequency_record(source_root: Path, cpu: int) -> dict[str, Any]:
    """Capture the AMD P-state and cpufreq facts for one logical CPU."""
    prefix = f"/sys/devices/system/cpu/cpu{cpu}/cpufreq"
    required = {
        "driver": "scaling_driver",
        "governor": "scaling_governor",
        "available_governors": "scaling_available_governors",
        "energy_performance_preference": "energy_performance_preference",
        "available_energy_preferences": "energy_performance_available_preferences",
        "minimum_khz": "cpuinfo_min_freq",
        "maximum_khz": "cpuinfo_max_freq",
        "current_khz": "scaling_cur_freq",
        "preferred_core_ranking": "amd_pstate_prefcore_ranking",
    }
    values = {
        key: _read_text(source_root, f"{prefix}/{file_name}")
        for key, file_name in required.items()
    }
    try:
        return {
            "driver": values["driver"],
            "governor": values["governor"],
            "available_governors": values["available_governors"].split(),
            "energy_performance_preference": values[
                "energy_performance_preference"
            ],
            "available_energy_preferences": values[
                "available_energy_preferences"
            ].split(),
            "minimum_khz": int(values["minimum_khz"]),
            "maximum_khz": int(values["maximum_khz"]),
            "current_khz": int(values["current_khz"]),
            "preferred_core_ranking": int(values["preferred_core_ranking"]),
        }
    except ValueError as error:
        raise CaptureError(f"CPU {cpu} has a nonnumeric frequency fact") from error


def _topology_record(source_root: Path, online_cpus: list[int]) -> dict[str, Any]:
    """Build the exact logical, core, socket, NUMA, sibling, and cache map."""
    cpu_records: list[dict[str, Any]] = []
    physical_cores: set[tuple[int, int]] = set()
    sockets: set[int] = set()
    numa_nodes: set[int] = set()
    for cpu in online_cpus:
        prefix = f"/sys/devices/system/cpu/cpu{cpu}"
        try:
            core_id = int(_read_text(source_root, f"{prefix}/topology/core_id"))
            package_id = int(
                _read_text(source_root, f"{prefix}/topology/physical_package_id")
            )
        except ValueError as error:
            raise CaptureError(f"CPU {cpu} topology identifier is not numeric") from error
        siblings = _parse_cpu_list(
            _read_text(source_root, f"{prefix}/topology/thread_siblings_list")
        )
        numa_node = _numa_node(source_root, cpu)
        frequency = _frequency_record(source_root, cpu)
        cpu_records.append(
            {
                "cpu": cpu,
                "core_id": core_id,
                "package_id": package_id,
                "numa_node": numa_node,
                "siblings": siblings,
                "preferred_core_ranking": frequency["preferred_core_ranking"],
                "caches": _cache_records(source_root, cpu),
            }
        )
        physical_cores.add((package_id, core_id))
        sockets.add(package_id)
        numa_nodes.add(numa_node)
    return {
        "logical_cpu_count": len(cpu_records),
        "physical_core_count": len(physical_cores),
        "socket_count": len(sockets),
        "numa_node_count": len(numa_nodes),
        "smt_active": _read_text(source_root, "/sys/devices/system/cpu/smt/active")
        == "1",
        "cpus": cpu_records,
    }


def _memory_record(source_root: Path) -> dict[str, Any]:
    """Capture page and memory facts relevant to repeatable measurements."""
    values = _parse_key_value_file(
        _read_text(source_root, "/proc/meminfo"), separator=":"
    )

    def first_integer(field: str) -> int:
        if field not in values:
            raise CaptureError(f"memory information is missing {field}")
        try:
            return int(values[field].split()[0])
        except (IndexError, ValueError) as error:
            raise CaptureError(f"memory information is malformed: {field}") from error

    return {
        "total_kib": first_integer("MemTotal"),
        "page_size_bytes": os.sysconf("SC_PAGE_SIZE"),
        "huge_pages_total": first_integer("HugePages_Total"),
        "huge_pages_free": first_integer("HugePages_Free"),
        "huge_page_size_kib": first_integer("Hugepagesize"),
        "transparent_hugepage": _read_optional(
            source_root, "/sys/kernel/mm/transparent_hugepage/enabled"
        ),
    }


def read_interrupt_totals(source_root: Path) -> dict[int, int]:
    """Sum all numeric interrupt counters for every listed CPU column."""
    lines = _read_text(source_root, "/proc/interrupts").splitlines()
    if not lines:
        raise CaptureError("/proc/interrupts is empty")
    header_cpus = [
        int(component.removeprefix("CPU"))
        for component in lines[0].split()
        if component.startswith("CPU")
    ]
    if not header_cpus:
        raise CaptureError("/proc/interrupts has no CPU columns")
    totals = {cpu: 0 for cpu in header_cpus}
    for line in lines[1:]:
        if ":" not in line:
            continue
        columns = line.split(":", maxsplit=1)[1].split()
        for index, cpu in enumerate(header_cpus):
            if index >= len(columns) or not columns[index].isdigit():
                break
            totals[cpu] += int(columns[index])
    return totals


def _thermal_record(source_root: Path) -> dict[str, Any]:
    """Capture all available k10temp millidegree inputs."""
    hwmon_root = _source_path(source_root, "/sys/class/hwmon")
    sensors: list[dict[str, Any]] = []
    for hwmon_path in sorted(hwmon_root.glob("hwmon*")):
        try:
            name = (hwmon_path / "name").read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if name != "k10temp":
            continue
        for input_path in sorted(hwmon_path.glob("temp*_input")):
            try:
                value = int(input_path.read_text(encoding="utf-8").strip())
            except (OSError, ValueError) as error:
                raise CaptureError("k10temp input is malformed") from error
            sensors.append({"sensor": input_path.stem, "millidegrees_c": value})
    if not sensors:
        raise CaptureError("k10temp is unavailable")
    return {"sensors": sensors}


def _powercap_record(source_root: Path) -> dict[str, Any]:
    """Capture available energy-counter names without requiring optional events."""
    powercap_root = _source_path(source_root, "/sys/class/powercap")
    zones: list[dict[str, Any]] = []
    if powercap_root.exists():
        for name_path in sorted(powercap_root.glob("**/name")):
            energy_path = name_path.parent / "energy_uj"
            if not energy_path.is_file():
                continue
            zones.append(
                {
                    "name": name_path.read_text(encoding="utf-8").strip(),
                    "energy_uj_available": True,
                }
            )
    return {"zones": zones}


def _tool_records(command_runner: CommandRunner) -> list[dict[str, Any]]:
    """Capture stable first-line identities for qualification dependencies."""
    commands = (
        ("clang++-21", "--version"),
        ("cmake", "--version"),
        ("ninja", "--version"),
        ("python3", "--version"),
        ("git", "--version"),
        ("perf", "--version"),
    )
    records: list[dict[str, Any]] = []
    for command in commands:
        result = command_runner(command)
        first_line = result.stdout.splitlines()[0] if result.stdout else ""
        records.append(
            {
                "name": command[0],
                "available": result.returncode == 0,
                "identity": first_line,
            }
        )
    return records


def _package_records(command_runner: CommandRunner) -> list[dict[str, str]]:
    """Capture only the package identities relevant to the locked host plan."""
    package_names = (
        "build-essential",
        "gfortran",
        "doxygen",
        "graphviz",
        "shellcheck",
        "hwloc",
        "lm-sensors",
        "libnuma-dev",
        "pkg-config",
    )
    records = []
    for name in package_names:
        result = command_runner(("dpkg-query", "-W", "-f=${Version}", name))
        records.append(
            {
                "name": name,
                "version": result.stdout.strip() if result.returncode == 0 else "absent",
            }
        )
    return records


def _real_command_runner(command: tuple[str, ...]) -> SimpleNamespace:
    """Run one bounded read-only command without shell interpretation."""
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return SimpleNamespace(returncode=127, stdout="", stderr=str(error))
    return SimpleNamespace(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _kernel_controls(source_root: Path) -> dict[str, bool]:
    """Reduce the kernel command line to approved measurement-control flags."""
    command_line = _read_text(source_root, "/proc/cmdline").split()
    names = {component.split("=", maxsplit=1)[0] for component in command_line}
    return {
        "isolcpus_configured": "isolcpus" in names,
        "nohz_full_configured": "nohz_full" in names,
        "rcu_nocbs_configured": "rcu_nocbs" in names,
    }


def _os_record(source_root: Path, command_runner: CommandRunner) -> dict[str, str]:
    """Capture OS ABI facts without hostname or access metadata."""
    release = _parse_key_value_file(_read_text(source_root, "/etc/os-release"))
    libc_result = command_runner(("getconf", "GNU_LIBC_VERSION"))
    if libc_result.returncode != 0:
        raise CaptureError("glibc identity is unavailable")
    required = ("ID", "VERSION_ID", "VERSION_CODENAME")
    if any(field not in release for field in required):
        raise CaptureError("OS release record is incomplete")
    return {
        "id": release["ID"],
        "version_id": release["VERSION_ID"],
        "version_codename": release["VERSION_CODENAME"],
        "kernel_release": _read_text(source_root, "/proc/sys/kernel/osrelease"),
        "kernel_version": _read_text(source_root, "/proc/sys/kernel/version"),
        "libc": libc_result.stdout.strip(),
        "architecture": platform.machine(),
    }


def build_capture(
    *,
    phase: str,
    source_root: Path,
    command_runner: CommandRunner,
    captured_at_utc: str,
    repository_root: Path,
) -> dict[str, Any]:
    """Build and validate one closed non-secret host capture.

    Args:
        phase: Capture lifecycle phase, either ``prestate`` or ``campaign``.
        source_root: Real Linux root or a controlled test fixture root.
        command_runner: Bounded runner for external read-only commands.
        captured_at_utc: Caller-supplied UTC timestamp for deterministic tests.
        repository_root: XOAS checkout whose source state is captured.

    Returns:
        A validated closed host record with no access or login metadata.

    Raises:
        CaptureError: A required host fact is missing or incompatible.
    """
    if phase not in {"prestate", "campaign"}:
        raise CaptureError("capture phase is not recognized")
    cpuinfo, processors = _parse_cpuinfo(source_root)
    online_cpus = _parse_cpu_list(
        _read_text(source_root, "/sys/devices/system/cpu/online")
    )
    if processors != online_cpus:
        raise CaptureError("CPU information and online CPU set differ")

    virtualization_result = command_runner(("systemd-detect-virt",))
    virtualization_kind = virtualization_result.stdout.strip()
    valid_bare_metal_result = (
        virtualization_kind == "none" and virtualization_result.returncode == 1
    )
    valid_virtualized_result = (
        virtualization_kind != "none" and virtualization_result.returncode == 0
    )
    if not valid_bare_metal_result and not valid_virtualized_result:
        raise CaptureError("virtualization state is unavailable")
    perf_result = command_runner(
        (
            "sudo",
            "-n",
            "perf",
            "stat",
            "-x,",
            "-e",
            "cycles,instructions",
            "--",
            "true",
        )
    )
    git_commit = command_runner(("git", "rev-parse", "HEAD"))
    git_status = command_runner(("git", "status", "--porcelain"))
    if git_commit.returncode != 0 or git_status.returncode != 0:
        raise CaptureError("repository identity is unavailable")

    frequencies = [
        {"cpu": cpu, **_frequency_record(source_root, cpu)}
        for cpu in online_cpus
    ]
    boot_id = _read_text(source_root, "/proc/sys/kernel/random/boot_id")
    record: dict[str, Any] = {
        "manifest_version": "xoas.target0-host-capture.v1",
        "performance_claim": False,
        "phase": phase,
        "captured_at_utc": captured_at_utc,
        "host": {
            "cpu": {
                "vendor_id": cpuinfo["vendor_id"],
                "family": int(cpuinfo["cpu family"]),
                "model": int(cpuinfo["model"]),
                "model_name": cpuinfo["model name"],
                "stepping": int(cpuinfo["stepping"]),
                "microcode": cpuinfo["microcode"],
                "isa_flags": sorted(cpuinfo["flags"].split()),
            },
            "topology": _topology_record(source_root, online_cpus),
            "memory": _memory_record(source_root),
            "os": _os_record(source_root, command_runner),
            "virtualization": {
                "kind": virtualization_kind,
            },
            "clocksource": {
                "current": _read_text(
                    source_root,
                    "/sys/devices/system/clocksource/clocksource0/current_clocksource",
                ),
                "available": _read_text(
                    source_root,
                    "/sys/devices/system/clocksource/clocksource0/available_clocksource",
                ).split(),
            },
            "boot_id_sha256": hashlib.sha256(boot_id.encode("ascii")).hexdigest(),
            "frequency": {
                "cpus": frequencies,
                "boost": int(
                    _read_text(
                        source_root, "/sys/devices/system/cpu/cpufreq/boost"
                    )
                ),
            },
            "thermal": _thermal_record(source_root),
            "powercap": _powercap_record(source_root),
            "perf": {
                "event_paranoid": int(
                    _read_text(source_root, "/proc/sys/kernel/perf_event_paranoid")
                ),
                "cycles_available": perf_result.returncode == 0,
                "instructions_available": perf_result.returncode == 0,
                "nmi_watchdog": int(
                    _read_text(source_root, "/proc/sys/kernel/nmi_watchdog")
                ),
            },
            "interrupts": {
                "per_cpu_totals": {
                    str(cpu): total
                    for cpu, total in read_interrupt_totals(source_root).items()
                },
            },
            "load": {
                "load_average": [
                    float(value)
                    for value in _read_text(source_root, "/proc/loadavg").split()[:3]
                ],
            },
            "kernel_controls": _kernel_controls(source_root),
            "tools": _tool_records(command_runner),
            "packages": _package_records(command_runner),
        },
        "repository": {
            "commit": git_commit.stdout.strip(),
            "tree_state": "clean" if not git_status.stdout.strip() else "dirty",
            "root_name": repository_root.name,
        },
    }
    validate_capture(record)
    return record


def _walk_record(value: Any, path: tuple[str, ...] = ()) -> None:
    """Reject credential, access, and network fields anywhere in a record."""
    forbidden_keys = {
        "address",
        "command_line",
        "environment",
        "home",
        "home_directory",
        "hostname",
        "ip",
        "ip_address",
        "login",
        "network",
        "ssh",
        "user",
        "username",
    }
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise CaptureError(f"capture object has a non-string key: {path}")
            normalized_key = key.lower()
            if normalized_key in forbidden_keys:
                raise CaptureError(
                    f"prohibited capture field: {'.'.join((*path, key))}"
                )
            _walk_record(nested, (*path, key))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _walk_record(nested, (*path, str(index)))
    elif isinstance(value, str):
        lowered = value.lower()
        if "-----begin " in lowered or lowered.startswith("ssh://"):
            raise CaptureError(f"credential-like capture value: {'.'.join(path)}")


def _require_exact_keys(value: Any, expected: set[str], path: str) -> None:
    """Require one closed record to contain exactly its reviewed fields."""
    if not isinstance(value, dict):
        raise CaptureError(f"{path} is not an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise CaptureError(
            f"{path} fields differ; missing={missing}, unknown={unknown}"
        )


def _require_record_list(value: Any, path: str) -> list[dict[str, Any]]:
    """Require one field to be an array containing only record objects."""
    if not isinstance(value, list):
        raise CaptureError(f"{path} is not an array")
    if any(not isinstance(record, dict) for record in value):
        raise CaptureError(f"{path} contains a non-object element")
    return value


def validate_capture(record: dict[str, Any]) -> None:
    """Validate load-bearing qualification and non-secret invariants.

    Raises:
        CaptureError: The record is incomplete, inconsistent, virtualized,
            non-TSC, PMU-ineligible, or contains a prohibited field.
    """
    _walk_record(record)
    _require_exact_keys(
        record,
        {
            "manifest_version",
            "performance_claim",
            "phase",
            "captured_at_utc",
            "host",
            "repository",
        },
        "capture",
    )
    host = record["host"]
    _require_exact_keys(
        host,
        {
            "cpu",
            "topology",
            "memory",
            "os",
            "virtualization",
            "clocksource",
            "boot_id_sha256",
            "frequency",
            "thermal",
            "powercap",
            "perf",
            "interrupts",
            "load",
            "kernel_controls",
            "tools",
            "packages",
        },
        "host",
    )
    _require_exact_keys(
        host["cpu"],
        {
            "vendor_id",
            "family",
            "model",
            "model_name",
            "stepping",
            "microcode",
            "isa_flags",
        },
        "host.cpu",
    )
    topology = host["topology"]
    _require_exact_keys(
        topology,
        {
            "logical_cpu_count",
            "physical_core_count",
            "socket_count",
            "numa_node_count",
            "smt_active",
            "cpus",
        },
        "host.topology",
    )
    cpu_records = _require_record_list(topology["cpus"], "host.topology.cpus")
    for index, cpu_record in enumerate(cpu_records):
        cpu_path = f"host.topology.cpus[{index}]"
        _require_exact_keys(
            cpu_record,
            {
                "cpu",
                "core_id",
                "package_id",
                "numa_node",
                "siblings",
                "preferred_core_ranking",
                "caches",
            },
            cpu_path,
        )
        cache_records = _require_record_list(
            cpu_record["caches"], f"{cpu_path}.caches"
        )
        for cache_index, cache_record in enumerate(cache_records):
            _require_exact_keys(
                cache_record,
                {"index", "level", "type", "size", "shared_cpus"},
                f"{cpu_path}.caches[{cache_index}]",
            )
    _require_exact_keys(
        host["memory"],
        {
            "total_kib",
            "page_size_bytes",
            "huge_pages_total",
            "huge_pages_free",
            "huge_page_size_kib",
            "transparent_hugepage",
        },
        "host.memory",
    )
    _require_exact_keys(
        host["os"],
        {
            "id",
            "version_id",
            "version_codename",
            "kernel_release",
            "kernel_version",
            "libc",
            "architecture",
        },
        "host.os",
    )
    _require_exact_keys(host["virtualization"], {"kind"}, "host.virtualization")
    _require_exact_keys(
        host["clocksource"], {"current", "available"}, "host.clocksource"
    )
    frequency = host["frequency"]
    _require_exact_keys(frequency, {"cpus", "boost"}, "host.frequency")
    frequency_records = _require_record_list(
        frequency["cpus"], "host.frequency.cpus"
    )
    for index, frequency_record in enumerate(frequency_records):
        _require_exact_keys(
            frequency_record,
            {
                "cpu",
                "driver",
                "governor",
                "available_governors",
                "energy_performance_preference",
                "available_energy_preferences",
                "minimum_khz",
                "maximum_khz",
                "current_khz",
                "preferred_core_ranking",
            },
            f"host.frequency.cpus[{index}]",
        )
    thermal = host["thermal"]
    _require_exact_keys(thermal, {"sensors"}, "host.thermal")
    sensor_records = _require_record_list(thermal["sensors"], "host.thermal.sensors")
    for index, sensor_record in enumerate(sensor_records):
        _require_exact_keys(
            sensor_record,
            {"sensor", "millidegrees_c"},
            f"host.thermal.sensors[{index}]",
        )
    powercap = host["powercap"]
    _require_exact_keys(powercap, {"zones"}, "host.powercap")
    zone_records = _require_record_list(powercap["zones"], "host.powercap.zones")
    for index, zone_record in enumerate(zone_records):
        _require_exact_keys(
            zone_record,
            {"name", "energy_uj_available"},
            f"host.powercap.zones[{index}]",
        )
    _require_exact_keys(
        host["perf"],
        {
            "event_paranoid",
            "cycles_available",
            "instructions_available",
            "nmi_watchdog",
        },
        "host.perf",
    )
    interrupts = host["interrupts"]
    _require_exact_keys(interrupts, {"per_cpu_totals"}, "host.interrupts")
    if not isinstance(interrupts["per_cpu_totals"], dict):
        raise CaptureError("host.interrupts.per_cpu_totals is not an object")
    _require_exact_keys(host["load"], {"load_average"}, "host.load")
    _require_exact_keys(
        host["kernel_controls"],
        {
            "isolcpus_configured",
            "nohz_full_configured",
            "rcu_nocbs_configured",
        },
        "host.kernel_controls",
    )
    tool_records = _require_record_list(host["tools"], "host.tools")
    for index, tool_record in enumerate(tool_records):
        _require_exact_keys(
            tool_record,
            {"name", "available", "identity"},
            f"host.tools[{index}]",
        )
    package_records = _require_record_list(host["packages"], "host.packages")
    for index, package_record in enumerate(package_records):
        _require_exact_keys(
            package_record,
            {"name", "version"},
            f"host.packages[{index}]",
        )
    _require_exact_keys(
        record["repository"],
        {"commit", "tree_state", "root_name"},
        "repository",
    )
    if record.get("manifest_version") != "xoas.target0-host-capture.v1":
        raise CaptureError("capture manifest version is invalid")
    if record.get("performance_claim") is not False:
        raise CaptureError("host capture cannot make a performance claim")
    if not isinstance(cpu_records, list) or not cpu_records:
        raise CaptureError("capture has no CPU topology records")
    if topology.get("logical_cpu_count") != len(cpu_records):
        raise CaptureError("logical CPU count does not match topology records")

    by_cpu: dict[int, dict[str, Any]] = {}
    for cpu_record in cpu_records:
        cpu = cpu_record.get("cpu")
        if not isinstance(cpu, int) or cpu in by_cpu:
            raise CaptureError("CPU topology contains an invalid duplicate")
        by_cpu[cpu] = cpu_record
    for cpu, cpu_record in by_cpu.items():
        siblings = cpu_record.get("siblings")
        if not isinstance(siblings, list) or len(siblings) != 2 or cpu not in siblings:
            raise CaptureError(f"CPU {cpu} does not expose one SMT pair")
        for sibling in siblings:
            if sibling not in by_cpu:
                raise CaptureError(f"CPU {cpu} names an absent sibling")
            sibling_record = by_cpu[sibling]
            if sibling_record.get("siblings") != siblings:
                raise CaptureError(f"CPU {cpu} sibling relation is not symmetric")
            if sibling_record.get("core_id") != cpu_record.get("core_id"):
                raise CaptureError(f"CPU {cpu} sibling has a different core")
            if sibling_record.get("package_id") != cpu_record.get("package_id"):
                raise CaptureError(f"CPU {cpu} sibling has a different package")
    interrupt_cpu_keys = set(interrupts["per_cpu_totals"])
    expected_interrupt_cpu_keys = {str(cpu) for cpu in by_cpu}
    if interrupt_cpu_keys != expected_interrupt_cpu_keys:
        raise CaptureError("interrupt counters do not match topology CPUs")
    if host.get("virtualization", {}).get("kind") != "none":
        raise CaptureError("Target 0 qualification requires bare metal")
    if host.get("clocksource", {}).get("current") != "tsc":
        raise CaptureError("Target 0 qualification requires the TSC clocksource")
    perf = host.get("perf", {})
    if perf.get("cycles_available") is not True:
        raise CaptureError("cycles PMU evidence is unavailable")
    if perf.get("instructions_available") is not True:
        raise CaptureError("instructions PMU evidence is unavailable")
    boot_digest = host.get("boot_id_sha256")
    if not isinstance(boot_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", boot_digest):
        raise CaptureError("boot ID digest is invalid")


def select_core(
    capture: dict[str, Any],
    *,
    before_interrupts: dict[int, int],
    after_interrupts: dict[int, int],
    window_seconds: int,
) -> dict[str, Any]:
    """Select one physical core by rank, interrupt delta, and CPU number.

    Returns:
        A non-claiming selection record containing the selected logical CPU,
        its SMT sibling, preferred-core ranking, and interrupt delta.

    Raises:
        CaptureError: The capture, sampling window, or counters are invalid.
    """
    validate_capture(capture)
    if window_seconds != QUALIFICATION_WINDOW_SECONDS:
        raise CaptureError("core selection requires the exact 60-second window")
    cpu_records = capture["host"]["topology"]["cpus"]
    representatives = [
        record for record in cpu_records if record["cpu"] == min(record["siblings"])
    ]
    candidates = []
    for record in representatives:
        cpu = record["cpu"]
        if cpu not in before_interrupts or cpu not in after_interrupts:
            raise CaptureError(f"CPU {cpu} interrupt sample is missing")
        delta = after_interrupts[cpu] - before_interrupts[cpu]
        if delta < 0:
            raise CaptureError(f"CPU {cpu} interrupt counter decreased")
        candidates.append(
            (
                -record["preferred_core_ranking"],
                delta,
                cpu,
                next(sibling for sibling in record["siblings"] if sibling != cpu),
            )
        )
    if not candidates:
        raise CaptureError("no physical core candidates are available")
    negative_ranking, delta, cpu, sibling = min(candidates)
    return {
        "manifest_version": "xoas.target0-core-selection.v1",
        "performance_claim": False,
        "window_seconds": window_seconds,
        "cpu": cpu,
        "sibling": sibling,
        "preferred_core_ranking": -negative_ranking,
        "interrupt_delta": delta,
    }


def _write_json_without_replacement(output_path: Path, record: dict[str, Any]) -> None:
    """Publish one complete JSON record without replacing prior evidence."""
    temporary_path = output_path.with_name(
        f"{output_path.name}.tmp.{os.getpid()}"
    )
    encoded = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor: int | None = None
    published = False
    try:
        descriptor = os.open(temporary_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "wb", closefd=True) as output_file:
            descriptor = None
            output_file.write(encoded)
            output_file.flush()
            os.fsync(output_file.fileno())
        os.link(temporary_path, output_path)
        published = True
        temporary_path.unlink()
    except OSError as error:
        if descriptor is not None:
            os.close(descriptor)
        temporary_path.unlink(missing_ok=True)
        if published:
            output_path.unlink(missing_ok=True)
        raise CaptureError(f"unable to publish capture: {output_path}") from error


def _utc_now() -> str:
    """Return a whole-second UTC timestamp in the retained record format."""
    return (
        datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _parse_arguments() -> argparse.Namespace:
    """Parse the closed capture and core-selection command interfaces."""
    parser = argparse.ArgumentParser(
        description="Capture non-secret XOAS Target 0 host qualification facts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--phase", choices=("prestate", "campaign"), required=True)
    capture_parser.add_argument("--output", type=Path, required=True)

    select_parser = subparsers.add_parser("select-core")
    select_parser.add_argument("--capture", type=Path, required=True)
    select_parser.add_argument("--interrupt-window-seconds", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    """Run the requested capture operation and return a diagnostic status."""
    arguments = _parse_arguments()
    try:
        if arguments.command == "capture":
            record = build_capture(
                phase=arguments.phase,
                source_root=Path("/"),
                command_runner=_real_command_runner,
                captured_at_utc=_utc_now(),
                repository_root=REPOSITORY_ROOT,
            )
            _write_json_without_replacement(arguments.output, record)
            return 0

        capture = json.loads(arguments.capture.read_text(encoding="utf-8"))
        validate_capture(capture)
        before_interrupts = read_interrupt_totals(Path("/"))
        start = time.monotonic_ns()
        time.sleep(arguments.interrupt_window_seconds)
        after_interrupts = read_interrupt_totals(Path("/"))
        selection = select_core(
            capture,
            before_interrupts=before_interrupts,
            after_interrupts=after_interrupts,
            window_seconds=arguments.interrupt_window_seconds,
        )
        selection["observed_window_ns"] = time.monotonic_ns() - start
        print(json.dumps(selection, indent=2, sort_keys=True))
        return 0
    except (CaptureError, json.JSONDecodeError, OSError) as error:
        print(f"capture_host.py: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
