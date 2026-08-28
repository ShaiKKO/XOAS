# XOAS Product and Research Charter

**Status:** Locked Target 0 contract under the user's 2026-08-28 approved execution handoff. M0 itself remains open until the acceptance gate records a qualified target and reviewed evidence.

**Controlling program:** [`../exact_instance_matrix_kernel_synthesizer_build_plan.md`](../exact_instance_matrix_kernel_synthesizer_build_plan.md)

## Mission

XOAS is an exact-instance, hardware-specific matrix-kernel synthesizer.

Given one stable matrix-product instance, one exact hardware target, an explicit numerical contract, and a reuse/tuning budget, XOAS will synthesize candidate arithmetic programs and schedules, independently verify their correctness and compatibility, compile them into inspectable artifacts, measure valid candidates on that target, and select the fastest statistically supported implementation for the declared lifecycle objective.

Exact stable information becomes code and compatibility state. It does not remain runtime metadata that a generic kernel must repeatedly rediscover.

Performance measurement is part of compilation. Static analysis may reject, prune, and rank candidates, but it may not declare the winner.

## Precise v0 claim

For a fixed `M x K` structural support of `A`, fixed `M`, `K`, and `N`, runtime-dynamic `float32` values at all structurally present positions of row-major `A`, dense runtime-dynamic row-major `B`, and disjoint row-major overwrite output `C`, XOAS will generate, verify, compile, and target-measure single-threaded x86-64 Linux implementations of `C = A x B`. It will reuse only artifacts whose complete semantic and target compatibility contract matches the invocation, and it will fall back safely when no generated plan wins or compatibility fails.

The claim is not that specialization always wins. The claim is that exact support can create measurable performance headroom on a pre-registered Target 0 corpus and that XOAS can find, verify, replay, invalidate, and honestly reject that headroom.

## Exact-instance specialization

Target 0 support specialization may:

- remove impossible products;
- hard-code legal `k` coordinates;
- remove sparse-index loads, row-pointer traversal, support discovery, and related branches;
- reuse an `A[i,k]` load across multiple contiguous `j` outputs;
- schedule exact contributions for the target ISA and cache hierarchy;
- recognize verified support motifs only after the scalar and bounded-vector proof foundations close.

It may not compile away a fact that is not stable for every invocation covered by the plan.

### Structural zero rule

A **structural zero** is a coordinate guaranteed absent from `A` for every invocation compatible with the plan. It may be removed without a runtime guard.

A **numerical zero** is a present coordinate whose current runtime value happens to equal zero. It remains part of the support and arithmetic contract because it may change on the next invocation.

External sparse files define support from their declared stored coordinates after required storage normalization. A stored coordinate is not removed because the file currently gives it the numeric value zero.

## Locked Target 0

Target 0 is limited to:

- Linux on one exact x86-64 CPU target and hardware fingerprint;
- single-threaded execution;
- `float32` input, accumulation, and output under the active numerical contract;
- `C = A x B`, overwriting `C`;
- fixed `M`, `K`, and `N` per plan;
- contiguous row-major `A`, `B`, and `C`;
- no aliasing between `A`, `B`, and `C`;
- exact compile-time structural support of `A`;
- runtime-dynamic values at every present coordinate of `A`;
- dense runtime-dynamic `B`;
- repeated invocation counts large enough to evaluate amortization;
- generated C++ compiled ahead of time by the selected Clang toolchain before lower-level or JIT backends;
- independent correctness verification and comparison with every serious applicable baseline.

The initial benchmark envelope emphasizes `M` and `K` from 4 through 256, `N` from 1 through 64, support densities of roughly 0.5% through 40%, synthetic and application-derived structures, and expected invocation counts from `10^3` through `10^9`. These are corpus ranges, not public API limits.

## Non-goals

Target 0 does not include:

- GPU code generation, despite GPU hardware on the development server;
- multithreading, NUMA scaling, or distributed execution;
- runtime-dynamic sparsity;
- mixed precision, bounded-error approximation, or automatic differentiation;
- arbitrary tensor contraction or a general BLAS replacement;
- reinforcement learning or learned search;
- unrestricted Strassen-like or AlphaTensor-style algorithm discovery;
- a custom MLIR dialect;
- a production JIT or remote compilation service;
- a universal sparse-format dispatcher;
- framework breadth as a substitute for proof evidence.

These programs require the controlling earlier gates and an approved architecture proposal.

## Numerical contract

Numerical correctness is a semantic input, not a tolerance added after code generation.

### `strict`

Strict mode preserves the specified `k`-reduction order, forbids reassociation and distributive factoring, and forbids FMA contraction unless the reference semantics explicitly include it. NaN, infinity, signed-zero, and subnormal behavior must be defined and tested before a strict artifact is accepted.

### `contracted`

Contracted mode permits multiply-add contraction while preserving reduction grouping otherwise. It is the recommended initial Target 0 production mode because it permits realistic vector FMA kernels without authorizing general algebraic rewrites.

The exact compiler flags, reference expression, subnormal environment, NaN behavior, and signed-zero behavior remain an M1/M2 contract-definition obligation. Until those fields are locked and tested, `contracted` is a named direction, not a correctness claim for executable code.

### Later modes

`reassociate`, `bounded_error`, and `approximate` are later opt-in programs. Algebraic equality over the real numbers never establishes IEEE-754 equivalence by itself. Bilinear IR and unrestricted algebraic discovery are not Target 0 prerequisites.

Every transformation rule must declare its legal numerical modes, structural and aliasing preconditions, proof or verification obligation, and expected effect on work and search space.

## Compilation lifecycle contract

A successful offline synthesis request will eventually:

1. parse and validate every semantic input;
2. canonicalize all correctness and compatibility properties;
3. compute a stable content identity covering the instance, target, semantics, compiler rules, and search space;
4. build exact structural representations and the legal contribution graph;
5. analyze motifs, locality, reuse, output fan-in, and code-size risk;
6. construct and verify decompositions;
7. generate legal arithmetic and schedule candidates;
8. reject illegal, incomplete, duplicative, incompatible, or statically dominated candidates;
9. emit and compile inspectable artifacts;
10. verify every candidate outside the timed region against an independent oracle;
11. measure valid candidates against the current winner and best applicable external baseline;
12. select only a statistically supported lifecycle winner;
13. persist plan, artifact, source, object, disassembly, samples, provenance, compatibility, and fallback.

Runtime execution validates compatibility and invokes a previously verified artifact. It does not repeat discovery work on a cache hit.

## Required output and fallback

An accepted plan must carry:

- the verified executable artifact and safe fallback;
- canonical, replayable problem, derivation, and schedule records;
- target ISA and compatibility requirements;
- generated source or lower-level IR, compiler invocation, object, and disassembly;
- prepack and scratch requirements;
- correctness and numerical evidence;
- ordered raw benchmark samples and statistical decision;
- baseline identities and configurations;
- analysis, search, compile, and tuning costs;
- code size and available hardware-counter evidence;
- break-even invocation count;
- provenance sufficient to reproduce or invalidate the artifact.

No generated plan may be deployed when it loses to the measured compatible fallback.

## Success and kill criteria

### Correctness gate

A generated plan is eligible for timing only after legality, coverage, duplicate, compatibility, numerical-contract, differential-oracle, and fallback checks pass. A benchmark completing does not imply correctness.

### Proof gate

Before broadening the system, at least one pre-registered nontrivial workload must show a generated kernel at least `2x` faster than the best applicable generic baseline under the locked protocol.

### Product-class gate

Target 0 is successful only if the frozen target subset shows at least `1.5x` geometric-mean speedup and at least one real or application-derived structure shows at least `2x`, with no deployed plan losing to the measured fallback. Code size, compilation/tuning cost, measurement variation, and break-even calls are mandatory evidence.

### Measurement-quality gate

Gate evidence requires stable core affinity, deliberate warm-up and calibration, interleaved candidate/baseline sampling, retained raw order, enough independent samples to estimate dispersion, process-restart repeatability, target/environment identity, and explicit treatment of unavailable controls or counters.

### Kill and narrowing behavior

If the proof gate fails, XOAS produces a reproducible bounded negative result or an explicitly approved scope-narrowing proposal. It must not widen Target 0, weaken the baseline, change numerical semantics, tune the corpus after seeing results, or add unrelated compiler breadth to manufacture a favorable claim.

## Lifecycle objective

Selection minimizes:

`analysis_time + search_time + compile_time + expected_invocations * execution_time`

One-time conversion and prepacking costs participate wherever the compared implementation requires them. Kernel-only timing is reported but cannot replace lifecycle accounting.

## Falsification

The precise v0 claim is falsified as a product-class claim if, on the frozen Target 0 manifests and qualified target, verified generated plans fail to achieve both the `1.5x` geometric-mean threshold and the `2x` real-structure threshold against the fastest correct applicable baseline under the locked benchmark protocol, after including the required lifecycle and variability evidence. A single cherry-picked win does not rescue that failure.

## M0 exit statement

XOAS v0 specializes the exact stable support of one runtime-valued sparse `float32` left operand into single-threaded x86-64 Linux matrix-multiplication code, then empirically selects only a verified compatible lifecycle winner. The closest reviewed systems each cover important portions—such as exact planning and measurement, sparse representation/schedule compilation, or algorithm discovery—but the M0 comparison must establish whether any already combines this exact input contract, ordinary reduced arithmetic, target schedule search, retained compatibility artifacts, and target measurement. The differentiator is the combined exact-support-to-code and measured-selection contract, not any one code-generation technique. The claim is falsified by the pre-registered proof and product-class benchmarks if XOAS cannot beat the fastest correct applicable generic baseline at the locked thresholds on the qualified target.

## Change control

Changes to Target 0, numerical semantics, public ABI, IR ownership, exact-support interpretation, fallback, canonical identity, target compatibility, benchmark method, baseline set, gate thresholds, milestone proof order, or research claim require the repository architecture-proposal process and explicit approval. Durable semantics-neutral implementation choices use an IDR.

This charter may be clarified without approval only when wording changes do not alter those contracts. Every clarification must remain traceable in Git.
