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
2. [`docs/milestones/status.md`](docs/milestones/status.md) — canonical current frontier and gate state.
3. [`docs/repository_discovery_and_project_understanding_report.md`](docs/repository_discovery_and_project_understanding_report.md) — point-in-time repository, host, toolchain, and evidence gaps.
4. Any approved architecture proposal, specification, milestone acceptance record, implementation plan, or IDR that scopes the task. These paths will be added to the architecture index when M0 establishes it.
5. The nearest scoped `AGENTS.md` if nested instructions are added later.

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
- `docs/milestones/status.md` — canonical frontier ledger.

There is currently no source, public include tree, build system, test tree, benchmark tree, schema, database, artifact store, script, README, or dependency manifest.

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

The repository has no build system or product code. Therefore no configure, build, format, lint, static-analysis, sanitizer, benchmark, or generated-artifact cleanup command exists yet.

The primary Linux development server is `gpu-2`, Ubuntu 24.04.4 LTS on x86-64 KVM/OpenStack. It is a development host and only a candidate measurement host until Target 0 qualification closes. Access credentials and network coordinates are external secrets and must never be committed.

At the discovery snapshot, `gpu-2` has Git 2.43.0 and Python 3.12.3, but lacks CMake, Ninja, GCC/G++, Clang/Clang++, SQLite development tooling, `pkg-config`, and detected BLAS packages. Do not claim the host is build-ready until provisioning is approved, performed, and recorded.

The local Apple M4/macOS machine is not valid for Target 0 performance evidence.

### Commands currently verified

```bash
git status --short --branch
git branch --show-current
git remote -v
git worktree list --porcelain
rg --files -uu -g '!.git/**'
```

These are inspection commands, not a product verification suite.

### Required future toolchain direction

The build plan selects C++23, CMake, Ninja, and Clang as the initial core toolchain; Python is limited to corpus generation, orchestration, plotting, and report assembly. Semantic compiler logic must not exist only in Python.

When M1 creates the build system, add the exact version floors, install provenance, configure presets, build commands, formatting, lint/static analysis, sanitizers, and safe cleanup commands here in the same change. Until then, do not invent or copy generic CMake commands.

## 7. Test commands and taxonomy

### Current command registry

No test harness or executable exists. Unit, property, differential, numerical, code-generation, artifact/serialization, regression, and benchmark-smoke commands are currently **unavailable**.

A successful no-op or missing-test invocation is not evidence. The change that introduces each harness must add its exact invocation here and to the relevant acceptance record.

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

- Documentation-only: link/path check, placeholder/conflict scan, `git diff --check`, and status consistency.
- Semantic/core/schema: unit + property + round-trip/hash-stability + invalid-input tests.
- Structure/transform: unit + positive/negative legality + coverage/duplicate checks + differential + numerical tests.
- Codegen/compiler driver: all preceding suites + generated artifact inspection + ABI/load + guard-page tests.
- Runtime/cache: serialization/compatibility/invalidation + fallback + regression tests.
- Performance claim: all correctness gates first, then the controlled benchmark protocol and retained raw evidence.

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

No performance claim is accepted without a versioned manifest and raw samples.

Before broadening the system, the proof gate requires at least one pre-registered nontrivial workload at least 2x faster than the best applicable generic baseline. Target 0 product-class success additionally requires at least 1.5x geometric-mean speedup on the pre-registered target subset and at least 2x on one real or application-derived structure. These are research gates, not promised outcomes. A failed gate produces a written no-go or explicitly approved narrower claim; it does not authorize silent scope expansion.

The future Target 0 workflow must:

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
11. collect cycles, instructions, cache/branch/stall/vector evidence where the host exposes trustworthy counters;
12. retain failed, tied, losing, and regressed experiments when analytically useful.

Always compare with the fastest correct configuration of every applicable serious baseline. Never compare only with a naive loop.

Report analysis, search, compile, and tuning time; generated code size; scratch/prepack requirements; kernel and fallback time; speedup; variability; and break-even invocation count.

Use:

`analysis + search + compilation + expected_invocations * execution_time`

for lifecycle comparison. Never deploy a generated plan that loses to the measured fallback.

Pre-register target and holdout subsets before milestone claims. If confidence intervals overlap materially or the delta is below the accepted noise floor, report a tie—not a win.

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
- one isolated worktree and task branch, or an explicitly documented shared-branch policy;
- a precise contract and controlling requirement;
- explicit inputs and outputs;
- explicit non-goals;
- dependency declarations;
- a review path;
- an evidence/acceptance path;
- an integration owner.

The head engineering agent owns integration and reconciliation against controlling documents. Do not give multiple agents overlapping architectural or file ownership without one integration owner and ordered handoffs.

Agents must not make architecture decisions on behalf of the integration owner, rewrite unrelated dirty work, or claim a milestone gate from their subtask. The integration owner reviews exact diffs, verification evidence, generated artifacts, and dependency assumptions before integration.

## 13. Change control

### Architecture proposals

Use `docs/architecture/proposals/AR-####-short-title.md` for material semantic or architecture changes. The first proposal number is `AR-0001`.

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

Use `docs/adr/IDR-####-short-title.md` for durable semantics-neutral implementation decisions. The first IDR number is `IDR-0001`.

An IDR records context, decision, alternatives, consequences, affected files/interfaces, verification, and reversal/migration path. It must not be used to smuggle in an architectural change.

## 14. Git and commit discipline

- Inspect branch, HEAD, worktrees, remotes, and dirty state before work.
- The repository was initialized on `main` with no commits at the discovery snapshot.
- Use `milestone/mN-short-name` for milestone branches and `task/mN-short-name` for bounded task branches.
- The primary worktree is owned by the integration agent. Delegated implementation uses non-overlapping linked worktrees unless a shared policy is explicit.
- Preserve all user and agent work. Never reset, clean, checkout over, or delete unrelated changes.
- Do not broadly stage. Stage exact reviewed paths.
- Keep commits single-purpose and bind acceptance claims to exact commits.
- Do not commit `.DS_Store`, credentials, private keys, public server coordinates, build caches, or unowned temporary output.
- Generated source, objects, disassembly, and benchmark data follow the retention policy established by the relevant milestone. Do not discard useful failures; do not put large binary evidence in Git without an approved storage policy.
- Do not hand-edit generated files.
- Do not push, merge, rewrite history, tag, or create releases outside the explicit task authority and verification gate.
- If the worktree is dirty, map ownership before editing overlapping files and report the residual state at handoff.
- No completion or gate claim is valid without the exact tested commit, or an explicit statement that the branch is unborn/uncommitted.

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

Current frontier: M0 is in progress and its gate is open. No product implementation begins before M0 closes. The next approved slice after discovery review is charter, prior-art matrix, benchmark protocol/result schema, corpus/baseline selection, and target qualification.

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
- Do not infer floating-point equivalence from real-number algebra.
- Do not let a static cost model declare the winner.
- Do not execute an incompatible or stale cached plan.
- Do not remove the fallback.
- Do not start Bilinear IR, RL, GPU, multithreading, custom MLIR, or JIT work before their proof dependencies and approvals.
- Do not create broad framework scaffolding in place of the earliest falsifiable milestone.
