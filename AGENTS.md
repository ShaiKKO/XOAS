# XOAS Engineering Agent Manual

## Scope and authority

This file applies to the entire repository. There are currently no nested `AGENTS.md` files.

This manual summarizes verified operating rules. It does **not** override approved architecture, numerical semantics, benchmark gates, or the controlling build plan.

## 1. Mission and success definition

XOAS builds an exact-instance, hardware-specific matrix-kernel synthesizer.

For one stable matrix-product instance, one exact target, one explicit numerical contract, and one reuse/tuning budget, the system must synthesize and empirically select the fastest verified compatible implementation it can find.

“Exact-instance specialization” means stable semantic facts become generated code and plan constraints. In Target 0, exact structural support of `A` may remove impossible products, index loads, traversal, and dispatch. Runtime values at structurally present coordinates remain dynamic.

A correct result requires all of the following independently:

- the requested semantics are represented without loss;
- structural facts are valid for every invocation covered by the plan;
- every required contribution is present exactly once unless an explicit reduction combines duplicates;
- transformations are legal in the active numerical mode;
- generated code passes an independent oracle outside the timed region;
- the artifact is compatible with the runtime target and contract;
- a safe fallback exists;
- any performance winner is supported by retained target measurements against the best applicable serious baseline.

Empirical target measurement is part of compilation because static models only prune and rank candidates. They do not select the winner.

## 2. Required reading and document precedence

Read these files before working:

1. [`docs/exact_instance_matrix_kernel_synthesizer_build_plan.md`](docs/exact_instance_matrix_kernel_synthesizer_build_plan.md) — controlling architecture, milestones, gates, IR model, Target 0, and research program.
2. [`docs/architecture/README.md`](docs/architecture/README.md) — actual architecture/decision/evidence inventory and approval state.
3. [`docs/architecture/000-charter.md`](docs/architecture/000-charter.md) — locked v0 claim, Target 0, numerical boundary, non-goals, and falsification.
4. [`docs/milestones/status.md`](docs/milestones/status.md) and the active milestone acceptance/implementation plan — canonical frontier, gate state, exact evidence, and current task contract.
5. For any source, tooling, CI, or review work: [`docs/engineering/coding-standards.md`](docs/engineering/coding-standards.md) and [`docs/adr/IDR-0001-engineering-quality-system.md`](docs/adr/IDR-0001-engineering-quality-system.md).
6. For benchmark, corpus, or performance work: [`docs/architecture/050-benchmark-protocol.md`](docs/architecture/050-benchmark-protocol.md), [`docs/experiments/baseline-matrix.md`](docs/experiments/baseline-matrix.md), and [`docs/experiments/corpus-policy.md`](docs/experiments/corpus-policy.md).
7. For research-claim work: [`docs/experiments/prior-art-matrix.md`](docs/experiments/prior-art-matrix.md).
8. For target/toolchain work: [`docs/architecture/proposals/AR-0001-target-0-host-qualification.md`](docs/architecture/proposals/AR-0001-target-0-host-qualification.md), [`docs/architecture/proposals/AR-0002-amd-target-baseline-admission.md`](docs/architecture/proposals/AR-0002-amd-target-baseline-admission.md), and the candidate/approved target manifest. AR-0001 Option 2 is approved: `gpu-2` is development-only, and the designated physical AMD Target 0 candidate must still be qualified. AR-0002 Option 1 is approved: AOCL-BLAS joins the admitted comparator set without removing existing applicable baselines.
9. [`docs/repository_discovery_and_project_understanding_report.md`](docs/repository_discovery_and_project_understanding_report.md) — point-in-time repository, host, toolchain, and evidence gaps; refresh drift-prone facts.
10. The nearest scoped `AGENTS.md` if nested instructions are added later.

Precedence:

1. User's latest explicit instruction.
2. Approved/locked specifications and approved architecture proposals.
3. The exact-instance build plan.
4. Scoped `AGENTS.md` instructions.
5. Accepted implementation plans and IDRs.
6. Existing code and tests as evidence, not authority over conflicting specifications.

If sources conflict, stop the affected work, quote the exact conflicting sections or interfaces, state the blocked and independent work, and use the change-control process below. Never resolve a semantic conflict silently.

## 3. Locked current scope and non-goals

Target 0 is:

- one exact x86-64 Linux target and hardware fingerprint;
- single-threaded;
- `float32` operands, accumulator, and result under the explicit active numerical mode;
- contiguous row-major `A`, `B`, and `C`;
- `C = A * B`, overwriting `C`;
- fixed `M`, `K`, and `N` per compiled plan;
- no aliasing among `A`, `B`, and `C`;
- exact compile-time structural support of `A`;
- runtime-dynamic values at present positions of `A`;
- dense runtime-dynamic `B`;
- repeated execution so tuning can be amortized;
- generated C++ and Clang AOT before lower-level/JIT backends;
- comparison with every applicable serious baseline.

Do not introduce before the controlling gates and an approved proposal:

- GPU code generation;
- multithreading, NUMA, or distributed execution;
- dynamic sparsity;
- mixed precision or approximation;
- arbitrary tensor contraction or general BLAS replacement;
- reinforcement learning or learned search;
- unrestricted Strassen-like/AlphaTensor discovery;
- custom MLIR dialect;
- remote compilation service;
- production JIT expansion.

The primary development server's NVIDIA hardware does not change Target 0.

The initial benchmark envelope is `M,K` from 4 to 256, `N` from 1 to 64, densities approximately 0.5% to 40%, synthetic and real random/banded/diagonal/block/repeated-row/power-law/mixed patterns, and expected invocation counts from `10^3` through `10^9`. These are corpus ranges, not API limits; family admission is controlled by estimated work, code size, and search budget.

## 4. Repository map

### Paths that exist

- `AGENTS.md` — this repository-wide operating manual.
- `docs/exact_instance_matrix_kernel_synthesizer_build_plan.md` — controlling program.
- `docs/repository_discovery_and_project_understanding_report.md` — discovery evidence snapshot.
- `docs/architecture/README.md` — architecture, decision, and evidence index.
- `docs/architecture/000-charter.md` — locked Target 0 product/research charter.
- `docs/architecture/050-benchmark-protocol.md` — locked v1 benchmark and evidence protocol.
- `docs/architecture/proposals/AR-0001-target-0-host-qualification.md` — approved primary-development designation and physical AMD replacement-host candidacy.
- `docs/architecture/proposals/AR-0002-amd-target-baseline-admission.md` — approved AOCL-BLAS admission decision for the physical AMD target.
- `docs/engineering/coding-standards.md` — approved LLVM-derived source, documentation, enforcement, and review contract.
- `docs/adr/IDR-0001-engineering-quality-system.md` — accepted engineering-quality design and staged implementation decision.
- `CMakeLists.txt` and `CMakePresets.json` — quality-only C++23 build, test, and sanitizer surface; they do not contain product modules.
- `.clang-format`, `.clang-tidy`, `.editorconfig`, and `Doxyfile.in` — pinned first-party formatting, static-analysis, editor, and documentation policy.
- `cmake/quality/` — reusable non-product quality checks, aggregate orchestration, and bounded cleanup.
- `tests/quality/` — positive/negative policy fixtures, closed quality contract, and CTest registrations; it is not a product test suite.
- `.github/workflows/quality.yml` — SHA-pinned GitHub-hosted enforcement with five required jobs.
- `toolchains/github-actions-v1.lock.json` — exact hosted action, runner, archive, and package lock.
- `docs/engineering/main-branch-protection-v1.json` and its adjacent request file — schema-valid live protection evidence, exact mutation body, and reversal.
- `tools/ci/install-locked-toolchain.sh` — ephemeral hosted-runner installer; do not run it on a persistent host as a convenience command.
- `docs/toolchain/gpu-2-development-toolchain-v1.md` — verified non-secret development-toolchain provenance, rollback, executable identities, and behavioral evidence.
- `toolchains/gpu-2-development-toolchain-v1.lock.json` — exact installed package closure and executable/probe identity; `build_ready=true` applies only to development.
- `docs/experiments/prior-art-matrix.md` — required and direct-comparator capability review.
- `docs/experiments/baseline-matrix.md` — baseline admission/configuration/cost policy.
- `docs/experiments/corpus-policy.md` — deterministic corpus generation, normalization, partition, and holdout policy.
- `docs/milestones/M0-implementation-plan.md` — executable M0 plan and commit boundaries.
- `docs/milestones/M0-acceptance.md` — open M0 evidence/gap record.
- `docs/milestones/status.md` — canonical frontier ledger.
- `docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md` — written, unexecuted physical-host qualification and baseline-provisioning plan.
- `benchmarks/manifests/` — synthetic result example, frozen synthetic/application/holdout corpus manifests, and the historical unqualified `gpu-2` candidate-target capture. AR-0001 Option 2 excludes that host from current Target 0 measurement authority. The directory contains no executable harness or measured performance result.
- `schemas/benchmark-result-v1.schema.json` — draft-2020-12 result/evidence schema; schema and synthetic example fully validated on `gpu-2`.
- `schemas/development-toolchain-v1.schema.json` — draft-2020-12 installed development-toolchain evidence schema.

There is currently no product source/public include tree, product library or executable, independent oracle, executable benchmark harness, database, artifact store, repository README, or product dependency manifest.
The existing build and test tree enforces engineering quality only.

### Planned paths

The directory tree in build-plan section 12 is planned, not implemented. Create only the paths required by the current approved milestone. Do not scaffold every future subsystem.

Expected future ownership, when those modules are authorized and created:

- `matmul-core`: semantic types, canonical encoding, target and diagnostics; no search or codegen.
- `matmul-ir`: IR definitions, controlled builders/verifiers, serialization, and printers.
- `matmul-analyze`: exact support, contribution graph, structural statistics, motifs, and eligibility.
- `matmul-discover`: transformations, search, pruning, empirical planning, and provenance.
- `matmul-codegen`: inspectable source/IR emission, compiler driver, objects, disassembly, loading.
- `matmul-bench`: independent oracle, baselines, inputs, measurement, counters, and statistics.
- `matmul-runtime`: compatible plan lookup, contract checks, scratch, invocation, and fallback.
- `matmul-db`: experiment/plan records and content-addressed artifacts.

Update this map only when actual paths and interfaces exist.

## 5. Architecture and IR boundaries

Keep these levels explicit:

- **Problem IR**: requested operation and all stable semantic facts. It contains no schedule, sparse-format, or codegen decision.
- **Structure IR**: exact support, legal contribution graph, structural statistics, and verified region decompositions.
- **Reduction IR**: conventional arithmetic after structural elimination—loads, multiplies/FMAs, reductions, vector forms, temporaries, and stores. It does not add distributive factorizations.
- **Bilinear IR**: later exact alternative-algorithm/tensor-decomposition search. It is not a Target 0 prerequisite.
- **Schedule IR**: one complete, serializable mapping of a selected arithmetic program to traversal, grouping, tiles, vectors, unrolling, packing, prefetching, tails, scratch, and ISA features.
- **Machine IR/artifacts**: generated C++ first, compiler command, object/shared artifact, metadata, and disassembly. These are retained review/test artifacts.

Each level needs named invariants and verification. Do not put semantics, legality, search policy, schedule, and emission into one generic graph or compiler file.

Structural optimization and algebraic optimization are separate pipelines with separate proof obligations.

## 6. Build and development environment

### Current verified state

The repository has a verified quality-only CMake build and test system but no product code.
Its targets validate policy fixtures and future first-party source; they do not build a synthesizer or benchmark executable.

The primary Linux development server is `gpu-2`, Ubuntu 24.04.4 LTS on x86-64 KVM/OpenStack. AR-0001 Option 2 makes it development-only; it is not the Target 0 measurement host. Access credentials and network coordinates are external secrets and must never be committed.

The fresh M0 capture at `2026-08-28T23:01:51Z` records `gpu-2` in `benchmarks/manifests/target-gpu-2-candidate.json`. Its development toolchain was verified at `2026-08-29T02:40:39Z`: versioned Clang/LLVM 21.1.8, GCC/G++ 13.3.0, CMake 3.28.3, Ninja 1.11.1, Doxygen 1.9.8, Graphviz, SQLite, `pkg-config`, ShellCheck, the pinned JSON Schema validator, PyYAML, Git 2.43.0, and Python 3.12.3 are installed. The exact 102-package closure, eight LLVM entry-package holds, 18 executable hashes, and ten behavior probes are bound by `toolchains/gpu-2-development-toolchain-v1.lock.json` under configuration SHA-256 `bf49239db2f78403ee592c1d1ddfaebdd7d9597433b6d39bbcfc7d0c4427347a`.

`build_ready=true` means the primary development toolchain passed its provisioning probes; it is not a product-build, quality-enforcement, baseline, or measurement claim. OpenBLAS, oneMKL, and LIBXSMM remain absent. PMU cycles/instructions remain unavailable to the unprivileged guest. Do not treat `gpu-2` as measurement-qualified.

The local Apple M4/macOS machine is not valid for Target 0 performance evidence.

### Commands currently verified

The following repository-inspection commands are verified in the local primary checkout. Do not infer that every local utility is installed on `gpu-2`:

```bash
git status --short --branch
git branch --show-current
git remote -v
git worktree list --porcelain
rg --files -uu -g '!.git/**'
git diff --check
python3 -m json.tool schemas/benchmark-result-v1.schema.json >/dev/null
python3 -m json.tool schemas/development-toolchain-v1.schema.json >/dev/null
python3 -m json.tool toolchains/gpu-2-development-toolchain-v1.lock.json >/dev/null
find benchmarks/manifests -name '*.json' -print0 | xargs -0 -n1 python3 -m json.tool >/dev/null
```

On `gpu-2`, the following version checks are verified:

```bash
clang-21 --version
clang++-21 --version
clang-format-21 --version
clang-tidy-21 --version
clangd-21 --version
ld.lld-21 --version
cmake --version
ninja --version
doxygen --version
pkg-config --version
sqlite3 --version
shellcheck --version
python3 --version
git --version
```

`ripgrep` is not installed on `gpu-2` and was outside the approved development-toolchain lock. Use `git ls-files`, `find`, or `grep` there when `rg` is unavailable; add packages only through a reviewed toolchain update.

Run full schema and toolchain-lock validation from the repository root on `gpu-2`:

```bash
python3 - <<'PY'
import hashlib
import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

checks = (
    (
        Path("schemas/benchmark-result-v1.schema.json"),
        Path("benchmarks/manifests/benchmark-result-v1.example.json"),
    ),
    (
        Path("schemas/development-toolchain-v1.schema.json"),
        Path("toolchains/gpu-2-development-toolchain-v1.lock.json"),
    ),
)
for schema_path, instance_path in checks:
    schema = json.loads(schema_path.read_text())
    instance = json.loads(instance_path.read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(
        schema, format_checker=FormatChecker()
    ).validate(instance)
lock = json.loads(checks[1][1].read_text())
assert lock["state"] == "installed_verified"
assert lock["build_ready"] is True
assert lock["target0_measurement_qualified"] is False
assert len(lock["installed_package_closure"]) == 102
assert len(lock["expected_binaries"]) == 18
assert all(item["result"] == "passed" for item in lock["validations"])
configuration = {
    "manifest_version": lock["manifest_version"],
    "host": lock["host"],
    "archive": {
        key: value
        for key, value in lock["archive"].items()
        if key != "apt_refreshed_at_utc"
    },
    "requested_packages": lock["requested_packages"],
    "expected_binaries": [item["name"] for item in lock["expected_binaries"]],
    "validations": [item["name"] for item in lock["validations"]],
}
configuration_bytes = json.dumps(
    configuration, sort_keys=True, separators=(",", ":"), ensure_ascii=True
).encode("ascii")
assert hashlib.sha256(configuration_bytes).hexdigest() == lock["configuration_sha256"]
closure_bytes = (
    json.dumps(lock["installed_package_closure"], indent=2, ensure_ascii=True)
    + "\n"
).encode()
assert hashlib.sha256(closure_bytes).hexdigest() == lock["installation"][
    "installed_package_closure_sha256"
]
for package in lock["installed_package_closure"]:
    actual = subprocess.run(
        [
            "dpkg-query",
            "-W",
            "-f=${Version}\t${Architecture}\n",
            package["name"],
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip("\n")
    assert actual == f'{package["version"]}\t{package["architecture"]}'
for binary in lock["expected_binaries"]:
    assert hashlib.sha256(Path(binary["path"]).read_bytes()).hexdigest() == binary[
        "sha256"
    ]
holds = subprocess.run(
    ["apt-mark", "showhold"], check=True, capture_output=True, text=True
).stdout.splitlines()
assert holds == lock["installation"]["holds"]
PY
```

The one-time provisioning probe configured a temporary CMake 3.28 project with `/usr/bin/clang++-21` and Ninja, built it, and passed CTest.
The repository quality project now provides the persistent verified commands below.

These are inspection, document/schema, and development-toolchain commands, not a product verification suite. The M0 plan and acceptance record contain the exact cross-manifest assertions and source-hash checks used for their checkpoint.

The immutable provisioning capture recorded `kernel.yama.ptrace_scope=2` and therefore isolated LeakSanitizer with `detect_leaks=0`. The user later approved `/etc/sysctl.d/90-xoas-lsan.conf` (SHA-256 `d36ae5ec5e8d2cbdf78a80b7b076629b7d71164e8bab7993be7aac4006b97188`) setting `kernel.yama.ptrace_scope = 1` on `gpu-2`. The persistent sanitizer gate must keep `detect_leaks=1`, verify that exact live host setting, and report this weaker development-host ptrace posture. This does not qualify `gpu-2` for Target 0 measurement.

### Verified repository quality commands

Run these commands from the repository root on `gpu-2`.
The presets require the exact versioned tools recorded by the development lock.

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target warnings
ctest --preset dev-debug --output-on-failure

cmake --preset dev-release
cmake --build --preset dev-release --target warnings
ctest --preset dev-release --output-on-failure

cmake --preset asan-ubsan
cmake --build --preset asan-ubsan --target asan-ubsan
ctest --preset asan-ubsan -R '^quality-sanitizer-' --output-on-failure
```

The stable non-mutating quality targets are:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target format-check
cmake --build --preset dev-debug --target tidy
cmake --build --preset dev-debug --target docs-check
cmake --build --preset dev-debug --target repository-policy
cmake --build --preset dev-debug --target quality
```

`quality` includes formatting, Debug warnings, Clang-Tidy, Doxygen, the complete
Debug CTest suite, repository policy, and the isolated ASan/UBSan preset.
The rewriting `format` target is developer-only and must be invoked deliberately;
hosted CI uses `format-check` and never rewrites source.

The only approved quality-build cleanup command is:

```bash
cmake -DXOAS_REPOSITORY_ROOT="$PWD" \
  -P cmake/quality/CleanBuildTrees.cmake
```

It may remove only `build/dev-debug`, `build/dev-release`, and
`build/asan-ubsan` after resolving them below the verified repository root.
It refuses redirected paths and never removes the `build/` parent.

### Required future toolchain direction

The build plan selects C++23, CMake, Ninja, and Clang as the initial core toolchain; Python is limited to corpus generation, orchestration, plotting, and report assembly. Semantic compiler logic must not exist only in Python.

M1 must extend this quality-only surface rather than bypass it when product modules are authorized.
Add product-specific targets and tests only with exact verified commands and the controlling milestone contract.

### Approved quality-system direction

[`docs/engineering/coding-standards.md`](docs/engineering/coding-standards.md) is mandatory for new first-party code.
It requires standards-safe LLVM-derived naming, `///` Doxygen blocks for files/non-trivial classes/public interfaces, rare rationale-focused `//` comments, distinct handwritten/generated/vendor policies, pinned Clang-native checks, sanitizers, protected-main CI, and narrow justified suppressions.

The design is implemented locally and in pinned GitHub-hosted CI.
Protected `main` requires `repository-policy`, `static-quality`,
`debug-build-and-test`, `release-build-and-test`, and `sanitizers`, each bound
to GitHub Actions App ID `15368`.
The exact protection evidence and reversal are retained in
`docs/engineering/main-branch-protection-v1.json`.
The exceptions/RTTI policy is deliberately deferred to a separate M1 IDR.

## 7. Test commands and taxonomy

### Current command registry

The executable quality harness exists under `tests/quality/` and runs through
the Debug, Release, and sanitizer commands in section 6.
It covers formatting, warnings, Clang-Tidy, documentation, repository policy,
aggregate wiring, cleanup boundaries, hosted-workflow policy, and the live
branch-protection evidence contract with positive and isolated negative probes.

Product unit, property, differential, numerical-semantic, generated-kernel,
artifact/serialization, regression, and benchmark-smoke suites remain
**unavailable** because no product implementation is authorized or present.

A successful no-op or missing-test invocation is not evidence. The change that introduces each harness must add its exact invocation here and to the relevant acceptance record.

Quality tests do not qualify product behavior or performance.
Use `ctest --preset dev-debug -N` to inspect the registered quality inventory;
do not convert the absence of product tests into a passing product claim.

### Required taxonomy

- **Unit tests**: schemas, canonicalization, IR verifiers, target features, cost features, and local utilities.
- **Property tests**: structural and algebraic properties, coordinate canonicalization, identity/diagonal/permutation/block fixtures, and invalid duplicates.
- **Differential tests**: every generated plan versus an independent reference over deterministic seeds and edge cases.
- **Numerical-semantic tests**: strict/contracted behavior, NaNs, infinities, signed zeros, subnormals, cancellation, and magnitude extremes.
- **Code-generation tests**: generated source/IR goldens, compiler diagnostics, ABI invocation, guard pages, and selected stable assembly properties.
- **Artifact/serialization tests**: round trips, deterministic bytes, digest sensitivity, provenance, compatibility rejection, and invalidation.
- **Regression tests**: minimized correctness, compiler, replay, and performance incidents with retained seeds/artifacts.
- **Benchmark smoke tests**: harness mechanics only; noisy timing values are not ordinary unit-test pass/fail gates.

### Mandatory suites by change class

- Documentation-only: `repository-policy`, `docs-check`, relevant CTest policy checks, `git diff --check`, and status consistency.
- Semantic/core/schema: unit + property + round-trip/hash-stability + invalid-input tests.
- Structure/transform: unit + positive/negative legality + coverage/duplicate checks + differential + numerical tests.
- Codegen/compiler driver: all preceding suites + generated artifact inspection + ABI/load + guard-page tests.
- Runtime/cache: serialization/compatibility/invalidation + fallback + regression tests.
- Performance claim: all correctness gates first, then the controlled benchmark protocol and retained raw evidence.

Every C++ or quality-infrastructure change runs the Debug `quality` aggregate,
the Release warning build and CTest suite, and its targeted red/green evidence.
Generated source is owned by its generator and must regenerate deterministically.
Vendored source remains isolated under an approved classification; a new
generated or vendor root requires a reviewed standard/IDR update.

## 8. Numerical and correctness rules

- Structural zero means guaranteed absent for every invocation of the plan. A runtime numerical zero may change and cannot be removed without a guard.
- `A`, `B`, and `C` are disjoint in Target 0. Any changed aliasing contract requires architecture approval and identity/ABI review.
- `strict`: preserve specified reduction order; no reassociation, distributive factoring, or implicit FMA unless reference semantics include it.
- `contracted`: FMA contraction may be permitted; reduction grouping otherwise remains fixed. Lock exact special-value behavior before implementation.
- `reassociate`: explicit opt-in only, with mathematical equivalence and floating-point error evidence.
- `bounded_error`: requires a configured bound and analyzer certificate.
- `approximate`: later and outside Target 0.
- Never enable global fast-math as an accidental numerical policy.
- Algebraic equality over reals does not prove IEEE-754 equivalence. For example, `a*b + a*c -> a*(b+c)` is illegal unless the active mode permits it and obligations close.
- Every transformation rule names legal modes, structural/aliasing preconditions, proof or verification obligation, and expected work/search effect.
- Region plans prove complete, duplicate-free contribution coverage.
- Correctness checks run outside timed benchmark regions against an independent oracle.
- Report bitwise equality where required and ULP, absolute/relative, and normwise error where permitted. Retain the failing seed and complete instance digest.

## 9. Benchmark and evidence protocol

[`docs/architecture/050-benchmark-protocol.md`](docs/architecture/050-benchmark-protocol.md) is the controlling v1 workflow and statistical contract. [`docs/experiments/baseline-matrix.md`](docs/experiments/baseline-matrix.md) controls baseline admission/configuration and cost accounting. No performance claim is accepted without a schema-valid versioned manifest and retained raw samples.

Before broadening the system, the proof gate requires at least one pre-registered nontrivial workload at least 2x faster than the best applicable generic baseline. Target 0 product-class success additionally requires at least 1.5x geometric-mean speedup on the pre-registered target subset and at least 2x on one real or application-derived structure. These are research gates, not promised outcomes. A failed gate produces a written no-go or explicitly approved narrower claim; it does not authorize silent scope expansion.

The Target 0 workflow must:

1. validate candidate correctness and compatibility before timing;
2. bind the process/thread to a selected core;
3. capture CPU/ISA/cache/topology, virtualization, kernel, microcode, compiler, libraries, and observable frequency/power state;
4. warm code and data deliberately;
5. calibrate iterations so timer overhead is negligible;
6. randomize or interleave candidate and baseline order;
7. consume a checksum to prevent dead-code elimination;
8. retain every raw sample and sample ordering;
9. repeat after process restart and, for gate evidence, system reboot;
10. record median, dispersion, sample count, and the confidence/noise rule used to select or reject a winner;
11. collect at least cycles and instructions, plus cache/branch/stall/vector evidence where the qualified host exposes trustworthy counters;
12. retain failed, tied, losing, and regressed experiments when analytically useful.

Admitted baseline families are the independent scalar oracle/fallback,
compiler-optimized dense C++ fallback, OpenBLAS dense SGEMM, AOCL-BLAS dense
SGEMM on admitted AMD targets, oneMKL dense and Sparse BLAS when installed and
applicable, inspector/executor CSR and alternative traversal paths, and
LIBXSMM dense/generated paths when installed and applicable. Always compare
with the fastest correct admitted configuration that passes the protocol.
Never compare only with a naive loop.

Report analysis, search, compile, and tuning time; generated code size; scratch/prepack requirements; kernel and fallback time; speedup; variability; and break-even invocation count.

Use:

`analysis + search + compilation + expected_invocations * execution_time`

for lifecycle comparison. Never deploy a generated plan that loses to the measured fallback.

The v1 protocol fixes smoke at one process/five rounds, search at three fresh processes/fifteen rounds, and gate evidence at two reboot-separated campaigns with five processes per campaign and thirty rounds per process. Use deterministic paired interleaving, the median of process medians, MAD/IQR, and the specified two-level 10,000-replicate percentile bootstrap. A winner requires the speedup confidence-interval lower bound above `1.02`; otherwise report a tie. The proof workload requires a lower bound of at least `2.0`; product-class evidence requires a geometric-mean lower bound of at least `1.5` plus one application-derived case at least `2.0`.

Pre-register target and holdout subsets before milestone claims. Do not delete timing outliers based on duration; invalidate a whole process only for the objective failures named by the protocol. The current `gpu-2` candidate cannot provide the build-plan-minimum cycles/instructions evidence and is not a qualified measurement target.

## 10. Canonical identity and artifact rules

A plan/cache identity must include every semantic or compatibility input:

- operation and output semantics;
- shapes and scalar/accumulator/output types;
- layouts, strides, alignment, and aliasing;
- exact support and stable values;
- numerical contract;
- target triple, ISA set, and hardware fingerprint;
- compiler version/configuration;
- transform-rule, search-space, and code-generation versions.

Canonicalize first with a versioned binary encoding, then compute a stable 256-bit digest. Human-readable YAML/JSON is for inspection and tests, not the canonical identity.

Retain, content-address, and bind together:

- canonical problem and selected plan;
- transform/search provenance;
- generated source or lower-level IR;
- exact compiler command/version;
- object/shared artifact and digest;
- metadata and disassembly;
- verification record;
- raw measurements/statistics;
- compatibility constraints;
- fallback;
- prepacked data and scratch metadata;
- rejection/selection reason.

Runtime cache hits validate compatibility and execute a previously verified artifact without discovery. Stale or incompatible artifacts must fail closed to the fallback.

Never hand-edit a generated artifact; change the generator and regenerate.

## 11. Engineering workflow

For every change:

1. Identify the controlling requirement, milestone, and gate.
2. Read the current frontier and scoped decisions.
3. Define the task contract, inputs/outputs, dependencies, acceptance evidence, and non-goals.
4. Escalate semantic or architectural conflicts before coding.
5. Write or identify the failing test/evidence check.
6. Implement the smallest correct change within the approved milestone.
7. Run the mandatory verification for the change class.
8. Inspect generated source/object/disassembly when applicable.
9. Benchmark only after correctness, legality, coverage, and compatibility close.
10. Update documentation, schemas, evidence, and the milestone ledger.
11. Obtain implementation-quality and independent review appropriate to risk.
12. Record the exact tested commit and dirty/clean state.

Before a multi-step coding slice, write a task-level implementation plan with exact files, interfaces, tests, commands, evidence, dependencies, and commit boundaries. Do not begin broad implementation directly from the build plan.

## 12. Task ownership and subagent coordination

Every delegated task has:

- exactly one owner;
- an explicit primary-checkout, task-branch, or shared-branch policy;
- a precise contract and controlling requirement;
- explicit inputs and outputs;
- explicit non-goals;
- dependency declarations;
- a review path;
- an evidence/acceptance path;
- an integration owner.

The head engineering agent owns integration and reconciliation against controlling documents. Do not give multiple agents overlapping architectural or file ownership without one integration owner and ordered handoffs.

Work in the primary checkout by default for the current greenfield stage. Use a linked worktree only when isolation is genuinely required—for example, concurrent overlapping implementation streams, a long-lived risky experiment, or a release/maintenance branch that cannot safely share the checkout. Do not create worktrees as routine ceremony.

Agents must not make architecture decisions on behalf of the integration owner, rewrite unrelated dirty work, or claim a milestone gate from their subtask. The integration owner reviews exact diffs, verification evidence, generated artifacts, and dependency assumptions before integration.

## 13. Change control

### Architecture proposals

Use `docs/architecture/proposals/AR-####-short-title.md` for material semantic or architecture changes. `AR-0001` exists; allocate the next unused number.

Each proposal includes:

- requested decision;
- affected specification sections, interfaces, and milestones;
- concrete evidence;
- alternatives considered;
- recommended option;
- correctness and numerical impact;
- ABI, identity, cache, artifact, and migration impact;
- benchmark and performance-gate impact;
- blocked work;
- independent work that may continue.

Approval is required before changing Target 0, numerical semantics, public ABI, canonical identity/invalidation, IR ownership boundaries, exact-support meaning, fallback requirements, benchmark methodology/gates, milestone proof order, provenance, or compatibility validation.

### Implementation decisions

Use `docs/adr/IDR-####-short-title.md` for durable semantics-neutral implementation decisions. `IDR-0001` exists; allocate the next unused number.

An IDR records context, decision, alternatives, consequences, affected files/interfaces, verification, and reversal/migration path. It must not be used to smuggle in an architectural change.

## 14. Git and commit discipline

- Inspect branch, HEAD, worktrees, remotes, and dirty state before work.
- `main` is the published integration branch and tracks `origin/main`. The discovery report's unborn-repository statement is historical snapshot evidence, not current state.
- Work in the primary checkout by default, but protected `main` now makes a bounded `milestone/mN-short-name` or `task/mN-short-name` branch and pull request the normal integration path. A linked worktree still requires a concrete isolation need.
- Normal scoped commits, task-branch pushes, pull requests, and green-check merges are part of the authorized engineering workflow. Review and verify exact staged paths before committing.
- `main` is live-protected with administrator enforcement, linear history, the five App-bound quality checks, a pull-request path, conversation resolution, and force-push/deletion prohibitions. Do not use an administrative bypass without explicit authority for that bypass.
- Preserve all user and agent work. Never reset, clean, checkout over, or delete unrelated changes.
- Do not broadly stage. Stage exact reviewed paths.
- Keep commits single-purpose and bind acceptance claims to exact commits.
- Do not commit `.DS_Store`, credentials, private keys, public server coordinates, build caches, or unowned temporary output.
- Generated source, objects, disassembly, and benchmark data follow the retention policy established by the relevant milestone. Do not discard useful failures; do not put large binary evidence in Git without an approved storage policy.
- Do not hand-edit generated files.
- Do not force-push, rewrite published history, merge unrelated branches, tag, or create a release without explicit authority for that operation.
- If the worktree is dirty, map ownership before editing overlapping files and report the residual state at handoff.
- No completion or gate claim is valid without the exact tested commit and its clean/dirty state.

## 15. Definition of done

Compilation alone is never done.

### Documentation/research task

- controlling requirement covered;
- claims trace to sources/evidence;
- conflicts and unknowns are explicit;
- links and paths resolve;
- no unresolved placeholders;
- required review and ledger update complete;
- exact diff and commit state reported.

### Semantic/IR task

- invariants specified;
- invalid inputs rejected diagnostically;
- canonical/serialization effects evaluated;
- unit, property, round-trip, and negative tests pass;
- independent review finds no contract deviation.

### Transformation/codegen task

- legality and numerical modes explicit;
- coverage/duplicate proof passes;
- differential/numerical/guard tests pass;
- generated source/object/disassembly inspected and retained;
- target compatibility and fallback behavior verified;
- replay/provenance evidence complete.

### Performance task

- all correctness gates closed first;
- serious baselines configured and identified;
- protocol and environment controls satisfied;
- raw samples and statistics retained;
- code size and lifecycle/break-even costs reported;
- exact target and commit bound;
- ties, failures, and regressions included;
- independent benchmark review complete.

### Milestone gate

- every exit criterion has evidence;
- an acceptance record names exact commits/artifacts/results;
- unresolved deviations are approved or the gate remains open;
- the milestone ledger records a go, no-go, or scope-narrowing decision.

## 16. Current frontier

Read and update [`docs/milestones/status.md`](docs/milestones/status.md).

Current frontier: M0 is in progress and its gate is open. Its charter, prior-art/baseline policies, benchmark protocol/schema, frozen corpus manifests, historical candidate-host capture, approved engineering-quality design, and target-host decision exist. AR-0001 Option 2 designates `gpu-2` as development-only; a physical AMD Ryzen 9 7900X Linux host is the designated replacement candidate but remains unqualified. AR-0002 Option 1 is approved, adding AOCL-BLAS without removing existing applicable comparators. No product implementation begins before M0 closes.

The written engineering-quality specification is implemented and enforced.
The development-toolchain plan and the local/hosted quality-gates plan have
been executed; stable targets, pinned hosted jobs, and protected-main controls
are repository capabilities with retained evidence.

The M0 critical path is review and execution of the written physical AMD
Target 0 qualification plan. Baseline installation, measurement controls, PMU
evidence, noise checks, and target-bound benchmark evidence belong on that
selected measurement host. Obtain the required independent review or explicit
review-model acceptance and update the acceptance record before M0 closes. Do
not begin M1 product scaffolding to bypass these blockers.

Do not embed percentage estimates. Record states, exact commits, evidence, deviations, and gates.

## 17. Explicit prohibitions

- Do not widen Target 0 silently.
- Do not compare only with a naive baseline.
- Do not benchmark an unverified candidate.
- Do not treat numerical zeros as structural zeros.
- Do not discard losing or failed evidence needed for analysis.
- Do not hand-edit generated artifacts without changing the generator.
- Do not collapse IR layers to shortcut implementation.
- Do not claim gate closure without exact commit and evidence.
- Do not hide architecture changes in ordinary code review, comments, or commits.
- Do not use C++ reserved implementation identifiers such as names containing `__`.
- Do not merge narrative comments, commented-out code, bare debt markers, or broad unexplained lint/format suppressions.
- Do not infer floating-point equivalence from real-number algebra.
- Do not let a static cost model declare the winner.
- Do not execute an incompatible or stale cached plan.
- Do not remove the fallback.
- Do not start Bilinear IR, RL, GPU, multithreading, custom MLIR, or JIT work before their proof dependencies and approvals.
- Do not create broad framework scaffolding in place of the earliest falsifiable milestone.
