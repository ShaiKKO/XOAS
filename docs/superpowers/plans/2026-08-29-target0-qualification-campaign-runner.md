# Target 0 Qualification Campaign Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, verify, and use one closed campaign runner that retains the
five-process, PMU, restoration, identity, and statistical evidence required for
Target 0 qualification campaign one.

**Architecture:** A pure Python campaign-contract module owns deterministic
identity, statistics, schema, inventory, and replay rules.
A narrow operator CLI owns preflight and live ordering, while the existing Bash
session controller remains the only CPU-control owner and gains one closed
privileged-`perf` mode that demotes the measured probe.

**Tech Stack:** Python 3.12.3 standard library plus pinned `jsonschema`, Bash,
CTest, CMake, ShellCheck, Clang 21, Linux `perf`, and the existing native C++23
qualification probe.

**Spec:**
[`../specs/2026-08-29-target0-qualification-campaign-runner-design.md`](../specs/2026-08-29-target0-qualification-campaign-runner-design.md)

## Global constraints

- Work in the primary checkout on the bounded task branch; do not create a
  linked worktree or delegate implementation.
- Follow red-green-refactor for every production behavior.
- Do not run physical-host controls until the exact implementation commit has
  passed complete Debug, Release, and sanitizer verification on `gpu-2`.
- Use only subprocess argument arrays and closed child environments.
- Never retain usernames, addresses, host aliases, credentials, private keys,
  private evidence roots, or arbitrary command output in JSON.
- Every evidence output is write-once; never resume or recycle a rejected or
  partially executed campaign root.
- The runner may execute campaign one only; it must stop before reboot or
  campaign two.
- No result from this plan is a matrix-kernel performance claim.
- Stage exact reviewed paths and record the exact tested commit and clean/dirty
  state at every external execution gate.

---

### Task 1: Bind the approved design and implementation contract

**Files:**

- Create:
  `docs/superpowers/specs/2026-08-29-target0-qualification-campaign-runner-design.md`
- Create: `docs/adr/IDR-0003-target0-qualification-campaign-runner.md`
- Create:
  `docs/superpowers/plans/2026-08-29-target0-qualification-campaign-runner.md`
- Modify: `docs/architecture/README.md`

**Interfaces:**

- Consumes: approved Task 5 runner design and the controlling AMD host
  qualification plan.
- Produces: accepted semantics-neutral decision, exact component ownership,
  operator interfaces, evidence layout, statistical definitions, and execution
  boundaries used by every later task.

- [x] **Step 1: Verify every new document link and authority statement**

Run:

```bash
cmake --build --preset dev-debug --target docs-check repository-policy
git diff --check
```

Expected: both targets and `git diff --check` exit zero.

- [x] **Step 2: Review the design against Task 5**

Require a direct mapping for exact bundle verification, five primary
processes, 30 retained rounds, separate PMU evidence, exact restoration,
identity drift rejection, the `0.005`/`0.010` MAD ratios, nearest-rank p99 ratio
`1.02`, write-once evidence, and the stop-before-reboot boundary.

- [x] **Step 3: Commit the approved design and plan**

```bash
git add docs/adr/IDR-0003-target0-qualification-campaign-runner.md \
  docs/architecture/README.md \
  docs/superpowers/plans/2026-08-29-target0-qualification-campaign-runner.md \
  docs/superpowers/specs/2026-08-29-target0-qualification-campaign-runner-design.md
git diff --cached --check
git commit -m "docs: specify Target 0 qualification campaign"
```

Expected: one documentation-only commit with no source or live-host effect.

---

### Task 2: Add the closed campaign contract and schema

**Files:**

- Create: `tools/target0/qualification_campaign.py`
- Create: `schemas/target0-qualification-campaign-v1.schema.json`
- Create: `tests/target0/qualification_campaign_test.py`
- Create:
  `tests/target0/fixtures/qualification-campaign-v1.example.json`
- Modify: `tests/target0/CMakeLists.txt`
- Modify: `cmake/quality/RepositoryPolicy.cmake`

**Interfaces:**

- Consumes:
  `prepare_qualification_bundle.canonical_json_bytes`, the existing process
  schema, and `capture_host.validate_capture`.
- Produces:
  `CampaignError`, `derive_process_seed()`, `process_statistics()`,
  `parse_perf_stat()`, `validate_campaign_manifest()`,
  `build_raw_inventory()`, and closed record validators used by Tasks 4 and 5.

- [x] **Step 1: Write failing deterministic seed and statistics tests**

Add literal expectations derived independently from the implementation:

```python
def test_seed_derivation_is_domain_separated_and_indexed(self) -> None:
    self.assertEqual(
        derive_process_seed("target0-campaign-01", 1),
        0x89651FC077B60C94,
    )
    self.assertNotEqual(
        derive_process_seed("target0-campaign-01", 1),
        derive_process_seed("target0-campaign-01", 2),
    )

def test_statistics_use_exact_mad_and_nearest_rank_p99(self) -> None:
    samples = [100_000_000] * 29 + [102_000_000]
    statistics = process_statistics(samples)
    self.assertEqual(statistics["median_ns"], {"numerator": 100000000, "denominator": 1})
    self.assertEqual(statistics["mad_ratio"], "0.000000000000")
    self.assertEqual(statistics["p99_ns"], 102000000)
    self.assertEqual(statistics["p99_ratio"], "1.020000000000")
```

The literal above is independently calculated from the normative byte string,
not from `qualification_campaign.py`.

Run:

```bash
python3 tests/target0/qualification_campaign_test.py \
  -k QualificationCampaignStatisticsTest
```

Expected: import failure because `qualification_campaign.py` does not exist.

- [x] **Step 2: Implement the minimum pure contract**

Implement these exact interfaces:

```python
class CampaignError(RuntimeError):
    """Report a condition that makes a qualification campaign inadmissible."""

def derive_process_seed(campaign_id: str, process_index: int) -> int:
    """Derive one deterministic unsigned 64-bit process seed."""

def process_statistics(elapsed_nanoseconds: Sequence[int]) -> dict[str, object]:
    """Return exact median, MAD, nearest-rank p99, and ratio records."""

def parse_perf_stat(raw_text: str, expected_events: Sequence[str]) -> list[dict[str, object]]:
    """Parse one closed semicolon-delimited perf-stat record."""
```

Use `fractions.Fraction` for every comparison and `decimal.Decimal` with
`ROUND_HALF_EVEN` only for the final 12-digit rendering.
Reject bools, non-integers, counts other than 30, nonpositive elapsed values,
unknown events, duplicates, missing fields, estimates, and malformed running
percentages.

Run the focused test and require it to pass.

- [x] **Step 3: Write failing schema and closed-validator tests**

The positive fixture must include exactly five process summaries, one required
PMU summary, eight optional PMU summaries, exact accepted thresholds, an
external-private-retention classification, and no private path.
Mutations must reject an added field, a username field, four process records,
a missing required counter, a non-unit required scale, a false restoration,
and an acceptance decision inconsistent with the statistics.

Run:

```bash
python3 tests/target0/qualification_campaign_test.py \
  -k QualificationCampaignSchemaTest
```

Expected: failure because the schema and validator do not exist.

- [x] **Step 4: Implement campaign, identity, restoration, PMU, and inventory validators**

Add exact interfaces:

```python
def validate_campaign_manifest(record: dict[str, object], schema_path: Path) -> None:
    """Validate schema closure and cross-field campaign acceptance."""

def validate_identity_record(record: dict[str, object]) -> None:
    """Validate one non-secret exact campaign identity snapshot."""

def validate_restoration_record(record: dict[str, object]) -> None:
    """Require one closed, successful, exactly restored session record."""

def validate_pmu_record(record: dict[str, object], *, required: bool) -> None:
    """Validate one supported or explicitly unsupported PMU record."""

def build_raw_inventory(campaign_root: Path) -> dict[str, object]:
    """Hash every raw retained regular file in bytewise relative-path order."""
```

Use draft-2020-12 meta-validation.
Reject every prohibited field recursively.
Exclude only `inventory.json`, `campaign.json`, `acceptance.json`, and
`rejection.json` from raw inventory.

Run the complete new test file and require it to pass.

- [x] **Step 5: Register schema and focused tests**

Add `target0-qualification-campaign-contract` and
`target0-qualification-campaign-schema` CTest entries.
Map the new schema to its positive fixture in `RepositoryPolicy.cmake` so an
unmapped tracked schema is impossible.

Run:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target target0-host-tools repository-policy
ctest --preset dev-debug \
  -R '^target0-qualification-campaign-(contract|schema)$' \
  --output-on-failure
```

Expected: configure, compilation checks, repository policy, and both tests pass.

- [x] **Step 6: Commit the pure campaign contract**

```bash
git add cmake/quality/RepositoryPolicy.cmake \
  schemas/target0-qualification-campaign-v1.schema.json \
  tests/target0/CMakeLists.txt \
  tests/target0/fixtures/qualification-campaign-v1.example.json \
  tests/target0/qualification_campaign_test.py \
  tools/target0/qualification_campaign.py
git diff --cached --check
git commit -m "tool: define Target 0 qualification campaign contract"
```

---

### Task 3: Add the dedicated privileged-perf session mode

**Files:**

- Modify: `tools/target0/measurement_session.sh`
- Modify: `tests/target0/measurement_session_test.py`

**Interfaces:**

- Consumes: the existing `measurement_session.sh` CPU, sibling, target-user,
  restoration-record, and command interface.
- Produces: optional `--execution-mode probe|privileged-perf`,
  `--perf-output PATH`, and `--perf-events EVENT_LIST` without changing the
  default probe behavior.

- [x] **Step 1: Write the failing privileged-perf fixture test**

Create an executable fake perf frontend inside the temporary test directory.
It must parse the real fixed frontend options, write a literal semicolon record
to `--output`, execute the child after `--`, and record no user value.

Add a test that invokes:

```text
--execution-mode privileged-perf
--perf-output NEW_PATH
--perf-events cycles,instructions
-- /usr/bin/python3 -c CONTROL_OBSERVATION
```

Assert the command sees performance governor, performance EPP, offline
sibling, and only the closed child environment; the perf record exists; the
restoration record reports success; and every control returns to pre-state.

Run:

```bash
python3 tests/target0/measurement_session_test.py \
  -k test_privileged_perf_mode_demotes_child_and_restores_exact_state
```

Expected: exit `2` because the new option is unknown.

- [x] **Step 2: Implement the minimum dedicated mode**

The default `probe` mode remains byte-for-byte behaviorally compatible.
The new mode must:

- require a previously nonexistent perf-output path;
- accept only `cycles,instructions` or one exact optional allowlisted event;
- use `/usr/bin/perf` outside test mode;
- allow only an explicit absolute `XOAS_TARGET0_PERF_PATH` in non-root fixture
  mode;
- construct `perf stat --no-big-num -x ';' --output PATH --event EVENTS --`;
- insert `runuser --user TARGET -- env -i ...` before the probe outside test
  mode;
- expose no general root wrapper;
- route signals and exit through the existing restoration trap.

Run the focused test and the complete session test file.

- [x] **Step 3: Write and pass rejection tests**

Reject missing perf output, existing perf output, missing events, unknown event,
multiple optional events, perf options in probe mode, root target user, fake
perf outside fixture mode, child failure, perf failure, TERM, and restoration
failure.
Require no precondition failure to mutate controls.

Run:

```bash
python3 tests/target0/measurement_session_test.py
shellcheck tools/target0/measurement_session.sh
```

Expected: all tests and ShellCheck pass with no new suppression.

- [x] **Step 4: Commit the privilege-boundary change**

```bash
git add tools/target0/measurement_session.sh \
  tests/target0/measurement_session_test.py
git diff --cached --check
git commit -m "tool: bound Target 0 privileged PMU sessions"
```

---

### Task 4: Implement read-only preflight and live identity recomputation

**Files:**

- Create: `tools/target0/run_qualification_campaign.py`
- Modify: `tools/target0/qualification_campaign.py`
- Modify: `tests/target0/qualification_campaign_test.py`
- Modify: `tests/target0/CMakeLists.txt`

**Interfaces:**

- Consumes: accepted bundle verification, repository/toolchain/compiler/linker
  validators, capture validator, locked core selector, and campaign contract.
- Produces: `preflight` CLI and `collect_live_identity()` with canonical
  write-once `preflight.json` and `core-selection.json`.

- [x] **Step 1: Write failing exact-identity tests**

Use a real temporary Git checkout and literal bundle/lock fixture identities.
Verify the accepted case and one mutation each for commit, tree, dirty state,
remote, bundle, executable, compiler, linker, source, lock, and boot digest.
The test must assert the public rejection code, not arbitrary exception text.

Run:

```bash
python3 tests/target0/qualification_campaign_test.py \
  -k QualificationCampaignIdentityTest
```

Expected: import or missing-function failure.

- [x] **Step 2: Implement live identity collection**

Add:

```python
def collect_live_identity(
    *,
    repository_root: Path,
    expected_commit: str,
    bundle_directory: Path,
    bundle_schema: Path,
    toolchain_lock: Path,
    selected_cpu: int,
    sibling: int,
    boot_id_sha256: str,
    command_runner: CommandRunner,
) -> dict[str, object]:
    """Recompute every identity required before one campaign process."""
```

Reuse public deployment validators.
Compare the accepted bundle's fixed source list byte-for-byte and reject any
added, missing, or changed source.
Serialize no private root or target username.

- [x] **Step 3: Write failing preflight eligibility tests**

Tests must cover explicit exclusivity, one-minute load `0.499` acceptance and
`0.5` rejection, aggregate interactive-session eligibility, no thermal alarm,
TSC, bare metal, cycles/instructions availability, exact 60-second selector
input, and unsafe/existing output roots.

Thermal fixtures must cover nonzero `crit_alarm`, nonzero `fault`, input at an
available critical threshold, input below a threshold, and a retained
`threshold_unavailable` sensor.
Session fixtures retain only aggregate counts and reject any non-target or root
interactive session.

Inject a zero-duration observation clock only at the core-selector boundary;
do not mock the identity or evidence validators.

- [x] **Step 4: Implement the closed preflight CLI**

The parser must require every design option.
Create the output root only after repository and path safety validation.
Write canonical preflight and selection records using exclusive create, flush,
hard-link publication, temporary unlink, and directory fsync.
Copy the verified bundle manifest, inventory, acceptance record, and executable
bytes into `inputs/` with exclusive creation, then invoke only that retained
executable during later process work.
On failure after safe creation, write one closed rejection record.

Run:

```bash
python3 tests/target0/qualification_campaign_test.py
ctest --preset dev-debug \
  -R '^target0-qualification-campaign-' \
  --output-on-failure
```

- [x] **Step 5: Commit accepted preflight behavior**

```bash
git add tools/target0/run_qualification_campaign.py \
  tools/target0/qualification_campaign.py \
  tests/target0/qualification_campaign_test.py \
  tests/target0/CMakeLists.txt
git diff --cached --check
git commit -m "tool: add Target 0 campaign preflight"
```

---

### Task 5: Implement five-process and PMU orchestration

**Files:**

- Modify: `tools/target0/run_qualification_campaign.py`
- Modify: `tools/target0/qualification_campaign.py`
- Modify: `tests/target0/qualification_campaign_test.py`

**Interfaces:**

- Consumes: accepted preflight, selected core/sibling, accepted executable,
  deterministic seeds, session controller, process schema, and PMU parser.
- Produces: the `run` CLI, five ordered primary process directories, required
  PMU evidence, eight optional PMU outcomes, and closed rejection behavior.

- [x] **Step 1: Write a failing five-process integration test**

Run the real operator code against temporary host, repository, session, probe,
and schema fixtures.
The fake probe must create complete process records with 30 literal samples;
the real runner must construct the five process commands and real evidence
layout.

Assert:

```python
self.assertEqual([record["process_index"] for record in processes], [1, 2, 3, 4, 5])
self.assertEqual(len({record["seed"] for record in processes}), 5)
self.assertTrue(all(record["sample_count"] == 30 for record in processes))
```

Run the focused test and observe failure because `run` is not implemented.

- [x] **Step 2: Implement the five primary process loop**

Before every process, capture host state and recompute the complete live
identity.
Invoke one new restoration record and one new process output through the
ordinary session mode.
Capture post-state only after the session exits.
Validate the process schema, selected CPU, bounds, checksum/status, thread
count, restoration, temperature, and identity equality before proceeding.

Do not catch a restoration failure as an ordinary process failure.
Write one rejection and stop immediately.

- [x] **Step 3: Write failing PMU ordering and parser integration tests**

Require one `cycles,instructions` session followed by exactly these separate
optional sessions in order:

```text
branches
branch-misses
cache-references
cache-misses
msr/aperf/
msr/mperf/
msr/tsc/
power/energy-pkg/
```

Test required unsupported and `99.99` percent running as campaign rejection.
Test each optional unsupported event as retained `unsupported` without
campaign rejection.

- [x] **Step 4: Implement PMU sessions through the dedicated session mode**

Every PMU session gets a fresh identity, process record, raw perf file,
restoration record, and before/after capture.
The required pair must be supported with unit scale.
Optional events never receive estimates or aliases.

- [x] **Step 5: Write and pass failure-injection tests**

Cover identity drift at process 2, invalid process schema, 19 ms and 201 ms
samples, migration, second thread, checksum failure, thermal alarm,
restoration failure, required PMU failure, and threshold failure.
For each case assert no acceptance marker, one rejection marker, retained prior
evidence, and no automatic retry.

Run:

```bash
python3 tests/target0/qualification_campaign_test.py
ctest --preset dev-debug \
  -R '^target0-(host-tools-session|qualification-campaign-)' \
  --output-on-failure
```

- [x] **Step 6: Commit the live orchestration behavior**

```bash
git add tools/target0/run_qualification_campaign.py \
  tools/target0/qualification_campaign.py \
  tests/target0/qualification_campaign_test.py
git diff --cached --check
git commit -m "tool: orchestrate Target 0 qualification campaign"
```

---

### Task 6: Finalize and independently verify campaign evidence

**Files:**

- Create: `tools/target0/verify_qualification_campaign.py`
- Modify: `tools/target0/qualification_campaign.py`
- Modify: `tools/target0/run_qualification_campaign.py`
- Modify: `tests/target0/qualification_campaign_test.py`
- Modify: `tools/target0/CMakeLists.txt`
- Modify: `tests/target0/CMakeLists.txt`
- Modify: `cmake/quality/RepositoryPolicy.cmake`

**Interfaces:**

- Consumes: complete raw attempt, campaign schema, process schema, bundle
  schema, and every closed validator.
- Produces: `finalize_campaign()`, `verify_finalized_campaign()`, canonical
  `inventory.json`, `campaign.json`, `acceptance.json`, and fresh verification
  CLI.

- [x] **Step 1: Write the failing finalization and tamper tests**

Accept a complete fixture attempt and require bytewise path ordering,
write-once output, canonical JSON, exact manifest/inventory binding, and one
accepted digest record.
After acceptance, independently mutate a raw process byte, add a file, remove a
file, alter the retained executable, alter the retained bundle record, alter a
statistic, alter the inventory, and alter acceptance.
Every mutation must fail fresh verification.

- [x] **Step 2: Implement deterministic finalization**

Add exact interfaces:

```python
def finalize_campaign(
    campaign_root: Path,
    campaign_manifest: dict[str, object],
    campaign_schema: Path,
) -> dict[str, object]:
    """Publish inventory, campaign, and acceptance records without replacement."""

def verify_finalized_campaign(
    campaign_root: Path,
    *,
    campaign_schema: Path,
    process_schema: Path,
    bundle_schema: Path,
) -> dict[str, object]:
    """Recompute and validate one finalized campaign without trusting digests."""
```

The acceptance output contains only manifest version, campaign ID, status,
performance/qualification false, campaign SHA-256, inventory SHA-256, expected
commit, boot ID SHA-256, selected CPU, and process count.

- [x] **Step 3: Implement the fresh verifier CLI**

The CLI accepts only the four design options, writes accepted canonical JSON to
stdout, prints one generic diagnostic on failure, and never writes files.

Run:

```bash
python3 tests/target0/qualification_campaign_test.py
python3 tools/target0/verify_qualification_campaign.py --help
```

- [x] **Step 4: Register all source and policy inputs**

Add the three Python campaign tools to `target0-host-tools` byte-compilation.
Register focused CTests and add all new source, test, and schema paths to the
qualification bundle's fixed source set.
Update bundle tests and examples to reject missing or stale campaign inputs.

Run:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug \
  --target target0-host-tools repository-policy
ctest --preset dev-debug -R '^target0-' --output-on-failure
```

- [x] **Step 5: Commit finalization and replay verification**

```bash
git add cmake/quality/RepositoryPolicy.cmake \
  tests/target0/CMakeLists.txt \
  tests/target0/prepare_qualification_bundle_test.py \
  tests/target0/fixtures/qualification-tool-bundle-v1.example.json \
  tests/target0/qualification_campaign_test.py \
  tools/target0/CMakeLists.txt \
  tools/target0/prepare_qualification_bundle.py \
  tools/target0/qualification_campaign.py \
  tools/target0/run_qualification_campaign.py \
  tools/target0/verify_qualification_campaign.py
git diff --cached --check
git commit -m "tool: verify Target 0 qualification campaigns"
```

Implemented through exact subject
`cf149ae25bbea5b55577791b8511ae9d2489445e`. The final focused `gpu-2` gate
passed repository policy and all 19 Target 0 tests, including five-process/PMU
orchestration, fresh-process replay, and re-bound semantic tamper rejection.
Protected-main ancestry synchronization
`f90c27d57586e1314568929c86bb1826500af730` changes no tree bytes.
Source-clean runner/verifier execution and direct regressions are committed at
`db0eb8797b54f26eb9a86417af9e0eb626f9669f`; its patched tree passed repository
policy and all 19 Target 0 tests on `gpu-2` without recreating source bytecode.

---

### Task 7: Close implementation quality on the exact pushed commit

**Files:**

- Modify: `AGENTS.md`
- Modify: `docs/adr/IDR-0003-target0-qualification-campaign-runner.md`
- Modify: `docs/architecture/README.md`
- Modify: `docs/milestones/M0-acceptance.md`
- Modify: `docs/milestones/status.md`
- Modify:
  `docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md`
- Modify:
  `docs/superpowers/plans/2026-08-29-target0-qualification-campaign-runner.md`

**Interfaces:**

- Consumes: Tasks 2–6 source and focused evidence.
- Produces: documented commands, exact implementation subject, quality evidence,
  pushed campaign branch, and open live-execution boundary.

- [x] **Step 1: Update durable commands and current frontier**

Document only commands that exist and pass.
Keep Task 5 open and state that no live session, campaign, qualification, or
reboot has occurred.

- [x] **Step 2: Run complete local pre-push verification on `gpu-2`**

At the exact clean task-branch subject run:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target quality
ctest --preset dev-debug --output-on-failure
cmake --preset dev-release
cmake --build --preset dev-release --target quality
ctest --preset dev-release --output-on-failure
cmake --build --preset dev-debug --target asan-ubsan
cmake --build --preset dev-debug --target repository-policy
git diff --check
git status --short --branch
```

Expected: every command exits zero; CTest reports zero failures; the checkout
contains only the exact reviewed documentation updates before their commit.

Exact clean subject `7b486e1fe6ef56e414c65ba0cf09ebc9bbc77dc6`
passed both complete Debug and Release `quality` aggregates and explicit 50/50
CTest replays on `gpu-2`, the isolated 3/3 sanitizer gate, repository policy,
`git diff --check`, absence of source-tree Python bytecode, and a final clean
checkout assertion. No physical host checkout, bundle replacement, live
preflight, campaign, or reboot occurred.

- [x] **Step 3: Commit documentation and push the exact subject**

```bash
git add AGENTS.md \
  docs/adr/IDR-0003-target0-qualification-campaign-runner.md \
  docs/architecture/README.md \
  docs/milestones/M0-acceptance.md \
  docs/milestones/status.md \
  docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md \
  docs/superpowers/plans/2026-08-29-target0-qualification-campaign-runner.md
git diff --cached --check
git commit -m "docs: bind Target 0 campaign runner evidence"
git push -u origin task/m0-target0-qualification-campaign
```

Re-run the complete Debug, Release, sanitizer, and repository-policy commands
at the resulting exact commit if the evidence-binding commit changes any input
covered by a quality check.

---

### Task 8: Build and cross-verify a fresh exact-commit native bundle

**Files:**

- Create externally: one new physical native qualification bundle.
- Create externally: one byte-identical `gpu-2` replica.
- Modify after verification:
  `benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json`
- Modify after verification:
  `benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.sha256`
- Modify after verification:
  `benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json`

**Interfaces:**

- Consumes: exact pushed Task 7 commit and the accepted deployment procedure in
  IDR-0002.
- Produces: physical-authoritative accepted executable and matching development
  replica for the campaign commit.

- [x] **Step 1: Advance both host checkouts to the exact pushed commit**

On each host with a live Task 8 branch require:

```bash
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/task/m0-target0-qualification-campaign)"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
```

Do not proceed on a dirty, divergent, or unpushed subject. For the completed
`a396f64` replacement only, the Task 8 branch had already been squash-merged
into protected `main` and deleted under the approved cleanup policy before the
`gpu-2` replica check. The user approved proceeding with a clean detached
checkout at that exact protected-main commit. The verifier additionally proved
the exact commit, tree, source set, and clean state. This recorded
implementation-neutral variance does not admit an arbitrary detached source;
future executions remain branch-bound unless a separate explicit approval
records equivalent identity evidence.

- [x] **Step 2: Prepare a new physical bundle**

From `/home/shaik/XOAS`:

```bash
xoasCampaignCommit=$(/usr/bin/git rev-parse HEAD)
xoasBundleRoot="/var/tmp/xoas-target0-qualification-tools.${xoasCampaignCommit}-$(date -u +%Y%m%dT%H%M%SZ)"
/usr/bin/python3 tools/target0/prepare_qualification_bundle.py \
  --repository-root /home/shaik/XOAS \
  --expected-commit "$xoasCampaignCommit" \
  --toolchain-lock toolchains/target0-amd-ryzen9-7900x-v1.lock.json \
  --output-directory "$xoasBundleRoot"
/usr/bin/python3 tools/target0/verify_qualification_bundle.py \
  --bundle-directory "$xoasBundleRoot" \
  --schema schemas/target0-qualification-tool-bundle-v1.schema.json
```

Expected: dual build, compatibility tests, inventory, and fresh verification
accept the new exact-commit source set.

- [x] **Step 3: Copy and independently verify the complete replica**

Use the externally authorized byte-copy transport without recording its access
coordinates.
In a clean `gpu-2` checkout at the same commit, run the same verifier against
the replica.
Require identical manifest, inventory, executable, and normalized executable
identity SHA-256 values.

- [x] **Step 4: Bind the replacement receipt and re-run policy**

Update the compact non-secret deployment receipt and target manifest without
claiming campaign execution or qualification.
Run schema validation, repository policy, exact digest checks, and the complete
`gpu-2` quality aggregate before committing and pushing the replacement
receipt.

---

### Task 9: Execute and review campaign-one preflight

**Files:**

- Create externally: one new campaign attempt root containing only accepted
  preflight and core-selection evidence.

**Interfaces:**

- Consumes: fresh Task 8 bundle, exact pushed commit, installed lock, external
  target username, and exclusive-use confirmation.
- Produces: accepted `preflight.json` and `core-selection.json` without host
  mutation.

- [x] **Step 1: Prove the replacement physical checkout and bundle are unchanged**

Re-run the clean checkout and fresh bundle verifier commands.
Confirm the one-minute load is below `0.5`, the development user is the only
expected interactive user, and the exclusive-use window remains valid.

- [x] **Step 2: Run the replacement read-only preflight**

Set one new nonexisting campaign-root name below `/var/tmp` and run the exact
`preflight` interface from the approved spec with campaign ID
`target0-amd-ryzen9-7900x-v1-campaign-01` and campaign number `1`.

Expected: the runner observes exactly 60 seconds of interrupts, selects the
core deterministically, and writes only preflight and selection records.

- [x] **Step 3: Independently review the replacement preflight before mutation**

Recompute every digest and inspect load, session eligibility, thermal state,
boot identity, core/sibling topology, preferred-core rank, interrupt delta,
bundle identity, source set, compiler, linker, lock, and clean checkout.
Reject the attempt rather than overriding a failed precondition.

Historical attempt-1 Task 8 bundle source
`1141713c3448eaaa392e09ace8924ebcaf0e38bd` passed physical dual build,
5/5 compatibility checks, matching physical/`gpu-2` fresh verification, and
repository receipt integration. Task 9 accepted preflight SHA-256
`c36ab9293eb622e17ee4e6869d12a8ce49a9994340203e6594dbb760b44a8abb`
and deterministic CPU 2/sibling 14 selection SHA-256
`200b5f84aab4d32e097982f27b1e89b0cd7b5b4e3b4ccd54363645c197a36ed1`.
No host control changed during preflight.

That preflight is terminal evidence for the rejected attempt and does not
authorize reuse with repaired source.

Replacement Task 9 ran on 2026-08-30 from the current Task 8 bundle at clean
detached source `a396f642d5c2ec6ed670cc2341170ec7d9f1a886` and tree
`7388f3a2b72ccac2352560c48d2e7eb310712330`. Fresh verification first matched
the accepted bundle-manifest, inventory, executable, and normalized
executable-identity digests. The read-only preflight then accepted with
preflight SHA-256
`08a3253b44a2bc1c0dc89abd3463c20def73e0fc313ac468441b9ce65c31935e`
and core-selection SHA-256
`718350bb2ff003000e1ed7ffd1f331fe0c52671cd56d21f3a5dde307bcead803`.
It selected CPU 1 and SMT sibling 13 at preferred-core rank 216 after a
60.001218589-second observation with interrupt delta 1,988. Eligibility
recorded one-minute load `0.12`, three expected and zero root/unexpected
sessions, bare metal, TSC, cycles/instructions availability, and no thermal
alarm, fault, or threshold violation.

Independent replay verified the exact six-file, non-symlink root; canonical
bytes for all five JSON records; all recorded file and identity digests; the
18-source, compiler, linker, provisioning-lock, clean-checkout, boot, topology,
and deterministic-selector bindings. The expected deployment-bundle
authentication input is present; no campaign acceptance/rejection marker,
campaign manifest, process directory, PMU, qualification, or performance
evidence exists. A separate read-only engineering review reported no critical,
important, or minor finding. No host control changed during preflight. Task 9
closed at that checkpoint. Task 10 later received one-attempt authority and
consumed this exact root; its terminal result is recorded below.

---

### Task 10: Execute campaign one and stop before reboot

**Files:**

- Continue externally: the exact accepted Task 9 attempt root, which becomes
  the complete immutable campaign-one raw evidence root.
- Create:
  `benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-01.json`
- Create:
  `benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-01.sha256`
- Modify: `benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json`
- Modify: `docs/targets/target0-amd-ryzen9-7900x-v1.md`
- Modify: `docs/milestones/M0-acceptance.md`
- Modify: `docs/milestones/status.md`
- Modify:
  `docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md`

**Interfaces:**

- Consumes: independently accepted Task 9 preflight.
- Produces: accepted or rejected campaign-one evidence and an exact stopping
  handoff at Task 6 Step 1.

#### Historical attempt 1 controlled phase

Invoke the approved `run` interface as root with the exact repository root,
campaign directory, and external target username.
Do not retry a failed process or rejected campaign.

#### Historical attempt 1 restoration result

Before interpreting timing, independently require the sibling, governor, EPP,
boost, boot, checkout, and identity states to equal their accepted pre-state.
A restoration difference is the terminal campaign result and requires a
bounded recovery decision before any new attempt.

Attempt 1 reached the physical host exactly once and terminated during primary
process 1 with controller exit 70 and closed `restoration_failure`. The probe
returned 0; sibling, governor, and boost restored; EPP remained `performance`
instead of pre-state `balance_performance`. Rejection SHA-256 is
`e6458e2dac1097fa5649371c0815403708c7985da0b80d2ebf5c8b049efc5868`.
A bounded recovery restored only EPP, and independent live identity and stable
host-state replay then matched preflight. The root is immutable and will not be
retried. Red subject `485eb6b` subsequently captured exact canonical-byte and
restoration-order regressions. Exact repair subject `93e9070` restores sibling,
governor, then EPP; makes native process and Bash restoration records compact,
sorted, and newline-terminated; and makes both runner and fresh verifier reject
noncanonical forms. Independent review then found a non-finite classification
gap; red subject `c68474c` and repair `c9af373` prove `NaN`, positive/negative
infinity, and overflowed syntax now reach the closed process/restoration
rejection classes. The final source subject passed complete Debug and Release
50/50 suites, isolated sanitizer 3/3, and repository policy on
`wineth-ubuntu`, and follow-up review reported no remaining finding. At that
checkpoint, physical restoration proof, a new exact-commit bundle/replica, and
a new preflight remained open. Those prerequisites later closed for historical
attempt 2 below; they are not authority for another attempt.

A bounded restoration-only control cycle later passed on the physical host at
clean merged source `a396f642d5c2ec6ed670cc2341170ec7d9f1a886`.
The controller returned 0 around `/usr/bin/true`; a separate live audit matched
sibling, governor, EPP, and boost to canonical pre-state. The restoration
record SHA-256 is
`5b6e2cefbac4c8c96f5228139978f776d55aff0dcffb9dc9fb19812cb50236e7`.
At that same source, a fresh physical-native bundle passed preparation and
fresh physical verification with bundle-manifest, inventory, executable, and
normalized executable-identity SHA-256 values
`15d58e20bbab593bd902782b917b79ba98a03cf1e79c784fbff2c450d23a99a0`,
`44d6ee1eec9791974098ce74c81647d1690bd0aef2bd54822e47635ebad1bbaf`,
`db82cd647e880b1780c2a5fb9d10f87398b184f35d4e84de9b6855db07fec015`,
and `753890dc53185727326bc5dba2585a59ed60bdf0465623dec3fb58bf63b388b3`.
The complete bundle was copied byte-for-byte to `gpu-2`. A fresh verifier from
a clean checkout at the same exact source accepted matching manifest,
inventory, executable, and normalized executable-identity digests. Task 8
replacement deployment is closed. Task 9 replacement preflight subsequently
accepted with SHA-256
`08a3253b44a2bc1c0dc89abd3463c20def73e0fc313ac468441b9ce65c31935e`
and CPU 1/sibling 13 selection SHA-256
`718350bb2ff003000e1ed7ffd1f331fe0c52671cd56d21f3a5dde307bcead803`.

#### Historical replacement attempt 2

- [x] **Step 1: Run the controlled phase exactly once**

One separately authorized invocation consumed the exact accepted Task 9 root
at source `a396f642d5c2ec6ed670cc2341170ec7d9f1a886`. It ran once and
was not retried.

- [x] **Step 2: Verify restoration immediately**

Five primary sessions and the required-PMU session produced six exact
restoration records. Independent live audit matched sibling, governor, EPP,
boost, boot, and checkout to accepted pre-state.

- [x] **Step 3: Fresh-verify the terminal evidence**

Five primary records and 150 samples validated. Required `perf` counted
`4083495660` cycles and `7381631799` instructions at `100.00` percent running,
then returned 2 without PMU process JSON because the target user could not
traverse the root-owned mode-`0700` `pmu/` parent. The fresh verifier returned
2 against terminal phase-`pmu` `process_schema_failure`.

- [x] **Step 4: Bind terminal non-secret evidence**

Rejection SHA-256
`0330baaba84c9cef592204e65f95391d8597f55cdd3fe8e182153ec9a6405ba1`
binds 48 diagnostic files in the 49-file immutable external root. No compact
accepted campaign receipt, campaign manifest, or acceptance record was
created.

- [x] **Step 5: Stop before reboot and further execution**

No optional PMU phase, controlled reboot, campaign two, qualification, or
performance claim occurred. The rejected root is never retried, rewritten, or
deleted.

Red `cc826f2` and repair `0a30b24` address the direct-parent traversal defect.
The changed authenticated source set invalidates the attempt-2 bundle and
preflight for future use. This plan defines no future live attempt. Before one
can be proposed, complete repair quality/review/integration, build and
cross-verify a fresh physical-native bundle, accept and independently review a
new read-only preflight in a new immutable root, and obtain separate attempt
authority. Controlled reboot authority remains separate.

---

## Completion evidence

This plan is complete only when:

- the campaign runner, schema, verifier, and dedicated PMU boundary pass the
  exact `gpu-2` quality contract;
- a fresh exact-pushed-commit physical native bundle and `gpu-2` replica match;
- campaign one is accepted or a bounded retained rejection is reported;
- all mutable host controls restore exactly;
- raw evidence, inventory, manifest, acceptance/rejection, and compact Git
  receipt are retained as applicable;
- no credential or access field is present;
- no controlled campaign reboot or campaign two has occurred;
- Target 0 and M0 remain open until the separately approved later gates close.
