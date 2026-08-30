#!/usr/bin/env python3
"""Behavioral tests for closed Target 0 qualification campaigns."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest

sys.dont_write_bytecode = True


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPOSITORY_ROOT / "tools/target0/qualification_campaign.py"
SCHEMA_PATH = (
    REPOSITORY_ROOT / "schemas/target0-qualification-campaign-v1.schema.json"
)
EXAMPLE_PATH = (
    REPOSITORY_ROOT
    / "tests/target0/fixtures/qualification-campaign-v1.example.json"
)


def load_campaign_module() -> ModuleType:
    """Load the real campaign contract after asserting its ownership path."""
    if not MODULE_PATH.is_file():
        raise AssertionError("qualification campaign module is missing")
    specification = importlib.util.spec_from_file_location(
        "xoas_qualification_campaign",
        MODULE_PATH,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("qualification campaign module cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class QualificationCampaignStatisticsTest(unittest.TestCase):
    """Verify deterministic seeds and exact qualification statistics."""

    def test_seed_derivation_is_domain_separated_and_indexed(self) -> None:
        """A changed seed encoding or index must change the literal contract."""
        campaign = load_campaign_module()

        self.assertEqual(
            campaign.derive_process_seed("target0-campaign-01", 1),
            0x89651FC077B60C94,
        )
        self.assertNotEqual(
            campaign.derive_process_seed("target0-campaign-01", 1),
            campaign.derive_process_seed("target0-campaign-01", 2),
        )

    def test_seed_derivation_rejects_invalid_identity_or_process_index(self) -> None:
        """Malformed campaign identities and non-primary indexes must fail."""
        campaign = load_campaign_module()

        invalid_inputs = (
            ("Target0-campaign-01", 1),
            ("target0/campaign-01", 1),
            ("", 1),
            ("a" * 97, 1),
            ("target0-campaign-01", 0),
            ("target0-campaign-01", 6),
            ("target0-campaign-01", True),
        )
        for campaign_id, process_index in invalid_inputs:
            with self.subTest(
                campaign_id=campaign_id,
                process_index=process_index,
            ):
                with self.assertRaises(RuntimeError):
                    campaign.derive_process_seed(campaign_id, process_index)

    def test_statistics_use_exact_mad_and_nearest_rank_p99(self) -> None:
        """A linear-interpolated percentile or inexact median must fail."""
        campaign = load_campaign_module()
        elapsed_nanoseconds = [100_000_000] * 29 + [102_000_000]
        self.assertTrue(
            hasattr(campaign, "process_statistics"),
            "process statistics contract is missing",
        )

        statistics = campaign.process_statistics(elapsed_nanoseconds)

        self.assertEqual(
            statistics,
            {
                "mad_ns": {"denominator": 1, "numerator": 0},
                "mad_ratio": "0.000000000000",
                "maximum_ns": 102_000_000,
                "median_ns": {"denominator": 1, "numerator": 100_000_000},
                "minimum_ns": 100_000_000,
                "p99_ns": 102_000_000,
                "p99_ratio": "1.020000000000",
                "sample_count": 30,
            },
        )

    def test_statistics_reject_invalid_sample_contracts(self) -> None:
        """Wrong count, type, or nonpositive durations must not be summarized."""
        campaign = load_campaign_module()
        invalid_samples = (
            [100_000_000] * 29,
            [100_000_000] * 31,
            [100_000_000] * 29 + [0],
            [100_000_000] * 29 + [-1],
            [100_000_000] * 29 + [True],
            [100_000_000] * 29 + [100_000_000.0],
        )

        for samples in invalid_samples:
            with self.subTest(samples=samples[-2:]):
                with self.assertRaises(RuntimeError):
                    campaign.process_statistics(samples)


class QualificationCampaignPerfTest(unittest.TestCase):
    """Verify closed parsing of raw Linux perf-stat evidence."""

    def test_perf_parser_retains_supported_and_unsupported_events(self) -> None:
        """A parser that estimates an unsupported event must fail this test."""
        campaign = load_campaign_module()
        self.assertTrue(
            hasattr(campaign, "parse_perf_stat"),
            "perf-stat parser is missing",
        )
        raw_text = (
            "123456789;;cycles;87654321;100.00;;\n"
            "<not supported>;;instructions;0;100.00;;\n"
        )

        records = campaign.parse_perf_stat(
            raw_text,
            ("cycles", "instructions"),
        )

        self.assertEqual(
            records,
            [
                {
                    "event": "cycles",
                    "running_percentage": "100.00",
                    "status": "supported",
                    "value": 123456789,
                },
                {
                    "event": "instructions",
                    "running_percentage": "100.00",
                    "status": "unsupported",
                    "value": None,
                },
            ],
        )

    def test_perf_parser_rejects_unknown_missing_duplicate_or_malformed_data(
        self,
    ) -> None:
        """An incomplete or operator-defined PMU record must fail closed."""
        campaign = load_campaign_module()
        cases = (
            (
                "unknown-request",
                "1;;operator/event/;1;100.00;;\n",
                ("operator/event/",),
            ),
            (
                "missing-event",
                "1;;cycles;1;100.00;;\n",
                ("cycles", "instructions"),
            ),
            (
                "duplicate-event",
                "1;;branches;1;100.00;;\n2;;branches;1;100.00;;\n",
                ("branches",),
            ),
            (
                "malformed-value",
                "estimated;;branches;1;100.00;;\n",
                ("branches",),
            ),
            (
                "not-counted",
                "<not counted>;;branches;1;100.00;;\n",
                ("branches",),
            ),
            (
                "missing-percentage",
                "1;;branches;1;;;\n",
                ("branches",),
            ),
        )

        for name, raw_text, expected_events in cases:
            with self.subTest(name=name):
                with self.assertRaises(RuntimeError):
                    campaign.parse_perf_stat(raw_text, expected_events)


class QualificationCampaignSchemaTest(unittest.TestCase):
    """Verify schema closure and cross-field campaign acceptance."""

    def test_schema_and_positive_example_are_closed_and_semantically_valid(
        self,
    ) -> None:
        """A missing schema, open field, or inconsistent decision must fail."""
        campaign = load_campaign_module()
        self.assertTrue(SCHEMA_PATH.is_file(), "campaign schema is missing")
        self.assertTrue(EXAMPLE_PATH.is_file(), "campaign example is missing")
        self.assertTrue(
            hasattr(campaign, "validate_campaign_manifest"),
            "campaign manifest validator is missing",
        )
        from jsonschema import Draft202012Validator

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(example)
        campaign.validate_campaign_manifest(example, SCHEMA_PATH)

        mutations = []
        added_field = copy.deepcopy(example)
        added_field["operator"] = "not-retainable"
        mutations.append(added_field)
        short_process_set = copy.deepcopy(example)
        short_process_set["processes"].pop()
        mutations.append(short_process_set)
        failed_restoration = copy.deepcopy(example)
        failed_restoration["processes"][0]["restored"] = False
        mutations.append(failed_restoration)
        inconsistent_decision = copy.deepcopy(example)
        inconsistent_decision["processes"][0]["statistics"]["p99_ratio"] = (
            "1.030000000000"
        )
        mutations.append(inconsistent_decision)

        validator = Draft202012Validator(schema)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                schema_errors = list(validator.iter_errors(mutation))
                if not schema_errors:
                    with self.assertRaises(RuntimeError):
                        campaign.validate_campaign_manifest(
                            mutation,
                            SCHEMA_PATH,
                        )

    def test_semantic_validator_rejects_inconsistent_session_aggregates(
        self,
    ) -> None:
        """An unexpected session hidden by aggregate counts must fail."""
        campaign = load_campaign_module()
        example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        example["preflight"]["interactive_sessions"]["expected"] = 2

        with self.assertRaises(RuntimeError):
            campaign.validate_campaign_manifest(example, SCHEMA_PATH)


class QualificationCampaignRecordTest(unittest.TestCase):
    """Verify closed identity, restoration, PMU, and inventory records."""

    @staticmethod
    def restoration_record() -> dict[str, object]:
        """Return one hand-authored exactly restored session record."""
        state = {
            "boost": 1,
            "energy_performance_preference": "balance_performance",
            "governor": "powersave",
            "selected_cpu_interrupts": 100,
            "sibling_online": 1,
        }
        return {
            "boost_unchanged": True,
            "command_exit_status": 0,
            "cpu": 4,
            "failure_reasons": [],
            "manifest_version": (
                "xoas.target0-measurement-session-restoration.v1"
            ),
            "performance_claim": False,
            "post_state": dict(state),
            "pre_state": dict(state),
            "restored": True,
            "sibling": 16,
            "status": "restored",
        }

    @staticmethod
    def identity_record() -> dict[str, object]:
        """Return one hand-authored exact non-secret identity record."""
        return {
            "boot_id_sha256": "11" * 32,
            "bundle": {
                "bundle_id": "target0-qualification-tools-example",
                "bundle_inventory_sha256": "22" * 32,
                "bundle_manifest_sha256": "33" * 32,
                "executable_identity_sha256": "44" * 32,
                "executable_sha256": "55" * 32,
            },
            "manifest_version": "xoas.target0-campaign-identity.v1",
            "performance_claim": False,
            "provisioning_lock": {
                "configuration_sha256": "66" * 32,
                "file_sha256": "77" * 32,
                "lock_id": "target0-amd-ryzen9-7900x-v1",
            },
            "repository": {
                "actual_commit": "8" * 40,
                "expected_commit": "8" * 40,
                "tree": "9" * 40,
                "tree_state": "clean",
            },
            "selected_core": {"cpu": 4, "sibling": 16},
            "sources": [
                {
                    "path": "schemas/target0-host-qualification-v1.schema.json",
                    "sha256": "aa" * 32,
                },
                {
                    "path": "tools/target0/qualification_probe.cpp",
                    "sha256": "bb" * 32,
                },
            ],
            "status": "accepted",
            "toolchain": {
                "compiler": {
                    "driver_path": "/usr/bin/clang++-21",
                    "package": {
                        "name": "clang-21",
                        "version": "1:21.1.8-6ubuntu1",
                    },
                    "resolved_path": "/usr/lib/llvm-21/bin/clang",
                    "sha256": "cc" * 32,
                    "target_triple": "x86_64-pc-linux-gnu",
                    "version": "Ubuntu clang version 21.1.8 (6ubuntu1)",
                },
                "linker": {
                    "driver_path": "/usr/bin/ld.lld-21",
                    "package": {
                        "name": "lld-21",
                        "version": "1:21.1.8-6ubuntu1",
                    },
                    "resolved_path": "/usr/lib/llvm-21/bin/lld",
                    "sha256": "dd" * 32,
                    "version": "Ubuntu LLD 21.1.8",
                },
            },
        }

    @staticmethod
    def required_pmu_record() -> dict[str, object]:
        """Return one hand-authored accepted required-counter record."""
        return {
            "command_exit_status": 0,
            "events": [
                {
                    "event": "cycles",
                    "running_percentage": "100.00",
                    "status": "supported",
                    "value": 100000000,
                },
                {
                    "event": "instructions",
                    "running_percentage": "100.00",
                    "status": "supported",
                    "value": 200000000,
                },
            ],
            "failure_reasons": [],
            "manifest_version": "xoas.target0-pmu-session.v1",
            "performance_claim": False,
            "required": True,
            "restored": True,
            "status": "passed",
        }

    def test_restoration_validator_requires_exact_state_and_status(self) -> None:
        """A false restore or unexpected child status must fail closed."""
        campaign = load_campaign_module()
        self.assertTrue(
            hasattr(campaign, "validate_restoration_record"),
            "restoration validator is missing",
        )
        record = self.restoration_record()

        campaign.validate_restoration_record(
            record,
            expected_command_status=0,
        )

        mutations = []
        changed_post_state = copy.deepcopy(record)
        changed_post_state["post_state"]["governor"] = "performance"
        mutations.append(changed_post_state)
        false_restore = copy.deepcopy(record)
        false_restore["restored"] = False
        mutations.append(false_restore)
        unexpected_status = copy.deepcopy(record)
        unexpected_status["command_exit_status"] = 1
        mutations.append(unexpected_status)
        added_field = copy.deepcopy(record)
        added_field["user"] = "not-retainable"
        mutations.append(added_field)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(RuntimeError):
                    campaign.validate_restoration_record(
                        mutation,
                        expected_command_status=0,
                    )

    def test_identity_validator_requires_exact_sorted_nonsecret_inputs(
        self,
    ) -> None:
        """Identity drift, unsorted sources, or private paths must fail."""
        campaign = load_campaign_module()
        self.assertTrue(
            hasattr(campaign, "validate_identity_record"),
            "identity validator is missing",
        )
        record = self.identity_record()

        campaign.validate_identity_record(record)

        mutations = []
        changed_commit = copy.deepcopy(record)
        changed_commit["repository"]["actual_commit"] = "e" * 40
        mutations.append(changed_commit)
        unsorted_sources = copy.deepcopy(record)
        unsorted_sources["sources"].reverse()
        mutations.append(unsorted_sources)
        private_path = copy.deepcopy(record)
        private_path["sources"][0]["path"] = "/home/operator/XOAS/source.py"
        mutations.append(private_path)
        same_cpu = copy.deepcopy(record)
        same_cpu["selected_core"]["sibling"] = 4
        mutations.append(same_cpu)
        added_user = copy.deepcopy(record)
        added_user["username"] = "not-retainable"
        mutations.append(added_user)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(RuntimeError):
                    campaign.validate_identity_record(mutation)

    def test_pmu_validator_distinguishes_required_and_optional_support(
        self,
    ) -> None:
        """Required scaling and optional unsupported status must remain exact."""
        campaign = load_campaign_module()
        self.assertTrue(
            hasattr(campaign, "validate_pmu_record"),
            "PMU record validator is missing",
        )
        required_record = self.required_pmu_record()
        campaign.validate_pmu_record(required_record, required=True)

        optional_unsupported = {
            "command_exit_status": 129,
            "events": [
                {
                    "event": "power/energy-pkg/",
                    "running_percentage": None,
                    "status": "unsupported",
                    "value": None,
                }
            ],
            "failure_reasons": [],
            "manifest_version": "xoas.target0-pmu-session.v1",
            "performance_claim": False,
            "required": False,
            "restored": True,
            "status": "unsupported",
        }
        campaign.validate_pmu_record(optional_unsupported, required=False)

        mutations = []
        nonunit_required = copy.deepcopy(required_record)
        nonunit_required["events"][0]["running_percentage"] = "99.99"
        mutations.append((nonunit_required, True))
        unsupported_required = copy.deepcopy(required_record)
        unsupported_required["events"][0].update(
            {
                "running_percentage": None,
                "status": "unsupported",
                "value": None,
            }
        )
        mutations.append((unsupported_required, True))
        estimated_optional = copy.deepcopy(optional_unsupported)
        estimated_optional["events"][0]["value"] = 1
        mutations.append((estimated_optional, False))
        successful_unsupported = copy.deepcopy(optional_unsupported)
        successful_unsupported["command_exit_status"] = 0
        mutations.append((successful_unsupported, False))

        for mutation, required in mutations:
            with self.subTest(mutation=mutation, required=required):
                with self.assertRaises(RuntimeError):
                    campaign.validate_pmu_record(
                        mutation,
                        required=required,
                    )

    def test_raw_inventory_is_bytewise_complete_and_rejects_symlinks(
        self,
    ) -> None:
        """An added, missing, reordered, or symlinked raw file must be visible."""
        campaign = load_campaign_module()
        self.assertTrue(
            hasattr(campaign, "build_raw_inventory"),
            "raw campaign inventory builder is missing",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            campaign_root = Path(temporary_directory)
            (campaign_root / "b").mkdir()
            (campaign_root / "a").mkdir()
            (campaign_root / "b/beta.txt").write_bytes(b"beta\n")
            (campaign_root / "a/alpha.txt").write_bytes(b"alpha\n")
            for excluded_name in (
                "acceptance.json",
                "campaign.json",
                "inventory.json",
                "rejection.json",
            ):
                (campaign_root / excluded_name).write_text(
                    "excluded\n",
                    encoding="utf-8",
                )

            inventory = campaign.build_raw_inventory(campaign_root)

            self.assertEqual(
                inventory,
                {
                    "file_count": 2,
                    "files": [
                        {
                            "path": "a/alpha.txt",
                            "sha256": (
                                "b6a98d9ce9a2d9149288fa3df42d377c"
                                "3e42737afdcdaf714e33c0a100b51060"
                            ),
                            "size_bytes": 6,
                        },
                        {
                            "path": "b/beta.txt",
                            "sha256": (
                                "f2c82decdd7181cf98945929a62598db7"
                                "e6b477e11f6e0eb0ae97020eff151ad"
                            ),
                            "size_bytes": 5,
                        },
                    ],
                    "manifest_version": (
                        "xoas.target0-campaign-raw-inventory.v1"
                    ),
                    "performance_claim": False,
                },
            )

            (campaign_root / "a/link.txt").symlink_to(
                campaign_root / "b/beta.txt"
            )
            with self.assertRaises(RuntimeError):
                campaign.build_raw_inventory(campaign_root)


if __name__ == "__main__":
    unittest.main()
