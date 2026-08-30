# Target 0 Qualification-Tool Deployment Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to
> implement this plan task by task in the primary checkout. Do not delegate or
> create a linked worktree unless the user separately requests that change.

**Goal:** Produce and retain one fail-closed, target-native, independently
authenticated qualification-tool bundle that is safe to hand to Target 0
qualification campaign one.

**Architecture:** Keep `gpu-2` as the complete development-quality authority and
use one narrow Python preparation command on the physical AMD target. The
command validates an exact clean checkout and installed toolchain lock, builds
the existing probe twice with the locked Clang/LLD contract, proves identical
bytes, records ELF/runtime provenance, runs target-compatibility tests, and
finalizes a closed content inventory. No part of this plan enters a measurement
session or executes a qualification campaign.

**Tech stack:** Python 3 standard library plus pinned `jsonschema`, JSON Schema
draft 2020-12, C++23, Clang/LLD 21.1.8, CMake/Ninja quality integration, Linux
ELF inspection tools, Git, SHA-256.

**Controlling design:**
[`../specs/2026-08-29-target0-qualification-tool-deployment-design.md`](../specs/2026-08-29-target0-qualification-tool-deployment-design.md)

**Controlling qualification plan:**
[`2026-08-29-amd-target0-host-qualification.md`](2026-08-29-amd-target0-host-qualification.md)

## Execution rules

- Work in the current primary checkout and existing
  `task/m0-target0-qualification-tools` branch.
- Inspect the exact staged paths before every commit. Push only tested commits.
- Use test-driven development: observe each new focused test fail for the
  intended reason before implementing its behavior.
- Do not change Target 0, numerical modes, benchmark gates, process-probe
  semantics, or measurement-session controls.
- Do not install packages, invoke `sudo`, start `perf`, enable measurement
  controls, run campaign one, or reboot the physical target in this slice.
- Do not commit access aliases, credentials, network coordinates, home paths,
  generated binaries, or raw external-host command transcripts.
- Preserve every failed physical preparation root. Never reuse it as a later
  accepted bundle.
- All target-host commands are run from the externally administered physical
  XOAS checkout. Access details remain outside Git.

## Commit map

1. `docs: design Target 0 qualification deployment`
2. `test: lock Target 0 qualification bundle contract`
3. `tool: validate Target 0 qualification preparation`
4. `tool: build authenticated Target 0 qualification probe`
5. `tool: verify Target 0 qualification runtime`
6. `tool: finalize Target 0 qualification bundle`
7. `docs: record Target 0 deployment procedure`
8. `docs: bind Target 0 qualification tool evidence`

The first seven commits form the reviewed implementation subject. The eighth is
created only after native execution and replica verification. If an intermediate
task cannot remain green independently, fold it into the immediately following
commit and record that dependency in the execution evidence; do not commit a
known-red integration state.

---

## Task 0: Publish the approved design and plan

**Files:**

- Add: `docs/superpowers/specs/2026-08-29-target0-qualification-tool-deployment-design.md`
- Add: `docs/superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md`

### Step 1: Verify planning authority and repository state

Run:

```bash
git status --short --branch
git rev-parse HEAD
git diff --check
test -f docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md
```

Expected: the branch is the existing task branch, the only new paths are the
approved design and implementation plan, whitespace validation passes, and the
controlling plan target exists.

### Step 2: Review and commit only the planning files

Run:

```bash
git diff -- docs/superpowers/specs/2026-08-29-target0-qualification-tool-deployment-design.md
git diff -- docs/superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md
git add \
  docs/superpowers/specs/2026-08-29-target0-qualification-tool-deployment-design.md \
  docs/superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md
git diff --cached --check
git diff --cached --stat
cmake \
  -DXOAS_GIT="$(command -v git)" \
  -DXOAS_PYTHON="$(command -v python3)" \
  -DXOAS_REPOSITORY_ROOT="$PWD" \
  -DXOAS_MARKDOWN_INPUT="$PWD/docs/superpowers/specs/2026-08-29-target0-qualification-tool-deployment-design.md" \
  -DXOAS_MARKDOWN_LOGICAL_PATH="docs/superpowers/specs/2026-08-29-target0-qualification-tool-deployment-design.md" \
  -P cmake/quality/MarkdownLinks.cmake
cmake \
  -DXOAS_GIT="$(command -v git)" \
  -DXOAS_PYTHON="$(command -v python3)" \
  -DXOAS_REPOSITORY_ROOT="$PWD" \
  -DXOAS_MARKDOWN_INPUT="$PWD/docs/superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md" \
  -DXOAS_MARKDOWN_LOGICAL_PATH="docs/superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md" \
  -P cmake/quality/MarkdownLinks.cmake
git commit -m "docs: design Target 0 qualification deployment"
git push origin task/m0-target0-qualification-tools
```

Expected: one documentation-only commit is pushed, with no product or host
state change.

---

## Task 1: Lock the bundle record and schema boundary

**Files:**

- Add: `schemas/target0-qualification-tool-bundle-v1.schema.json`
- Add: `tests/target0/fixtures/qualification-tool-bundle-v1.example.json`
- Add: `tests/target0/prepare_qualification_bundle_test.py`
- Modify: `tests/target0/CMakeLists.txt`
- Modify: `cmake/quality/RepositoryPolicy.cmake`

### Step 1: Add the failing closed-schema test

Create `PrepareQualificationBundleSchemaTest` with tests that:

```python
self.validator.validate(self.example)
self.assertEqual(
    self.example["manifest_version"],
    "xoas.target0-qualification-tool-bundle.v1",
)
self.assertIs(self.example["performance_claim"], False)
self.assertEqual(self.example["status"], "passed")
```

Also mutate the example to prove rejection of:

- `performance_claim: true`;
- an unknown top-level field;
- a short or uppercase SHA-256;
- a dirty repository state;
- a passed build whose `identical` decision is false;
- a passed state with a nonempty rejection list;
- an absent runtime dependency hash;
- an unclosed test result.

Register `target0-qualification-bundle-schema` in
`tests/target0/CMakeLists.txt`, passing the schema and example paths explicitly.

Run:

```bash
python3 tests/target0/prepare_qualification_bundle_test.py \
  --schema schemas/target0-qualification-tool-bundle-v1.schema.json \
  --example tests/target0/fixtures/qualification-tool-bundle-v1.example.json
```

Expected: FAIL because the schema and example do not yet exist.

### Step 2: Add the smallest closed schema and synthetic example

The schema must set `additionalProperties: false` at every object boundary and
define at least these closed records:

- repository identity;
- provisioning-lock identity;
- source inputs;
- compiler and linker identity;
- exact build invocations and two-build equality;
- ELF and runtime dependencies;
- compatibility-test results;
- bundle status and rejection reasons.

Every digest uses `^[0-9a-f]{64}$`. Every retained path is either explicitly
classified or relative to the bundle; no access identity or network coordinate
field exists. The synthetic example uses clearly non-live identities and
`performance_claim: false`.

Draft 2020-12 validates the structure and the passed-state `identical: true`
decision. It cannot compare two arbitrary sibling digest strings. Task 5's
production semantic validator therefore owns and tests actual first/second
digest equality before acceptance.

Update `RepositoryPolicy.cmake` so the schema is mapped to the synthetic
example. Do not classify it as runtime-only: the repository must always carry
one positive schema instance.

### Step 3: Run focused schema tests and policy validation

Run:

```bash
python3 tests/target0/prepare_qualification_bundle_test.py \
  --schema schemas/target0-qualification-tool-bundle-v1.schema.json \
  --example tests/target0/fixtures/qualification-tool-bundle-v1.example.json
python3 -m json.tool \
  schemas/target0-qualification-tool-bundle-v1.schema.json >/dev/null
python3 -m json.tool \
  tests/target0/fixtures/qualification-tool-bundle-v1.example.json >/dev/null
cmake --preset dev-debug
cmake --build --preset dev-debug --target repository-policy
ctest --preset dev-debug \
  -R '^target0-qualification-bundle-schema$' --output-on-failure
```

Expected: schema tests pass, draft-2020-12 meta-validation passes through
repository policy, and the new CTest passes.

### Step 4: Commit the contract

Run:

```bash
git add \
  cmake/quality/RepositoryPolicy.cmake \
  schemas/target0-qualification-tool-bundle-v1.schema.json \
  tests/target0/CMakeLists.txt \
  tests/target0/fixtures/qualification-tool-bundle-v1.example.json \
  tests/target0/prepare_qualification_bundle_test.py
git diff --cached --check
git diff --cached --stat
git commit -m "test: lock Target 0 qualification bundle contract"
```

---

## Task 2: Implement fail-closed CLI, path, repository, and lock validation

**Files:**

- Add: `tools/target0/prepare_qualification_bundle.py`
- Modify: `tests/target0/prepare_qualification_bundle_test.py`
- Modify: `tests/target0/CMakeLists.txt`
- Modify: `tools/target0/CMakeLists.txt`

### Step 1: Add failing preflight tests

Extend the test with an import loader for the real preparation module and a
bounded fake command runner. Add focused tests for:

```python
with self.assertRaises(module.PreparationError):
    module.validate_repository(dirty_fixture, expected_commit, runner)

with self.assertRaises(module.PreparationError):
    module.create_staging_root(existing_path, allowed_root)

with self.assertRaises(module.PreparationError):
    module.validate_toolchain_lock(mutated_lock, lock_schema)
```

Cover:

- all four CLI inputs required;
- malformed and abbreviated commit IDs rejected;
- clean exact commit/tree/public remote accepted;
- dirty, mismatched, missing-origin, and credential-bearing remote rejected
  without echoing the remote;
- output accepted only as a new immediate child of the allowed evidence root;
- existing, symlinked, broad, install-prefix, repository, home, and ancestor
  paths rejected;
- lock schema/meta-schema validation;
- lock state exactly `installed_verified`;
- stable configuration digest recomputation;
- Target 0 CPU/OS/architecture match from unprivileged host facts;
- provisioning execution subject retained separately from campaign commit;
- production orchestration validates the repository before creating output;
- no full process environment captured.

Run the focused test and confirm the intended import failure:

```bash
python3 tests/target0/prepare_qualification_bundle_test.py \
  --schema schemas/target0-qualification-tool-bundle-v1.schema.json \
  --example tests/target0/fixtures/qualification-tool-bundle-v1.example.json
```

Expected: FAIL because `prepare_qualification_bundle.py` is absent.

### Step 2: Implement the narrow preparation surface

Add:

```python
class PreparationError(RuntimeError):
    """Report a condition that makes a deployment bundle inadmissible."""


class CommandRunner(Protocol):
    """Run one fixed argument array in an explicit working directory."""


def canonical_json_bytes(record: object) -> bytes:
    """Serialize one retained record deterministically."""


def validate_repository(...) -> dict[str, object]:
    """Return a closed clean-checkout identity or fail."""


def validate_toolchain_lock(...) -> dict[str, object]:
    """Validate the installed lock and its stable digest."""


def create_staging_root(...) -> Path:
    """Create one new private evidence root without replacement."""
```

The real command runner must use `subprocess.run` with a sequence, explicit
working directory, `shell=False`, captured text, and a timeout. It must never
fall back to `PATH` for the compiler/linker and never capture the caller's full
environment.

CLI parsing accepts exactly the approved four options. Before target execution,
tests call helpers with fixture roots; the production CLI fixes the allowed
physical evidence root to `/var/tmp` and basename prefix to
`xoas-target0-qualification-tools.`.

Register `target0-qualification-bundle-preflight` with a focused unittest
filter and the same explicit schema/example arguments as the schema test.

### Step 3: Register syntax enforcement and rerun focused tests

Add the new Python file to the `target0-host-tools` byte-compilation command in
`tools/target0/CMakeLists.txt`.

Run:

```bash
python3 tests/target0/prepare_qualification_bundle_test.py \
  --schema schemas/target0-qualification-tool-bundle-v1.schema.json \
  --example tests/target0/fixtures/qualification-tool-bundle-v1.example.json
cmake --build --preset dev-debug --target target0-host-tools
ctest --preset dev-debug \
  -R '^target0-qualification-bundle-' --output-on-failure
```

Expected: preflight tests pass without compiling a probe or touching a real
host-control path.

### Step 4: Commit preflight behavior

Run:

```bash
git add \
  tests/target0/CMakeLists.txt \
  tests/target0/prepare_qualification_bundle_test.py \
  tools/target0/CMakeLists.txt \
  tools/target0/prepare_qualification_bundle.py
git diff --cached --check
git diff --cached --stat
git commit -m "tool: validate Target 0 qualification preparation"
```

---

## Task 3: Implement the exact compiler contract and dual native build

**Files:**

- Modify: `tools/target0/prepare_qualification_bundle.py`
- Modify: `tests/target0/prepare_qualification_bundle_test.py`
- Modify: `tests/target0/CMakeLists.txt`

### Step 1: Add failing compiler-identity and build tests

Tests must prove:

- `/usr/bin/clang++-21` is the invoked C++ driver;
- its resolved executable, first version line, target triple, and digest match
  the installed lock;
- `/usr/bin/ld.lld-21` belongs to the exact locked `lld-21` package version,
  passes `dpkg -V`, and has a retained path/version/digest;
- a compiler or linker symlink resolving elsewhere is rejected;
- the build command contains C++23, `-O3`, `-DNDEBUG`, the complete warning
  set, absolute LLD selection, one source, and one output;
- `-march=native`, `-ffast-math`, arbitrary environment flags, and caller flags
  cannot enter the command;
- two equal output hashes pass;
- deliberately different first/second build bytes reject the bundle;
- a failed compiler command retains diagnostics but cannot publish an accepted
  artifact.

Pass these extra CTest inputs explicitly:

```text
--cmake-cache ${PROJECT_BINARY_DIR}/CMakeCache.txt
--compile-commands ${PROJECT_BINARY_DIR}/compile_commands.json
--cmake-presets ${PROJECT_SOURCE_DIR}/CMakePresets.json
--warning-module ${PROJECT_SOURCE_DIR}/cmake/quality/XoasWarnings.cmake
```

The drift test compares the preparation flags with the qualification probe's
real configured compile command, the cached Release flags, the warning module,
and the locked LLD preset.

Run:

```bash
ctest --preset dev-debug \
  -R '^target0-qualification-bundle-build$' --output-on-failure
```

Expected: FAIL because compiler validation and dual-build functions are absent.

### Step 2: Implement identity validation and fixed command construction

Add helpers with narrow return records:

```python
def validate_compiler(lock: dict[str, object], runner: CommandRunner) -> dict[str, object]:
    """Authenticate the fixed Target 0 C++ driver against the lock."""


def validate_linker(lock: dict[str, object], runner: CommandRunner) -> dict[str, object]:
    """Authenticate LLD against the locked package closure and live bytes."""


def qualification_compile_arguments(source: Path, output: Path) -> tuple[str, ...]:
    """Return the closed native qualification-probe build contract."""


def build_probe_twice(...) -> dict[str, object]:
    """Build independently and require byte-identical executables."""
```

Use a private temporary directory under each build directory for `TMPDIR` and
an explicit environment containing only `HOME=/nonexistent`, `LANG=C.UTF-8`,
`LC_ALL=C.UTF-8`, fixed `PATH`, `SOURCE_DATE_EPOCH` derived from the reviewed
commit, and that private `TMPDIR`. Retain the realized environment, excluding
the staging-specific temporary path from executable identity.

Create outputs with private permissions. Require regular, non-symlink,
nonempty executable files before hashing.

Copy the already-hashed probe source bytes into both private build directories
under the same relative filename. Run both compiler invocations from their
respective build directories with identical relative source and output
arguments. This prevents a repository home path or staging-attempt name from
entering the command or executable identity while preserving byte equality
with the reviewed source.

Register `target0-qualification-bundle-build` with a focused unittest filter
and the cache/compile-command/preset/warning inputs above.

### Step 3: Run build-contract tests in Debug and Release configurations

Run:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug \
  --target xoas-target0-qualification-probe
ctest --preset dev-debug \
  -R '^target0-qualification-bundle-(build|schema)$' --output-on-failure

cmake --preset dev-release
cmake --build --preset dev-release \
  --target xoas-target0-qualification-probe
ctest --preset dev-release \
  -R '^target0-qualification-bundle-(build|schema)$' --output-on-failure
```

Expected: both configurations pass, and the drift test confirms the direct
physical build contract remains aligned with the CMake qualification target.

### Step 4: Commit the authenticated build path

Run:

```bash
git add \
  tests/target0/CMakeLists.txt \
  tests/target0/prepare_qualification_bundle_test.py \
  tools/target0/prepare_qualification_bundle.py
git diff --cached --check
git diff --cached --stat
git commit -m "tool: build authenticated Target 0 qualification probe"
```

---

## Task 4: Add ELF provenance and target-runtime verification

**Files:**

- Modify: `tools/target0/prepare_qualification_bundle.py`
- Modify: `tests/target0/prepare_qualification_bundle_test.py`
- Modify: `tests/target0/CMakeLists.txt`

### Step 1: Add failing inspection and compatibility-test cases

Fixture command results must cover:

- valid `file`, `readelf -h`, `readelf -n`, `readelf -d`, and `ldd` output;
- missing or malformed ELF64/x86-64 identity;
- unresolved, duplicate, relative, or unexpected dynamic dependencies;
- canonicalized dependency realpaths and SHA-256 values;
- `dpkg-query -S` owner and exact `dpkg-query -W` version for each system
  runtime dependency;
- optional build ID present or explicitly absent;
- nonzero Python byte-compilation, Bash syntax, focused capture/session tests,
  qualification-probe behavioral tests, or schema validation;
- full command log capture without environment/access leakage.

Run:

```bash
ctest --preset dev-debug \
  -R '^target0-qualification-bundle-inspection$' --output-on-failure
```

Expected: FAIL because inspection and compatibility-test orchestration are
absent.

### Step 2: Implement ELF/runtime collection

Add pure parsers separate from command execution so malformed-output behavior
is fixture-testable. Run only absolute or lock-validated tools. Record:

- ELF class, endianness, machine, type, interpreter, and build ID;
- each `NEEDED` entry;
- each resolved dependency's loader path, realpath, size, SHA-256, owning
  package, and package version;
- the complete inspection command status and log digest.

Reject unresolved dependencies, non-system dependency injection, or a loaded
library below an unapproved writable/staging path. The qualification probe is
not allowed to load any baseline library from `/opt/xoas/target0-v1`.

### Step 3: Implement physical compatibility-test orchestration

The accepted build must run these existing tests from the exact checkout with
explicit paths and the allowlisted environment:

```bash
python3 -m py_compile \
  tools/target0/prepare_qualification_bundle.py \
  tools/target0/capture_host.py
bash -n tools/target0/measurement_session.sh
python3 tests/target0/capture_host_test.py
python3 tests/target0/measurement_session_test.py
python3 tests/target0/qualification_probe_test.py \
  --probe "$xoasAcceptedProbe" \
  --schema schemas/target0-host-qualification-v1.schema.json
```

`xoasAcceptedProbe` denotes the verified relative `bin/` copy created only after
the two build hashes match; the preparation implementation supplies that path
as an argument rather than evaluating this shell notation. Each command
receives a separate retained stdout/stderr log and closed result record. The
preparation tool then meta-validates and validates the process and bundle
schemas using the physical host's installed `jsonschema`.

Register `target0-qualification-bundle-inspection` with a focused unittest
filter.

### Step 4: Rerun focused tests

Run:

```bash
python3 tests/target0/prepare_qualification_bundle_test.py \
  --schema schemas/target0-qualification-tool-bundle-v1.schema.json \
  --example tests/target0/fixtures/qualification-tool-bundle-v1.example.json \
  --cmake-cache build/dev-debug/CMakeCache.txt \
  --compile-commands build/dev-debug/compile_commands.json \
  --cmake-presets CMakePresets.json \
  --warning-module cmake/quality/XoasWarnings.cmake
ctest --preset dev-debug \
  -R '^target0-qualification-bundle-' --output-on-failure
```

Expected: schema, build, inspection, failure, and compatibility orchestration
tests all pass with fixture commands only.

### Step 5: Commit target-runtime verification

Run:

```bash
git add \
  tests/target0/CMakeLists.txt \
  tests/target0/prepare_qualification_bundle_test.py \
  tools/target0/prepare_qualification_bundle.py
git diff --cached --check
git diff --cached --stat
git commit -m "tool: verify Target 0 qualification runtime"
```

---

## Task 5: Finalize deterministic inventory and rejection behavior

**Files:**

- Modify: `tools/target0/prepare_qualification_bundle.py`
- Add: `tools/target0/verify_qualification_bundle.py`
- Modify: `tests/target0/prepare_qualification_bundle_test.py`
- Modify: `tests/target0/fixtures/qualification-tool-bundle-v1.example.json`
- Modify: `tests/target0/CMakeLists.txt`
- Modify: `tools/target0/CMakeLists.txt`

### Step 1: Add failing finalization tests

Tests must assert:

```python
self.assertEqual(
    module.canonical_json_bytes(record),
    module.canonical_json_bytes(copy.deepcopy(record)),
)
self.assertEqual(
    [item["path"] for item in inventory["files"]],
    sorted(item["path"] for item in inventory["files"]),
)
```

Also prove:

- inventory paths are relative, unique, regular files and never symlinks;
- every size and digest is recomputed from bytes;
- `inventory.json` excludes itself and `acceptance.json`;
- `acceptance.json` authenticates the exact inventory digest and bundle
  manifest digest;
- unequal first/second executable digests are rejected even when a malformed
  retained record claims `identical: true`;
- final revalidation detects a changed byte, missing file, extra file, unsafe
  type, or changed acceptance record;
- a rejected attempt has `status: rejected`, a closed reason, nonzero CLI
  status, and no `acceptance.json`;
- an accepted attempt cannot overwrite or reuse a prior root;
- the fresh-process verifier accepts an unchanged bundle and rejects every
  changed, missing, extra, or unsafe file case;
- timestamps and staging paths do not affect normalized executable identity;
- no credential, access alias, network coordinate, home path, or full
  environment enters retained JSON/log metadata.

Run:

```bash
ctest --preset dev-debug \
  -R '^target0-qualification-bundle-finalization$' --output-on-failure
```

Expected: FAIL because finalization is absent.

### Step 2: Implement write-once finalization

Add:

```python
def build_inventory(bundle_root: Path) -> dict[str, object]:
    """Hash every retained regular file in canonical path order."""


def validate_inventory(bundle_root: Path, inventory: dict[str, object]) -> None:
    """Recompute one finalized bundle without trusting retained hashes."""


def finalize_bundle(...) -> dict[str, object]:
    """Publish a closed manifest, inventory, and final acceptance record."""
```

Use no replacement writes. Flush and `fsync` each file before publication.
Publish `acceptance.json` last. On any error, write only a rejected diagnostic
record when that can be done safely; never create the acceptance record.

The `main()` success path is now complete:

1. parse explicit inputs;
2. validate the exact clean repository identity;
3. validate safe output intent and create the private staging root;
4. validate the lock, target, compiler, and linker;
5. build twice and compare;
6. inspect ELF and dependencies;
7. execute target compatibility checks;
8. write and schema-validate `bundle.json`;
9. write and validate `inventory.json`;
10. publish `acceptance.json` last;
11. independently revalidate the finalized bundle;
12. return zero.

Register `target0-qualification-bundle-finalization` with a focused unittest
filter.

Add the narrow replica-verification interface:

```text
python3 tools/target0/verify_qualification_bundle.py
  --bundle-directory PATH
  --schema PATH
```

The verifier imports the retained validation implementation but starts a fresh
process, trusts no manifest digest, recomputes every file, revalidates the
closed records, and emits only the accepted inventory, manifest, and executable
digests on success. Add it to the `target0-host-tools` byte-compilation gate.

### Step 3: Run the entire targeted suite

Run:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug \
  --target xoas-target0-qualification-probe target0-host-tools
ctest --preset dev-debug \
  -R '^target0-(qualification-bundle|qualification-probe|host-tools-)' \
  --output-on-failure
git diff --check
```

Expected: all existing and new Target 0 tests pass; no real measurement control
is touched.

### Step 4: Commit complete tool behavior

Run:

```bash
git add \
  tests/target0/CMakeLists.txt \
  tests/target0/fixtures/qualification-tool-bundle-v1.example.json \
  tests/target0/prepare_qualification_bundle_test.py \
  tools/target0/CMakeLists.txt \
  tools/target0/prepare_qualification_bundle.py \
  tools/target0/verify_qualification_bundle.py
git diff --cached --check
git diff --cached --stat
git commit -m "tool: finalize Target 0 qualification bundle"
```

---

## Task 6: Integrate the durable decision and operator contract

**Files:**

- Add: `docs/adr/IDR-0002-target0-qualification-tool-deployment.md`
- Modify: `docs/architecture/README.md`
- Modify: `docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md`
- Modify: `docs/milestones/M0-acceptance.md`
- Modify: `docs/milestones/status.md`
- Modify: `docs/targets/target0-amd-ryzen9-7900x-v1.md`
- Modify: `docs/superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md`
- Modify: `AGENTS.md`

### Step 1: Record the implementation decision

IDR-0002 must record:

- physical native-build authority and `gpu-2` quality authority;
- the exact operator interface and `/var/tmp` output policy;
- the fresh-process bundle-verification interface;
- compiler direct-lock validation and LLD package-plus-live-byte validation;
- dual-build equality;
- interpreted-tool and ELF/runtime evidence;
- external two-host retention with compact Git evidence;
- no campaign, benchmark, qualification, reboot, or product authority;
- reversal and invalidation behavior.

### Step 2: Bind the deployment prerequisite into Task 5

Update the controlling qualification plan before its core-selection step to
require:

- an accepted bundle at the exact campaign commit;
- matching physical and `gpu-2` inventory digests;
- pre-process recomputation of executable, compiler, linker, source, lock,
  checkout, and boot identities;
- complete campaign rejection on drift;
- no interpretation of deployment compatibility timings as campaign samples.

Do not mark Task 5 started or passed.

### Step 3: Update the manual and frontier with verified commands only

Add the new development test command and physical preparation interface to
`AGENTS.md`. Clearly label the physical command unavailable until native
execution proves it. Update the repository map, schema taxonomy, artifact
rules, and frontier without embedding a percentage or claiming target
qualification.

Update M0 acceptance/status and the target record to say implementation exists
but native deployment evidence is still pending.

### Step 4: Run documentation and policy checks

Run:

```bash
cmake --build --preset dev-debug --target docs-check repository-policy
ctest --preset dev-debug \
  -R '^(quality-policy|target0-qualification-bundle-)' \
  --output-on-failure
git diff --check
```

Expected: documentation links, schema map, policy checks, and deployment tests
pass; the frontier still says M0 and qualification are open.

### Step 5: Commit documentation integration

Run:

```bash
git add \
  AGENTS.md \
  docs/adr/IDR-0002-target0-qualification-tool-deployment.md \
  docs/architecture/README.md \
  docs/milestones/M0-acceptance.md \
  docs/milestones/status.md \
  docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md \
  docs/superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md \
  docs/targets/target0-amd-ryzen9-7900x-v1.md
git diff --cached --check
git diff --cached --stat
git commit -m "docs: record Target 0 deployment procedure"
```

---

## Task 7: Prove the exact development implementation subject

**Files:** No planned source changes. Any corrective change returns to its
own failing test and receives a scoped commit.

### Step 1: Run a clean Debug quality aggregate

Run on `gpu-2` from a clean clone or clean primary checkout at the exact branch
head:

```bash
cmake -DXOAS_REPOSITORY_ROOT="$PWD" \
  -P cmake/quality/CleanBuildTrees.cmake
cmake --preset dev-debug
cmake --build --preset dev-debug --target quality
ctest --preset dev-debug --output-on-failure
```

Expected: configuration succeeds with the locked development toolchain and the
complete quality aggregate plus all CTests pass.

### Step 2: Run Release and sanitizer evidence explicitly

Run:

```bash
cmake --preset dev-release
cmake --build --preset dev-release --target warnings
ctest --preset dev-release --output-on-failure

cmake --preset asan-ubsan
cmake --build --preset asan-ubsan --target asan-ubsan
ctest --preset asan-ubsan \
  -R '^quality-sanitizer-' --output-on-failure
```

Expected: Release compilation/tests and isolated ASan/UBSan gates pass.

### Step 3: Review the exact diff and evidence boundary

Review:

```bash
git diff origin/main...HEAD --stat
git diff origin/main...HEAD -- \
  schemas/target0-qualification-tool-bundle-v1.schema.json \
  tools/target0/prepare_qualification_bundle.py \
  tests/target0/prepare_qualification_bundle_test.py \
  tests/target0/fixtures/qualification-tool-bundle-v1.example.json
git log --oneline --decorate origin/main..HEAD
git status --short --branch
```

The head-engineering review must explicitly check:

- no shell-evaluated subprocess;
- no implicit compiler or commit;
- no environment/credential leakage;
- no overwrite or unsafe cleanup;
- no self-authentication;
- exact schema closure;
- complete negative coverage;
- no campaign or performance claim;
- no M1/product scaffolding.

Record the exact review model. If no independent reviewer is authorized, state
that fact and obtain explicit user acceptance before calling the deployment
implementation reviewed.

### Step 4: Push the tested implementation subject

Run:

```bash
git status --short --branch
git push origin task/m0-target0-qualification-tools
git rev-parse HEAD
git ls-remote --heads origin task/m0-target0-qualification-tools
```

Expected: the local and remote branch identify the same full tested commit.
Record that commit as the implementation subject.

---

## Task 8: Build and retain the native physical-host bundle

**Files on the physical host:**

- Read: exact clean XOAS checkout at the implementation subject
- Read: `toolchains/target0-amd-ryzen9-7900x-v1.lock.json`
- Create externally: one new
  `/var/tmp/xoas-target0-qualification-tools.*` evidence root

**Repository files:** No Git changes during native execution.

### Step 1: Advance the clean physical checkout explicitly

From the physical checkout, first prove the existing tree is clean. Then run:

```bash
git status --porcelain
git fetch origin task/m0-target0-qualification-tools
xoasImplementationCommit=$(git rev-parse \
  refs/remotes/origin/task/m0-target0-qualification-tools)
git checkout --detach "$xoasImplementationCommit"
git status --short --branch
git rev-parse HEAD
git status --porcelain
```

Expected: the initial and final porcelain outputs are empty, and the detached
HEAD is the exact tested implementation subject. Stop rather than overwrite any
unexpected physical-host change.

### Step 2: Recheck the immutable inputs

Run from the physical checkout:

```bash
python3 -m json.tool \
  toolchains/target0-amd-ryzen9-7900x-v1.lock.json >/dev/null
sha256sum \
  tools/target0/prepare_qualification_bundle.py \
  tools/target0/qualification_probe.cpp \
  tools/target0/capture_host.py \
  tools/target0/measurement_session.sh \
  schemas/target0-host-qualification-v1.schema.json \
  schemas/target0-qualification-tool-bundle-v1.schema.json
/usr/bin/clang++-21 --version
/usr/bin/ld.lld-21 --version
git status --porcelain
```

Expected: all inputs exist, compiler/linker report 21.1.8, and the checkout
remains clean. The preparation bundle independently repeats these checks.

### Step 3: Execute one fresh preparation attempt

Before execution, select one unique attempt basename, confirm it is absent, and
record it in the operator evidence. Then run the approved interface:

```bash
python3 tools/target0/prepare_qualification_bundle.py \
  --repository-root "$PWD" \
  --expected-commit "$xoasImplementationCommit" \
  --toolchain-lock \
    "$PWD/toolchains/target0-amd-ryzen9-7900x-v1.lock.json" \
  --output-directory "$xoasBundleDirectory"
```

`xoasBundleDirectory` is the prechecked absolute immediate child of `/var/tmp`
with the required basename prefix. It is assigned in the external execution
record so no access or home path enters Git.

Expected: exit zero, `acceptance.json` exists, the two build digests match, all
target tests pass, and every record says `performance_claim: false`. If the
command fails, retain the entire rejected root and return to root-cause analysis;
do not retry with the same directory.

### Step 4: Independently verify the physical inventory

Run the fresh-process verifier:

```bash
python3 tools/target0/verify_qualification_bundle.py \
  --bundle-directory "$xoasBundleDirectory" \
  --schema \
    schemas/target0-qualification-tool-bundle-v1.schema.json
```

It loads `inventory.json`, recomputes every listed regular-file size and
SHA-256, rejects unlisted files other than `inventory.json` and
`acceptance.json`, validates the closed records, and checks the acceptance
record's inventory and manifest digests.

Record:

- bundle manifest SHA-256;
- inventory SHA-256;
- executable SHA-256;
- physical checkout commit/tree/clean state;
- compiler/linker versions and executable hashes;
- test count and statuses;
- boot ID digest as deployment metadata only.

No duration becomes a performance or campaign sample.

### Step 5: Replicate byte-for-byte to `gpu-2`

Use the approved external transport without retaining credentials, aliases, or
network coordinates in Git. Copy the complete finalized directory into a new
`/var/tmp` evidence location on `gpu-2`. Re-run the fresh inventory verification
there and require the same inventory, manifest, and executable SHA-256 values.

Do not rebuild on `gpu-2` and call that artifact target-authoritative. The
replica is storage and verification evidence for the physical bytes.

### Step 6: Stop before campaign execution

Confirm:

- no measurement session was entered;
- no governor, EPP, boost, or sibling state was changed;
- no `perf` campaign was run;
- no reboot occurred;
- physical and `gpu-2` accepted-bundle digests match.

Task 5 campaign execution remains outside this plan.

---

## Task 9: Bind deployment evidence into the repository

**Files:**

- Add: `benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json`
- Add: `benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.sha256`
- Modify: `benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json`
- Modify: `cmake/quality/RepositoryPolicy.cmake`
- Modify: `docs/milestones/M0-acceptance.md`
- Modify: `docs/milestones/status.md`
- Modify: `docs/targets/target0-amd-ryzen9-7900x-v1.md`
- Modify: `AGENTS.md`

### Step 1: Add compact non-secret deployment evidence

Copy only the closed text manifest/receipt required by the approved schema.
The repository evidence must bind:

- implementation commit and tree;
- provisioning-lock/configuration digest;
- source, compiler, linker, executable, manifest, and inventory digests;
- dual-build equality;
- physical compatibility-test results;
- physical and `gpu-2` replica digest equality;
- external storage classification without access details;
- `performance_claim: false`;
- explicit statements that campaign, qualification, and reboot did not occur.

Do not commit the ELF executable, raw test logs, access metadata, or broad
environment data.

Extend the repository-policy schema map so the actual deployment receipt and
the synthetic fixture are both validated by the bundle schema. Add a focused
cross-check that the `.sha256` record matches the committed receipt bytes and
that the target manifest names the same inventory and executable digests.

### Step 2: Update state without overclaiming

Set the deployment gate to passed and record the exact bundle evidence. Leave:

- `candidate_unqualified` unchanged;
- campaign one pending;
- campaign two pending;
- `target0_measurement_qualified: false`;
- M0 open;
- the baseline numerical-admission dependency conflict explicit.

Update `AGENTS.md` from planned to verified only for commands actually run on
the physical host and `gpu-2`.

### Step 3: Validate evidence and run final development quality

Run on `gpu-2` at the evidence commit candidate:

```bash
python3 -m json.tool \
  benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json \
  >/dev/null
python3 -m json.tool \
  benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json >/dev/null
git diff --check
cmake --preset dev-debug
cmake --build --preset dev-debug --target quality
ctest --preset dev-debug --output-on-failure
cmake --preset dev-release
cmake --build --preset dev-release --target warnings
ctest --preset dev-release --output-on-failure
```

Expected: all schema/policy checks and Debug/Release suites pass at the exact
evidence state. The acceptance record states that deployment—not campaign
qualification—is closed.

### Step 4: Commit and push the evidence checkpoint

Run:

```bash
git add \
  AGENTS.md \
  benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json \
  benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.sha256 \
  benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json \
  cmake/quality/RepositoryPolicy.cmake \
  docs/milestones/M0-acceptance.md \
  docs/milestones/status.md \
  docs/targets/target0-amd-ryzen9-7900x-v1.md
git diff --cached --check
git diff --cached --stat
git commit -m "docs: bind Target 0 qualification tool evidence"
git push origin task/m0-target0-qualification-tools
git status --short --branch
git rev-parse HEAD
```

Expected: one exact clean pushed evidence commit. The handoff names both the
tested implementation subject and final evidence commit, retained bundle
digests, every command/result, unresolved review/dependency gaps, and Task 5 as
the next separately authorized execution slice.

## Completion gate

This plan is complete only when:

- all new schema and behavior tests pass;
- the full `gpu-2` development quality contract passes at the implementation
  and evidence subjects;
- one target-native bundle is accepted from a clean exact physical checkout;
- compiler, linker, runtime, source, repository, lock, executable, and bundle
  provenance is closed;
- independent dual-build and replica digest checks pass;
- the repository contains only compact non-secret text evidence;
- no campaign, performance claim, qualification, host-control mutation, or
  reboot occurred;
- the exact commits and dirty/clean states are reported.

Only then is qualification-tool deployment closed and Task 5 campaign one
ready for a separate execution decision.
