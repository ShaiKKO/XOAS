# Target 0 Baseline Admission and Configuration Matrix

**Status:** M0 policy locked; executable availability remains open until the reference host is provisioned, version-pinned, and measured.

## Governing rule

For each benchmark instance, the performance baseline is the fastest correct applicable configuration among every admitted implementation. XOAS may not select a weak preferred baseline, exclude an implementation because it wins, or compare only with a naive loop.

Correctness, numerical equivalence, thread count, input/output layout, overwrite semantics, and target compatibility are eligibility gates. A baseline result that violates the active contract is labeled inapplicable, not slower.

The independent oracle is timed for transparency. It is not expected to win, but it remains in the competition if it does.

## Initial admission matrix

| ID | Implementation | Role | Applicability | Fixed-instance knowledge allowed | One-time/setup accounting | Required configuration evidence |
|---|---|---|---|---|---|---|
| `oracle-scalar` | Independent scalar reference, implemented separately from generated kernels | Correctness oracle and transparent performance floor | Every Target 0 case whose numerical mode it implements | Shape and support input, but no generator/shared reduction code | None beyond deterministic input construction | Source/commit, compiler/flags, exact reference reduction/FMA policy, special-value behavior |
| `clang-dense-fixed` | Compiler-optimized dense row-major C++ loop with `M`, `K`, and `N` constants | Serious dense crossover baseline | Every case | Fixed dimensions, alignment, no-aliasing contract; **not** sparse support | Compile time participates in reproducibility; ordinary execution has no conversion | Clang version, flags, emitted object/disassembly, vectorization diagnostics, chosen loop orders and unroll variants |
| `csr-generic` | Clean generic CSR-by-dense row-major SpMM loop | Transparent sparse traversal baseline | Every normalized support representable as zero-based CSR | CSR arrays built once; loop loads row pointers and column indices at runtime | CSR construction is reported; reuse-amortized and cold lifecycle views are separate | Source/commit, compiler/flags, row/column ordering, index width, alignment, loop/order variants |
| `support-array` | Exact-support runtime-array loop with compact values plus stored coordinate/index arrays | Isolates benefit of code-embedded support from support-known data | Every Target 0 case | Stable ordering/support arrays are prebuilt, but coordinates remain runtime loads | Support-array construction reported; persistent arrays count as prepack bytes | Same compiler/flags as generated code, index width/order, disassembly, code size |
| `openblas-sgemm` | [OpenBLAS](https://www.openblas.net/) single-precision dense GEMM | Maintained optimized dense library | Every dense materialization of `A`; useful where density/shape makes sparse specialization lose | Library sees only dense `A`, `B`, `C` and dimensions | Sparse-to-dense materialization reported separately and excluded only when caller contract supplies persistent dense `A` | Exact release/commit, build target and dynamic architecture policy, single-thread control/effective thread count, `SGEMM` entry point, `alpha=1`, `beta=0`, layout/transposition, library path/hash |
| `aocl-blas-sgemm` | [AMD AOCL-BLAS](https://www.amd.com/en/developer/aocl.html) single-precision dense GEMM | AMD-vendor-optimized dense library | Every dense materialization of `A` on an admitted AMD target when the exact artifact and active numerical mode pass admission | Library sees only dense `A`, `B`, `C` and dimensions | Sparse-to-dense materialization, initialization, and any packing are reported separately; persistent state bytes are retained | Exact release/source revision and license, build provenance, Zen dispatch evidence, single-thread path/effective thread count, CBLAS row-major/no-transpose call, `alpha=1`, `beta=0`, loaded-library path/hash |
| `onemkl-sgemm` | Intel oneMKL single-precision dense GEMM | Vendor-optimized dense library on Intel target | Every dense materialization of `A` when installed and licensed for the host | Library sees dense operands/dimensions | Dense materialization and any pack API cost reported; persistent packed-state bytes recorded | Exact oneMKL release, dispatch/ISA controls, single-thread control, CBLAS row-major/no-transpose call, `alpha=1`, `beta=0`, loaded-library identity |
| `onemkl-sparse-mm` | Intel oneMKL [`mkl_sparse_s_mm`](https://www.intel.com/content/www/us/en/docs/onemkl/developer-reference-c/2024-1/mkl-sparse-mm.html) | Vendor sparse-by-dense baseline | Zero-based CSR general non-transposed row-major cases are directly supported; BSR and declared symmetric cases are additional configurations only when semantically identical | Persistent sparse handle may encode structure | Handle creation, conversion, hints, and optimization are reported separately; measure both steady-state execution and lifecycle break-even | Exact release, CSR/BSR format, descriptor, index base, row-major layout, columns/leading dimensions, `alpha=1`, `beta=0`, optimize/hint calls, single-thread evidence |
| `libxsmm-gemm` | [LIBXSMM](https://libxsmm.github.io/libxsmm/documentation/) dispatched/JIT FP32 GEMM | Specialized small/fixed-shape dense comparator | Cases supported by its FP32 GEMM semantics; its documented approximate small-matrix envelope `(M*N*K)^(1/3) <= 64` overlaps Target 0 | Fixed `M`, `N`, `K`, flags and scalars | First dispatch/JIT and initialization cost reported separately; kernel and lifecycle views both retained | Exact release/commit, target dispatch, GEMM flags, `alpha=1`, `beta=0`, JIT cache state, generated-code size where exposed, loaded library hash |
| `libxsmm-sparse` | LIBXSMM sparse/generated functionality | Structure-specialized comparator | Only when an official installed interface accepts the case without changing semantics | Interface-specific; exact support may be supplied | Generation/dispatch/prepack cost and persistent state included | Exact API/sample lineage, release, target, code-generation inputs, numerical semantics, artifact identity |
| `jitspmm` | [JITSpMM](https://github.com/charlifu/JitSpMM) | Research comparator for generated AVX-512 SpMM | Only if a single-thread configuration, `float32` layout, fixed `N`, and overwrite/numerical semantics can be made equivalent | Runtime matrix/support information drives generated instructions | JIT, conversion, and code-cache costs included | Exact commit, patches (if any), single-thread proof, compiler/AsmJit versions, generated code/disassembly, input conversion, special-value behavior |

## Baseline configuration search

Every admitted implementation receives a bounded, predeclared configuration search proportionate to the search granted to XOAS. The result record retains all tried configurations, including losing and failed ones.

### Common dimensions

- fixed logical shape and identical normalized support;
- identical deterministic runtime values and output initialization;
- one effective execution thread, with no hidden library workers;
- equivalent row-major/no-transpose semantics;
- alignment variants allowed by the instance contract;
- warm and cold/cache-state scenarios declared by the protocol, not mixed;
- the same selected CPU affinity and environment controls;
- compiler/library ISA dispatch recorded rather than assumed.

### Dense baselines

Search only a small registered set of loop orders, unroll factors, and compiler
options for `clang-dense-fixed`. Do not enable numerical flags outside the
active contract. Dense library calls include OpenBLAS, AOCL-BLAS on admitted
AMD targets, and oneMKL when available and applicable; whichever is faster and
correct wins for that case.

### Sparse baselines

At minimum compare generic CSR, support-array, and oneMKL CSR. BSR, symmetric descriptors, vendor inspector/optimizer calls, or library-specific prepacking enter only when their conversion is deterministic and the resulting numerical operation matches the instance. Both steady-state execution and lifecycle-amortized totals are reported.

### Generated/JIT baselines

LIBXSMM and JITSpMM are not waived merely because they specialize code. Their generation costs, code-cache state, code size, supported envelope, and compatibility identity must be reported on the same basis as XOAS.

## Numerical admission

Each adapter states whether it implements `strict` or `contracted` semantics. A library name does not establish equivalence.

Before timing, compare against the independent oracle on:

- deterministic finite random values;
- exact small-integer values;
- cancellation and wide-magnitude cases;
- positive/negative zero;
- subnormals;
- infinities and NaNs where the selected mode claims support.

Record compiler flags, floating-point environment, FMA/contraction behavior, FTZ/DAZ state, and comparison policy. A baseline that cannot satisfy a mode may compete in another mode but cannot be used to weaken the mode under test.

## Cost accounting

For each implementation, record these separately:

- library/process initialization;
- input normalization and format conversion;
- sparse handle creation and inspector/optimization;
- dense materialization or packing;
- JIT/code generation and compilation;
- per-call execution;
- persistent prepack/code bytes and scratch bytes;
- cleanup where it is part of the caller lifecycle.

The primary steady-state kernel table never hides setup cost; the lifecycle table computes:

`setup + expected_invocations * execution_time`

for every expected-invocation class. Break-even is reported against the fastest compatible fallback.

## Availability snapshot

The historical 2026-08-28 `gpu-2` snapshot did not contain baseline
libraries. Its development toolchain is now installed, but AR-0001 excludes
that VM from Target 0 measurement authority. On 2026-08-29 the user designated
a physical AMD Ryzen 9 7900X Linux host as the replacement candidate and
approved AR-0002 Option 1, admitting AOCL-BLAS. The replacement host currently
has no detected OpenBLAS, AOCL-BLAS, or LIBXSMM installation. Therefore:

- this document locks baseline candidates and admission/configuration rules;
- it does **not** claim any external baseline is installed or runnable;
- exact versions are not locked until controlled provisioning records package/repository provenance;
- M0 cannot claim “baselines available on the reference machine” until the
  approved physical-host provisioning plan produces that evidence.

OpenBLAS's official site listed release `0.3.33` on the research date. Intel's official C reference documents the `mkl_sparse_s_mm` row-major sparse-by-dense operation. LIBXSMM's official documentation establishes FP32 specialized dense/sparse operations and JIT specialization. These observations select candidates; installed binaries and their hashes will control experiments.

## Disqualification and failure reporting

A run is disqualified, not silently dropped, when:

- output fails the active numerical policy;
- more than one effective execution thread is observed;
- the implementation reads a different support or value set;
- layout, transpose, `alpha`, `beta`, or overwrite semantics differ;
- target dispatch is incompatible or cannot be identified;
- setup state leaks across implementations contrary to the protocol;
- a crash, timeout, unsupported return, or instrumentation failure occurs.

Retain the configuration, error, seed, instance digest, environment, and decision. Unsupported is evidence about applicability, not a performance loss.

## M2 lock condition

Before M2 baseline implementation begins, qualify the reference target and
record exact OpenBLAS, AOCL-BLAS, oneMKL, LIBXSMM, and other comparator
source/package versions as applicable, with install provenance, licenses,
adapter APIs, and allowed configuration sets. Any later baseline-set removal
or material method change requires architecture approval because it can change
the research claim.
