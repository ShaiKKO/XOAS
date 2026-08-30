#!/usr/bin/env python3
"""Fresh-verify one finalized Target 0 qualification campaign."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from prepare_qualification_bundle import canonical_json_bytes
from qualification_campaign import CampaignError, verify_finalized_campaign


def parse_arguments(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the closed read-only campaign verification interface."""
    parser = argparse.ArgumentParser(
        description="Fresh-verify one finalized XOAS Target 0 campaign."
    )
    parser.add_argument("--campaign-directory", required=True, type=Path)
    parser.add_argument("--campaign-schema", required=True, type=Path)
    parser.add_argument("--process-schema", required=True, type=Path)
    parser.add_argument("--bundle-schema", required=True, type=Path)
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    """Emit only the compact accepted digest record on successful replay."""
    options = parse_arguments(arguments)
    try:
        acceptance = verify_finalized_campaign(
            options.campaign_directory,
            campaign_schema=options.campaign_schema,
            process_schema=options.process_schema,
            bundle_schema=options.bundle_schema,
        )
    except (CampaignError, OSError):
        print("qualification campaign verification failed", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(canonical_json_bytes(acceptance))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
