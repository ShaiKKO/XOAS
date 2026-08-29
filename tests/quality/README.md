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

The aggregate-contract test was separately observed red while `quality` remained
red, then passed only after every contract entry was green and every mapped
target was present.

## Verified local aggregate

The local development surface is:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target quality
cmake --preset dev-release
cmake --build --preset dev-release --target warnings
ctest --preset dev-release --output-on-failure
```

`quality` runs non-mutating format checks, Debug warnings, Clang-Tidy, Doxygen,
the complete Debug CTest suite, repository policy, and the isolated ASan/UBSan
preset.
The sanitizer sub-build uses
`build/dev-debug/quality-stamps/asan-ubsan.stamp`, whose dependencies are all
tracked files observed at configure time, to avoid a cross-preset build cycle.

The only approved quality-build cleanup command is:

```bash
cmake -DXOAS_REPOSITORY_ROOT="$PWD" \
  -P cmake/quality/CleanBuildTrees.cmake
```

It may remove only `build/dev-debug`, `build/dev-release`, and
`build/asan-ubsan` after resolving each path beneath the verified repository
root.
It refuses a redirected path and never removes the `build/` parent.

The clean candidate run under toolchain lock
`gpu-2-development-toolchain-v1-20260829t013505z` took 10.13 seconds for cleanup,
the Debug aggregate, Release warning build, and Release CTest sequence.
That duration is engineering-gate cost on the development host, not Target 0
performance evidence or a kernel-performance claim.
