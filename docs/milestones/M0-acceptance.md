# M0 Acceptance Record

**Milestone:** M0 — Charter, prior-art map, and benchmark protocol

**Decision:** OPEN — not accepted, not rejected

**Evaluation date:** 2026-08-28

**Verified integration subject:** `3d635d3c6e142cbed60b600a0dc0fa2f894d073b` (`docs: integrate M0 evidence foundation`)

**AR-0001 decision integration:** `6904d49e4978f48d9ca3c5db29fac59bbc3233c6` (`docs: approve gpu-2 development-only role`)

**Development-toolchain intent:** `11d1b19371489f0f75cb01eeb078bf64897cf88b` (`ops: lock gpu-2 development toolchain intent`)

**Development-toolchain verification:** `ce1d27df6fda8b3d91dacadb6afbc6a2c83509c5` (`ops: verify gpu-2 development toolchain`)

**Development-toolchain subject tree state:** Clean; local `main` and `origin/main` matched the verification commit immediately after push.

**Qualification-tool implementation subject:** `a312aa2bbbb403b31ffb67cf40200da063527a4f`
(`build: add native Target 0 qualification bundle preparation`)

**Campaign-runner implementation subject:**
`db0eb8797b54f26eb9a86417af9e0eb626f9669f`
(`fix: keep campaign execution source clean`), building on core implementation
`cf149ae25bbea5b55577791b8511ae9d2489445e`.

**Campaign-runner exact quality subject:**
`7b486e1fe6ef56e414c65ba0cf09ebc9bbc77dc6`
(`docs: bind Target 0 campaign runner evidence`).

**Protected-main ancestry synchronization:**
`f90c27d57586e1314568929c86bb1826500af730`; its tree is byte-identical to
core implementation subject `cf149ae` and precedes source-clean execution fix
`db0eb87`.

**Qualification-tool implementation tree:** `b7279b22e40c848da7aecd7f3e4197a6857aa85f`

**Qualification-tool deployment receipt:**
[`../../benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json`](../../benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json),
SHA-256 `0d62ab0c143fa224d31e4cde925e4c30a5a512c5cd391c4d8cd030b6608572ff`

**Qualification-tool protected-main integration:** PR #4, squash merge
`a51a7f943689116bac69062c3f8a8e620740bcae`.

**Subject tree state:** The campaign branch was clean and pushed at
`7b486e1fe6ef56e414c65ba0cf09ebc9bbc77dc6` before this documentation update;
local `main` and `origin/main` matched protected merge `a51a7f9`. The active
campaign branch was the only remaining task branch.

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
| Qualification-tool deployment implementation | [`../../tools/target0/prepare_qualification_bundle.py`](../../tools/target0/prepare_qualification_bundle.py), [`../../tools/target0/verify_qualification_bundle.py`](../../tools/target0/verify_qualification_bundle.py), the closed [`../../schemas/target0-qualification-tool-bundle-v1.schema.json`](../../schemas/target0-qualification-tool-bundle-v1.schema.json), accepted [`../../benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json`](../../benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json), and [`../adr/IDR-0002-target0-qualification-tool-deployment.md`](../adr/IDR-0002-target0-qualification-tool-deployment.md) | Exact implementation subject `a312aa2bbbb403b31ffb67cf40200da063527a4f` passed Debug 38/38, Release 38/38, and sanitizer 3/3 on `gpu-2`, establishing the deployment path. At clean source `a396f64`, the replacement physical host bundle produced byte-identical dual builds, passed 5/5 compatibility tests, and matched fresh physical and `gpu-2` verification for the manifest, inventory, executable, and normalized executable-identity digests. The current receipt binds that replacement. Deployment is closed without campaign, qualification, reboot, host-control, or performance authority. |
| Target qualification campaign runner | [`../../schemas/target0-qualification-campaign-v1.schema.json`](../../schemas/target0-qualification-campaign-v1.schema.json), [`../../tools/target0/qualification_campaign.py`](../../tools/target0/qualification_campaign.py), [`../../tools/target0/run_qualification_campaign.py`](../../tools/target0/run_qualification_campaign.py), [`../../tools/target0/verify_qualification_campaign.py`](../../tools/target0/verify_qualification_campaign.py), and [`../adr/IDR-0003-target0-qualification-campaign-runner.md`](../adr/IDR-0003-target0-qualification-campaign-runner.md) | Implementation Tasks 1–6 plus source-clean runner/verifier execution are committed through `db0eb87`; exact clean evidence subject `7b486e1` passed complete Debug and Release quality on `gpu-2`. Replacement bundle and preflight passed at source `1141713c`; campaign-one attempt 1 was retained as `restoration_failure` before PMU after CPU 2 EPP failed to restore, and bounded recovery returned exact pre-state. Repair reds are at `485eb6b` and `c68474c`; exact reviewed repair `c9af373` passed complete Debug and Release 50/50 suites, sanitizer 3/3, and repository policy on `wineth-ubuntu`. At clean merged source `a396f64`, a bounded physical restoration-only cycle passed, the fresh native bundle passed physical plus byte-identical `gpu-2` verification, and replacement Task 9 preflight independently accepted CPU 1/sibling 13. Accepted campaign one, reboot, qualification, and performance claims remain open. |

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

On 2026-08-30, explicit user direction superseded the earlier decision not to
install a supplemental quality environment on the physical host. The isolated
toolchain in
[`../adr/IDR-0004-wineth-quality-toolchain.md`](../adr/IDR-0004-wineth-quality-toolchain.md)
preserves Ubuntu's system Python, Doxygen, and ShellCheck while supplying the
repository-pinned versions to XOAS. Clean `main` subject `93f164c` passed the
complete Debug and Release quality aggregates, explicit 50/50 replays for
both configurations, and the final isolated 3/3 sanitizer gate on
`wineth-ubuntu`, without a suppression or source change.

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

The qualification-tool bundle implementation first passed the complete targeted
development surface on `gpu-2`:

```bash
cmake --build --preset dev-debug \
  --target xoas-target0-qualification-probe target0-host-tools
ctest --preset dev-debug \
  -R '^target0-(qualification-bundle|qualification-probe|host-tools-)' \
  --output-on-failure
```

All eight tests passed, including real probe execution, capture/session
fixtures, closed schema, preflight, dual-build, ELF/runtime inspection, and
fresh-process finalization verification. A regression test first reproduced
and then closed checkout-before-output ordering drift.

### Qualification-tool deployment verification

Clean implementation subject `a312aa2bbbb403b31ffb67cf40200da063527a4f`
passed the complete pinned `gpu-2` development contract:

- Debug quality and CTest: 38/38 passed;
- Release warning build and CTest: 38/38 passed;
- isolated ASan/UBSan CTest: 3/3 passed;
- repository policy, formatting, Doxygen, and Clang-Tidy passed.

The native physical preparation produced accepted bundle
`target0-qualification-tools-a312aa2bbbb403b3`. Both independent native
builds produced the same executable bytes, and all 5/5 compatibility checks
passed. Fresh-process verification on the physical host and on `gpu-2` matched:

- bundle manifest SHA-256
  `0d62ab0c143fa224d31e4cde925e4c30a5a512c5cd391c4d8cd030b6608572ff`;
- inventory SHA-256
  `4ead541d5c43be871833509a561fb4c170ec83d0f297343f8dd6e78058407b20`;
- executable SHA-256
  `2b2352baf105ccb2b2ef3a1bb89046fc7a8259224f0c928747f473d11e215b8f`;
- normalized executable-identity SHA-256
  `a976d18ae90df3d008749683592f9cc7663b7e94d667d5e3eb78654344b2ad25`.

The receipt is canonical schema-valid JSON and is bound by the adjacent digest
record and repository-policy cross-check to the target manifest, implementation
commit/tree, provisioning configuration, 11 retained source identities,
compiler/linker identities, dual-build result, compatibility result, and
external-private two-host retention classification. The failed earlier
`bc800ff` physical build attempt remains retained as non-claiming evidence.

No campaign, real measurement-session control, benchmark, controlled campaign
reboot, qualification, or performance claim occurred. Deployment compatibility
timing is not benchmark evidence.

### Campaign-runner implementation verification

Exact implementation subject
`db0eb8797b54f26eb9a86417af9e0eb626f9669f` contains the closed campaign
schema/contract, dedicated privileged-`perf` session mode, read-only preflight,
five primary process and nine PMU-session orchestration, deterministic
finalization, and fresh replay verifier. On `gpu-2`, the focused final gate
passed repository policy and 19/19 Target 0 tests in 97.96 seconds. The
integration fixture executes the real runner and session-controller boundary,
retains five ordered 30-sample primary records, required and optional PMU
records, finalizes canonical evidence, and rejects raw, identity, selector,
thermal, restoration, inventory, acceptance, and whole-file-set tampering even
after outer digests are deliberately rebound.

The same subject passed the complete Debug `quality` aggregate and an explicit
50/50 Debug CTest replay; the aggregate included repository policy,
formatting, Doxygen, Clang-Tidy, and the isolated 3/3 ASan/UBSan gate. Exact
clean evidence subject `7b486e1fe6ef56e414c65ba0cf09ebc9bbc77dc6`
passed both complete Debug and Release quality aggregates and explicit 50/50
CTest replays, the isolated 3/3 sanitizer gate, repository policy, and final
source-clean checkout verification. Task 7 is closed. Protected-main ancestry
synchronization `f90c27d` changed no bytes relative to the earlier `cf149ae`
tree. No physical checkout, live preflight, measurement control,
campaign, counter collection, reboot, or qualification decision occurred.

### Campaign-one attempt 1 rejection

At exact pushed source `1141713c3448eaaa392e09ace8924ebcaf0e38bd`, a
fresh physical-native bundle and matching `gpu-2` replica passed independent
verification. The physical read-only preflight accepted CPU 2 with sibling 14,
normalized boot-ID SHA-256
`20da156151d62d87c68308e4bf82f1469c0db20c713a4178a0623bcc6d2beb8c`,
load and session eligibility, TSC, required PMU availability, thermal state,
clean checkout, bundle, source, compiler, linker, and lock identity.

The first primary probe returned 0 and produced a schema-valid 30-sample
record, but the session controller returned restoration exit 70. Its retained
pre/post record proves that sibling, governor, and boost restored while EPP
remained `performance` instead of `balance_performance`. The runner published
closed `restoration_failure` rejection SHA-256
`e6458e2dac1097fa5649371c0815403708c7985da0b80d2ebf5c8b049efc5868`,
binding 11 diagnostic files. No process 2–5, PMU, campaign manifest, inventory,
or acceptance record exists. The public fresh verifier returned 2 and refused
the rejected root.

A bounded recovery wrote only CPU 2 EPP back to the retained pre-state.
Independent post-recovery capture matched sibling online 1, governor
`powersave`, EPP `balance_performance`, boost 1, boot, checkout, toolchain,
source, bundle, thermal, and stable host identities. The immutable rejected
root remains external and will not be retried or rewritten. No controlled
campaign reboot, qualification, or performance claim occurred.

### Physical restoration-only proof and fresh bundle candidate

At clean merged source
`a396f642d5c2ec6ed670cc2341170ec7d9f1a886`, one bounded
restoration-only session on CPU 2/sibling 14 completed around `/usr/bin/true`
with controller status 0. The canonical record reported `restored=true` and no
failure reasons. Independent live audit matched sibling online 1, governor
`powersave`, EPP `balance_performance`, and boost 1 to the record and pre-state.
The externally retained restoration-record SHA-256 is
`5b6e2cefbac4c8c96f5228139978f776d55aff0dcffb9dc9fb19812cb50236e7`.

The same clean source produced physical-native bundle
`target0-qualification-tools-a396f642d5c2ec6e`, accepted by preparation and a
fresh physical verifier. Its bundle-manifest, inventory, executable, and
normalized executable-identity SHA-256 values are
`15d58e20bbab593bd902782b917b79ba98a03cf1e79c784fbff2c450d23a99a0`,
`44d6ee1eec9791974098ce74c81647d1690bd0aef2bd54822e47635ebad1bbaf`,
`db82cd647e880b1780c2a5fb9d10f87398b184f35d4e84de9b6855db07fec015`,
and `753890dc53185727326bc5dba2585a59ed60bdf0465623dec3fb58bf63b388b3`.
The complete bundle was copied byte-for-byte to `gpu-2`. A fresh verifier in a
clean checkout at the same exact source accepted identical manifest,
inventory, executable, and normalized executable-identity digests.

### Replacement campaign-one preflight

The physical host remained clean and detached at exact source `a396f64` and
tree `7388f3a2b72ccac2352560c48d2e7eb310712330`. Fresh bundle verification
passed before the new read-only preflight. The canonical preflight SHA-256 is
`08a3253b44a2bc1c0dc89abd3463c20def73e0fc313ac468441b9ce65c31935e`;
the core-selection SHA-256 is
`718350bb2ff003000e1ed7ffd1f331fe0c52671cd56d21f3a5dde307bcead803`.
It selected CPU 1 and SMT sibling 13 at preferred rank 216 after a
60.001218589-second interrupt window with delta 1,988. Eligibility passed at
load `0.12`, three expected and zero root/unexpected sessions, bare metal,
TSC, cycles/instructions availability, and no thermal alarm, fault, or
threshold violation.

Independent replay verified the exact six-file root, canonical JSON, every
digest, all 115 inventory entries, 18 sources, toolchain, lock, boot,
repository, topology, and deterministic selection. A separate read-only
engineering review reported no critical, important, or minor finding. No host
control, campaign process, PMU phase, qualification, controlled campaign
reboot, or performance claim occurred. The incidental administrator reboot
remains non-campaign evidence.

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

No product compiler, generated kernel candidate, independent executable oracle,
baseline adapter, or benchmark harness exists. No benchmark timing has been
performed and no product-kernel correctness, performance, lifecycle, or
break-even claim is made. The qualification-tool compatibility checks above
establish only that the retained probe executable ran under its deployment
contract; their timings are not measurement samples.

The benchmark-result example is synthetic and explicitly non-claiming.

## Review

- Head engineering self-review: performed incrementally against the exact Task 4 provisioning subject `16d698d`, installed lock, live artifact hashes, retained upstream logs, build-plan M0 requirements, and the active AMD qualification plan. The deployment review examined exact subject `a312aa2`, its source and subprocess boundaries, canonical closed receipt, native dual-build/runtime evidence, compatibility results, and fresh cross-host verifier equality. Campaign-runner review examined exact subject `db0eb87`, privilege separation, identity/statistical closure, restoration dominance, deterministic selector replay, canonical write-once finalization, fresh verification, re-bound semantic tampering, and source-clean CLI execution. Replacement-preflight replay examined its exact file set, canonical bytes, digests, eligibility, identity closure, deterministic selection, and negative claim boundary. Earlier M0 integration self-review remains bound to `3d635d3`.
- Independent implementation-quality review: a read-only engineering-agent review of `a8d5065..82ed387` found no critical issue, one important non-finite evidence-classification gap, and one minor restoration-order assertion gap. Red `c68474c` and repair `c9af373` resolved both; follow-up review of `82ed387..c9af373` reported no remaining critical, important, or minor finding. A separate read-only review independently replayed the replacement preflight's exact six-file root, canonical encoding, digests, eligibility, bundle/source/toolchain/lock/boot bindings, core selection, and non-claiming boundary and reported no critical, important, or minor finding. These are implementation and evidence reviews, not the independent final M0 acceptance review.
- Architecture approval: AR-0001 Option 2 approved by the user on 2026-08-28 and integrated at `6904d49e4978f48d9ca3c5db29fac59bbc3233c6`.

Self-review is not represented as independent review.

## Deviations and evidence gaps

1. The build-plan front matter still says `Proposed architectural program`; the user handoff approved it as execution authority. The charter and index record the authority distinction without rewriting technical semantics.
2. The historical `gpu-2` VM still denies unprivileged cycles and instructions and remains ineligible. The designated AMD candidate exposes working privileged events, but its PMU policy and reboot stability are not yet qualified.
3. The physical host's system tools remain Python 3.14.4, Doxygen 1.15.0, and ShellCheck 0.11.0. The isolated versions in IDR-0004 close the repository-quality gap without changing system defaults, the target-native bundle identity, or measurement qualification. The historical provisioning lock and candidate manifest remain point-in-time captures rather than a live inventory of this supplemental development prefix.
4. JITSpMM has no license statement at the pinned inspection revision; no build or use is authorized unless M2 resolves that boundary.
5. Corpus supports are specified but not materialized by code; no canonical support digests exist.
6. Independent implementation-quality review of this repair is closed, but independent final M0 acceptance review remains absent. Task 6 self-review is not substituted for final acceptance.
7. The qualification plan says Task 7 may set qualification true only when every requirement and review gate passes, while the candidate manifest defers `baseline_numerical_admission` to M2 and M1 is blocked on M0. This dependency conflict must be resolved explicitly before the Task 7 decision; it does not block Task 5 infrastructure qualification.
8. Campaign-one attempt 1 proved a physical restoration defect: restoring EPP before the governor leaves EPP at `performance` on the `amd-pstate-epp` target. Test-first source repair through `c9af373` restores sibling, governor, then EPP, and the bounded physical restoration-only cycle at `a396f64` passed. The fresh physical-native bundle also passed byte-identical `gpu-2` verification, and the replacement read-only preflight independently accepted. A separately authorized campaign attempt remains open. The retained rejection is terminal.
9. The normative campaign-runner design requires every retained JSON file to use canonical compact encoding. Source repair through `c9af373` makes the native probe and Bash restoration record canonical and maps noncanonical/non-finite bytes to the closed rejection classes in both consumers. The rejected live files remain immutable noncanonical failure evidence; the correction requires a new bundle and new root.
10. The Task 8 branch had already been squash-merged and deleted under the repository branch-cleanup policy. The user approved proceeding with `gpu-2` as the second host and a clean detached checkout at exact protected-main ancestor `a396f64` rather than recreating the deleted branch. Exact commit, tree, source, and clean-state identity were unchanged; the active plan now records this implementation-neutral execution variance without relaxing future evidence gates.

## Gate decision and blockers

M0 remains **OPEN**. Closing it requires:

1. qualified, approved Target 0 manifest for the designated physical AMD host required by Option 2;
2. two accepted controlled qualification campaigns, including the separately approved reboot boundary;
3. resolution of the Task 7 versus M2 numerical-admission dependency conflict;
4. independent review or explicit user acceptance of the documented review model.

## Earliest executable next slice

The earliest valid slice is still within M0. The test-first repair,
exact-commit repository-quality gates, physical restoration-only proof, and
fresh cross-host deployment are closed through `a396f64`.
Next:

1. obtain explicit authority for one new campaign-one attempt in the exact
   independently accepted replacement-preflight root. The retained
   rejected root is never reused, rewritten, or retried;
2. stop again before any controlled reboot unless campaign one is accepted and
   separate reboot authority is granted.

The reviewed engineering-quality-gates plan is now unblocked as independent development-environment work, but it cannot substitute for the measurement-host critical path or authorize M1 product code.

M1 product implementation does not begin while M0 remains open.
