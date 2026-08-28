# Repository Discovery and Project Understanding Report

**Discovery date:** 2026-08-28

**Repository root:** `/Users/shaiiko/XOAS`

**Controlling document found at:** [`docs/exact_instance_matrix_kernel_synthesizer_build_plan.md`](exact_instance_matrix_kernel_synthesizer_build_plan.md)

**Checkpoint scope:** Repository orientation, evidence capture, durable operating guidance, and frontier identification only. No optimizer or product implementation was started.

## Evidence labels

- **Verified fact** means the statement was observed in a repository file, command result, remote host query, or primary source during this discovery.
- **Inference** means the statement follows from verified facts but has not itself been accepted as an architecture decision.
- **Recommendation** means proposed next work or risk treatment; it is not an approved change.

## Executive summary

**Verified fact:** This is a greenfield repository. At discovery start, the workspace contained only `.DS_Store` and the 1,904-line build plan. It had no Git metadata, source code, tests, build files, benchmark harness, schemas, artifacts, result database, README, contribution guide, architecture records, or agent instructions.

At the user's direction, the workspace was initialized as an empty Git repository on `main` and configured with `origin` at `https://github.com/ShaiKKO/XOAS.git`. The branch is unborn: there is no HEAD commit and no history. A read-only `git ls-remote --refs origin` returned successfully with no refs, so the configured upstream is also empty as of this snapshot. Nothing was staged, committed, or pushed during discovery.

The primary development server is reachable and authenticated. It is an x86-64 Ubuntu 24.04.4 KVM/OpenStack VM backed by an Intel Xeon Gold 6348 with AVX2 and AVX-512 features. It is suitable for Linux development once the required toolchain is provisioned. It is not yet qualified as the Target 0 measurement host because physical-host exclusivity, performance-counter support, frequency/power controls, and measurement stability have not been established.

No milestone gate is closed. M0 is the earliest executable slice. The correct next work after checkpoint review is M0 documentation and target/baseline qualification, not compiler scaffolding.

## 1. Exact repository and Git state

### Discovery baseline

| Fact | Observed state | Evidence |
|---|---|---|
| Repository root | `/Users/shaiiko/XOAS` | `pwd`; later `git rev-parse --show-toplevel` |
| Git state at first inspection | Not a Git repository | Initial `git rev-parse` and `git status` both failed with “not a git repository” |
| Initial files | `.DS_Store`; `docs/exact_instance_matrix_kernel_synthesizer_build_plan.md` | `rg --files -uu`; `ls -la` |
| Root instructions | No `AGENTS.md` | `rg --files -uu -g 'AGENTS.md'` returned no paths |
| Other repository documents | None | Markdown/text inventory returned only the build plan |
| Code, tests, build, benchmarks, schemas, artifacts | None | Complete non-`.git` file inventory |

### Git initialization requested during discovery

| Fact | Observed state | Evidence |
|---|---|---|
| Branch | `main` | `git branch --show-current` |
| HEAD | Unborn; no commit hash exists | `git rev-parse --verify HEAD` failed with “Needed a single revision” |
| Local worktree | One worktree at `/Users/shaiiko/XOAS` | `git worktree list --porcelain` |
| Remote | `origin` fetch/push URL is `https://github.com/ShaiKKO/XOAS.git` | `git remote -v` |
| Remote refs | None | Escalated read-only `git ls-remote --refs origin`, exit 0, no output |
| Recent history | None | `git log` failed because `main` has no commits |
| Initial untracked state after init | `docs/` | `git status --short --branch` |

**Verified fact:** There are no active linked worktrees, branches with commits, tags, generated-artifact directories, benchmark-result directories, or historical commits to attribute to milestones.

**Safety note:** Existing untracked files were preserved. No reset, clean, checkout, staging, commit, push, deletion, or remote write occurred.

## 2. Authoritative documents and precedence

### Repository document inventory

| Path | Status and role | Discovery result |
|---|---|---|
| [`docs/exact_instance_matrix_kernel_synthesizer_build_plan.md`](exact_instance_matrix_kernel_synthesizer_build_plan.md) | Controlling architecture/build plan under the user's authority order | Read in full: 1,904 lines, 7,273 words |
| [`docs/milestones/status.md`](milestones/status.md) | Canonical current-frontier ledger created by this checkpoint | Records M0 open and all later gates unclosed |
| `AGENTS.md` | Root operating manual created after discovery | Summarizes verified rules; does not override architecture |
| This report | Point-in-time evidence and recommendations | Not an architecture specification |

No README, contribution guide, coding standard, dependency guide, schema document, benchmark protocol, architecture proposal, ADR/IDR, experiment ledger, accepted/rejected research note, or milestone acceptance record existed before this checkpoint.

### Effective precedence

1. The user's latest explicit instruction.
2. Approved or locked architecture/specification documents and approved architecture proposals.
3. The exact-instance build plan.
4. Scoped `AGENTS.md` files.
5. Accepted implementation plans and implementation-decision records.
6. Code and tests as evidence, never as authority over contradictory specifications.

### Document conflict and stale metadata

**Verified fact:** The build plan front matter says **“Status: Proposed architectural program.”** The handoff says the research architecture is approved and directs the head agent to preserve it.

**Resolution for this checkpoint:** The user's later explicit instruction has higher authority, so the build plan controls current discovery and M0 planning. The stale front-matter label was not silently edited.

**Work blocked:** No discovery work is blocked. Before a future acceptance record describes the plan itself as an approved repository artifact, M0 should reconcile the status metadata or record the approval in the repository's chosen decision/acceptance convention.

### External prerequisite reading

Section 20 of the build plan names research anchors that must inform M0. Primary papers or official documentation were reviewed for orientation:

- [FFTW3 design and implementation](https://fftw.org/fftw-paper-ieee.pdf): generated codelets, rule-based decompositions, hardware-adaptive empirical planning, and reusable plans.
- [SPIRAL](https://www.spiral.net/) and [small-scale linear algebra/LGen](https://arxiv.org/abs/1805.04775): program generation and platform adaptation across mathematical formulas and implementations.
- [AlphaTensor](https://doi.org/10.1038/s41586-022-05172-4): exact tensor-decomposition search at the algorithmic level; explicitly later than Target 0.
- [TACO](https://tensor-compiler.org/files/kjolstad-oopsla17-tensor-compiler.pdf): generic dense/sparse tensor expression compilation and iteration/merge structures.
- [SparseTIR](https://arxiv.org/abs/2207.04606): composable sparse formats, composable transformations, and joint empirical search.
- [MLIR SparseTensor](https://mlir.llvm.org/docs/Dialects/SparseTensorOps/) and [Vector](https://mlir.llvm.org/docs/Dialects/Vector/) documentation: sparse lowering and vector-level infrastructure.
- [SABLE](https://arxiv.org/abs/2407.00829): structure-adaptive blocked sparse computation and dense/hyper-sparse block treatment.
- [TVM TensorIR](https://tvm.apache.org/docs/deep_dive/tensor_ir/index.html) and [MetaSchedule](https://tvm.apache.org/docs/deep_dive/tensor_ir/tutorials/meta_schedule.html): serializable schedule transformations, cost-guided search, target measurement, and record persistence.
- [Triton matrix multiplication/autotuning](https://triton-lang.org/main/getting-started/tutorials/03-matrix-multiplication.html): GPU block scheduling and empirical configuration search; a later non-goal for this project.
- [LLVM ORC design](https://llvm.org/docs/ORCv2.html): modular JIT linking/compilation; later than the required inspectable AOT backend.

**Verified gap:** No repository prior-art comparison matrix exists, and no differentiation claim has been accepted. External reading is not a substitute for the M0 deliverable, baseline replication where appropriate, or an exact falsifiable comparison.

## 3. Project mission and differentiator

The project compiles one stable matrix-product instance for one exact hardware target under one explicit numerical contract. Its job is to select the fastest verified implementation it can find after accounting for analysis, search, compilation, and expected reuse—not merely to emit a generic sparse loop.

The differentiator is the joint but explicitly layered search over:

- the legal arithmetic contributions implied by exact stable structure;
- structural decompositions such as dense blocks, bands, diagonals, repeated supports, and irregular tails;
- the schedule mapping one selected arithmetic program onto one target;
- empirical compiled performance against the best applicable serious baseline.

Only structural facts guaranteed for every invocation may become code. A runtime value that happens to be zero is not structural evidence and cannot be compiled away without a guard.

Correctness, legality, coverage, numerical semantics, target compatibility, and performance are separate gates. A candidate that compiles or completes a benchmark has not thereby passed any other gate.

## 4. Locked Target 0 and non-goals

### Target 0

- one exact x86-64 Linux target machine and hardware fingerprint;
- single-threaded execution;
- `float32` inputs, accumulation, and output under the active numerical contract;
- contiguous row-major `A`, `B`, and `C`;
- `C = A * B`, overwriting `C`;
- fixed `M`, `K`, and `N` per plan;
- disjoint `A`, `B`, and `C`;
- exact compile-time structural support of `A`;
- runtime-dynamic values at structurally present positions of `A`;
- dense runtime-dynamic `B`;
- repeated execution sufficient to amortize tuning;
- independent correctness oracle and all serious applicable baselines;
- generated C++ plus Clang AOT before lower-level or JIT backends.

### Explicit non-goals before the required gates

- GPU code generation;
- multithreading, NUMA, or distributed execution;
- reinforcement learning or learned search;
- unrestricted Strassen-like/AlphaTensor bilinear discovery;
- dynamic sparsity;
- mixed precision or approximate modes;
- arbitrary tensor contraction or general BLAS replacement;
- custom MLIR dialect;
- remote compilation service;
- production JIT/runtime expansion.

The available NVIDIA L4 does not change this scope.

## 5. Intended architecture versus actual architecture

### Intended architecture

The build plan separates:

| Layer/component | Responsibility |
|---|---|
| Problem IR / `matmul-core` | Operation semantics and stable facts; canonical serialization; target and diagnostics; no schedule choice |
| Structure IR / `matmul-analyze` | Exact support, contribution graph, motifs, locality/reuse statistics, region candidates, coverage evidence |
| Reduction IR | Ordinary structurally reduced loads, multiplies/FMAs, reductions, vector forms, temporaries, and stores |
| Bilinear IR | Later exact alternative-algorithm search; not a Target 0 prerequisite |
| Schedule IR / `matmul-discover` | Serializable mapping of one arithmetic program to traversal, vectorization, tiling, unrolling, packing, and ISA requirements |
| Machine IR / `matmul-codegen` | Initially inspectable generated C++ and Clang AOT artifacts; later LLVM/MLIR/JIT only after gates |
| `matmul-bench` | Independent oracles, baselines, inputs, controlled measurement, counters, statistics, and manifests |
| `matmul-runtime` | Compatible plan lookup, contract validation, artifact invocation, scratch management, and fallback |
| `matmul-db` | SQLite experiment/plan data and content-addressed artifacts |

### Actual architecture

**Verified fact:** None of these modules or interfaces exists. There are no headers, libraries, tools, schemas, tests, databases, generated artifacts, public APIs, or dependency edges to map.

The repository layout in section 12 of the build plan is a recommended future layout, not present implementation. It must not be described as current or created wholesale before its milestone requires it.

### Current interface map

There are no public or internal software interfaces. The only current repository interface is documentary:

```text
user authority
    -> controlling build plan
        -> root AGENTS.md operating summary
        -> milestone ledger
        -> future M0 deliverables
```

### Intended data flow

The following is specified but not implemented:

```text
problem description
  -> semantic validation and canonical identity
  -> exact support and contribution graph
  -> structural analysis and legal candidate families
  -> arithmetic and schedule candidates
  -> static legality/coverage/compatibility pruning
  -> source generation and AOT compilation
  -> independent verification
  -> interleaved empirical comparison with baselines
  -> statistically supported plan or fallback
  -> retained plan, artifact, provenance, samples, and compatibility record
  -> runtime compatibility validation and cached execution
```

## 6. Numerical-contract status

The plan specifies the intended modes `strict`, `contracted`, `reassociate`, `bounded_error`, and later `approximate`.

**Verified fact:** No schema, parser, type, oracle policy, comparison implementation, edge-case suite, or rewrite registry exists. Therefore no numerical mode is implemented or qualified.

Target 0 is expected to begin with `contracted` after its exact rules are locked, permitting FMA contraction while preserving reduction grouping otherwise. This expectation is architectural guidance, not evidence of implementation.

No distributive rewrite, reassociation, algebraic factorization, or `fast-math` behavior may enter the initial structural compiler implicitly. Each future transformation must name its legal modes, preconditions, proof/test obligations, and effect on work and search space.

## 7. Canonical identity, artifact, and compatibility status

The plan requires canonical identity to cover operation semantics, dimensions, types, layouts/strides, alignment/aliasing, exact support, static values, numerical contract, target/ISA/hardware fingerprint, compiler version, transformation rules, search space, and code-generation version, followed by a stable 256-bit digest.

**Verified fact:** No encoding, digest implementation, version registry, target schema, plan schema, artifact format, compatibility check, cache, invalidation rule, fallback ABI, or provenance record exists.

**Gate consequence:** M1 is not started. No cache or artifact claim can be made, and no code may use an ad hoc hash as a substitute for the semantic model.

## 8. Oracle, tests, and benchmark status

### Correctness and tests

No independent oracle, high-precision checker, property generator, numerical edge-case corpus, guard-page test, unit test, differential test, fuzz target, code-generation golden, serialization test, or regression test exists.

### Baselines

No baseline adapter or locked baseline configuration exists. The required future set includes at least:

- simple scalar dense;
- compiler-optimized dense loop;
- best available dense BLAS;
- best applicable generic sparse library path;
- CSR-like exact computation with runtime indices;
- exact-support loop with compile-time indices.

The best correct applicable result across serious baselines must be the comparison target. A naive loop alone is never sufficient.

### Corpus and result evidence

No synthetic corpus, application-derived corpus, holdout corpus, seed registry, benchmark manifest, result schema, raw samples, environment fingerprint, statistical comparison, noise study, experiment ledger, or performance claim exists.

**Verified fact:** There is no speedup evidence to validate or invalidate. Any speedup claim would currently be unsupported.

## 9. Build, test, lint, sanitizer, benchmark, and cleanup commands

### Repository commands verified

```bash
git status --short --branch
git branch --show-current
git remote -v
git worktree list --porcelain
rg --files -uu -g '!.git/**'
```

These commands inspect state only.

### Commands that do not exist

| Workflow | Verified state |
|---|---|
| Configure debug/release | Unavailable: no `CMakeLists.txt`, presets, or build script |
| Build | Unavailable: no build graph or source |
| Unit/property/differential/numerical/codegen/regression tests | Unavailable: no test harness or test files |
| Benchmark or replay | Unavailable: no benchmark executable, manifest, database, or result |
| Format/lint/static analysis | Unavailable: no configuration or source set |
| Sanitizers | Unavailable: no build targets or presets |
| Safe generated-artifact cleanup | Unavailable: no generated paths or documented ownership boundary |

No guessed command was run or documented as authoritative. In particular, `cmake -S . -B ...`, `ctest`, benchmark commands, and cleanup commands would be fictional at this frontier.

## 10. Host and toolchain truth

### Local control host

**Verified fact:** The local workspace is on macOS 26.5, Darwin 25.5.0, Apple M4 arm64, 10 cores, and 16 GiB RAM. It is not the locked x86-64 Linux target and cannot support Target 0 performance claims.

Available locally:

- Git 2.49.0;
- CMake 4.3.1;
- Ninja 1.13.2;
- Apple Clang 21.0.0 targeting arm64 Darwin;
- Python 3.14.4;
- SQLite CLI/library 3.51.x;
- Homebrew OpenBLAS 0.3.30 and GoogleTest 1.17.0.

Linux affinity/performance tools `taskset`, `perf`, `numactl`, `lscpu`, and `ldconfig` are absent locally, as expected.

### Primary Linux development server

Access was authenticated read-only as the `ubuntu` account using the externally supplied PEM key. Credentials and network coordinates are intentionally not stored in the repository.

| Fact | Verified value |
|---|---|
| Hostname | `gpu-2` |
| OS | Ubuntu 24.04.4 LTS (`noble`) |
| Kernel | Linux 6.8.0-137-generic, x86-64 |
| Virtualization | KVM guest on OpenStack Nova |
| CPU | Intel Xeon Gold 6348 @ 2.60 GHz; family 6, model 106, stepping 6 |
| Visible topology | 16 logical CPUs, 8 cores, 2 threads/core, 1 socket, 1 NUMA node |
| ISA | SSE through AVX2/FMA plus AVX-512F/DQ/CD/BW/VL/IFMA/VBMI/VBMI2/VNNI/BITALG/VPOPCNTDQ and related features |
| Cache | 48 KiB L1d/core, 32 KiB L1i/core, approximately 1.25 MiB L2/core, 42 MiB shared L3 |
| Memory | 62 GiB visible, no swap |
| Root filesystem | 99 GiB ext4, approximately 93 GiB free at capture |
| Frequency visibility | `/proc/cpuinfo` reported 2599.998 MHz for all vCPUs; cpufreq driver/governor and Intel turbo controls are not exposed |
| Performance counters | `perf_event_paranoid=4`; unprivileged cycles/instructions rejected and reported unsupported; privileged PMU usefulness is not yet established |
| GPU exposure | NVIDIA L4 appears on PCI, but `nvidia-smi`, `/dev/nvidia*`, and NVIDIA kernel modules are absent |
| Time | UTC, synchronized by NTP |

Installed development tools:

- Git 2.43.0;
- Python 3.12.3;
- Linux `perf` 6.8.12;
- `taskset` from util-linux 2.39.3;
- `numactl` executable.

Not installed at capture:

- CMake;
- Ninja;
- GCC/G++;
- Clang/Clang++;
- SQLite CLI/development package;
- `pkg-config`;
- OpenBLAS/BLAS/BLIS development or runtime packages detected by `dpkg-query`/`ldconfig`.

### Qualification inference

**Inference:** `gpu-2` is a viable primary Linux development host after controlled toolchain provisioning. It is only a candidate measurement host. Virtualization does not automatically invalidate it, but the Target 0 manifest cannot be locked until the team establishes scheduling isolation/dedication, repeatability across restarts/reboots, exact baseline versions, counter availability or an accepted counter limitation, and observable frequency/power behavior.

## 11. Milestone-by-milestone status

The canonical table is in [`docs/milestones/status.md`](milestones/status.md).

| Milestone | Status | Evidence summary |
|---|---|---|
| M0 | In progress; gate open | Plan exists; discovery and candidate-host capture exist; all named M0 deliverables are missing |
| M1 | Not started | No core types, schemas, canonical encoding/digest, target capture tool, or inspect CLI |
| M2 | Not started | No oracle, baselines, harness, raw-result store, noise study, or replay |
| M3 | Not started | No Structure IR, contribution graph, scalar generator, compiler driver, loader, or artifacts |
| M4 | Not started | No Reduction/Schedule IR, vector families, intrinsic backend, replay, or cost model |
| M5 | Not started | No empirical planner, database, cache, fallback selection, or amortization report |
| M6 | Not started | No motif/region planner, hybrid kernels, holdout evidence, or 2x proof/no-go report |
| M7 | Not started | No frozen target subset, holdout run, reboot study, assembly review, or product-class decision |
| M8 | Not started | No two-sided support or sparse-output contract |
| M9 | Not started | No static-value artifact/prepack pipeline |
| M10 | Not started | No rewrite registry, proof checker, or equality search |
| M11 | Not started | No Bilinear IR, tensor verifier, or discovery search |
| M12 | Not started | No stable C ABI, runtime package, JIT, migration, or release qualification |
| M13 | Not started | No separate parallel/GPU design review or implementation |

There are no implementing commits or acceptance records for any milestone, and no later work incorrectly depends on an open earlier gate.

## 12. Contradictions, missing information, debt, and blockers

### Contradictions or stale sources

1. The controlling plan says “Proposed”; the user's later handoff says approved and locked. The user instruction controls, but repository metadata remains stale.
2. The build plan shows a recommended repository tree; the actual repository has none of it. Planned paths must stay labeled planned.
3. The server is named and provisioned as a GPU host, but GPU support is a Target 0 non-goal and the guest currently lacks an NVIDIA driver/device nodes.

### Missing information

- Whether `gpu-2` is development-only or the intended measurement host.
- VM tenancy/dedication, host migration policy, and vCPU scheduling guarantees.
- Approved compiler version and reproducible installation/source.
- Serious baseline libraries and exact configurations.
- Target corpus sources, seed policy, and frozen holdout boundary.
- Benchmark noise floor and statistical acceptance method.
- Exact strict/contracted comparison rules for special IEEE-754 values.
- Canonical binary encoding and versioning policy.
- Artifact storage/retention and experiment-database backup policy.
- License, contribution, CI, review, and release policies.

### Current technical debt

- `.DS_Store` exists, is untracked, and is ignored by `/Users/shaiiko/.gitignore_global`; it should not enter history.
- Repository provenance is absent until an initial commit is explicitly authorized and created.
- No dependency lock, build environment, or target manifest exists.
- No benchmark counter path is currently demonstrated on the VM.

### Blocking boundaries

- Product implementation is blocked by the M0 exit gate.
- Target-specific performance claims are blocked by target qualification and benchmark infrastructure.
- M1 is blocked by M0.
- All optimizer/codegen work is blocked by M1/M2 proof dependencies.
- GPU work remains prohibited regardless of available hardware.

## 13. Risks

### Correctness

- Implementing schedule or code generation before the oracle and numerical contracts would make passing executions meaningless.
- Treating runtime zeros as stable support would produce semantically invalid kernels.
- Collapsing IR levels would obscure transformation legality and make later replay/proof difficult.

### Reproducibility

- An unborn repository cannot bind evidence to a commit.
- A VM may migrate or share physical resources unless the provider guarantees otherwise.
- Hidden power/governor state and unavailable PMU events can make causal performance analysis weak.
- Unpinned compiler and baseline versions would invalidate plan identity and comparisons.

### Research claim

- Mature dense and sparse libraries may erase apparent gains.
- A comparison against a naive baseline or cherry-picked structure would not support the thesis.
- Tuning cost, code size, or structural instability may eliminate lifecycle benefit even when kernel time improves.
- Prior systems—especially SparseTIR, SABLE, TACO, SPIRAL/LGen, and FFTW-style planners—may narrow the novel claim after M0 comparison.

### Security and operations

- Credentials, private keys, public IPs, and cloud identifiers must remain outside repository artifacts.
- Generated code compilation and later artifact loading will require explicit trust and sandbox boundaries before accepting untrusted inputs.

## 14. Earliest executable next slice

After this checkpoint is reviewed, execute **M0 only**. A reviewable M0 slice should produce:

1. `docs/architecture/000-charter.md` with the exact v0 claim, closest prior system, differentiator, falsifying benchmark, and non-goals.
2. `docs/experiments/prior-art-matrix.md` comparing what each named system searches, when it measures, and whether it specializes an exact instance.
3. `docs/architecture/050-benchmark-protocol.md` with affinity, warm-up, calibration, interleaving, raw-sample retention, restart/reboot replication, statistics, and prohibited claims.
4. A versioned result schema and initial synthetic/application/holdout manifest policy without prematurely populating the holdout from tuned examples.
5. A reference-target manifest for an approved host, including virtualization and counter limitations.
6. A locked serious-baseline matrix with exact library/compiler versions and configurations.
7. An M0 acceptance record with an exact commit and go/no-go decision.

Do not scaffold M1–M13 while doing this work.

## 15. Architecture decisions requiring escalation

No decision blocks drafting the charter, prior-art matrix, benchmark protocol, or corpus policy.

Before locking the M0 target manifest and measurement protocol, one load-bearing choice requires explicit approval:

> Is `gpu-2` the reproducible Target 0 benchmark machine, accepting and documenting its KVM/OpenStack boundaries, or is it development-only while a dedicated/non-migrating x86-64 Linux measurement host is selected?

If evidence during M0 shows that this choice changes benchmark validity or the success gate, create `docs/architecture/proposals/AR-0001-target-0-host-qualification.md` using the proposal contents defined in `AGENTS.md`. Do not silently relax measurement requirements to accommodate the VM.

## 16. Commands run and outcomes

### Local repository

- File/document inventories with `rg --files -uu`: only the plan and `.DS_Store` existed initially.
- Git state commands before initialization: failed because no repository existed.
- `git init -b main`: initialized an empty repository after explicit user approval.
- `git remote add origin ...`: configured the user-specified remote; no push.
- `git ls-remote --refs origin`: exit 0 with no refs.
- Git status/history/worktree inspection: unborn `main`, one worktree, no history.
- OS/hardware/tool versions: captured; local host is arm64 macOS, not Target 0.

### Primary development server

- SSH banner/host-key probes: stable OpenSSH 9.6p1 Ubuntu server; host key pinned temporarily for the session.
- Public-key authentication: succeeded as `ubuntu`; server advertised public-key-only authentication.
- `hostnamectl`, `/etc/os-release`, `uname`, `lscpu`, `lscpu -e`, and `lscpu -C`: captured OS, VM, CPU, ISA, topology, and cache facts.
- `/proc/cpuinfo` and sysfs/proc controls: captured frequency/microcode visibility and missing governor/turbo controls.
- `taskset`: verified process affinity can be restricted to one vCPU.
- `perf stat`: unprivileged hardware-event access rejected; useful PMU access not yet evidenced.
- `lspci`, module/device checks: NVIDIA L4 PCI function visible; driver and device nodes absent.
- tool/package inventories: required C++ build stack and baseline libraries absent.

### Product verification

No configure, build, test, lint, sanitizer, code-generation, benchmark, or artifact-replay command was run because no corresponding repository implementation or command exists.

## 17. Checkpoint conclusion

The repository is understood well enough to begin M0 after review, but it is not ready for compiler implementation. The core architectural thesis, Target 0 boundaries, IR separation, numerical obligations, benchmark discipline, and milestone order are clear. The missing foundation is deliberate and total: M0 must establish the falsifiable claim and measurement contract before M1 types or M2/M3 software begin.
