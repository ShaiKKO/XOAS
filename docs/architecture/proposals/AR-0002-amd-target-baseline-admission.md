# AR-0002: AMD Target Baseline Admission

**Status:** Approved — Option 1

**Decision owner:** User / architecture authority

**Prepared:** 2026-08-29

## Requested decision

Admit AMD AOCL-BLAS as a required dense `float32` comparator for the
designated physical AMD Target 0 host. Preserve OpenBLAS, LIBXSMM, and every
other already admitted baseline when applicable. Treat Intel oneMKL as
applicable only when its installed implementation, license, numerical
semantics, and target behavior satisfy the existing admission rules; it does
not substitute for an AMD-vendor baseline on this target.

This decision changes the admitted comparator set. It does not approve a
specific AOCL artifact, accept a license, install software, modify the host,
or qualify the host. Those actions require the separately reviewed Target 0
qualification and provisioning plan.

## Affected specifications, interfaces, and milestones

- Build-plan M0 requirement to lock baseline libraries available on the
  reference machine.
- Build-plan measurement-quality gate and the requirement to compare every
  generated winner with the best serious applicable baseline.
- [`../../experiments/baseline-matrix.md`](../../experiments/baseline-matrix.md)
  admission and configuration policy.
- [`../050-benchmark-protocol.md`](../050-benchmark-protocol.md) baseline
  preregistration, artifact identity, thread control, and lifecycle rules.
- M0 target qualification and acceptance.
- M2 baseline adapters and every later performance claim.
- Future benchmark-result baseline identities and retained artifacts.

No product ABI, numerical contract, IR boundary, cache identity, or generated
artifact currently exists.

## Evidence motivating the change

The selected Target 0 candidate is a physical AMD Ryzen 9 7900X system. A
read-only capture on 2026-08-29 established:

- bare-metal x86-64 Linux with no detected virtualization boundary;
- AMD family 25/model 97/stepping 2 with 12 cores and two threads per core;
- AVX2, FMA, and AVX-512 exposure;
- working privileged `cycles` and `instructions` PMU events;
- an observable `amd-pstate-epp` frequency policy and boost control;
- an AMD `k10temp` hardware-monitor source;
- no installed OpenBLAS, AOCL-BLAS, or LIBXSMM library.

Host access aliases, login identities, credentials, and network coordinates
are deliberately excluded from repository evidence.

AMD documents AOCL as optimized for Zen-based EPYC, Ryzen, and Threadripper
processors. Its AOCL-BLAS distribution provides single-threaded binaries,
Zen-family dynamic dispatch, and CBLAS-compatible dense operations. The
official sources controlling later artifact selection are:

- [AMD AOCL 5.3 download and checksum inventory](https://www.amd.com/en/developer/aocl.html)
- [AOCL-BLAS prebuilt-binary documentation](https://docs.amd.com/r/en-US/57404-AOCL-user-guide/4.1.8.-Using-Pre-Built-Binaries)
- [AOCL dynamic-dispatch documentation](https://docs.amd.com/r/en-US/57404-AOCL-user-guide/Using-Dynamic-Dispatch)
- [AMD AOCL source integration repository](https://github.com/amd/aocl)

The existing policy admits Intel oneMKL as a vendor baseline for an Intel
target but names no AMD-vendor implementation. On an AMD target, omitting
AOCL-BLAS could allow XOAS to claim a win without competing against the most
direct vendor-optimized dense comparator.

## Alternatives considered

### Option 1: Admit AOCL-BLAS in addition to the existing set

Require an exact official AOCL-BLAS release or source revision, artifact hash,
build provenance, target-dispatch evidence, single-thread proof, numerical
admission, setup accounting, and lifecycle accounting.

**Advantages:** preserves the strongest-baseline rule on AMD hardware; uses a
vendor implementation designed for Zen/Ryzen; makes a positive result more
defensible.

**Disadvantages:** adds provisioning, licensing, adapter, configuration-search,
and review work; AOCL may win and therefore raise the proof bar.

### Option 2: Use the Ubuntu BLIS package as an AMD proxy

Admit the distribution's generic BLIS package instead of AOCL-BLAS.

**Advantages:** simple package provenance and installation.

**Disadvantages:** the repository package is not evidence that the current
AMD-vendor Zen 4 implementation was tested; a favorable XOAS result would
remain vulnerable to a stronger omitted comparator.

### Option 3: Keep the Intel-oriented baseline set unchanged

Use OpenBLAS and LIBXSMM on AMD and classify oneMKL according to availability.

**Advantages:** no architecture or provisioning change.

**Disadvantages:** knowingly omits the direct AMD-vendor dense baseline and
weakens the controlling best-applicable-baseline claim.

## Recommendation

Approve **Option 1**. Admit AOCL-BLAS without removing any existing applicable
baseline. Select and pin the exact AOCL artifact only in the reviewed host
qualification plan after checking distribution terms, hashes, build/runtime
dependencies, and coexistence with the other libraries.

Use the single-threaded library path for Target 0. If only a multithreaded path
is available, it must prove one effective worker thread before admission.
Record runtime architecture dispatch rather than inferring it from the host.

## Correctness and numerical impact

This proposal does not change `strict`, `contracted`, or any later numerical
mode. AOCL-BLAS must pass the same independent-oracle checks as every other
baseline, including finite random values, exact small integers, cancellation,
wide magnitudes, signed zero, subnormals, infinities, and NaNs where the active
mode claims support.

The adapter must record contraction behavior, floating-point environment,
FTZ/DAZ state, row-major semantics, transpose state, `alpha=1`, `beta=0`, and
overwrite behavior. A failure makes that configuration inapplicable; it does
not weaken the numerical contract.

## ABI, identity, cache, artifact, and migration impact

- No XOAS public ABI or runtime cache identity changes.
- Benchmark/result identity must include the exact AOCL release or source
  revision, artifact hash, build configuration, compiler/runtime dependencies,
  dispatch controls, loaded-library path, and thread controls.
- Changing any of those facts invalidates affected baseline evidence and
  winner selections.
- AOCL artifacts and licenses follow the later approved third-party retention
  policy; no binary is committed merely because it was installed.
- Existing `gpu-2` development artifacts remain non-authoritative for Target 0
  performance and compatibility.

## Benchmark and performance-gate impact

- AOCL-BLAS competes wherever its `float32` GEMM semantics are applicable.
- The fastest correct admitted configuration remains the controlling baseline;
  AOCL-BLAS does not receive preferred status.
- Setup, initialization, packing, persistent bytes, kernel time, and lifecycle
  break-even are recorded independently.
- Losing and failed AOCL configurations remain evidence.
- No threshold, corpus partition, sample count, confidence rule, or outlier
  policy changes.
- No performance claim is authorized by this proposal.

## Work blocked by the decision

Until the approved decision is integrated into the baseline policy:

- the Target 0 baseline set cannot be frozen for the AMD host;
- the host qualification/provisioning plan cannot name its final baseline
  package set;
- M0 cannot lock reference-machine library identities;
- M1 remains blocked by the open M0 gate.

## Work that can continue independently

- Read-only host capture and collision checks.
- Review of official AOCL distribution, source, checksum, and license facts.
- Drafting reversible measurement-control probes that do not assume an AOCL
  artifact.
- Independent review of existing M0 documents and evidence.

## Decision record

On 2026-08-29, after the physical AMD host was designated as the Target 0
measurement candidate, the user selected the head engineering recommendation:
Option 1, add AOCL-BLAS while retaining every existing applicable comparator.

After reviewing this written record, the user approved its exact terms on
2026-08-29. This approves baseline-policy integration and preparation of the
separate qualification/provisioning plan. It does not itself accept a
third-party license, install software, modify the host, qualify the target, or
authorize a performance claim.
