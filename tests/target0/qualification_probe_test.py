#!/usr/bin/env python3
"""Behavioral tests for the Target 0 qualification process probe."""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from jsonschema import Draft202012Validator


def canonical_json_bytes(record: object) -> bytes:
    """Return the normative canonical JSON encoding for one test record."""
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


def parse_arguments() -> argparse.Namespace:
    """Parse paths supplied by CTest without consuming unittest options."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    arguments, unittest_arguments = parser.parse_known_args()
    unittest.main_argv = [__file__, *unittest_arguments]
    return arguments


class QualificationProbeTest(unittest.TestCase):
    """Verify the observable process-record contract of the native probe."""

    @classmethod
    def setUpClass(cls) -> None:
        """Run two real processes once for deterministic and schema checks."""
        if not ARGUMENTS.probe.is_file():
            raise AssertionError("probe executable is missing")
        if not ARGUMENTS.schema.is_file():
            raise AssertionError("probe schema is missing")

        cls.requested_cpu = min(os.sched_getaffinity(0))
        cls.temporary_directory = tempfile.TemporaryDirectory()
        cls.working_directory = Path(cls.temporary_directory.name)
        cls.records = []
        cls.output_paths = []
        for process_index in range(2):
            output_path = cls.working_directory / f"process-{process_index}.json"
            completed = cls.run_probe(output_path)
            if completed.returncode != 0:
                raise AssertionError(completed.stderr)
            cls.output_paths.append(output_path)
            cls.records.append(
                json.loads(output_path.read_text(encoding="utf-8"))
            )

        cls.schema = json.loads(ARGUMENTS.schema.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    @classmethod
    def tearDownClass(cls) -> None:
        """Release process records owned by this test class."""
        cls.temporary_directory.cleanup()

    @classmethod
    def run_probe(
        cls,
        output_path: Path,
        *,
        cpu: int | None = None,
        warmup_rounds: str = "5",
        rounds: str = "30",
        iterations: str = "16777216",
        seed: str = "42",
        extra_arguments: tuple[str, ...] = (),
    ) -> subprocess.CompletedProcess[str]:
        """Execute the real probe with one explicit qualification request."""
        requested_cpu = cls.requested_cpu if cpu is None else cpu
        return subprocess.run(
            [
                ARGUMENTS.probe,
                "--cpu",
                str(requested_cpu),
                "--warmup-rounds",
                warmup_rounds,
                "--rounds",
                rounds,
                "--iterations",
                iterations,
                "--seed",
                seed,
                "--output",
                output_path,
                *extra_arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_valid_run_emits_schema_valid_measurements(self) -> None:
        """A valid pinned run must retain the complete non-claiming record."""
        record = self.records[0]
        self.validator.validate(record)

        self.assertEqual(
            record["manifest_version"],
            "xoas.target0-qualification-process.v1",
        )
        self.assertIs(record["performance_claim"], False)
        self.assertEqual(record["warmup_rounds"], 5)
        self.assertEqual(len(record["samples"]), 30)
        self.assertTrue(
            all(sample["elapsed_ns"] > 0 for sample in record["samples"])
        )
        self.assertTrue(
            all(
                sample["observed_cpu_start"] == self.requested_cpu
                for sample in record["samples"]
            )
        )
        self.assertTrue(
            all(
                sample["observed_cpu_end"] == self.requested_cpu
                for sample in record["samples"]
            )
        )
        self.assertEqual(record["max_observed_threads"], 1)
        self.assertEqual(len(record["timer_overhead_ns"]), 10000)
        self.assertEqual(record["samples"][0]["checksum"], "b6347d16b98f0445")

    def test_valid_run_emits_exact_canonical_json_bytes(self) -> None:
        """The native producer must retain the normative byte representation."""
        for output_path, record in zip(self.output_paths, self.records):
            with self.subTest(output=output_path.name):
                self.assertEqual(
                    output_path.read_bytes(),
                    canonical_json_bytes(record),
                )

    def test_same_seed_preserves_deterministic_fields(self) -> None:
        """Timing and scheduler noise must not change workload identity."""
        normalized_records = []
        for source_record in self.records:
            record = copy.deepcopy(source_record)
            del record["timer_overhead_ns"]
            del record["process_id"]
            del record["process_context_switches"]
            for sample in record["samples"]:
                del sample["elapsed_ns"]
                del sample["voluntary_context_switches"]
                del sample["involuntary_context_switches"]
            normalized_records.append(record)

        self.assertEqual(normalized_records[0], normalized_records[1])
        self.assertEqual(
            [sample["round"] for sample in self.records[0]["samples"]],
            list(range(30)),
        )

    def test_schema_rejects_claims_unknown_fields_and_broken_rounds(self) -> None:
        """Closed evidence must reject claim inflation and incomplete ordering."""
        mutations = []

        claiming_record = copy.deepcopy(self.records[0])
        claiming_record["performance_claim"] = True
        mutations.append(claiming_record)

        extended_record = copy.deepcopy(self.records[0])
        extended_record["unreviewed_field"] = "not allowed"
        mutations.append(extended_record)

        duplicate_round_record = copy.deepcopy(self.records[0])
        duplicate_round_record["samples"][1]["round"] = 0
        mutations.append(duplicate_round_record)

        missing_sample_record = copy.deepcopy(self.records[0])
        missing_sample_record["samples"].pop()
        mutations.append(missing_sample_record)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertFalse(self.validator.is_valid(mutation))

    def test_schema_accepts_an_observed_thread_failure(self) -> None:
        """A measured thread-count violation must remain valid failure evidence."""
        failure_record = copy.deepcopy(self.records[0])
        failure_record["status"] = "failed"
        failure_record["failure_reasons"] = ["thread_count_changed"]
        failure_record["max_observed_threads"] = 2

        self.validator.validate(failure_record)

    def test_invalid_requests_fail_without_partial_output(self) -> None:
        """Invalid CLI and destinations must never publish partial evidence."""
        invalid_cases = [
            (
                "unknown-option",
                {"extra_arguments": ("--unknown", "value")},
                self.working_directory / "unknown.json",
            ),
            (
                "offline-cpu",
                {"cpu": max(os.sched_getaffinity(0)) + 1024},
                self.working_directory / "offline.json",
            ),
            (
                "zero-rounds",
                {"rounds": "0"},
                self.working_directory / "zero-rounds.json",
            ),
            (
                "unwritable-directory",
                {},
                Path("/proc/xoas-target0-qualification-process.json"),
            ),
        ]

        for name, overrides, output_path in invalid_cases:
            with self.subTest(name=name):
                completed = self.run_probe(output_path, **overrides)
                self.assertNotEqual(completed.returncode, 0)
                self.assertFalse(output_path.exists())

        existing_output = self.working_directory / "existing.json"
        existing_output.write_text("sentinel\n", encoding="utf-8")
        completed = self.run_probe(existing_output)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(existing_output.read_text(encoding="utf-8"), "sentinel\n")


ARGUMENTS = parse_arguments()


if __name__ == "__main__":
    unittest.main(argv=unittest.main_argv)
