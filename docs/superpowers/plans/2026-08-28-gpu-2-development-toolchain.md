# gpu-2 Development Toolchain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provision and pin the smallest complete C++ quality toolchain on `gpu-2`, prove each required tool with positive and negative probes, and record a non-secret reproducible identity without implying Target 0 measurement qualification.

**Architecture:** Treat server provisioning as a reversible evidence-producing operation. First verify the host and planned system paths, then install the official LLVM 21 stable branch and Ubuntu Noble support tools by exact package version. Use versioned LLVM executable names and leave system-wide compiler alternatives unchanged. Record the requested package set, installed dependency closure, executable hashes, validation results, and rollback facts in a machine-readable lock plus a human review record. The later quality-gates plan consumes this lock; no product/compiler source is introduced here.

**Tech Stack:** Ubuntu 24.04 Noble APT, apt.llvm.org LLVM 21 packages, Clang/clang-tidy/clang-format/LLD/compiler-rt, CMake, Ninja, Doxygen, Graphviz, ShellCheck, SQLite development tools, JSON Schema draft 2020-12, PyYAML, Git, and Python 3.12 standard-library validation.

**Spec:** [`docs/engineering/coding-standards.md`](../../engineering/coding-standards.md), [`docs/adr/IDR-0001-engineering-quality-system.md`](../../adr/IDR-0001-engineering-quality-system.md), [`docs/architecture/proposals/AR-0001-target-0-host-qualification.md`](../../architecture/proposals/AR-0001-target-0-host-qualification.md), and [`docs/exact_instance_matrix_kernel_synthesizer_build_plan.md`](../../exact_instance_matrix_kernel_synthesizer_build_plan.md).

## Global Constraints

- AR-0001 Option 2 must be recorded at an exact commit before state-changing execution. That prerequisite is satisfied once the milestone ledger names the decision integration commit.
- Work in the primary checkout; do not create a worktree unless a concrete isolation need appears.
- Do not record network coordinates, login identities, credentials, private-key locations, or connection commands in repository content or handoff text.
- Begin from an already authenticated shell on `gpu-2`; server access setup is outside this plan.
- Do not install baseline libraries, a benchmark harness, product code, GPU tooling, or a self-hosted CI runner.
- Do not claim that a development-toolchain result qualifies `gpu-2` for Target 0 measurements.
- Use LLVM 21's versioned packages and executables. Do not install moving unversioned LLVM meta-packages and do not change `update-alternatives`.
- Use Ubuntu's `libstdc++` host ABI for provisioning probes. This does not decide M1's public ABI, exception model, or RTTI policy.
- Resolve exact package candidates only after a successful fresh APT metadata update. Never substitute an assumed or locally cached version.
- Every state-changing server command has a preceding collision check, a recorded pre-state, and a documented rollback command. Do not perform rollback during normal execution.
- Stop if a planned XOAS-owned system path already exists with unexpected content, the archive key fingerprint differs, an exact candidate disappears, or a validation probe fails.
- Apply the LLVM-style documentation rules to repository-authored records. Temporary negative fixtures are test inputs and are removed after evidence capture.

---

## Task 1: Reconfirm the Host and Capture the Immutable Pre-State

**Files:**

- Create: `docs/toolchain/gpu-2-development-toolchain-v1.md`

- [x] **Step 1: Verify the repository boundary**

Run locally:

```bash
git status --short --branch
git rev-parse HEAD
git diff --check
```

Expected: `main` tracks `origin/main`, the tree has only the approved planning changes when execution begins, and no unrelated diff is present.

- [x] **Step 2: Verify the server identity and privilege boundary**

Run inside the authenticated `gpu-2` shell:

```bash
set -eu
test "$(hostname -s)" = gpu-2
. /etc/os-release
test "$ID" = ubuntu
test "$VERSION_CODENAME" = noble
test "$(dpkg --print-architecture)" = amd64
sudo -n true
```

Expected: every check exits zero. If non-interactive privilege is unavailable, stop and request an administrator-approved privilege path without storing a password.

- [x] **Step 3: Prove the planned system paths are collision-free**

Inspect, without modifying:

```bash
for path in \
  /usr/share/keyrings/xoas-llvm-archive-keyring.gpg \
  /etc/apt/sources.list.d/xoas-llvm-21.list; do
  if test -e "$path"; then
    sudo stat "$path"
    sudo sha256sum "$path"
  fi
done
apt-mark showhold
dpkg-query -W > /tmp/xoas-toolchain-dpkg-prestate.txt
```

Expected: XOAS-owned paths are absent. If either exists, compare it with the planned content and stop on any mismatch.

- [x] **Step 4: Create or verify the clean server checkout**

Use the non-secret path `$HOME/XOAS` without recording the expanded home path or login identity. First require `$HOME` to resolve below `/home` and not to `/`, `/home`, or an empty value. If `$HOME/XOAS` is absent, clone the public `origin` repository there. If it exists, require it to be a Git checkout with the expected public remote, a clean working tree, and no untracked files; stop rather than overwrite unexpected content.

Fetch `origin/main`, fast-forward the checkout, and require its `HEAD` to equal the exact approved planning commit before subsequent tasks consume repository lock files. Do not create a linked worktree or store credentials in the remote URL.

- [x] **Step 5: Write the pre-state section**

Create `docs/toolchain/gpu-2-development-toolchain-v1.md` with:

- authority and scope;
- capture time in UTC and exact XOAS commit;
- non-secret OS and architecture confirmation;
- whether each XOAS-owned system path was absent or matched;
- existing package holds;
- explicit statement that no package or source was changed during Task 1;
- server checkout path expressed only as `$HOME/XOAS` and its exact commit;
- rollback policy and stop conditions;
- Target 0 measurement non-qualification warning.

- [x] **Step 6: Verify the record**

```bash
rg -n "Scope|Pre-state|Rollback|Target 0|No package" docs/toolchain/gpu-2-development-toolchain-v1.md
git diff --check
```

Expected: all required sections are found and no whitespace error is reported.

**Commit boundary:** none; Task 1 evidence is completed with the package lock in Task 3.

---

## Task 2: Add and Authenticate the Versioned LLVM 21 Source

**Files:**

- Modify: `docs/toolchain/gpu-2-development-toolchain-v1.md`

- [x] **Step 1: Create a guarded temporary workspace**

Run inside `gpu-2`:

```bash
xoasTmpDir=$(mktemp -d /tmp/xoas-llvm-source.XXXXXX)
test "$(dirname "$(realpath "$xoasTmpDir")")" = /tmp
trap 'find "$xoasTmpDir" -xdev -type f -delete; rmdir "$xoasTmpDir"' EXIT
```

Expected: a unique directory exists directly below `/tmp` and cleanup is armed.

- [x] **Step 2: Download and verify the official archive key**

```bash
curl --fail --show-error --silent --location \
  https://apt.llvm.org/llvm-snapshot.gpg.key \
  --output "$xoasTmpDir/llvm-snapshot.gpg.key"
gpg --show-keys --with-colons "$xoasTmpDir/llvm-snapshot.gpg.key" \
  > "$xoasTmpDir/key-record.txt"
test "$(awk -F: '$1 == "fpr" {print $10; exit}' \
  "$xoasTmpDir/key-record.txt")" = \
  6084F3CF814B57C1CF12EFD515CF4D18AF4F7421
gpg --batch --yes --dearmor \
  --output "$xoasTmpDir/xoas-llvm-archive-keyring.gpg" \
  "$xoasTmpDir/llvm-snapshot.gpg.key"
```

Expected: the fingerprint comparison succeeds exactly. A mismatch is a hard stop.

- [x] **Step 3: Prepare exact source content and recheck collisions**

```bash
printf '%s\n' \
  'deb [signed-by=/usr/share/keyrings/xoas-llvm-archive-keyring.gpg] https://apt.llvm.org/noble/ llvm-toolchain-noble-21 main' \
  > "$xoasTmpDir/xoas-llvm-21.list"
test ! -e /usr/share/keyrings/xoas-llvm-archive-keyring.gpg
test ! -e /etc/apt/sources.list.d/xoas-llvm-21.list
```

Expected: content is exact and both destination paths remain absent.

- [x] **Step 4: Install only the authenticated source metadata**

```bash
sudo install -o root -g root -m 0644 \
  "$xoasTmpDir/xoas-llvm-archive-keyring.gpg" \
  /usr/share/keyrings/xoas-llvm-archive-keyring.gpg
sudo install -o root -g root -m 0644 \
  "$xoasTmpDir/xoas-llvm-21.list" \
  /etc/apt/sources.list.d/xoas-llvm-21.list
sudo apt-get update
```

Expected: APT authenticates the new source and completes without repository, signature, or release-file warnings.

- [x] **Step 5: Record source provenance and rollback**

Append the key fingerprint, source line, file hashes, APT refresh time, and these rollback operations to the toolchain record:

```bash
sudo apt-mark unhold clang-21 clang-tools-21 clang-format-21 \
  clang-tidy-21 clangd-21 lld-21 llvm-21 libclang-rt-21-dev
sudo test -f /etc/apt/sources.list.d/xoas-llvm-21.list
sudo unlink /etc/apt/sources.list.d/xoas-llvm-21.list
sudo test -f /usr/share/keyrings/xoas-llvm-archive-keyring.gpg
sudo unlink /usr/share/keyrings/xoas-llvm-archive-keyring.gpg
sudo apt-get update
```

Do not execute the rollback during normal provisioning.

---

## Task 3: Resolve and Commit the Exact Package Lock Before Installation

**Files:**

- Create: `schemas/development-toolchain-v1.schema.json`
- Create: `toolchains/gpu-2-development-toolchain-v1.lock.json`
- Modify: `docs/toolchain/gpu-2-development-toolchain-v1.md`
- Modify: `docs/architecture/README.md`

- [x] **Step 1: Define the closed lock schema**

Use JSON Schema draft 2020-12 with `additionalProperties: false` at every closed record. Require:

- `manifest_version`, `lock_id`, `captured_at_utc`, and exact XOAS commit;
- non-secret host OS, codename, and architecture;
- archive URL, suite, component, key fingerprint, and source-file SHA-256;
- requested packages with exact candidate version, origin class, reason, and hold policy;
- installed package closure, initially an empty array with state `resolved_not_installed`;
- expected versioned binaries;
- validation state and named probes;
- rollback paths and pre-existing hold facts;
- explicit booleans for build readiness and Target 0 measurement qualification.

Durable hashes are lowercase 64-character SHA-256 strings. The schema must prohibit credential and network-coordinate fields.

- [x] **Step 2: Resolve every exact candidate from the refreshed cache**

The requested package set is:

```text
build-essential
cmake
ninja-build
doxygen
graphviz
pkg-config
sqlite3
libsqlite3-dev
python3-jsonschema
python3-yaml
shellcheck
clang-21
clang-tools-21
clang-format-21
clang-tidy-21
clangd-21
lld-21
llvm-21
libclang-rt-21-dev
```

For each literal package name in the requested set, run `apt-cache policy "$packageName"` from a shell loop and require one non-`(none)` candidate. Record the exact candidate string and the repository origin shown by `apt-cache policy`.

- [x] **Step 3: Prove every requested version is installable before mutation**

Run one simulation whose arguments are generated as `name=exact-version` pairs from the proposed lock:

```bash
mapfile -t xoasPackageSpecs < <(
  python3 - <<'PY'
import json
from pathlib import Path

lock = json.loads(
    Path("toolchains/gpu-2-development-toolchain-v1.lock.json").read_text()
)
for package in lock["requested_packages"]:
    print(f'{package["name"]}={package["version"]}')
PY
)
test "${#xoasPackageSpecs[@]}" -eq 19
sudo apt-get --simulate --no-install-recommends install \
  "${xoasPackageSpecs[@]}"
```

Expected: exit zero, no removals, and no architecture change. Preserve the generated arguments in the evidence record so the simulation is tied to the reviewed lock.

- [x] **Step 4: Write and validate the pre-install lock**

Set `installed_package_closure` to `[]`, `state` to `resolved_not_installed`, `build_ready` to `false`, and `target0_measurement_qualified` to `false`.

Perform syntax and cross-field checks before installation. Full schema validation is a mandatory Task 5 probe after the locked validator package is installed:

```bash
python3 -m json.tool schemas/development-toolchain-v1.schema.json >/dev/null
python3 -m json.tool toolchains/gpu-2-development-toolchain-v1.lock.json >/dev/null
python3 - <<'PY'
import json
from pathlib import Path

lock = json.loads(
    Path("toolchains/gpu-2-development-toolchain-v1.lock.json").read_text()
)
assert lock["state"] == "resolved_not_installed"
assert lock["build_ready"] is False
assert lock["target0_measurement_qualified"] is False
assert all(item["version"] for item in lock["requested_packages"])
assert len({item["name"] for item in lock["requested_packages"]}) == 19
PY
git diff --check
```

- [x] **Step 5: Commit and push the immutable install intent**

```bash
git add docs/toolchain/gpu-2-development-toolchain-v1.md \
  docs/architecture/README.md \
  schemas/development-toolchain-v1.schema.json \
  toolchains/gpu-2-development-toolchain-v1.lock.json
git commit -m "ops: lock gpu-2 development toolchain intent"
git push origin main
```

Expected: the exact planned package versions are reviewable in Git before installation begins.

**Commit boundary:** `ops: lock gpu-2 development toolchain intent`

---

## Task 4: Install Exact Packages and Hold the LLVM Tool Surface

**Files:**

- Modify: `toolchains/gpu-2-development-toolchain-v1.lock.json`
- Modify: `docs/toolchain/gpu-2-development-toolchain-v1.md`

- [x] **Step 1: Revalidate the reviewed lock against live candidates**

Pull the just-pushed commit on the server's clean checkout or transfer only the reviewed lock through the established secure development channel. Re-run `apt-cache policy` for every requested package and require exact equality with the lock. Stop if any candidate drifted; update and review the lock in a separate commit before continuing.

- [x] **Step 2: Perform the exact install**

Run the same literal `name=exact-version` list proven by Task 3:

```bash
mapfile -t xoasPackageSpecs < <(
  python3 - <<'PY'
import json
from pathlib import Path

lock = json.loads(
    Path("toolchains/gpu-2-development-toolchain-v1.lock.json").read_text()
)
for package in lock["requested_packages"]:
    print(f'{package["name"]}={package["version"]}')
PY
)
test "${#xoasPackageSpecs[@]}" -eq 19
sudo apt-get --no-install-recommends install "${xoasPackageSpecs[@]}"
```

Expected: exit zero, no removals, no unreviewed top-level package, and no unversioned LLVM meta-package.

- [x] **Step 3: Hold the versioned LLVM entry packages**

```bash
sudo apt-mark hold clang-21 clang-tools-21 clang-format-21 \
  clang-tidy-21 clangd-21 lld-21 llvm-21 libclang-rt-21-dev
apt-mark showhold
```

Expected: all eight LLVM entry packages appear in the hold list. Ubuntu support packages remain eligible for security updates; any later version drift must fail the repository lock verification until reviewed.

- [x] **Step 4: Capture the installed dependency closure**

Record, without truncation:

- every package newly installed relative to Task 1's dpkg pre-state;
- exact `dpkg-query` version and architecture;
- package origin from APT policy;
- which entry packages are held;
- hashes of the two XOAS-owned APT files.

Update the lock state to `installed_unverified`. Do not mark the host build-ready yet.

- [x] **Step 5: Capture rollback commands without executing them**

Generate an explicit `apt-get remove` simulation for only the newly installed entry packages, record whether dependencies would be autoremovable, and retain the pre-state package list. The human record must state that removal is an operator decision because a later workload may have begun depending on the tools.

---

## Task 5: Prove Tool Behavior with Positive and Negative Probes

**Files:**

- Modify: `toolchains/gpu-2-development-toolchain-v1.lock.json`
- Modify: `docs/toolchain/gpu-2-development-toolchain-v1.md`

- [x] **Step 1: Capture exact binary identities**

For every required executable, record resolved path, first version line, and SHA-256:

```text
clang-21
clang++-21
clang-format-21
clang-tidy-21
clangd-21
ld.lld-21
llvm-ar-21
llvm-cov-21
llvm-profdata-21
cmake
ninja
doxygen
dot
pkg-config
sqlite3
shellcheck
python3
git
```

Require all paths to be system paths and all hashes to use lowercase SHA-256.

- [x] **Step 2: Prove warning-clean C++23 compilation**

Create a temporary documented C++ source and compile/run it with:

```bash
clang++-21 -std=c++23 -Wall -Wextra -Wpedantic -Werror \
  -fuse-ld=lld /tmp/xoas-toolchain-probe.cpp \
  -o /tmp/xoas-toolchain-probe
/tmp/xoas-toolchain-probe
```

Expected: compilation and execution both exit zero.

- [x] **Step 3: Prove formatter and tidy failure modes**

Use one intentionally misformatted temporary source. Require:

```bash
clang-format-21 --dry-run --Werror /tmp/xoas-format-negative.cpp
```

to fail, then format a copy and require the same check to pass. Use a separate source containing a reserved implementation identifier and require:

```bash
clang-tidy-21 /tmp/xoas-tidy-negative.cpp \
  --checks=-*,bugprone-reserved-identifier \
  --warnings-as-errors='*' -- -std=c++23
```

to fail. Require a standards-safe equivalent to pass.

- [x] **Step 4: Prove sanitizer failure modes**

Compile one temporary heap-use-after-free probe with AddressSanitizer and one signed-overflow probe with UndefinedBehaviorSanitizer. Each negative executable must exit nonzero under fail-fast options and emit its expected sanitizer family. Compile and run the positive C++23 probe under both sanitizers and require exit zero.

- [x] **Step 5: Prove CMake, Ninja, Doxygen, SQLite, and schema tooling**

Use a temporary CMake project configured with `clang++-21` and Ninja; build and test it. Run a minimal Doxygen input with warnings-as-errors. Compile and link a tiny SQLite C API probe using `pkg-config --cflags --libs sqlite3`. Import both `jsonschema` and `yaml`, then run:

```bash
python3 - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft202012Validator
import yaml

schema = json.loads(
    Path("schemas/development-toolchain-v1.schema.json").read_text()
)
lock = json.loads(
    Path("toolchains/gpu-2-development-toolchain-v1.lock.json").read_text()
)
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema).validate(lock)
assert yaml.__version__
PY
```

Expected: every positive probe passes and every named negative probe fails for the intended reason.

- [x] **Step 6: Remove temporary probes and record evidence**

Delete only the individually named `/tmp/xoas-*` probe files created by this task after validating their paths. Record command, exit status, concise diagnostic identity, and timestamp in the human record; do not store temporary negative binaries in Git.

---

## Task 6: Integrate the Verified Toolchain Identity

**Files:**

- Modify: `toolchains/gpu-2-development-toolchain-v1.lock.json`
- Modify: `benchmarks/manifests/target-gpu-2-candidate.json`
- Modify: `docs/toolchain/gpu-2-development-toolchain-v1.md`
- Modify: `docs/adr/IDR-0001-engineering-quality-system.md`
- Modify: `docs/milestones/M0-acceptance.md`
- Modify: `docs/milestones/status.md`
- Modify: `AGENTS.md`

- [x] **Step 1: Finalize the lock**

Set the lock state to `installed_verified`, populate the complete installed package closure and binary identities, record every probe as passed, and set `build_ready` to `true`. Keep `target0_measurement_qualified` false.

- [x] **Step 2: Update the candidate host manifest without rewriting history**

Replace its stale toolchain `installed` and `missing` facts with the verified capture, set `build_ready` true, and split the combined open requirement so C++ provisioning is closed while admitted measurement baselines remain open. Preserve its original capture time and add a new toolchain verification timestamp rather than pretending the full host was recaptured.

- [x] **Step 3: Record the durable implementation decision**

Update IDR-0001 with:

- LLVM 21 stable/versioned package selection;
- exact lock path and configuration digest;
- Ubuntu Noble CMake/Ninja/Doxygen identities;
- Clang with host `libstdc++` for quality probes only;
- held-versus-drift-detected package policy;
- explicit exclusion of public ABI, exceptions, RTTI, baselines, and measurement qualification.

- [x] **Step 4: Publish exact commands in the operating manual**

Update root `AGENTS.md` only with commands that just passed on `gpu-2`: version checks, CMake/Ninja smoke configuration, full JSON Schema validation, and toolchain-lock verification. Remove statements that the core C++ toolchain is absent. Retain every Target 0 warning.

- [x] **Step 5: Validate all changed records**

```bash
python3 -m json.tool schemas/development-toolchain-v1.schema.json >/dev/null
python3 -m json.tool toolchains/gpu-2-development-toolchain-v1.lock.json >/dev/null
python3 -m json.tool benchmarks/manifests/target-gpu-2-candidate.json >/dev/null
git diff --check
git status --short
```

Run the repository's current link, secret, and unfinished-marker audits exactly as recorded in `AGENTS.md`. Expected: all pass.

- [x] **Step 6: Commit, push, and verify the exact remote subject**

```bash
git add AGENTS.md benchmarks/manifests/target-gpu-2-candidate.json \
  docs/adr/IDR-0001-engineering-quality-system.md \
  docs/milestones/M0-acceptance.md docs/milestones/status.md \
  docs/toolchain/gpu-2-development-toolchain-v1.md \
  schemas/development-toolchain-v1.schema.json \
  toolchains/gpu-2-development-toolchain-v1.lock.json
git commit -m "ops: verify gpu-2 development toolchain"
git push origin main
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
git status --short --branch
```

Expected: local and remote commits match and the working tree is clean.

**Commit boundary:** `ops: verify gpu-2 development toolchain`

---

## Acceptance Evidence

This plan is complete only when all of the following are true on one exact commit:

- the pre-state, archive authentication, exact requested versions, dependency closure, holds, binary hashes, and rollback facts are recorded;
- the lock validates against its schema;
- C++23 warnings, formatter, reserved-identifier tidy, ASan, UBSan, CMake/Ninja, Doxygen, SQLite, and JSON Schema probes demonstrate their intended pass/fail behavior;
- versioned LLVM executables are used and global alternatives are untouched;
- root `AGENTS.md` contains only verified commands;
- the candidate host manifest says build-ready but still not measurement-qualified;
- baseline libraries, product code, and self-hosted CI remain absent;
- the exact verified commit is pushed and reported.

Completion of this plan closes only the primary-development-toolchain prerequisite. It does not close M0, designate or qualify the replacement measurement host, close the benchmark baseline gate, or support any performance claim.
