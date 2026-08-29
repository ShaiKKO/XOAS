#!/usr/bin/env python3
"""Behavioral tests for Target 0 qualification-tool deployment bundles."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


def parse_arguments() -> argparse.Namespace:
    """Parse explicit fixture paths without consuming unittest options."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--example", required=True, type=Path)
    arguments, unittest_arguments = parser.parse_known_args()
    unittest.main_argv = [__file__, *unittest_arguments]
    return arguments


class PrepareQualificationBundleSchemaTest(unittest.TestCase):
    """Verify the closed retained bundle evidence contract."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load the real schema and its hand-authored positive instance."""
        if not ARGUMENTS.schema.is_file():
            raise AssertionError("bundle schema is missing")
        if not ARGUMENTS.example.is_file():
            raise AssertionError("bundle example is missing")
        cls.schema = json.loads(ARGUMENTS.schema.read_text(encoding="utf-8"))
        cls.example = json.loads(ARGUMENTS.example.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def test_schema_and_example_are_present(self) -> None:
        """Deployment evidence must have a schema and positive instance."""
        self.assertTrue(ARGUMENTS.schema.is_file(), "bundle schema is missing")
        self.assertTrue(ARGUMENTS.example.is_file(), "bundle example is missing")

    def test_example_is_a_valid_nonclaiming_passed_bundle(self) -> None:
        """The positive instance must demonstrate the complete passed shape."""
        self.validator.validate(self.example)
        self.assertEqual(
            self.example.get("manifest_version"),
            "xoas.target0-qualification-tool-bundle.v1",
        )
        self.assertIs(self.example.get("performance_claim"), False)
        self.assertEqual(self.example.get("status"), "passed")

    def test_example_retains_every_provenance_section(self) -> None:
        """A passed receipt cannot omit a load-bearing provenance category."""
        self.assertEqual(
            set(self.example),
            {
                "build",
                "bundle_id",
                "compatibility_tests",
                "created_at_utc",
                "elf",
                "manifest_version",
                "performance_claim",
                "provisioning_lock",
                "rejection_reasons",
                "repository",
                "runtime_dependencies",
                "sources",
                "status",
                "target_id",
                "toolchain",
            },
        )

    def test_schema_rejects_claims_and_unknown_fields(self) -> None:
        """A bundle cannot inflate its authority or extend the closed record."""
        claiming = copy.deepcopy(self.example)
        claiming["performance_claim"] = True
        extended = copy.deepcopy(self.example)
        extended["unreviewed_field"] = "not allowed"

        self.assertFalse(self.validator.is_valid(claiming))
        self.assertFalse(self.validator.is_valid(extended))

    def test_schema_rejects_malformed_digests(self) -> None:
        """Every retained SHA-256 must use one canonical lowercase spelling."""
        short_digest = copy.deepcopy(self.example)
        short_digest["sources"][0]["sha256"] = "abcd"
        uppercase_digest = copy.deepcopy(self.example)
        uppercase_digest["build"]["executable_sha256"] = "A" * 64

        self.assertFalse(self.validator.is_valid(short_digest))
        self.assertFalse(self.validator.is_valid(uppercase_digest))

    def test_schema_rejects_dirty_or_unconfirmed_builds(self) -> None:
        """Passed evidence requires a clean checkout and confirmed dual build."""
        dirty = copy.deepcopy(self.example)
        dirty["repository"]["tree_state"] = "dirty"
        unconfirmed = copy.deepcopy(self.example)
        unconfirmed["build"]["identical"] = False

        self.assertFalse(self.validator.is_valid(dirty))
        self.assertFalse(self.validator.is_valid(unconfirmed))

    def test_schema_rejects_passed_bundles_with_rejections(self) -> None:
        """A passed bundle cannot retain a contradictory rejection reason."""
        contradictory = copy.deepcopy(self.example)
        contradictory["rejection_reasons"] = ["build_failed"]

        self.assertFalse(self.validator.is_valid(contradictory))

    def test_schema_requires_dependency_hashes(self) -> None:
        """Every resolved runtime dependency must remain byte-authenticated."""
        unbound_dependency = copy.deepcopy(self.example)
        del unbound_dependency["runtime_dependencies"][0]["sha256"]

        self.assertFalse(self.validator.is_valid(unbound_dependency))

    def test_schema_rejects_unclosed_compatibility_results(self) -> None:
        """Compatibility checks cannot add an unreviewed outcome or field."""
        unclosed_status = copy.deepcopy(self.example)
        unclosed_status["compatibility_tests"][0]["status"] = "warning"
        unclosed_field = copy.deepcopy(self.example)
        unclosed_field["compatibility_tests"][0]["duration_ns"] = 1

        self.assertFalse(self.validator.is_valid(unclosed_status))
        self.assertFalse(self.validator.is_valid(unclosed_field))


ARGUMENTS = parse_arguments()


if __name__ == "__main__":
    unittest.main(argv=unittest.main_argv)
