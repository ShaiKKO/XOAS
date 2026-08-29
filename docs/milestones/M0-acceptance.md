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
The user also approved AR-0002 Option 1, admitting AOCL-BLAS without removing
any existing applicable comparator.

## Deliverable traceability

| M0 requirement | Evidence | State |
|---|---|---|
| Product charter and non-goals | [`../architecture/000-charter.md`](../architecture/000-charter.md) | Implemented and committed at `60044e8` |
| Lock Target 0 | Charter; target decision [`../architecture/proposals/AR-0001-target-0-host-qualification.md`](../architecture/proposals/AR-0001-target-0-host-qualification.md) | Option 2 integrated at `6904d49`; physical AMD replacement candidate designated but not qualified |
| Required prior-art comparison | [`../experiments/prior-art-matrix.md`](../experiments/prior-art-matrix.md) | Implemented and committed at `30616bc` |
| Baseline selection | [`../experiments/baseline-matrix.md`](../experiments/baseline-matrix.md) and [`../../toolchains/target0-amd-ryzen9-7900x-v1.lock.json`](../../toolchains/target0-amd-ryzen9-7900x-v1.lock.json) | Admission policy committed at `30616bc`; exact AOCL-BLAS, OpenBLAS, and LIBXSMM source builds are installed and artifact-verified, but no baseline adapter is numerically admitted |
| Benchmark protocol | [`../architecture/050-benchmark-protocol.md`](../architecture/050-benchmark-protocol.md) | Implemented and committed at `00afbf7`; no harness exists |
| Result schema | [`../../schemas/benchmark-result-v1.schema.json`](../../schemas/benchmark-result-v1.schema.json) and non-claiming example | Draft-2020-12 meta-schema and example validation passed on `gpu-2`; the example remains synthetic and non-claiming |
| Synthetic and application sources | [`../experiments/corpus-policy.md`](../experiments/corpus-policy.md) and three corpus manifests | Frozen and committed at `8a7032b`; M1 materialization not implemented |
| Holdout | [`../../benchmarks/manifests/holdout-v0.json`](../../benchmarks/manifests/holdout-v0.json) | Frozen, public identity, no measurements, design use prohibited |
| Reference hardware fingerprint | [`../../benchmarks/manifests/target-gpu-2-candidate.json`](../../benchmarks/manifests/target-gpu-2-candidate.json) | Historical candidate capture committed at `6e6adf3`; its development toolchain is now verified, but Option 2 keeps it ineligible as the reference target |
| Architecture index and operating manual | [`../architecture/README.md`](../architecture/README.md) and root [`../../AGENTS.md`](../../AGENTS.md) | Integrated and verified at `3d635d3` |
| Target qualification process contract | [`../../schemas/target0-host-qualification-v1.schema.json`](../../schemas/target0-host-qualification-v1.schema.json), [`../../tools/target0/qualification_probe.cpp`](../../tools/target0/qualification_probe.cpp), and behavioral tests | Task 1 implemented at `8a247a2`; this is non-claiming host-qualification tooling and does not qualify the AMD target |
| Target capture and reversible controls | [`../../tools/target0/capture_host.py`](../../tools/target0/capture_host.py), [`../../tools/target0/measurement_session.sh`](../../tools/target0/measurement_session.sh), and fixture tests | Task 2 implemented at `864f7fa` and repository-root integration repaired at `b7371ae`; no real measurement control was changed |
| Physical candidate and provisioning lock | [`../targets/target0-amd-ryzen9-7900x-v1.md`](../targets/target0-amd-ryzen9-7900x-v1.md), [`../../benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json`](../../benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json), and closed lock/schema | Task 3 resolved exact pre-state at `ee57ff5`; Task 4 installed and verified the 26-package closure plus AOCL-BLAS, OpenBLAS, and LIBXSMM against clean subject `16d698d`, with repository evidence committed at `9d44f64`; the candidate remains unqualified |

## Exit-gate statement

XOAS v0 specializes exact stable support of a runtime-valued sparse `float32` left operand into single-threaded x86-64 Linux `C=A*B` code and empirically selects only a verified compatible lifecycle winner. EGGS is the closest reviewed match to the stable-pattern/dynamic-values input, SABLE v5 to per-matrix hybrid regional C generation, JITSpMM to exact SpMM instruction specialization, and FFTW3/TVM MetaSchedule to measured planning. XOAS's scoped distinction is the combined exact-support contribution program, explicit numerical-legality boundary, bounded arithmetic/schedule search, pre-timing correctness and compatibility gates, target-measured baseline competition, lifecycle accounting, replay/invalidation provenance, and fallback. The claim is falsified if the qualified-target frozen benchmarks fail the `2x` proof threshold or the `1.5x` product-class geometric mean plus `2x` application threshold under the locked confidence rules.

The team can state the required paragraph, but the gate remains open because
the designated reference candidate has not passed controlled qualification
campaigns or the accepted review gate. Executable baseline availability is now
locked; numerical adapter admission remains later work.

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
- The Target 0 process schema passed draft-2020-12 meta-validation and validated real build-tree probe records on `gpu-2`; closed-schema mutations rejected claim inflation, unknown fields, duplicate rounds, and missing samples.
- The Target 0 toolchain-lock schema passed draft-2020-12 meta-validation and validated the installed lock. On the physical host, all 288 recorded installed-file hashes matched the live versioned prefix and the configuration digest recomputed exactly.

### Target 0 Task 4 verification

The published evidence head
`9b28162152bfd4c0329a2d5de59f23c65f832a85` passed both pinned `gpu-2`
aggregates:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target quality
cmake --preset dev-release
cmake --build --preset dev-release --target quality
```

Each configuration passed repository policy, formatting, documentation,
Clang-Tidy, the isolated ASan/UBSan gate, all 33 CTest cases, and the Target 0
tooling tests. On the physical host, draft-2020-12 lock validation, canonical
configuration-digest recomputation, and all 288 live installed-file hashes
passed. A direct full repository-policy diagnostic passed there only after a
temporary exclusion for ShellCheck 0.11 SC2329; no exclusion was committed,
and the authoritative pinned `gpu-2` policy passed without accommodation.

### Target qualification process checks

On `gpu-2`, the Task 1 implementation passed the complete Debug, Release, and
ASan/UBSan CTest surfaces. The targeted command is:

```bash
cmake --build --preset dev-debug \
  --target xoas-target0-qualification-probe
ctest --preset dev-debug \
  -R '^target0-qualification-probe$' --output-on-failure
```

The test runs two real fixed-count processes, checks the literal seed-42 round-0
checksum `b6347d16b98f0445`, validates deterministic fields and ordered samples,
exercises invalid CLI/CPU/output behavior, and accepts closed failure evidence.
No retained output is a performance claim or target-qualification result.

The Task 2 host tools passed:

```bash
cmake --build --preset dev-debug --target target0-host-tools
ctest --preset dev-debug \
  -R '^target0-host-tools-' --output-on-failure
```

Capture fixtures proved the closed non-secret record, exact SMT/cache/NUMA
topology parsing, TSC and PMU requirements, credential-field rejection, and
preferred-rank/interrupt/CPU selector order. Session fixtures observed active
performance policy and sibling-offline state from inside the command, then
proved exact restoration after success, exit 23, `TERM`, and an injected
sysfs write failure. This evidence does not establish behavior on the physical
AMD host. Task 3 subsequently exercised the fixed read-only capture boundary;
the real session controller remains unexecuted until Task 5.

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

The designated physical AMD candidate was captured separately at
`2026-08-29T18:01:12Z`. The closed record bound Ubuntu 26.04 `resolute`, Ryzen
9 7900X family 25/model 97/stepping 2, 24 logical CPUs/12 cores, one NUMA node,
TSC, bare metal, exact cache/frequency/thermal facts, and working privileged
cycles/instructions to clean planning commit `60c4eeb`. Capture SHA-256 is
`019376b74df12d12129dca2618d215dfcd32ad51cdb0ca06b51b19d0977c0106`.

The complete sorted 1,502-package pre-state and zero holds are retained in the
toolchain lock. The version-pinned nine-package request installed its simulated
26-package closure with zero upgrades/removals, and all closure file checks
passed. AOCL-BLAS 5.3.2, OpenBLAS 0.3.34, and corrected-prefix LIBXSMM 2.1.0
passed their upstream suites, deterministic smoke probes, single-thread checks,
and explicit loader-coexistence checks. The lock retains 288 regular installed
file hashes and configuration SHA-256
`810c21d5891b67e7aaccd4992318ad7dd86902070aa947baa817ef7ea5914de3`.
Four build-source license files were hashed. The pinned JITSpMM revision
contains no license statement, so its adapter/use is explicitly blocked and
deferred to M2 without removing it from admission.

An administrator reboot interrupted Task 4 and cleared volatile temporary
logs. Persistent source/build evidence and package-manager history were
recovered, rechecked, and re-indexed. The event is not a controlled campaign,
does not satisfy reboot approval, and is not qualification evidence.

## Performance and correctness evidence

No compiler, generated candidate, independent executable oracle, baseline adapter, or benchmark harness exists. No timing has been performed and no speedup, correctness, compatibility, lifecycle, or break-even claim is made.

The benchmark-result example is synthetic and explicitly non-claiming.

## Review

- Head engineering self-review: performed incrementally against the exact Task 4 provisioning subject `16d698d`, installed lock, live artifact hashes, retained upstream logs, build-plan M0 requirements, and the active AMD qualification plan. Earlier M0 integration self-review remains bound to `3d635d3`.
- Independent implementation-quality review: not performed. No subagent or external reviewer was requested for this stage.
- Architecture approval: AR-0001 Option 2 approved by the user on 2026-08-28 and integrated at `6904d49e4978f48d9ca3c5db29fac59bbc3233c6`.

Self-review is not represented as independent review.

## Deviations and evidence gaps

1. The build-plan front matter still says `Proposed architectural program`; the user handoff approved it as execution authority. The charter and index record the authority distinction without rewriting technical semantics.
2. The historical `gpu-2` VM still denies unprivileged cycles and instructions and remains ineligible. The designated AMD candidate exposes working privileged events, but its PMU policy and reboot stability are not yet qualified.
3. The physical host exposes Python 3.14.4 while repository configuration pins Python 3.12.3; a direct policy diagnostic also observes ShellCheck 0.11 SC2329 differences from the pinned development lane. Qualification-tool deployment is not yet closed.
4. JITSpMM has no license statement at the pinned inspection revision; no build or use is authorized unless M2 resolves that boundary.
5. Corpus supports are specified but not materialized by code; no canonical support digests exist.
6. Independent review remains absent. Task 6 self-review is recorded but is not substituted for it.
7. The qualification plan says Task 7 may set qualification true only when every requirement and review gate passes, while the candidate manifest defers `baseline_numerical_admission` to M2 and M1 is blocked on M0. This dependency conflict must be resolved explicitly before the Task 7 decision; it does not block Task 5 infrastructure qualification.

## Gate decision and blockers

M0 remains **OPEN**. Closing it requires:

1. qualified, approved Target 0 manifest for the designated physical AMD host required by Option 2;
2. exact qualification-tool deployment and two accepted controlled campaigns;
3. resolution of the Task 7 versus M2 numerical-admission dependency conflict;
4. independent review or explicit user acceptance of the documented review model.

## Earliest executable next slice

The earliest valid slice is still within M0:

1. resolve an exact, reviewed deployment path for the already-implemented
   qualification tools on the physical host without weakening the development
   lock or repository checks;
2. execute the Task 5 pre-session and reversible-control checks;
3. run non-claiming qualification smoke, PMU, and noise characterization;
4. complete campaign one;
5. stop for separate approval before any controlled campaign reboot.

The reviewed engineering-quality-gates plan is now unblocked as independent development-environment work, but it cannot substitute for the measurement-host critical path or authorize M1 product code.

M1 product implementation does not begin while M0 remains open.
