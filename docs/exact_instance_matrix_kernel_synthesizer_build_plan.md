# Exact-Instance Matrix Kernel Synthesizer
## Head Engineering Build Plan

**Status:** Proposed architectural program  
**Purpose:** Build a compiler and empirical planner that generates the fastest correct implementation it can find for one precisely described matrix product on one precisely described hardware target.

---

## 0. Executive directive

The system is not “another BLAS,” a static sparse-matrix library, or a generic GEMM autotuner.

It accepts a matrix multiplication problem together with all information that is stable for the intended workload:

- exact dimensions;
- scalar type;
- layouts, strides, alignment, and aliasing guarantees;
- exact structural support of either or both operands;
- any values that are compile-time constants;
- output requirements;
- numerical semantics;
- exact target hardware;
- expected invocation count;
- tuning-time budget.

It emits:

1. a verified executable kernel;
2. any prepacked constant data and scratch-space requirements;
3. a reproducible plan describing how the kernel was derived;
4. a benchmark record against the best available baselines;
5. an amortization report showing when specialization pays for itself.

The compiler must optimize two distinct questions:

1. **What arithmetic should be performed?**
   - eliminate structurally impossible products;
   - exploit exact support;
   - find dense, diagonal, banded, block, repeated, or factored structure;
   - optionally discover an equivalent bilinear algorithm.

2. **How should that arithmetic execute on this machine?**
   - choose decomposition, traversal, layout, packing, loop order, tiling, vectorization, unrolling, prefetching, threading, and instruction selection;
   - compile candidates;
   - measure them on the target;
   - retain the best verified plan.

The first engineering objective is not generality. It is to prove, on a deliberately narrow workload class, that exact-instance specialization produces material wins over the best honest baseline.

---

# 1. Product definition

## 1.1 Product statement

> Given a stable matrix-product instance and a target machine, synthesize and empirically select the fastest correct kernel under an explicit numerical contract.

## 1.2 Meaning of “exact instance”

“Exact” must not be left ambiguous. The compiler records which properties are static and which remain dynamic.

### Shape-specialized

Known:

- `M`, `K`, `N`;
- data type;
- operand and result layouts;
- strides and alignment;
- target hardware.

Dynamic:

- all numerical values.

### Structure-specialized

Additionally known:

- exact coordinates that may be nonzero;
- exact block, diagonal, banded, or repeated support;
- structural zeros are guaranteed to remain zero.

Dynamic:

- values at structurally present coordinates.

### Operand-specialized

Additionally known:

- one operand’s numerical values are invariant;
- it may be folded, transformed, or prepacked.

### Fully value-specialized

Both input matrices are invariant. This is normally not a runtime multiplication problem; the output should be precomputed. The compiler may still support it for generated pipelines, but it is not a primary product case.

## 1.3 Structural zero versus numerical zero

The compiler must distinguish:

- **structural zero:** guaranteed absent for every invocation of the plan;
- **numerical zero:** a runtime value that happens to equal zero.

Only structural zeros may be eliminated without a runtime check.

## 1.4 The final product split

The system should eventually expose two modes:

### Offline discovery

A command-line or service workflow performs expensive analysis, candidate generation, compilation, verification, and benchmarking. It emits a reusable plan and binary artifact.

### Runtime execution

A small runtime library looks up a compatible plan, validates the target and operand contract, and calls the compiled kernel. Runtime must not repeat expensive search unless explicitly configured to do so.

This planning/execution separation is central. It keeps production execution predictable and allows deep search when amortization justifies it.

---

# 2. Recommended first target

## 2.1 Target 0

Lock the first accepted target to:

- Linux;
- one x86-64 CPU machine;
- one hardware fingerprint;
- single-threaded execution;
- `float32`;
- contiguous row-major storage;
- `C = A × B`, overwriting `C`;
- no aliasing between `A`, `B`, and `C`;
- dimensions fixed per plan;
- exact structural support of `A` known;
- `A` values dynamic;
- `B` dense and dynamic;
- repeated execution of the same structural instance.

This is fixed sparse matrix times fixed-width dense matrix, but generated from the general matrix-product model.

## 2.2 Why this is the correct first wedge

For

\[
C_{ij} = \sum_{k \in \operatorname{support}(A_i)} A_{ik} B_{kj},
\]

exact support allows the compiler to remove:

- row-pointer traversal;
- column-index loads;
- support discovery;
- branches on sparsity;
- generic bounds and dispatch;
- many indirect address calculations.

It can hard-code `k`, share one `A[i,k]` load across multiple `j` outputs, vectorize contiguous slices of `B` and `C`, group rows with identical support, and extract dense or diagonal subregions.

This workload proves the core hypothesis without immediately taking on two-sided sparse symbolic multiplication, GPU scheduling, multithreading, or algebra-discovery research.

## 2.3 Target 0 benchmark envelope

The initial corpus should emphasize:

- `M` and `K` from 4 to 256;
- `N` from 1 to 64;
- densities from roughly 0.5% to 40%;
- random, banded, diagonal, block-sparse, repeated-row, power-law, and mixed patterns;
- both synthetic and real structures;
- repeated execution counts from \(10^3\) through \(10^9\).

These are benchmark ranges, not API limits. Admission to a generated family must be determined by estimated work, code size, and search budget rather than a hard dimension cutoff.

## 2.4 Explicit non-goals for Target 0

Do not implement any of the following before the first proof gate:

- GPU code generation;
- multithreading or NUMA;
- dynamic sparsity;
- distributed execution;
- mixed precision;
- automatic differentiation integration;
- arbitrary tensor contractions;
- reinforcement learning;
- novel Strassen-like discovery;
- a custom MLIR dialect;
- a production remote compiler service;
- a general replacement for BLAS.

---

# 3. Success criteria and kill criteria

## 3.1 Correctness gates

A generated plan is acceptable only when:

- it passes differential tests against an independent reference implementation;
- it passes randomized property tests;
- it passes edge-case tests for zeros, subnormals, infinities, NaNs, signed zeros, and extreme magnitudes according to its numerical contract;
- all structural transformations carry a legality record;
- algebraically transformed programs carry an exact symbolic proof before floating-point benchmarking;
- the runtime validates all plan assumptions that cannot be guaranteed by the caller’s type or API.

## 3.2 Performance gates

Use the best result among all relevant baselines, not a preferred or weak baseline.

### Proof gate

Before broadening the system, find at least one pre-registered, nontrivial workload where the generated kernel is at least **2× faster** than the best applicable generic baseline.

### Product-class gate

Before calling the Target 0 compiler successful:

- achieve at least **1.5× geometric-mean speedup** on a pre-registered target subset;
- achieve at least **2× on one real or application-derived structure**;
- never deploy a generated plan that loses to the measured fallback;
- report code size, compilation time, tuning time, and break-even invocation count.

These are recommended research gates, not a promise that the result will occur.

## 3.3 Measurement-quality gate

The benchmark harness must demonstrate:

- stable core affinity;
- warm-up and calibration;
- interleaved candidate and baseline measurements;
- enough samples to estimate variance;
- median and dispersion reporting;
- repeatability after process restart;
- complete environment capture.

A candidate cannot be declared faster when confidence intervals overlap materially or when the observed difference is below the accepted noise floor.

## 3.4 Kill or pivot conditions

Pause expansion and re-evaluate the thesis when any of these occurs:

1. After the structural-specialization milestone, no meaningful workload exceeds the best baseline by 2×.
2. After hybrid decomposition, the pre-registered target subset does not reach 1.5× geometric-mean improvement.
3. Compile and tune cost cannot be amortized by realistic invocation counts.
4. Generated code size or instruction-cache pressure erases the gain.
5. The exact structures available in real applications change too often to reuse plans.
6. The closest existing systems already provide equivalent capability with comparable results and materially lower integration cost.

A failed gate should produce a written result, not a quiet scope expansion.

---

# 4. Architectural principles

## 4.1 Separate semantics, arithmetic, schedule, and machine code

Do not represent the entire system as one generic computation graph.

Use distinct levels:

1. **Problem IR** — what operation is required and what is known.
2. **Structure IR** — exact support and discovered motifs.
3. **Reduction IR** — the ordinary contribution/reduction graph.
4. **Bilinear IR** — optional alternative arithmetic algorithms.
5. **Schedule IR** — how a chosen arithmetic program maps to loops, vectors, memory, and threads.
6. **Machine IR** — target-specific code prepared for compilation.

Each level must have explicit invariants and verification.

## 4.2 Keep structural and algebraic optimization separate

Structural specialization may remove terms proven absent and reorder independent work subject to the numerical contract.

Algebraic optimization may change the arithmetic graph, for example:

\[
ab + ac \rightarrow a(b+c).
\]

These have different correctness obligations and must not share an informal rewrite pipeline.

## 4.3 Empirical measurement is the final performance authority

Static models prune obviously poor candidates and prioritize search. They do not declare the winner.

The final selection is made by verified execution on the actual target machine.

## 4.4 Every plan is content-addressed and reproducible

A plan identity must include:

- operation semantics;
- dimensions;
- data types;
- layouts and strides;
- exact structural support;
- static values, if any;
- numerical contract;
- target triple and ISA feature set;
- relevant hardware fingerprint;
- compiler version;
- transform-rule version;
- search-space version;
- code-generation version.

Do not use an ad hoc fast hash as the semantic model. Serialize the canonical instance and plan, then compute a stable 256-bit digest. Hash speed is irrelevant compared with compilation and tuning.

## 4.5 Never require a generated kernel

The runtime must retain a safe fallback. If no generated candidate is verified or measured faster, the plan should choose the baseline.

---

# 5. System architecture

```text
                       matmul-cli
             inspect / generate / tune / verify / run
                              |
              +---------------+----------------+
              |                                |
       matmul-compiler                    matmul-runtime
              |                                |
       +------+------+                    plan loading
       |             |                    contract checks
 matmul-analyze  matmul-discover           fallback dispatch
       |             |
 Structure IR    candidate search
       |             |
       +------+------+ 
              |
       matmul-codegen
      C++ / LLVM / MLIR
              |
       compiler driver
              |
      object / shared artifact
              |
       matmul-bench
              |
         plan database
```

## 5.1 Core components

### `matmul-core`

Owns:

- scalar and layout types;
- problem contract;
- static/dynamic property model;
- canonical serialization;
- target fingerprint;
- status and diagnostic types.

It contains no search policy and no target code generation.

### `matmul-ir`

Owns:

- Problem IR;
- Structure IR;
- Reduction IR;
- Bilinear IR;
- Schedule IR;
- plan serialization and printers.

Each IR must be immutable or use controlled builders followed by verification.

### `matmul-analyze`

Owns:

- support canonicalization;
- contribution-graph construction;
- motif detection;
- reuse and locality statistics;
- candidate-family eligibility;
- code-size and work estimates.

### `matmul-discover`

Owns:

- transformation rules;
- candidate generation;
- hierarchical search;
- pruning;
- cost models;
- empirical planner integration;
- search provenance.

### `matmul-codegen`

Owns:

- scalar C++ reference emission;
- intrinsic C++ emission;
- LLVM/MLIR lowering;
- object-file production;
- disassembly capture;
- executable loading.

### `matmul-bench`

Owns:

- reference oracles;
- baseline adapters;
- input generation;
- benchmark protocol;
- hardware-counter collection;
- statistical summaries;
- result manifests.

### `matmul-runtime`

Owns:

- plan lookup;
- artifact loading;
- runtime contract checks;
- scratch management;
- function invocation;
- fallback selection.

It must remain small and independent from the discovery engine.

### `matmul-db`

Initially an SQLite-backed experiment and plan database plus a content-addressed artifact directory.

Logical tables:

- `instances`;
- `targets`;
- `plans`;
- `plan_edges`;
- `builds`;
- `verifications`;
- `measurements`;
- `baselines`;
- `artifacts`.

---

# 6. Problem contract

A plan request should be equivalent to:

```yaml
operation:
  kind: matmul
  equation: C = A * B

scalar:
  input: f32
  accumulator: f32
  output: f32

shape:
  m: 37
  k: 51
  n: 16

lhs:
  layout: row_major
  strides: [51, 1]
  alignment: 64
  values: dynamic
  structure:
    kind: exact_coordinates
    coordinates_digest: "<content digest>"

rhs:
  layout: row_major
  strides: [16, 1]
  alignment: 64
  values: dynamic
  structure:
    kind: dense

output:
  layout: row_major
  strides: [16, 1]
  alignment: 64
  initialization: overwrite

aliasing:
  a_b: disjoint
  a_c: disjoint
  b_c: disjoint

numerics:
  mode: contracted
  nan_behavior: preserve
  signed_zero_behavior: preserve

target:
  triple: x86_64-unknown-linux-gnu
  cpu_fingerprint: "<captured target record>"

workload:
  expected_invocations: 10000000
  tuning_budget_ms: 60000
  objective: throughput
```

The actual canonical format should be a versioned binary encoding. A human-readable YAML or JSON form is for inspection and tests.

---

# 7. Intermediate representations

## 7.1 Problem IR

Represents only semantics and stable facts.

Required fields:

- operation;
- operand shapes and element types;
- layouts and strides;
- static-value masks;
- exact support;
- output initialization;
- aliasing;
- alignment;
- numerical contract;
- target;
- workload objective.

Verifier examples:

- `A.cols == B.rows`;
- `C.shape == [A.rows, B.cols]`;
- coordinates are sorted, unique, and in bounds;
- structural support is compatible with layout;
- compile-time values exist exactly where declared;
- aliasing promises are internally consistent.

## 7.2 Structure IR

Canonical graph forms:

### Support sets

- `SupportA = {(i,k)}`;
- `SupportB = {(k,j)}`;
- possible `SupportC = {(i,j)}`.

### Contribution graph

A contribution node represents:

\[
A_{ik} B_{kj} \rightarrow C_{ij}.
\]

For Target 0, `B` is dense, so contributions are generated from every `(i,k)` in `SupportA` and every `j`.

### Structural statistics

Compute and store:

- row and column nonzero counts;
- contribution count;
- support intersections;
- repeated row and column signatures;
- contiguous runs;
- dense block candidates;
- diagonal and band candidates;
- block-size histograms;
- input reuse;
- output fan-in;
- estimated working set;
- estimated straight-line code size.

### Region plan

Represents a disjoint partition of work into regions such as:

- dense block;
- diagonal;
- band;
- repeated support group;
- irregular remainder.

The region plan must prove complete coverage and no duplicate contribution unless the output reduction explicitly combines duplicates.

## 7.3 Reduction IR

Represents the conventional multiplication after structural elimination.

Core nodes:

- `LoadA(i,k)`;
- `LoadB(k,j)`;
- `Mul`;
- `Fma`;
- `Reduce`;
- `StoreC(i,j)`;
- vector forms;
- temporaries.

It supports:

- legal ordering changes;
- common address computation;
- load reuse;
- output grouping;
- vector packing;
- reduction trees.

It does not introduce distributive factorizations that alter the set of multiplications.

## 7.4 Bilinear IR

This is the research IR for alternative algorithms.

Represent an algorithm as rank-one terms:

\[
T = \sum_{r=1}^{R} u_r \otimes v_r \otimes w_r,
\]

where the target tensor `T` encodes the exact bilinear map from permitted `A` variables and `B` variables to required `C` variables.

Each term means:

1. form one linear combination of `A` values;
2. form one linear combination of `B` values;
3. multiply them;
4. distribute the result through one linear combination of outputs.

Initial coefficient domain:

- `{-1, 0, 1}`.

Later domains may include small integers or rationals.

A candidate is symbolically valid only when the summed outer products equal the target tensor exactly over the proof domain.

## 7.5 Schedule IR

A schedule is a complete implementation decision for one arithmetic program.

It records:

- traversal order;
- row, column, and reduction grouping;
- tile sizes;
- vector width;
- unroll factors;
- register-block shape;
- packing decisions;
- scratch layout;
- prefetch decisions;
- instruction-family requirements;
- remainder handling;
- code-size estimate;
- parallel mapping when that phase arrives.

Schedule transforms must be serializable. A measured plan must be reconstructible from its transform trace.

## 7.6 Machine IR

Recommended progression:

1. generated scalar C++ for transparency and the first end-to-end proof;
2. generated intrinsic C++ for explicit vector families;
3. LLVM IR or MLIR lowering for faster and more controlled candidate compilation;
4. ORC JIT only after offline AOT planning is stable;
5. GPU IR only after the CPU product-class gate.

Do not build a custom MLIR dialect until the custom high-level IR has stabilized and repeated lowering patterns justify one.

---

# 8. Candidate families

## 8.1 Baseline families

Always include:

1. simple scalar triply nested loop;
2. compiler-optimized dense loop;
3. best available dense BLAS;
4. best applicable sparse library path;
5. CSR-like generated loop using runtime index arrays;
6. exact-support generated loop with compile-time indices.

These distinguish gains from compiler flags, generic sparse representation, and true instance specialization.

## 8.2 Target 0 generated families

### Family A — Hard-coded sparse row walker

Generate a loop over `j` with compile-time `k` coordinates for each row.

Benefits:

- no column-index loads;
- no row-pointer loads;
- predictable addresses.

### Family B — Vectorized output slices

For each nonzero `A[i,k]`, broadcast `A[i,k]` and update contiguous vectors from `B[k,:]` and `C[i,:]`.

Search:

- vector width;
- `j` tile;
- number of accumulators;
- unroll;
- masked versus scalar tail.

### Family C — Output-stationary row kernel

Keep one or more `C` row tiles in registers while traversing all contributing `k`.

Search:

- rows grouped together;
- output tile width;
- register pressure;
- reduction order.

### Family D — Repeated-support groups

Rows with identical or equivalent support share one generated kernel template and differ only in data base addresses.

Search:

- grouping threshold;
- inter-row vectorization;
- code duplication versus loops.

### Family E — Dense-block plus sparse-tail

Extract dense subblocks and use a dense microkernel for them. Use exact sparse code for the remainder.

Search:

- block shapes;
- region-selection objective;
- packing threshold;
- composition order.

### Family F — Diagonal or band kernels

Use direct offset loops for diagonal or band regions and exact sparse code for exceptions.

### Family G — Straight-line kernel

For very small contribution counts, fully unroll the computation.

Admission is controlled by a code-size budget and instruction-cache estimate.

## 8.3 Later families

- both operands exact sparse;
- one operand constant;
- block-low-rank regions;
- symmetric or triangular structure;
- batched identical instances;
- multithreaded partitioning;
- GPU tensor-core or SIMT mappings;
- algebraically discovered bilinear programs.

---

# 9. Search architecture

## 9.1 Hierarchical search

Never search the Cartesian product of every decision.

Use five stages.

### Stage 1 — Family selection

The analyzer emits eligible implementation families from structural facts.

### Stage 2 — Structural decomposition

Generate a bounded set of region plans:

- all-irregular;
- dense-block extractions;
- band-plus-tail;
- repeated-support groups;
- combinations allowed by the current milestone.

### Stage 3 — Schedule generation

For each arithmetic/region plan, generate schedules:

- traversal;
- tile;
- vector width;
- unroll;
- packing;
- register blocking.

### Stage 4 — Static pruning

Reject candidates for:

- numerical illegality;
- target incompatibility;
- excessive code size;
- excessive estimated register pressure;
- known aliasing violations;
- duplicated or missing work;
- dominated estimated cost.

### Stage 5 — Compile, verify, and measure

Compile top candidates, run correctness checks, benchmark survivors, and update the search database.

## 9.2 Search methods by maturity

### Initial

- exhaustive enumeration of small spaces;
- deterministic rules;
- beam search for decomposition;
- simple linear cost model;
- empirical top-K measurement.

### Intermediate

- evolutionary mutation of schedule traces;
- transfer of good schedules between structurally similar instances;
- learned cost ranking trained only from the project’s own measurements.

### Advanced

- equality saturation for bounded arithmetic rewrite domains;
- Monte Carlo tree search or reinforcement learning for bilinear decomposition;
- cross-instance learned proposal models.

Do not introduce learning until the deterministic compiler has generated a substantial, trustworthy measurement corpus.

## 9.3 Candidate provenance

Every candidate must record:

- parent plan;
- transform applied;
- transform parameters;
- static cost before and after;
- legality result;
- compiler command and version;
- generated source or IR digest;
- build result;
- verification result;
- measurement distribution;
- rejection or selection reason.

This is essential for debugging search quality and publishing credible results.

## 9.4 Cost model

Initial cost features:

- scalar multiplications;
- scalar additions;
- vector operations;
- loads and stores by width;
- bytes transferred;
- indirect accesses;
- estimated unique cache lines;
- input reuse;
- output live range;
- estimated vector-lane utilization;
- estimated register pressure;
- spills observed after compilation;
- code size;
- branches;
- pack/unpack work.

The cost model ranks candidates. It never replaces target measurement.

---

# 10. Numerical contracts

## 10.1 Required modes

### `strict`

- preserve the specified reduction order;
- no reassociation;
- no distributive factoring;
- no FMA contraction unless the reference semantics include it;
- define handling of NaNs, infinities, signed zero, and subnormals.

### `contracted`

- permit multiply-add contraction;
- preserve reduction grouping otherwise.

This should be the recommended Target 0 mode because it enables realistic vector FMA kernels without opening the full algebraic search space.

### `reassociate`

- permit reassociation and distributive transformations;
- require documented error testing;
- preserve the mathematical bilinear map.

### `bounded_error`

- permit transformations only when an error analyzer certifies a configured bound.

### `approximate`

- later mode for mixed precision or approximate arithmetic;
- explicitly out of Target 0.

## 10.2 Algebraic proof versus floating-point behavior

For Bilinear IR, prove exact equality over integers, rationals, or a suitable finite-field validation set. Then separately evaluate floating-point error.

The symbolic proof establishes that no mathematical terms were lost or invented. It does not establish bitwise IEEE-754 equivalence.

## 10.3 Verification suite

For every generated family:

- random finite values;
- exact small-integer cases;
- cancellation-heavy cases;
- wide-magnitude cases;
- zeros and signed zeros;
- subnormals;
- infinities and NaNs where the mode claims support;
- alignment variations allowed by the plan;
- minimum and maximum supported dimensions for that family;
- guard-page tests for out-of-bounds access.

Report:

- bitwise equality where required;
- maximum ULP distance;
- maximum absolute and relative error;
- normwise forward error;
- failure seed and complete instance digest.

---

# 11. Benchmarking and evidence

## 11.1 Benchmark process

For CPU Target 0:

1. bind the process and thread to a selected core;
2. record frequency policy, topology, cache hierarchy, microcode, kernel, compiler, and library versions;
3. warm the code and data;
4. calibrate iterations so a sample is long enough to dominate timer overhead;
5. randomize or interleave candidate and baseline order;
6. collect at least enough samples to observe stable median and dispersion;
7. verify output outside the timed region;
8. consume a checksum so work cannot be eliminated;
9. repeat after process restart;
10. retain raw samples.

## 11.2 Metrics

At minimum:

- wall-clock nanoseconds;
- cycles;
- instructions;
- code size;
- compilation time;
- tuning time;
- scratch bytes;
- break-even invocation count.

Where available:

- L1, L2, and LLC misses;
- branch misses;
- vector instruction counts;
- frontend and backend stalls;
- register spills from compiler reports or disassembly.

## 11.3 Amortization

For each winning plan compute:

\[
T_{\text{total}} =
T_{\text{analysis}} +
T_{\text{search}} +
T_{\text{compile}} +
R \cdot T_{\text{execute}}.
\]

Report the smallest `R` for which the generated plan beats the fallback in total lifecycle time.

## 11.4 Benchmark discipline

- Pre-register benchmark subsets before tuning milestone claims.
- Keep a holdout corpus not used to design heuristics.
- Never publish only the best cherry-picked instance.
- Compare against the fastest correct configuration of each baseline.
- Include failed, tied, and regressed cases in the result ledger.
- Keep one-command reproduction of every reported figure.

---

# 12. Repository layout

```text
/
├── CMakeLists.txt
├── cmake/
├── docs/
│   ├── architecture/
│   │   ├── 000-charter.md
│   │   ├── 010-problem-contract.md
│   │   ├── 020-ir-stack.md
│   │   ├── 030-numerical-contracts.md
│   │   ├── 040-search-and-planning.md
│   │   └── 050-benchmark-protocol.md
│   ├── decisions/
│   ├── experiments/
│   └── milestones/
├── include/matmul/
│   ├── core/
│   ├── ir/
│   ├── analyze/
│   ├── discover/
│   ├── codegen/
│   ├── bench/
│   └── runtime/
├── lib/
│   ├── core/
│   ├── ir/
│   ├── analyze/
│   ├── discover/
│   ├── codegen/
│   ├── bench/
│   └── runtime/
├── tools/
│   ├── matmul-cli/
│   ├── matmul-bench/
│   ├── matmul-inspect/
│   └── matmul-replay/
├── tests/
│   ├── unit/
│   ├── property/
│   ├── differential/
│   ├── codegen/
│   ├── numerical/
│   └── regression/
├── benchmarks/
│   ├── manifests/
│   ├── synthetic/
│   ├── application/
│   └── holdout/
├── schemas/
├── third_party/
└── scripts/
```

Keep source files narrow. IR definitions, verification, parsing, transforms, code generation, and measurement must not accumulate in one compiler file.

---

# 13. Detailed milestone program

## M0 — Charter, prior-art map, and benchmark protocol

### Objective

Lock what is being built, how it differs from adjacent systems, and how performance claims will be judged.

### Work

- Write the product charter and non-goals.
- Lock Target 0.
- Create a comparison matrix covering at least:
  - FFTW planner/codelet architecture;
  - SPIRAL and LGen;
  - AlphaTensor;
  - TACO;
  - SparseTIR;
  - MLIR SparseTensor;
  - SABLE;
  - TVM/TensorIR/MetaSchedule;
  - Triton autotuning.
- Identify what each system searches:
  - arithmetic algorithm;
  - sparse format;
  - schedule;
  - hardware mapping;
  - exact instance;
  - measured runtime.
- Lock baseline libraries available on the reference machine.
- Lock the benchmark protocol and result schema.
- Select synthetic and application-derived corpus sources.
- Record the reference hardware fingerprint.

### Deliverables

- `docs/architecture/000-charter.md`
- `docs/architecture/050-benchmark-protocol.md`
- `docs/experiments/prior-art-matrix.md`
- initial benchmark manifests
- reference target manifest

### Exit gate

The team can state in one paragraph:

- the precise v0 claim;
- the closest prior system;
- what is different;
- the exact benchmark that could falsify the claim.

No compiler implementation begins before this gate.

---

## M1 — Core types and canonical instance identity

### Objective

Represent an exact matrix instance without losing semantic information.

### Work

- Implement scalar, layout, shape, support, aliasing, target, numerical, and workload types.
- Implement versioned human-readable parsing.
- Implement canonical binary serialization.
- Implement sorted-coordinate support canonicalization.
- Implement a stable 256-bit content digest.
- Implement target fingerprint capture.
- Implement `matmul inspect`.
- Add invalid-input diagnostics.
- Add round-trip, canonicalization, and hash-stability tests.

### Deliverables

- `matmul-core`
- instance schema
- target schema
- inspection CLI
- corpus manifest parser

### Exit gate

- equivalent instances serialize identically;
- any semantic difference changes the canonical identity;
- malformed support is rejected;
- all accepted manifests round-trip;
- no performance code exists in this milestone.

---

## M2 — Reference semantics and honest baselines

### Objective

Build the oracle and measurement foundation before generating optimized code.

### Work

- Implement a simple independent reference multiplication.
- Implement high-precision or double-precision checking for `float32`.
- Implement strict and contracted comparison policies.
- Add baseline adapters for:
  - scalar dense;
  - optimized dense compiler loop;
  - dense BLAS;
  - generic CSR or equivalent sparse path;
  - exact-support loop with runtime arrays.
- Implement input generation and deterministic seeds.
- Implement benchmark calibration, affinity, sampling, and environment capture.
- Implement raw-result persistence.
- Establish benchmark noise on the reference machine.
- Add one-command replay.

### Deliverables

- `matmul-bench`
- baseline adapter interface
- benchmark database schema
- initial result ledger

### Exit gate

- all baselines agree within their declared numerical semantics;
- benchmark noise is understood and documented;
- results reproduce after process restart;
- the harness can reject a fake 1% “win” when noise is larger.

---

## M3 — Contribution graph and scalar code generation

### Objective

Prove the complete compile-load-run loop with exact support.

### Work

- Build Structure IR from the instance.
- Build the Target 0 contribution graph.
- Verify complete and duplicate-free coverage.
- Emit scalar C++ using compile-time support coordinates.
- Compile to an object or shared library with Clang.
- Load and call through a stable C ABI.
- Store generated source, compiler command, object, and disassembly.
- Differential-test generated kernels.
- Compare:
  - generic CSR;
  - exact-support loop;
  - fully generated scalar loop.

### Deliverables

- Structure IR
- scalar generator
- compiler driver
- artifact loader
- first generated-plan record

### Exit gate

- every corpus instance generates and executes correctly;
- generated artifacts are reproducible;
- the compiler can explain each output contribution;
- no schedule search is required yet.

---

## M4 — Reduction IR and explicit CPU schedules

### Objective

Move from “generated code” to a real schedule compiler.

### Work

- Introduce Reduction IR.
- Introduce Schedule IR.
- Implement candidate families A through D:
  - hard-coded row walker;
  - vectorized output slices;
  - output-stationary row kernel;
  - repeated-support groups.
- Add explicit vector intrinsic emission.
- Add target feature legality.
- Add code-size and register-pressure estimates.
- Add compiler report and disassembly parsing for spills.
- Add schedule serialization and replay.
- Implement deterministic enumeration over:
  - vector width;
  - output tile;
  - row group;
  - unroll;
  - scalar or masked tail.

### Deliverables

- Reduction IR
- Schedule IR
- intrinsic backend
- schedule replayer
- static schedule cost model

### Exit gate

- at least one generated vector family beats generated scalar code;
- all schedule traces replay to identical generated IR;
- illegal ISA plans are rejected before compilation;
- code-size limits prevent pathological unrolling.

---

## M5 — Empirical planner and plan cache

### Objective

Select kernels by target measurement rather than fixed heuristics.

### Work

- Implement candidate queue and search budget.
- Implement compile, verify, benchmark, and rank loop.
- Use confidence-aware comparison.
- Add `quick`, `standard`, and `deep` planning tiers.
- Recommended initial budgets:
  - quick: 100 ms;
  - standard: 10 s;
  - deep: 10 min.
- Implement plan-cache lookup by instance and target identity.
- Implement fallback retention.
- Add amortization reporting.
- Add search provenance visualization or textual trace.
- Ensure interrupted searches can resume.

### Deliverables

- empirical planner
- plan database
- planning CLI
- cached runtime artifact
- plan report

### Exit gate

- the planner never selects a candidate that failed verification;
- repeated deep runs converge on statistically indistinguishable winners;
- cached execution performs no search;
- the report shows total tuning cost and break-even call count.

---

## M6 — Structural motif discovery and hybrid kernels

### Objective

Exploit structure beyond a hard-coded CSR traversal.

### Work

- Implement motif detectors:
  - dense rectangles;
  - diagonal runs;
  - fixed-width bands;
  - repeated row support;
  - regular blocks;
  - irregular tail.
- Implement a region-plan verifier.
- Implement candidate families E and F.
- Implement region composition with one final output.
- Search decomposition and schedule jointly but hierarchically.
- Add holdout structures.
- Measure code size and instruction-cache behavior.
- Compare against sparse baselines and any available structured compiler.

### Deliverables

- motif analysis
- region planner
- dense-block and band emitters
- hybrid-kernel composer
- structural explanation report

### Exit gate

- find the first honest 2× case or issue a written no-go report;
- no contribution is omitted or duplicated;
- the winning plan explains which regions use which kernel family;
- product-class benchmark subset is frozen for the next gate.

---

## M7 — Target 0 product-class proof

### Objective

Decide whether the structural exact-instance compiler is worth continuing.

### Work

- Run the frozen target subset.
- Run the holdout subset.
- Perform repeated measurements across process restarts and system reboots.
- Inspect winner assembly.
- Compute geometric-mean speedup, code-size distribution, tuning cost, and break-even calls.
- Red-team baseline configuration.
- Produce a technical report including failures.

### Exit gate

Continue only when the recommended performance gates are met or the team explicitly approves a narrower workload claim supported by the evidence.

---

## M8 — Two-sided exact sparsity

### Objective

Support exact structural patterns for both `A` and `B`.

### Work

- Extend Structure IR to support exact `B`.
- Construct only feasible `(i,k,j)` products.
- Derive possible output support.
- Add output-dense and output-sparse policies.
- Add row-oriented, column-oriented, and output-oriented contribution schedules.
- Add code-size controls for irregular graphs.
- Add graph partitioning for very large contribution sets.
- Compare straight-line, grouped, and looped representations.

### Deliverables

- two-sided contribution graph
- sparse-output contract
- two-sided generated families
- expanded corpus

### Exit gate

- exact coverage proof passes;
- generated plans remain bounded in code size;
- at least one meaningful class benefits beyond the one-sided compiler.

---

## M9 — Constant-operand specialization

### Objective

Exploit numerical values that remain fixed across calls.

### Work

- Add static-value masks and constant storage.
- Prepack constant rows or blocks.
- Fold zeros, ones, negative ones, powers of two where numerically legal.
- Hoist invariant linear combinations.
- Generate specialized load and broadcast paths.
- Account for prepack cost and artifact size.
- Detect the fully static case and precompute the result.

### Deliverables

- constant-data artifact format
- prepack pipeline
- constant-aware cost model
- constant-operand candidate families

### Exit gate

- lifecycle cost includes prepack;
- constants are included in plan identity;
- runtime rejects mismatched constant digests;
- measured gains survive artifact-loading overhead.

---

## M10 — Algebraic rewrite engine

### Objective

Search equivalent Reduction IR programs without yet attempting unrestricted tensor-rank discovery.

### Work

- Define rewrite rules with:
  - match;
  - legality mode;
  - proof obligation;
  - cost effect;
  - code-size effect.
- Implement bounded common-subexpression elimination.
- Implement distributive factoring for `reassociate` mode.
- Implement reduction-tree alternatives.
- Introduce an e-graph or bounded equality-saturation engine only after a small explicit rule engine is validated.
- Extract candidates under multiple cost functions.
- Verify each extracted program symbolically.
- Benchmark only verified survivors.

### Deliverables

- arithmetic rewrite registry
- proof checker
- bounded equality search
- extraction cost model

### Exit gate

- every rewrite is covered by positive and negative legality tests;
- symbolic proof catches injected invalid rewrites;
- at least one rewrite produces a target-measured gain not available to schedule-only search.

---

## M11 — Bilinear algorithm discovery

### Objective

Search for alternative multiplication algorithms for small exact structural instances.

### Work

- Build the sparse target tensor from the exact variable support.
- Implement exact decomposition verification.
- Start with coefficients in `{-1,0,1}`.
- Build known standard and Strassen-style examples as fixtures.
- Implement simple search in this order:
  1. local term elimination;
  2. beam search;
  3. stochastic mutation;
  4. SAT/SMT-assisted or integer-search methods if justified;
  5. MCTS or reinforcement learning only after lower-cost methods.
- Define runtime-aware cost:
  - linear-form additions;
  - multiplications;
  - output combinations;
  - memory traffic;
  - vectorizability;
  - measured target runtime.
- Lower discovered decompositions through the same Schedule IR.
- Keep discovery and low-level scheduling as separate nested searches.

### Deliverables

- Bilinear IR
- exact tensor verifier
- small-instance search engine
- discovered-algorithm corpus
- runtime-aware objective

### Exit gate

- rediscover known small algorithms;
- prove all emitted algorithms exactly;
- discover at least one nontrivial exact-pattern algorithm or produce a bounded negative result;
- show whether arithmetic improvement survives real code generation.

---

## M12 — Production runtime and JIT

### Objective

Turn the research compiler into an embeddable system.

### Work

- Freeze a C ABI.
- Implement plan loading and compatibility validation.
- Add ORC JIT or equivalent in-process compilation only where it materially improves workflow.
- Sign or checksum artifacts.
- Add cache invalidation and compiler-version migration.
- Add sandboxing or out-of-process compilation where untrusted inputs are possible.
- Add structured diagnostics and telemetry.
- Add stable fallback integration.
- Add package, install, and versioning.

### Deliverables

- `matmul-runtime`
- public C ABI
- artifact compatibility policy
- runtime integration examples
- release qualification suite

### Exit gate

- cached-plan execution has negligible dispatch overhead relative to target kernels;
- stale or incompatible plans cannot execute;
- no compiler dependency is required for ordinary cached execution;
- fallback behavior is deterministic.

---

## M13 — Parallel CPU and GPU expansion

This is a separate program and must receive a new design review.

### Parallel CPU

Add:

- thread partitioning;
- output ownership;
- cache sharing;
- false-sharing avoidance;
- NUMA placement;
- nested parallelism policy.

### GPU

Choose one initial route:

1. emit Triton for rapid scheduling experiments;
2. use MLIR GPU/NVVM/ROCDL for compiler control;
3. emit CUDA/HIP for explicit architecture work.

Do not support all three first.

The GPU search adds:

- CTA and warp shapes;
- shared-memory layout;
- tensor-core instruction selection;
- pipeline stages;
- asynchronous copy;
- occupancy and register caps;
- persistent kernels;
- launch amortization.

---

# 14. Testing strategy

## 14.1 Unit tests

- schemas;
- canonicalization;
- structure analysis;
- contribution coverage;
- transform legality;
- target feature checks;
- cost features;
- serialization.

## 14.2 Golden tests

- human-readable IR;
- generated source;
- schedule traces;
- selected assembly snippets where stable;
- plan reports.

## 14.3 Differential tests

For every generated plan, compare with an independent reference over many seeds and edge cases.

## 14.4 Property tests

Properties include:

- zero matrix;
- identity;
- diagonal;
- permutation;
- block diagonal;
- transpose-related fixtures;
- duplicate-coordinate rejection;
- structural permutation preserving results.

## 14.5 Fuzzing

Fuzz:

- instance parser;
- support coordinates;
- region partitions;
- transformation sequences;
- generated-kernel inputs;
- artifact loader.

## 14.6 Performance regression tests

Do not make noisy microbenchmark values ordinary unit-test pass/fail gates.

Use:

- a dedicated controlled runner;
- historical distributions;
- alert thresholds;
- required manual review for small deltas;
- hard failure only for large, repeatable regressions.

---

# 15. Initial implementation technology

## 15.1 Recommended language

Use C++23 for the compiler and runtime core because the likely backend, tooling, and performance-debugging ecosystem are LLVM/MLIR-native.

Use Python only for:

- corpus generation;
- experiment orchestration;
- plotting;
- report assembly.

Do not place semantic compiler logic solely in Python.

## 15.2 Build and test

- CMake and Ninja;
- Clang as the primary compiler;
- GCC as a portability lane later;
- GoogleTest or Catch2 for unit tests;
- LLVM FileCheck where appropriate;
- sanitizer builds;
- reproducible release flags;
- continuous benchmark runner separate from ordinary CI.

## 15.3 Backend progression

- generated C++ and Clang AOT first;
- LLVM IR or MLIR once schedule generation exists;
- LLVM ORC for in-process JIT after cached AOT plans work;
- target intrinsics for explicit CPU vector families.

## 15.4 Data and artifacts

- versioned binary schemas;
- human-readable debug mirrors;
- SQLite experiment database;
- content-addressed artifact directory;
- raw benchmark sample preservation.

---

# 16. Risks and mitigations

## Search explosion

**Risk:** arithmetic, decomposition, layout, and schedule create an intractable product space.

**Mitigation:** hierarchical search, family eligibility, deterministic bounded spaces first, static pruning, code-size limits, and empirical top-K evaluation.

## Dense-library maturity

**Risk:** dense GEMM has little practical headroom.

**Mitigation:** target exact structured and sparse instances first. Treat large ordinary dense GEMM only as a sanity baseline.

## Floating-point unsoundness

**Risk:** apparently valid algebraic rewrites change results beyond acceptable semantics.

**Mitigation:** explicit numerical modes, exact symbolic proof, separate floating-point validation, and no implicit fast-math.

## Overfitting to the tuning machine

**Risk:** a plan wins during one noisy run but is not robust.

**Mitigation:** interleaved measurements, repeated processes, holdout data, raw samples, confidence-aware selection, and target-specific cache identity.

## Code-size explosion

**Risk:** full unrolling creates instruction-cache misses and long compile times.

**Mitigation:** code-size budget, looped fallback, region grouping, measured code-size feature, and compiler time in objective.

## Weak baseline selection

**Risk:** impressive gains disappear against a correctly configured library.

**Mitigation:** baseline red-team milestone, best-of-baselines policy, published configurations, and fallback retention.

## Sparse pattern instability

**Risk:** plans are invalidated too frequently.

**Mitigation:** require an expected reuse contract, report break-even calls, and add structural-class specialization only after exact specialization is proven.

## Premature machine learning

**Risk:** RL consumes the project before a competent deterministic compiler exists.

**Mitigation:** prohibit learned search until the compiler has a verified IR, search trace, measurement database, and deterministic baseline.

## Prior-art collision

**Risk:** the proposed contribution is already available in SPIRAL/LGen, SABLE, SparseTIR, or another system.

**Mitigation:** M0 replication and comparison, explicit differentiation, and willingness to integrate or narrow rather than reimplement blindly.

---

# 17. Head engineering agent operating rules

The head agent owns implementation and integration but does not silently redefine the product.

## Mandatory rules

1. Do not widen Target 0 without a written architecture decision.
2. Do not begin algorithm discovery before the structural product-class gate.
3. Do not add GPU support before the CPU gate.
4. Do not claim a speedup without the raw benchmark manifest.
5. Do not merge an optimization without:
   - legality reasoning;
   - correctness tests;
   - generated artifact inspection;
   - target measurement.
6. Do not compare only against a naive baseline.
7. Do not collapse structural, arithmetic, schedule, and machine IRs.
8. Do not optimize cache-key hashing as a project milestone.
9. Preserve every failed experiment in the ledger.
10. Prefer a smaller falsifiable milestone over a broader speculative framework.

## Required documents

Maintain:

- architecture index;
- decision records;
- milestone acceptance records;
- benchmark protocol;
- experiment ledger;
- prior-art matrix;
- performance results;
- known limitations;
- risk register.

## Change control

Escalate for approval when changing:

- numerical semantics;
- Target 0;
- public ABI;
- canonical instance identity;
- benchmark success criteria;
- baseline set;
- milestone order;
- proof obligations.

Implementation details within an approved milestone remain the head agent’s responsibility.

---

# 18. First 30 engineering days

## Days 1–5

- complete M0 charter;
- lock target machine;
- capture prior-art matrix;
- define benchmark protocol;
- select baseline libraries;
- choose corpus seeds;
- create repository and architecture index.

## Days 6–10

- implement problem types and schemas;
- implement support canonicalization;
- implement target fingerprint;
- implement canonical identity;
- land round-trip and invalid-input tests.

## Days 11–15

- implement reference multiplication;
- implement baseline adapters;
- implement benchmark affinity, calibration, sampling, and result storage;
- characterize noise;
- produce first baseline report.

## Days 16–22

- implement Structure IR and contribution graph;
- implement coverage verifier;
- emit scalar C++;
- compile, load, execute, and differential-test;
- store source, object, and disassembly.

## Days 23–30

- implement first vectorized output-slice family;
- search a small deterministic parameter set;
- compare against all baselines;
- publish M3/M4 evidence;
- decide whether the first performance signal justifies M5.

The expected result after 30 days is not a general compiler. It is a trustworthy end-to-end system that can prove whether hard-coding an exact support pattern creates real performance headroom on the reference hardware.

---

# 19. Initial handoff directive

The head engineering agent should begin with the following directive:

> Build only the Target 0 proof: single-threaded `float32`, row-major, exact support of `A`, dense dynamic `B`, dynamic values, one x86-64 Linux target. First establish an independent oracle, honest baselines, and a reproducible benchmark harness. Then generate a scalar exact-support kernel, followed by a bounded vector schedule search. Do not build GPU support, RL, algebra discovery, multithreading, or a custom compiler dialect. Each milestone must end with a written acceptance record containing correctness evidence, raw measurements, generated-code artifacts, and a go/no-go decision.

---

# 20. Research anchors

The implementation team should read and compare these systems before freezing M0:

- Matteo Frigo and Steven G. Johnson, **The Design and Implementation of FFTW3**.
- The **SPIRAL** program-generation system and LGen.
- Fawzi et al., **Discovering Faster Matrix Multiplication Algorithms with Reinforcement Learning**.
- Kjolstad et al., **The Tensor Algebra Compiler (TACO)**.
- Ye et al., **SparseTIR: Composable Abstractions for Sparse Compilation in Deep Learning**.
- MLIR **SparseTensor**, **Vector**, **GPU**, and LLVM lowering documentation.
- SABLE, **Bring Your Own Formats and Kernels: Composable Abstractions for Sparse Matrix Computation**.
- TVM **TensorIR** and **MetaSchedule**.
- Triton matrix-multiplication and autotuning documentation.
- LLVM **ORC JIT** design and tutorials.

These are not templates to copy wholesale. They establish the existing boundaries between algorithm discovery, format selection, schedule search, target adaptation, and exact-matrix specialization.
