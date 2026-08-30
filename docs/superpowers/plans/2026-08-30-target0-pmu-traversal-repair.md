# Target 0 PMU Traversal Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:executing-plans` to implement this plan task-by-task in the
> primary checkout. The user has already selected serial inline execution;
> do not create a worktree or dispatch overlapping owners.

**Goal:** Preserve the terminal campaign-one rejection and repair the nested
PMU output boundary so the unprivileged probe can publish through the exact
root-owned session path without weakening retained-evidence privacy.

**Architecture:** Keep the existing campaign layout and privilege split. The
root runner temporarily grants execute-only traversal (`0711`) on the immediate
`pmu/` parent while the selected PMU child directory is temporarily `1733`,
then restores the child and parent to `0700` in nested `finally` blocks. Primary
process directories remain unchanged, and the terminal rejected root is never
modified or retried.

**Tech Stack:** Python 3.12.3, CMake 3.31.6, Ninja 1.12.1, Clang/LLVM 21.1.8,
`unittest`, fixture-driven Target 0 tests, ASan/UBSan, protected-main CI.

**Spec:**
[`../specs/2026-08-29-target0-qualification-campaign-runner-design.md`](../specs/2026-08-29-target0-qualification-campaign-runner-design.md)

## Global Constraints

- The rejected attempt root with rejection SHA-256
  `0330baaba84c9cef592204e65f95391d8597f55cdd3fe8e182153ec9a6405ba1`
  is immutable and is never retried, rewritten, copied into an accepted root,
  or deleted.
- The source repair does not authorize a new bundle, preflight, campaign,
  controlled reboot, qualification decision, or performance claim.
- A changed fixed source set invalidates the accepted bundle. Any future live
  attempt requires a fresh physical-native bundle, byte-identical `gpu-2`
  replica, new read-only preflight, independent review, and separate authority.
- `measurement_session.sh` remains the sole owner of CPU-control mutation and
  exact restoration.
- The unprivileged target user receives only the minimum path permissions
  needed during one PMU session. Every changed directory returns to `0700`
  before the runner interprets evidence.
- Do not change the campaign schema, numerical semantics, Target 0 scope,
  benchmark gates, retained layout, fallback requirements, or canonical
  identity model.
- Follow [`../../../AGENTS.md`](../../../AGENTS.md),
  [`../../engineering/coding-standards.md`](../../engineering/coding-standards.md),
  and [`../../adr/IDR-0003-target0-qualification-campaign-runner.md`](../../adr/IDR-0003-target0-qualification-campaign-runner.md).

---

### Task 1: Prove the nested PMU traversal defect

**Files:**

- Modify: `tests/target0/qualification_campaign_runner_test.py`

**Interfaces:**

- Consumes: `PmuSessionRunner.__call__()` and
  `QualificationCampaignPrimaryProcessTest.test_five_primary_processes_are_ordered_unique_and_complete()`.
- Produces: a regression that requires the immediate PMU parent to be `0711`
  only while the session runner is active and `0700` after execution.

- [x] **Step 1: Add the live-failure regression**

In `PmuSessionRunner.__call__()`, immediately after resolving `process_path`,
add:

```python
pmu_parent = process_path.parent.parent
if stat.S_IMODE(pmu_parent.stat().st_mode) != 0o711:
    raise AssertionError("PMU parent traversal boundary is not executable")
```

After the existing assertions on PMU child-directory modes, add:

```python
self.assertEqual(
    stat.S_IMODE((campaign_root / "pmu").stat().st_mode),
    0o700,
)
```

- [x] **Step 2: Run the focused test and observe RED**

Run:

```bash
python3 tests/target0/qualification_campaign_runner_test.py \
  QualificationCampaignPrimaryProcessTest.test_five_primary_processes_are_ordered_unique_and_complete
```

Expected: FAIL with
`AssertionError: PMU parent traversal boundary is not executable` during the
first required PMU session. The failure must occur after the five primary
fixtures pass, reproducing the live component boundary rather than a setup
error.

- [x] **Step 3: Commit the red regression**

```bash
git add tests/target0/qualification_campaign_runner_test.py
git commit -m "test: expose nested PMU traversal boundary"
```

---

### Task 2: Temporarily open and exactly restore PMU traversal

**Files:**

- Modify: `tools/target0/run_qualification_campaign.py`
- Verify: `tests/target0/qualification_campaign_runner_test.py`

**Interfaces:**

- Consumes: `_run_measurement_session(session_directory, session_runner,
  command, repository_root)` and the `pmu_root` created by
  `execute_pmu_sessions()`.
- Produces: an optional internal `traversal_directory: Path | None` argument.
  When supplied, it must be the direct non-symlink parent of
  `session_directory`, begin at mode `0700`, be `0711` only during the child
  session, and return to `0700` even when the runner raises or returns nonzero.

- [x] **Step 1: Implement the minimal descriptor-scoped boundary**

Extend `_run_measurement_session()` with:

```python
traversal_directory: Path | None = None,
```

Open the optional traversal directory with
`os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW`. Require that it is a directory,
is the resolved direct parent of `session_directory`, is not a symlink, and has
mode `0700`. Change it to `0711` before changing the child to `1733`. Use nested
`try/finally` blocks so the child returns to `0700` before the parent returns to
`0700`, and close both descriptors even if restoration raises.

In `execute_pmu_sessions()`, call:

```python
result = _run_measurement_session(
    session_directory=session_directory,
    traversal_directory=pmu_root,
    session_runner=session_runner,
    command=command,
    repository_root=repository_root,
)
```

Do not pass a traversal directory for primary sessions.

- [x] **Step 2: Run the focused test and observe GREEN**

Run the Task 1 command again.

Expected: PASS. The fake PMU child observes parent `0711`, all required and
optional PMU sessions complete, and the final PMU parent and children are
`0700`.

- [x] **Step 3: Run the complete campaign-runner test module**

```bash
python3 tests/target0/qualification_campaign_runner_test.py
```

Expected: all tests pass without warnings or residual files.

- [x] **Step 4: Commit the minimal repair**

```bash
git add tools/target0/run_qualification_campaign.py
git commit -m "fix: open PMU traversal during sessions"
```

---

### Task 3: Record the terminal rejected attempt

**Files:**

- Modify: `AGENTS.md`
- Modify: `docs/architecture/README.md`
- Modify: `docs/adr/IDR-0003-target0-qualification-campaign-runner.md`
- Modify: `docs/milestones/M0-acceptance.md`
- Modify: `docs/milestones/status.md`
- Modify: `docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md`
- Modify: `docs/superpowers/plans/2026-08-29-target0-qualification-campaign-runner.md`
- Modify: `docs/targets/target0-amd-ryzen9-7900x-v1.md`

**Interfaces:**

- Consumes: the immutable 49-file external root, its 48-file rejection
  inventory, the accepted Task 9 digests, the five validated primary records,
  six exact restoration records, required-PMU counter text, permission audit,
  and fresh-verifier exit 2.
- Produces: a non-secret durable record of a terminal
  `process_schema_failure` in phase `pmu`; no compact accepted campaign receipt.

- [x] **Step 1: Record exact non-secret evidence**

Record:

- exact run source `a396f642d5c2ec6ed670cc2341170ec7d9f1a886`;
- rejection SHA-256
  `0330baaba84c9cef592204e65f95391d8597f55cdd3fe8e182153ec9a6405ba1`;
- 49 total files and 48 digest/size-bound diagnostics;
- five valid primary processes and 150 retained samples;
- six exact restorations and unchanged sibling/governor/EPP/boost/boot/checkout;
- required PMU values `4083495660` cycles and `7381631799` instructions at
  `100.00` percent running;
- required-PMU command status 2, absent PMU process/PMU JSON, and fresh verifier
  status 2;
- root cause: the target user could traverse the target-user-owned campaign
  root but not root-owned mode-`0700` `pmu/`; child mode `1733` therefore could
  not make its output path reachable;
- no acceptance, campaign manifest, optional PMU phase, reboot, qualification,
  or performance claim.

Do not record the private external root path, username, session identifiers,
hostname, network coordinate, or command line.

- [x] **Step 2: Close only the rejected-attempt checklist**

Move replacement attempt 2 into a clearly terminal historical subsection.
Mark the one-shot run, immediate restoration audit, terminal replay, evidence
binding, and stop-before-reboot steps complete only for that rejected attempt.
Leave a future live attempt absent until the new source, bundle, replica, and
preflight prerequisites close.

- [ ] **Step 3: Run documentation policy checks**

```bash
git diff --check
cmake --build --preset dev-debug --target repository-policy
```

- [ ] **Step 4: Commit the rejection record**

```bash
git add AGENTS.md docs
git commit -m "docs: record terminal Target 0 PMU rejection"
```

---

### Task 4: Verify, review, and integrate the repair

**Files:**

- Verify all files changed in Tasks 1–3.

**Interfaces:**

- Consumes: the red test commit, minimal repair commit, and terminal evidence
  record.
- Produces: exact-commit quality evidence and a protected-main merge. It does
  not produce deployment or live-measurement authority.

- [ ] **Step 1: Run focused Target 0 verification on `gpu-2`**

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug \
  --target target0-host-tools repository-policy
ctest --preset dev-debug -R '^target0-' --output-on-failure
python3 tools/target0/verify_qualification_campaign.py --help
```

- [ ] **Step 2: Run complete Debug, Release, and sanitizer gates on `gpu-2`**

```bash
cmake --build --preset dev-debug --target quality
ctest --preset dev-debug --output-on-failure
cmake --preset dev-release
cmake --build --preset dev-release --target quality
ctest --preset dev-release --output-on-failure
cmake --preset asan-ubsan
cmake --build --preset asan-ubsan --target asan-ubsan
ctest --preset asan-ubsan -R '^quality-sanitizer-' --output-on-failure
```

- [ ] **Step 3: Review exact semantics and permissions**

Review the diff for descriptor closure, symlink refusal, direct-parent
validation, child-before-parent restoration, exception paths, unchanged
primary behavior, rejected-root immutability, and explicit absence of new live
authority. Resolve every critical, important, and minor finding before merge.

- [ ] **Step 4: Push, merge, and verify protected `main`**

Push the scoped branch, open one PR, require all protected checks, squash-merge,
delete and prune the merged branch, and verify the post-merge main workflow.
Synchronize local, `gpu-2`, and the physical host to the exact merged commit.

- [ ] **Step 5: Stop before deployment or another live attempt**

Report the exact merged commit, rejection digest, tested commands, review
result, clean states, and open prerequisite chain. Do not build or transfer a
replacement bundle, run preflight, execute another campaign, or reboot without
new user authority.

---

## Self-review

- **Spec coverage:** The plan preserves the existing operator interface,
  retained layout, privilege split, immutable rejection rule, exact restoration
  requirement, and fresh-verifier behavior. It adds only the missing nested
  path traversal window and its regression.
- **Placeholder scan:** The plan contains no unresolved placeholder, bare debt
  marker, guessed command, or unspecified error-handling step.
- **Type consistency:** The only production interface change is the optional
  internal `Path | None` traversal argument; the PMU caller passes `pmu_root`
  and primary callers retain the default.
