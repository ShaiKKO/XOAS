#!/usr/bin/env python3
"""Independently verify one retained Target 0 qualification-tool bundle."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from prepare_qualification_bundle import (
    PreparationError,
    canonical_json_bytes,
    verify_finalized_bundle,
)


def parse_arguments(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the closed replica-verification interface."""
    parser = argparse.ArgumentParser(
        description="Verify a finalized XOAS Target 0 qualification-tool bundle."
    )
    parser.add_argument("--bundle-directory", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    """Recompute one bundle and emit only its accepted digest record."""
    options = parse_arguments(arguments)
    try:
        acceptance = verify_finalized_bundle(
            options.bundle_directory,
            options.schema,
        )
    except PreparationError:
        print("qualification bundle verification failed", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(canonical_json_bytes(acceptance))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
