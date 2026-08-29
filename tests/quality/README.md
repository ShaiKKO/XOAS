# Quality Harness

This directory owns executable evidence for XOAS's engineering-quality gates.
It is infrastructure-only and must not acquire product or compiler semantics.

## Source classifications

The classifications are closed for the initial quality system:

- Handwritten: `include/`, `src/`, `tests/` except classified fixtures,
  `cmake/`, and `tools/`.
- Generated: `tests/quality/fixtures/generated/output/` only.
- Vendored: `tests/quality/fixtures/vendor/` only.

A filename, comment, or build property cannot reclassify first-party source.
A future generated or vendored root requires an accepted IDR or a reviewed
update to the normative coding standard.

## Initial red evidence

At the quality-contract checkpoint, `cmake --preset dev-debug` configured
successfully on `gpu-2` while
`cmake --build --preset dev-debug --target quality` failed with Ninja's
`unknown target 'quality'` diagnostic.
That failure is intentional evidence that the aggregate gate did not exist
before its implementations.

Each later gate must retain a positive fixture and an isolated negative fixture
that proves intended rejection without mutating the source tree.
