# M0 Acceptance Record

**Milestone:** M0 — Charter, prior-art map, and benchmark protocol

**Decision:** OPEN — not accepted, not rejected

**Evaluation date:** 2026-08-28

**Verified integration subject:** `3d635d3c6e142cbed60b600a0dc0fa2f894d073b` (`docs: integrate M0 evidence foundation`)

**AR-0001 decision integration:** `6904d49e4978f48d9ca3c5db29fac59bbc3233c6` (`docs: approve gpu-2 development-only role`)

**Development-toolchain intent:** `11d1b19371489f0f75cb01eeb078bf64897cf88b` (`ops: lock gpu-2 development toolchain intent`)

**Development-toolchain verification:** `ce1d27df6fda8b3d91dacadb6afbc6a2c83509c5` (`ops: verify gpu-2 development toolchain`)

**Development-toolchain subject tree state:** Clean; local `main` and `origin/main` matched the verification commit immediately after push.

**Subject tree state:** Clean at verification; `main` was one commit ahead of `origin/main` before this documentation-only evidence update.

## Controlling requirements

- [`../exact_instance_matrix_kernel_synthesizer_build_plan.md`](../exact_instance_matrix_kernel_synthesizer_build_plan.md), M0 and its prerequisite sections.
- [`../architecture/000-charter.md`](../architecture/000-charter.md).
- [`../architecture/050-benchmark-protocol.md`](../architecture/050-benchmark-protocol.md).
- Root [`../../AGENTS.md`](../../AGENTS.md).
- User's 2026-08-28 instruction to begin the first stage on a fresh repository and to use the current server as the primary development host.

The user approved AR-0001 Option 2: `gpu-2` is development-only and is not the Target 0 measurement host.
On 2026-08-29, the user designated a physical AMD Ryzen 9 7900X Linux
desktop as the replacement Target 0 measurement-host candidate. The host is
not yet qualified.

## Deliverable traceability

| M0 requirement | Evidence | State |
|---|---|---|
| Product charter and non-goals | [`../architecture/000-charter.md`](../architecture/000-charter.md) | Implemented and committed at `60044e8` |
| Lock Target 0 | Charter; target decision [`../architecture/proposals/AR-0001-target-0-host-qualification.md`](../architecture/proposals/AR-0001-target-0-host-qualification.md) | Option 2 integrated at `6904d49`; physical AMD replacement candidate designated but not qualified |
| Required prior-art comparison | [`../experiments/prior-art-matrix.md`](../experiments/prior-art-matrix.md) | Implemented and committed at `30616bc` |
| Baseline selection | [`../experiments/baseline-matrix.md`](../experiments/baseline-matrix.md) | Admission policy committed at `30616bc`; selected measurement host and its binaries unavailable |
| Benchmark protocol | [`../architecture/050-benchmark-protocol.md`](../architecture/050-benchmark-protocol.md) | Implemented and committed at `00afbf7`; no harness exists |
| Result schema | [`../../schemas/benchmark-result-v1.schema.json`](../../schemas/benchmark-result-v1.schema.json) and non-claiming example | Draft-2020-12 meta-schema and example validation passed on `gpu-2`; the example remains synthetic and non-claiming |
| Synthetic and application sources | [`../experiments/corpus-policy.md`](../experiments/corpus-policy.md) and three corpus manifests | Frozen and committed at `8a7032b`; M1 materialization not implemented |
| Holdout | [`../../benchmarks/manifests/holdout-v0.json`](../../benchmarks/manifests/holdout-v0.json) | Frozen, public identity, no measurements, design use prohibited |
| Reference hardware fingerprint | [`../../benchmarks/manifests/target-gpu-2-candidate.json`](../../benchmarks/manifests/target-gpu-2-candidate.json) | Historical candidate capture committed at `6e6adf3`; its development toolchain is now verified, but Option 2 keeps it ineligible as the reference target |
| Architecture index and operating manual | [`../architecture/README.md`](../architecture/README.md) and root [`../../AGENTS.md`](../../AGENTS.md) | Integrated and verified at `3d635d3` |

## Exit-gate statement

XOAS v0 specializes exact stable support of a runtime-valued sparse `float32` left operand into single-threaded x86-64 Linux `C=A*B` code and empirically selects only a verified compatible lifecycle winner. EGGS is the closest reviewed match to the stable-pattern/dynamic-values input, SABLE v5 to per-matrix hybrid regional C generation, JITSpMM to exact SpMM instruction specialization, and FFTW3/TVM MetaSchedule to measured planning. XOAS's scoped distinction is the combined exact-support contribution program, explicit numerical-legality boundary, bounded arithmetic/schedule search, pre-timing correctness and compatibility gates, target-measured baseline competition, lifecycle accounting, replay/invalidation provenance, and fallback. The claim is falsified if the qualified-target frozen benchmarks fail the `2x` proof threshold or the `1.5x` product-class geometric mean plus `2x` application threshold under the locked confidence rules.

The team can state the required paragraph, but the gate remains open because the reference machine and executable baseline availability are not locked.

## Verification performed

### Repository/document checks

- Required charter headings and M0 research-anchor names were checked with `rg`.
- Required baseline names and policies were checked with `rg`.
- Commit `3d635d3c6e142cbed60b600a0dc0fa2f894d073b` passed `git diff --check` from a clean tree.
- A repository-relative Markdown-link audit resolved every local link across `AGENTS.md` and 12 documentation files.
- The Task 6 placeholder scan initially matched its own literal in the committed implementation plan. The command was corrected to avoid embedding its search terms, then the placeholder and secret scans passed at the verified subject commit.
- Secret scans found no committed network coordinates, credential values, key paths, or private-key material. A first scanner revision matched its own sensitive literals; the plan was corrected before the initial commit.

### JSON checks

- `python3 -m json.tool` passed for the benchmark-result schema, synthetic example, and all corpus manifests.
- Standard-library assertions passed at `3d635d3` for 37 unique/disjoint cases, four pinned source identities, partition membership, shapes, seed lengths, source references, coordinate counts, holdout state, ten raw-sample ordering records, statistical interval ordering, target qualification state, and absence of secret provenance fields.
- On `gpu-2`, `jsonschema` 4.10.3 passed draft-2020-12 meta-schema validation and validated the synthetic benchmark-result example.
- The development-toolchain schema and installed lock passed draft-2020-12 validation with format checks, stable configuration-digest verification, live package-closure checks, and live executable-hash checks.

### External corpus evidence

Official NIST artifacts were downloaded into temporary storage, never committed, and checked:

| Matrix | Compressed SHA-256 | Decompressed SHA-256 | Structural normalization fact |
|---|---|---|---|
| WEST0067 | `228c55ac4746e8be7bb7f7e03e590d7066cdfe9ba9c06616dd19c04104ff6adb` | `c2b90a218948d55185f7068fa0c4dd9f5322a8321940830b1a303200b486b0fb` | 294 stored/general coordinates |
| ARC130 | `574287deae85599973f1a022b832447f01787b73e542b051d42dc9b08b77ed6a` | `c04d50cb2b1e29b0cac38e90437ec005376c07cee07a31804d6a7e2f6ab9705c` | 1,282 stored coordinates, including 245 explicit numerical zeros retained as support |
| LUND_A | `ae81bed9b45552f4ac42ce94feebd2a951bd1d1e22d7496d807a57e4b62da4f8` | `9d9cc6b77f0e3057317009c5e06d658e40a137a3d551ff298654d26eccce8c25` | 1,298 stored symmetric coordinates, 2,449 after expansion |
| ASH85 | `f183acc1101b11a63864210713de295cdd0a98fc67bb756316a8d510933e92b3` | `9e6fd11538539680aa48e7974529ad518e2bcfc5849ca464c274e90d1b850c73` | 304 stored symmetric pattern coordinates, 523 after expansion |

The temporary files are retrieval evidence only. M1 must implement reproducible fetch/materialization and canonical support digests.

### Candidate host capture

A fresh read-only capture at `2026-08-28T23:01:51Z` verified:

- Ubuntu 24.04.4 LTS, kernel `6.8.0-137-generic`, glibc 2.39;
- KVM/OpenStack x86-64 VM;
- Intel Xeon Gold 6348 guest identity, family 6/model 106/stepping 6;
- 16 logical CPUs, eight cores, SMT active, one NUMA node;
- AVX2/FMA and broad AVX-512 exposure;
- TSC clocksource;
- `perf_event_paranoid=4` and unavailable unprivileged task-clock/cycles events;
- no cpufreq/intel_pstate control surfaces;
- Git 2.43.0 and Python 3.12.3 present;
- the exact versioned Clang/LLVM 21, CMake, Ninja, Doxygen, SQLite, and support-tool development stack installed and behaviorally verified;
- admitted measurement baseline libraries absent.

Credentials, access coordinates, and key material are excluded from repository evidence.

## Performance and correctness evidence

No compiler, generated candidate, independent executable oracle, baseline adapter, or benchmark harness exists. No timing has been performed and no speedup, correctness, compatibility, lifecycle, or break-even claim is made.

The benchmark-result example is synthetic and explicitly non-claiming.

## Review

- Head engineering self-review: performed incrementally and again against the exact `3d635d3` diff, build-plan M0 work/deliverables/exit gate, and M0 implementation plan.
- Independent implementation-quality review: not performed. No subagent or external reviewer was requested for this stage.
- Architecture approval: AR-0001 Option 2 approved by the user on 2026-08-28 and integrated at `6904d49e4978f48d9ca3c5db29fac59bbc3233c6`.

Self-review is not represented as independent review.

## Deviations and evidence gaps

1. The build-plan front matter still says `Proposed architectural program`; the user handoff approved it as execution authority. The charter and index record the authority distinction without rewriting technical semantics.
2. The historical `gpu-2` VM still denies unprivileged cycles and instructions and remains ineligible. The designated AMD candidate exposes working privileged events, but its PMU policy and reboot stability are not yet qualified.
3. The M0 instruction to lock libraries available on the reference machine cannot close because the designated AMD candidate has no admitted libraries installed and its AOCL-BLAS admission decision is awaiting written review.
4. Corpus supports are specified but not materialized by code; no canonical support digests exist.
5. Independent review remains absent. Task 6 self-review is recorded but is not substituted for it.

## Gate decision and blockers

M0 remains **OPEN**. Closing it requires:

1. qualified, approved Target 0 manifest for the designated physical AMD host required by Option 2;
2. exact installed compiler and serious baseline-library identities on that target;
3. independent review or explicit user acceptance of the documented review model.

## Earliest executable next slice

The earliest valid slice is still within M0:

1. approve the written AOCL-BLAS admission decision;
2. write and review the designated AMD host's qualification/baseline plan;
3. install and pin the admitted baselines on that selected measurement host;
4. enable/verify measurement controls and PMU evidence;
5. run non-claiming qualification smoke and noise characterization;
6. add the qualified target manifest and update this acceptance record.

The reviewed engineering-quality-gates plan is now unblocked as independent development-environment work, but it cannot substitute for the measurement-host critical path or authorize M1 product code.

M1 product implementation does not begin while M0 remains open.
