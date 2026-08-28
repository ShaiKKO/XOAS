# M0 Prior-Art Comparison Matrix

**Status:** M0 research baseline, frozen for the initial Target 0 charter review on 2026-08-28.

**Purpose:** Establish the actual boundary between XOAS and adjacent systems before implementation. This is a capability comparison, not a comprehensive novelty proof and not a performance comparison.

## Method

The comparison uses primary papers and official project documentation. A cell means:

- **Yes:** the source makes the capability a central, implemented part of the system.
- **Partial:** the system contains a narrower version, exposes a manual mechanism, or applies it to a different object or lifecycle.
- **No:** the reviewed source puts the capability outside its central design.
- **Not shown:** the reviewed source does not establish the capability; this is not proof that no later implementation has it.

The axes are deliberately separate:

- **Arithmetic:** searches or synthesizes a materially different arithmetic algorithm, not only a loop schedule.
- **Format/decomposition:** selects or composes sparse storage/structural regions.
- **Schedule:** searches or transforms traversal, tiling, vectorization, unrolling, or related mappings.
- **Hardware mapping:** emits or lowers for specific machines/ISAs.
- **Exact instance:** specializes generated executable code to one stable input structure or exact small problem.
- **Measured selection:** uses executed target timing to select a plan/configuration.
- **Replay model:** preserves a plan/database/artifact mechanism that can be reused; this does not imply XOAS-compatible identity semantics.
- **Numerics:** exposes a first-class floating-point legality/contract boundary comparable to XOAS's required modes.

## Required-anchor matrix

| System | Primary object and search | Arithmetic | Format / decomposition | Schedule | Hardware mapping | Exact stable instance | Measured selection | Replay model | Numerical contract | Boundary relative to XOAS v0 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| [FFTW3](https://fftw.org/fftw-paper-ieee.pdf) | FFT algorithms are assembled from generated codelets; a planner evaluates legal plans for a transform/problem | Yes, within FFT identities | No sparse format | Yes | Yes | Partial: exact transform size/strides/alignment, not exact matrix support | Yes | Yes: reusable wisdom/plans | Partial: documented transform semantics, not XOAS-style rewrite modes | Strongest architectural precedent for separate generated primitives, runtime planning, measurement, and reusable decisions |
| [SPIRAL](https://spiral-software.github.io/spiral-software/introduction.html) | Formula-driven algorithm generation and platform-tuned implementation of transforms and numerical kernels | Yes | Partial for supported structured operators | Yes | Yes, software and hardware targets | Partial: problem/formula and parameters, not generally one exact sparse support graph | Yes in search workflows | Yes, generated code/formulas | Partial; not the reviewed system's primary search boundary | Closest broad program-generation philosophy; much broader operator algebra and less specific to the Target 0 support contract |
| [LGen / SLinGen](https://acl.inf.ethz.ch/research/LGen/) | Generates vectorized code for fixed-size small-scale linear algebra expressions and applications | Partial: explores linear-algebra program structure | No sparse-support format search shown | Yes | Yes, vectorized C | Yes for fixed small expressions/shapes; exact sparse support is not its stated object | Partial/not central in reviewed source | Generated code | Partial/not central | Important precedent for fixed small matrix expressions and code-size-aware generation |
| [AlphaTensor](https://doi.org/10.1038/s41586-022-05172-4) | Reinforcement-learning search for low-rank decompositions of matrix-multiplication tensors, including hardware-runtime reward variants | Yes, central | Partial: structured multiplication tensors, not sparse storage regions | Partial: hardware reward influences algorithm; low-level implementation is explicitly distinct | Partial | No for Target 0's one stable support/value-dynamic instance | Yes in hardware-reward experiments | Algorithm records | No comparable IEEE-754 contract; paper identifies numerical stability as future work | Direct precedent for Bilinear IR research, explicitly later than Target 0 |
| [TACO](https://tensor-compiler.org/files/kjolstad-oopsla17-tensor-compiler.pdf) | Compiles tensor index notation by co-iterating dense/sparse formats; later work adds format abstraction and sparse schedules | No general alternative arithmetic discovery | Yes | Yes through scheduling extensions | Yes, CPU/GPU | Partial: code specializes to expression and format, normally traversing runtime coordinates | Partial; scheduling API can feed an autotuner but core paper does not make exact-instance measurement the contract | Generated code/schedules | Not shown as XOAS-style modes | Foundational separation of expression, sparse iteration, format, and schedule; not proof that runtime support traversal is eliminated for one exact matrix |
| [SparseTIR](https://arxiv.org/abs/2207.04606) | Composable sparse formats and transformations create a tuning search space for deep-learning sparse operators | No | Yes, central | Yes | Yes, especially heterogeneous/GPU | Partial: formats and operators can reflect structure, but the stated abstraction targets sparse workloads rather than one immutable support identity | Yes in tuning/evaluation workflow | TIR/schedule artifacts | Not shown as first-class rewrite modes | Strong precedent for composable format and schedule spaces; later than XOAS's scalar/vector proof dependency |
| [MLIR SparseTensor](https://mlir.llvm.org/docs/Dialects/SparseTensorOps/) | Lowers sparsity-agnostic tensor expressions through encodings, iteration graphs/lattices, loops, and sparse runtime/storage | No | Yes | Partial: sparse iteration lowering, with surrounding MLIR transforms | Yes through MLIR lowering | No in the reviewed default model: generated loops still operate over sparse storage coordinates | No built-in empirical winner contract | MLIR modules/pipelines | Not shown as XOAS-style modes | Candidate future lowering infrastructure, not a reason to collapse Problem, Structure, Reduction, and Schedule IR or to add a custom dialect in Target 0 |
| [MLIR Vector](https://mlir.llvm.org/docs/Dialects/Vector/) | Retargetable virtual vector operations with progressive lowering toward hardware vectors/LLVM | No | No | Yes at vector lowering level | Yes | No | No | MLIR modules/pipelines | Operation semantics exist, but no XOAS transform-mode contract | Potential later lowering vocabulary; it does not discover exact support or select plans |
| [SABLE v5, Bring Your Own Formats and Kernels](https://arxiv.org/abs/2407.00829v5) | Plan-extract-dispatch composition: user extractors carve target matrices into format-specific regions; kernels emit C per region | No alternative bilinear algorithm shown | Yes, central hybrid regions (including diagonal, VBR, CSR) | Partial: kernel/region strategy is composed; empirical schedule search is not the paper's central contract | Yes via generated C/compiler | Yes, central | No target-measured winner selection shown; evaluation measures chosen compositions | Generated per-matrix C/programs | Not shown as first-class modes | Closest reviewed structural-hybrid compiler. XOAS must compare directly and cannot claim that per-matrix regional C generation is novel |
| [TVM TensorIR](https://tvm.apache.org/docs/deep_dive/tensor_ir/index.html) + [MetaSchedule](https://tvm.apache.org/docs/deep_dive/tensor_ir/tutorials/meta_schedule.html) | Tensor program IR plus schedule transformations; MetaSchedule searches designs and measures candidates on real hardware | No general arithmetic discovery | Partial, extended by sparse systems such as SparseTIR | Yes, central | Yes | Partial: specializes operator/shape/target rather than necessarily exact sparse coordinates | Yes, central in MetaSchedule | Yes: schedule traces/database | Not shown as XOAS-style modes | Closest mature schedule-search and measurement architecture; XOAS adds the exact-support contribution program and stricter artifact/semantic identity |
| [Triton autotuning](https://triton-lang.org/main/getting-started/tutorials/03-matrix-multiplication.html) | Programmer supplies a GPU kernel and a finite set of block/warp/stage configurations; decorator benchmarks configs keyed by dimensions | No | No general sparse format discovery | Yes, bounded configuration choice | Yes, GPU | Partial: keys/shapes, not one exact sparse support | Yes | Partial: autotune cache/results | Kernel semantics, but no XOAS numerical-mode/rewrite record | Clear precedent for bounded measured schedule selection; GPU and predetermined kernel structure are outside Target 0 |
| [LLVM ORC](https://llvm.org/docs/ORCv2.html) | Modular runtime compilation, linking, symbol materialization, eager/lazy compilation, and custom program representations | No | No | No search by itself | Yes through supplied compiler layers | Only as supplied by the client | No planner by itself | Yes at JIT/link/session level | Delegated to client/compiler | A possible later machine-artifact mechanism, not an optimizer or Target 0 prerequisite |

## Direct structure-specialization comparators

The required anchors are insufficient by themselves because several systems are closer to XOAS's exact-support wedge.

| System | Established capability | Exact-instance relationship | Search/measurement boundary | XOAS obligation |
|---|---|---|---|---|
| [Sympiler](https://arxiv.org/abs/1705.06575) | Separates compile-time symbolic inspection from numerical execution and applies inspector-guided transformations for stable sparse patterns | Yes for sparse-method symbolic structure; values may change while pattern remains stable | Domain-specific transformations; no reviewed evidence of an XOAS-style empirical candidate planner | Credit symbolic/numeric separation and compare contribution-graph analysis against its inspectors rather than rebranding the idea |
| [EGGS](https://onlinelibrary.wiley.com/doi/10.1111/cgf.14080) | Generates reusable sparsity-specific implementations with vector intrinsics when matrix structure is known and values may change | This is the closest reviewed statement of the Target 0 input stability contract | Generates optimized implementations for broader sparse/dense expression algorithms; target-measured plan selection and replay identity are not established in the reviewed paper | Treat EGGS as a primary closest prior system and reproduce or explain applicable comparisons before novelty/performance claims |
| [SpComp](https://arxiv.org/abs/2307.06109) | Uses essential-indices analysis to customize computations to positions and emit piecewise-regular loops without indirect references | Yes, including matrix operations beyond simple dense-output cases | Compile-time analysis and code generation; no reviewed empirical search contract | Compare coverage, indirection removal, applicability, and code-size behavior |
| [JITSpMM](https://arxiv.org/abs/2312.05639) | Generates SIMD assembly at runtime for SpMM, unrolls critical loops, merges columns, and allocates registers using runtime matrix information | Yes in the JIT specialization sense | Uses designed code-generation strategies; the paper evaluates them but does not establish broad per-instance plan search/replay/fallback semantics | A serious generated-code comparator where its AVX-512, shape, threading, and numerical semantics can be made equivalent |

## Capability conclusions

### Closest prior systems

There is no honest single-name answer because the nearest systems differ by layer:

- **Closest input and specialization contract:** EGGS—known sparsity structure, changing values, reusable vectorized code.
- **Closest structural decomposition and hybrid code generation:** SABLE v5—format-specific extraction and C kernels composed for a target matrix.
- **Closest exact SpMM instruction specialization:** JITSpMM—runtime matrix information drives unrolled SIMD assembly.
- **Closest empirical planner architecture:** FFTW3 and TVM MetaSchedule—candidate planning/search plus real-hardware measurement and reusable decisions.
- **Closest broad algorithm generator:** SPIRAL; AlphaTensor is the direct later-program anchor for Bilinear IR.

These findings narrow the permissible XOAS claim. “Generate code for a fixed sparsity pattern,” “remove sparse indirections,” “extract structured regions,” and “benchmark configurations” are all prior capabilities.

### Defensible Target 0 differentiator

Based on the reviewed sources, XOAS's v0 research object is the combined contract:

1. exact stored-coordinate support with runtime-dynamic present values;
2. explicit separation of problem, structure, ordinary reduction, schedule, and machine artifacts;
3. verified complete/duplicate-free contribution programs;
4. bounded schedule and later structural-family search without requiring bilinear discovery;
5. a first-class IEEE-754 numerical legality mode;
6. independent pre-timing correctness and compatibility gates;
7. empirical selection against every applicable serious baseline on one exact target;
8. lifecycle/break-even accounting, fallback, and retained replay/invalidation provenance.

The reviewed sources do not establish one system with all eight obligations as a single product contract. That is a scoped inference from this matrix, not a universal novelty claim. A newly found system that does establish them must be added before any novelty statement is repeated.

## Decisions carried into implementation

- Target 0 begins with ordinary structurally reduced multiplication, not AlphaTensor/Bilinear IR search.
- Generated C++ and Clang AOT remain the inspectable first backend; MLIR and ORC are later integration candidates.
- Structure and schedule remain separate even though SparseTIR, TACO, SABLE, and TVM show useful compositional mechanisms.
- SABLE, EGGS, SpComp, JITSpMM, oneMKL sparse SpMM, dense BLAS, and LIBXSMM applicability must be revisited when executable baselines are provisioned.
- Exact support specialization is not itself a novelty claim.

## Source and version notes

- SABLE's arXiv identifier retained the 2024 staging-blocked lineage, but the official arXiv API reported version 5 on 2026-06-26 under the title used above. Pin version 5 for this M0 comparison.
- TVM, MLIR, Triton, LLVM, OpenBLAS, oneMKL, and LIBXSMM documentation evolves. Executable comparisons must pin source/package versions and cannot rely on this research-date snapshot as runtime identity.
- Paper-reported speedups are not XOAS evidence. This document compares mechanisms only.
