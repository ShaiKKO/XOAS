# M0 Evidence Foundation Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Close M0 only when XOAS has a falsifiable Target 0 charter, a primary-source prior-art comparison, an honest baseline policy, a frozen benchmark contract and initial corpus manifests, and a qualified reference-target decision.

**Architecture:** M0 is documentation and evidence infrastructure, not compiler scaffolding. It creates the durable contracts that M1 and later milestones must consume. JSON manifests are human-readable inspection records for M0; their canonical binary identities are deliberately deferred to M1. The development server is recorded as a candidate target, and remains unqualified for gate measurements until the target decision record closes its measurement-control requirements.

**Tech stack:** Markdown, JSON Schema draft 2020-12, JSON manifests, Python 3.12 standard library for syntax/consistency checks, Git inspection commands, and primary-source research links.

**Controlling requirements:** `docs/exact_instance_matrix_kernel_synthesizer_build_plan.md` sections 2, 3, 10, 11, 13 M0, 17, and 20; root `AGENTS.md`; `docs/milestones/status.md`.

**Task contract:** This plan may add only M0 documents, schemas, and manifests; update the root manual and milestone ledger to reflect verified M0 state; and record target-qualification evidence. It must not add product code, a build system, benchmark executables, dependencies, server packages, generated kernels, or performance claims.

**Execution policy:** Execute inline in task order and use the listed scoped commit boundaries. Work directly in the primary checkout unless isolation becomes essential because concurrent or high-risk work would otherwise overlap. Push verified commits to the configured remote as normal repository integration work.

---

## Task 1: Lock the M0 charter and architecture index

**Files:**

- Create: `docs/architecture/README.md`
- Create: `docs/architecture/000-charter.md`
- Modify: `docs/milestones/status.md`

**Step 1: Write the failing contract check**

Run this inspection and retain its failure in the work log until the files exist:

```bash
test -f docs/architecture/README.md
test -f docs/architecture/000-charter.md
```

**Step 2: Create the architecture index**

List only documents that actually exist. For each entry, record its authority, approval/gate state, owner, and when it must be updated. Separate controlling architecture, proposals, IDRs, milestone plans, acceptance records, and evidence.

**Step 3: Create the charter**

Lock all of the following without adding implementation design:

- exact-instance specialization and the lifecycle-cost objective;
- precise v0 input and output claim;
- Target 0 constraints and explicit non-goals;
- structural-zero versus numerical-zero rule;
- strict and contracted numerical modes, with contracted as the initial production target but not an authorization for reassociation;
- required fallback, compatibility, provenance, and replay obligations;
- proof, product-class, and measurement-quality gates;
- one-paragraph M0 falsifiability statement;
- no-go behavior if the proof signal fails.

Reconcile the build-plan front-matter phrase `Proposed architectural program` by recording that the user's 2026-08-28 handoff approved the plan as execution authority. Do not rewrite the build plan's technical semantics.

**Step 4: Update the ledger**

Mark Task 1 evidence present while M0 remains `In progress`. Do not claim gate closure.

**Step 5: Verify**

```bash
test -f docs/architecture/README.md
test -f docs/architecture/000-charter.md
rg -n "Precise v0 claim|Falsification|Structural zero|Non-goals|Proof gate" docs/architecture/000-charter.md
git diff --check
```

**Commit boundary:** `docs: lock the XOAS Target 0 charter`

---

## Task 2: Produce the prior-art and baseline decision matrices

**Files:**

- Create: `docs/experiments/prior-art-matrix.md`
- Create: `docs/experiments/baseline-matrix.md`

**Step 1: Define comparison axes before conclusions**

Use the required axes: arithmetic-algorithm search, sparse-format search, schedule search, hardware mapping, exact stable instance specialization, empirical runtime selection, artifact/replay model, and numerical-contract boundary.

**Step 2: Compare every required research anchor**

Cover FFTW3; SPIRAL; LGen; AlphaTensor; TACO; SparseTIR; MLIR SparseTensor and Vector; SABLE; TVM TensorIR and MetaSchedule; Triton autotuning; and LLVM ORC as a later backend boundary. Use primary papers or official project documentation. Mark facts, scoped inference, and XOAS decision separately.

**Step 3: State the closest-prior-system conclusion**

Name the closest system by individual capability and state why no reviewed system, based on the reviewed sources, establishes the full XOAS v0 claim. Keep the conclusion falsifiable and avoid novelty claims broader than the source review supports.

**Step 4: Lock baseline admission and configuration policy**

The baseline matrix must include these initial candidates:

- independent scalar oracle, excluded from performance competition unless it wins;
- compiler-optimized dense row-major loop;
- generic CSR runtime-index SpMM loop;
- exact-support runtime-array loop that still loads indices;
- OpenBLAS `SGEMM`;
- Intel oneMKL `SGEMM`;
- Intel oneMKL `mkl_sparse_s_mm` where the installed version and sparse handle path support the case;
- LIBXSMM dense or sparse/JIT path where its supported envelope and semantics apply.

For each baseline record applicability, semantic equivalence, one-time versus per-call conversion/packing cost, thread control, ISA dispatch, tuning/configuration search, artifact/version identity, and disqualification conditions. The winner is the fastest correct applicable configuration, not a preferred library.

Server availability is not established until exact packages/versions are installed and recorded. M0 locks candidates and admission rules, not fictional availability.

**Step 5: Verify coverage**

```bash
for term in FFTW3 SPIRAL LGen AlphaTensor TACO SparseTIR SparseTensor SABLE TensorIR MetaSchedule Triton ORC; do rg -q "$term" docs/experiments/prior-art-matrix.md; done
for term in OpenBLAS oneMKL mkl_sparse_s_mm LIBXSMM CSR; do rg -q "$term" docs/experiments/baseline-matrix.md; done
git diff --check
```

**Commit boundary:** `docs: establish M0 prior art and baseline policy`

---

## Task 3: Lock the benchmark protocol and result schema

**Files:**

- Create: `docs/architecture/050-benchmark-protocol.md`
- Create: `schemas/benchmark-result-v1.schema.json`
- Create: `benchmarks/manifests/benchmark-result-v1.example.json`

**Step 1: Define eligibility before timing**

Require instance validation, numerical-contract validation, coverage/duplicate verification where applicable, differential correctness, target compatibility, and fallback availability before a candidate enters a timed sample.

**Step 2: Lock environment and sample procedure**

Specify core affinity, SMT-sibling control, NUMA placement, warm-up, calibration threshold, deterministic inputs, checksum consumption, randomized interleaving, raw ordering, process restarts, reboot evidence for gate claims, sample minimums, outlier policy, and stop rules. Unavailable PMU events must be recorded as unavailable, never fabricated or silently omitted.

**Step 3: Lock statistical decision rules**

Use per-process medians as the primary unit, median and MAD/IQR as dispersion, paired/interleaved ratios, nonparametric bootstrap confidence intervals, and a predeclared practical noise floor. If the interval crosses parity or the effect is below the floor, declare a tie. Do not tune these thresholds after seeing a candidate.

**Step 4: Define lifecycle and baseline accounting**

Separate analysis, search, compile, prepack, setup, kernel, fallback, and total lifecycle time. Record code size, scratch/prepack bytes, raw samples, baseline configurations, correctness evidence, and break-even invocations.

**Step 5: Create the schema and conforming example**

The schema must require:

- schema/protocol version and immutable run identity;
- exact commit and dirty-tree state;
- instance, numerical contract, target, compiler, and baseline identities;
- candidate plan and artifact provenance;
- correctness gate outcome;
- environment controls and limitations;
- ordered raw samples with phase, implementation, process, sequence, iterations, elapsed nanoseconds, and checksum;
- statistical summary and decision;
- analysis/search/compile/prepack costs;
- code, scratch, prepack, and break-even metrics;
- retained artifact references.

Use `additionalProperties: false` at closed record boundaries. Durations are integer nanoseconds. Digests use lowercase SHA-256 hex. The example is explicitly synthetic and makes no performance claim.

**Step 6: Verify JSON and cross-field invariants**

```bash
python3 -m json.tool schemas/benchmark-result-v1.schema.json >/dev/null
python3 -m json.tool benchmarks/manifests/benchmark-result-v1.example.json >/dev/null
python3 - <<'PY'
import json
from pathlib import Path

schema = json.loads(Path('schemas/benchmark-result-v1.schema.json').read_text())
example = json.loads(Path('benchmarks/manifests/benchmark-result-v1.example.json').read_text())
assert schema['$schema'] == 'https://json-schema.org/draft/2020-12/schema'
assert example['schema_version'] == 'xoas.benchmark-result.v1'
assert example['claim']['performance_claim'] is False
assert example['measurement']['raw_samples']
assert all(sample['elapsed_ns'] > 0 for sample in example['measurement']['raw_samples'])
PY
git diff --check
```

Full JSON Schema meta-validation and instance validation become an M1 build dependency; M0 must record that tooling gap rather than claim it ran.

**Commit boundary:** `docs: lock benchmark protocol and result contract`

---

## Task 4: Freeze the initial synthetic, application, and holdout manifests

**Files:**

- Create: `benchmarks/manifests/synthetic-target-v0.json`
- Create: `benchmarks/manifests/application-target-v0.json`
- Create: `benchmarks/manifests/holdout-v0.json`
- Create: `docs/experiments/corpus-policy.md`

**Step 1: Define deterministic synthetic generation**

Use the `PCG-XSL-RR 128/64` family identifier and fixed 128-bit seeds. Define exact coordinate-generation algorithms, duplicate handling, row sorting, density interpretation, and admission constraints. Cover random, banded, diagonal, block-sparse, repeated-row, power-law, and mixed support families across the build-plan envelope.

The manifest must pre-register separate smoke, proof-target, product-class, and design-training subsets. Each case has a stable case ID, `M`, `K`, `N`, support family parameters, expected invocations, and role.

**Step 2: Freeze application-derived structures**

Use official NIST Matrix Market artifacts and pin the compressed upstream SHA-256 digests:

- `WEST0067`, real general, `67 x 67`, 294 stored coordinates, SHA-256 `228c55ac4746e8be7bb7f7e03e590d7066cdfe9ba9c06616dd19c04104ff6adb`;
- `ARC130`, real general, `130 x 130`, 1,282 stored coordinates including explicit numerical zeros, SHA-256 `574287deae85599973f1a022b832447f01787b73e542b051d42dc9b08b77ed6a`;
- `LUND_A`, real symmetric, `147 x 147`, 1,298 stored lower-triangle coordinates and 2,449 coordinates after symmetry expansion, SHA-256 `ae81bed9b45552f4ac42ce94feebd2a951bd1d1e22d7496d807a57e4b62da4f8`;
- `ASH85`, pattern symmetric, `85 x 85`, 304 stored lower-triangle coordinates and 523 coordinates after symmetry expansion, SHA-256 `f183acc1101b11a63864210713de295cdd0a98fc67bb756316a8d510933e92b3`.

For every source, the support is the set of stored coordinates after required symmetry expansion. Do not remove a coordinate because its source value parses as zero. Values used in benchmark invocations are newly generated dynamic `float32` values; the external artifact supplies support provenance, not compile-time values.

Use fixed `N` variants and expected-invocation classes. Preregister `WEST0067` and `LUND_A` for the visible product-class subset; reserve `ARC130` and `ASH85` as holdout structures so heuristic design cannot consume them.

**Step 3: Define holdout governance**

The holdout manifest exposes identity/provenance and the cases required for reproducibility but prohibits its measurements from shaping transforms, cost features, schedule ranges, thresholds, or family admission. Any unblinding before M7 invalidates the affected claim and requires a versioned replacement manifest before further tuning.

**Step 4: Verify exact partitions and source facts**

```bash
for file in benchmarks/manifests/synthetic-target-v0.json benchmarks/manifests/application-target-v0.json benchmarks/manifests/holdout-v0.json; do python3 -m json.tool "$file" >/dev/null; done
python3 - <<'PY'
import json
from pathlib import Path

synthetic = json.loads(Path('benchmarks/manifests/synthetic-target-v0.json').read_text())
visible = json.loads(Path('benchmarks/manifests/application-target-v0.json').read_text())
holdout = json.loads(Path('benchmarks/manifests/holdout-v0.json').read_text())

synthetic_ids = {case['case_id'] for case in synthetic['cases']}
visible_ids = {case['case_id'] for case in visible['cases']}
holdout_ids = {case['case_id'] for case in holdout['cases']}
assert synthetic_ids and visible_ids and holdout_ids
assert synthetic_ids.isdisjoint(visible_ids | holdout_ids)
assert visible_ids.isdisjoint(holdout_ids)
assert {source['matrix_id'] for source in visible['sources']} == {'WEST0067', 'LUND_A'}
assert {source['matrix_id'] for source in holdout['sources']} == {'ARC130', 'ASH85'}
assert all(len(source['compressed_sha256']) == 64 for source in visible['sources'] + holdout['sources'])
PY
git diff --check
```

**Commit boundary:** `bench: freeze initial Target 0 corpus manifests`

---

## Task 5: Record and qualify the reference target candidate

**Files:**

- Create: `benchmarks/manifests/target-gpu-2-candidate.json`
- Create: `docs/architecture/proposals/AR-0001-target-0-host-qualification.md`
- Create: `docs/milestones/M0-acceptance.md`

**Step 1: Capture only non-secret compatibility facts**

Record the verified development-host facts: Ubuntu 24.04.4 LTS; x86-64 KVM/OpenStack; Intel Xeon Gold 6348, family 6/model 106/stepping 6; 16 logical CPUs, 8 cores, one socket and NUMA node; cache sizes; AVX2/FMA and exposed AVX-512 feature set; memory; kernel and microcode if freshly recaptured; observable frequency state; installed tool versions; and unavailable controls.

Never record the IP address, username/password, private-key path, private key, or SSH command in the repository.

**Step 2: Create the load-bearing target decision proposal**

The proposal must compare:

1. qualify `gpu-2` as Target 0 after controls close;
2. use `gpu-2` only for development and acquire a stable bare-metal/controlled VM target;
3. narrow measurement claims to the VM fingerprint and explicitly accept provider noise.

Recommend an option based on evidence. State correctness, identity/cache, benchmark-gate, migration, and blocked-work impact. Work on M1 semantics can continue after M0, but no gate-quality performance claim can proceed without an approved option and a fresh target manifest.

**Step 3: Define qualification checks**

Require repeated CPU/ISA/topology identity across reboot; stable core affinity; SMT sibling isolation policy; exclusive-use evidence; frequency/turbo/governor observability or an accepted limitation; timer stability; process/reboot noise characterization; PMU availability decision; installed compiler and baseline-library identities; and a clean server repository checkout bound to a commit.

Do not install packages or mutate the server as part of M0 documentation work. Provisioning is a separately reviewed execution action.

**Step 4: Write the M0 acceptance record**

Record exact files, commands, hashes, source retrieval evidence, review outcome, deviations, and an explicit gate decision. If the target proposal is unapproved or qualification evidence is incomplete, M0 remains open; say so directly and identify work that can proceed independently.

**Step 5: Verify**

```bash
python3 -m json.tool benchmarks/manifests/target-gpu-2-candidate.json >/dev/null
rg -n "requested decision|alternatives|correctness|identity|cache|benchmark|blocked" docs/architecture/proposals/AR-0001-target-0-host-qualification.md
! rg -n "ssh""pass|([0-9]{1,3}[.]){3}[0-9]{1,3}|[.]pem|password[[:space:]]*[:=]|BEGIN [A-Z ]*PRIVATE KEY" . -g '!.git/**'
git diff --check
```

**Commit boundary:** `docs: record Target 0 host qualification decision`

---

## Task 6: Integrate, independently review, and state the M0 gate outcome

**Files:**

- Modify: `AGENTS.md`
- Modify: `docs/architecture/README.md`
- Modify: `docs/milestones/status.md`
- Modify: `docs/milestones/M0-acceptance.md`

**Step 1: Update the durable manual from verified facts**

Add actual M0 paths, protocol/manifests, exact documentation-verification commands, baseline admission rules, holdout governance, and the current target-decision status. Do not add build/test commands that still do not exist.

**Step 2: Perform a controlling-plan traceability review**

Map every M0 build-plan work item and deliverable to a file and section. Check that the one-paragraph exit statement names the precise v0 claim, closest prior capability set, differentiator, and falsifying benchmark.

**Step 3: Perform evidence-integrity checks**

```bash
python3 -m json.tool schemas/benchmark-result-v1.schema.json >/dev/null
find benchmarks/manifests -name '*.json' -print0 | xargs -0 -n1 python3 -m json.tool >/dev/null
git diff --check
rg -n "TO""DO|T""BD|FIX""ME|PLACE""HOLDER" AGENTS.md docs benchmarks schemas
! rg -n "ssh""pass|([0-9]{1,3}[.]){3}[0-9]{1,3}|[.]pem|password[[:space:]]*[:=]|BEGIN [A-Z ]*PRIVATE KEY" . -g '!.git/**'
git status --short --branch
```

`rg` returns exit status 1 when no placeholder matches; that is the expected result.

**Step 4: Obtain implementation-quality review**

Review against the root manual and M0 exit gate. Because no subagent delegation was requested, perform an explicit self-review now and leave independent review as a named gate item for the user or a later authorized reviewer. Do not represent self-review as independent review.

**Step 5: Make the gate decision**

Close M0 only if all deliverables exist, the target decision is approved, qualification evidence meets the accepted option, and review evidence is recorded against an exact commit. Otherwise retain `In progress`, list the exact remaining items, and identify the earliest independent M1 preparation that policy permits without claiming M0 closure.

**Commit boundary:** `docs: integrate M0 evidence foundation`

---

## Completion evidence

This plan is complete when:

- every M0 deliverable exists and passes the commands above;
- all external facts are linked to primary sources and all downloaded corpus artifacts have pinned digests;
- M0 has an explicit go/no-go/open decision rather than an implied status;
- target and benchmark limitations remain visible;
- root `AGENTS.md` and the canonical ledger match actual repository state;
- no product/compiler code or unapproved server mutation was introduced;
- any completion claim is bound to the exact reviewed commit, or explicitly says the repository remains uncommitted.
