# CMake Quality Policy

This directory owns reusable CMake policy for XOAS engineering gates.
It must remain independent of future product-module semantics and search logic.

Public target names and their evidence contract are defined by
[`../../tests/quality/contracts/expected-gates.json`](../../tests/quality/contracts/expected-gates.json).
Checks operate on tracked paths and keep handwritten, generated, and vendored
classification explicit.

Required checks are non-mutating.
Developer convenience targets that rewrite files must be separate and may not be
used by hosted CI.
