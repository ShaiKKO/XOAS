# AMD Target 0 Host Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provision, characterize, and qualify the designated physical AMD
Ryzen 9 7900X Linux host as XOAS's sole Target 0 measurement authority, with
versioned baseline libraries, reversible measurement controls, two
reboot-separated campaigns, and a reviewed M0 acceptance decision.

**Architecture:** Keep repository tooling, host state, and retained evidence
separate. Repository-owned capture/probe/session tools produce closed JSON;
host packages and source-built libraries live under versioned prefixes; a
temporary measurement session changes only one selected CPU policy and its SMT
sibling, then restores them with a trap. Two campaigns with distinct boot IDs
must agree before the candidate manifest can become the reference manifest.

**Tech Stack:** C++23, CMake 4.2, Ninja 1.13, Clang/LLVM 21, Python 3.14
standard library plus JSON Schema 4.19, Bash, ShellCheck, Linux `perf` 7.0,
`taskset`, `numactl`, `cpupower`, AOCL-BLAS 5.3.2 source, OpenBLAS 0.3.34
source, and LIBXSMM 2.1.0 source.

**Spec:**
[`docs/architecture/proposals/AR-0001-target-0-host-qualification.md`](../../architecture/proposals/AR-0001-target-0-host-qualification.md),
[`docs/architecture/proposals/AR-0002-amd-target-baseline-admission.md`](../../architecture/proposals/AR-0002-amd-target-baseline-admission.md),
[`docs/architecture/050-benchmark-protocol.md`](../../architecture/050-benchmark-protocol.md),
and [`docs/experiments/baseline-matrix.md`](../../experiments/baseline-matrix.md).

## Global Constraints

- Target 0 remains single-threaded `float32`, contiguous row-major
  `C = A * B` on one exact x86-64 Linux target.
- `gpu-2` remains the primary development host and cannot contribute Target 0
  performance evidence.
- Work in the primary checkout. Do not create a linked worktree.
- Host access aliases, usernames, passwords, key paths, IP addresses, and SSH
  commands remain outside repository content and retained evidence.
- No command in this plan accepts a binary-package EULA. AOCL-BLAS is built
  from its public source tag. Adding AMD's prebuilt package requires explicit
  license acceptance and a reviewed plan revision.
- Source identities are fixed: AOCL integration tag
  `AOCL-5.3.2-Submodules` at
  `2fab7ee97dfce6ebc3cb0522c254a3653429f472`, AOCL-BLAS tag `5.3.2` at
  `25cad99a6840855ade0a49871197f48ee0e1d317`, OpenBLAS tag `v0.3.34` at
  `e0166008be8e466242aa76b2ff75ce3f0fbf574a`, LIBXSMM tag `2.1.0` at
  `7944bf36cf847c846b3fa0eb194789295e00b624`, and JITSpMM inspection
  revision `85b502a4c6603ecdeabb641b3c45b24a61117a4a`.
- Install source-built baseline artifacts only below
  `/opt/xoas/target0-v1`. Stop if that path exists with unrecognized content.
- Do not change `perf_event_paranoid`, the NMI watchdog, kernel command line,
  IRQ affinity, boost state, or system-wide CPU policy persistently.
- A measurement session may temporarily set the selected CPU's governor and
  energy preference to `performance` and offline only its SMT sibling. It
  must restore exact pre-state on success, failure, signal, or timeout.
- PMU collection runs separately from primary elapsed-time sampling. Use
  privileged `perf` while executing the probe as the unprivileged target user.
- Do not remove packages during rollback. Quarantine versioned XOAS prefixes
  and retain the package pre-state for administrator review.
- Do not reboot until the user separately approves the exact reboot action.
- No smoke, qualification, or counter result is a kernel-performance claim.
- M0 remains open until independent review or explicit user acceptance of the
  recorded review model closes.

---

## Task 1: Add Closed Qualification Contracts and the Deterministic Probe

**Files:**

- Create: `schemas/target0-host-qualification-v1.schema.json`
- Create: `tools/target0/CMakeLists.txt`
- Create: `tools/target0/qualification_probe.cpp`
- Create: `tests/target0/CMakeLists.txt`
- Create: `tests/target0/qualification_probe_test.py`
- Modify: `AGENTS.md`
- Modify: `CMakeLists.txt`
- Modify: `cmake/quality/RepositoryPolicy.cmake`
- Modify: `docs/milestones/M0-acceptance.md`

**Interfaces:**

- Produces executable `xoas-target0-qualification-probe`.
- CLI:
  `xoas-target0-qualification-probe --cpu UINT --warmup-rounds 5 --rounds 30 --iterations 16777216 --seed UINT64 --output PATH`.
- Output is one schema-valid `xoas.target0-qualification-process.v1` JSON
  object containing process/round order, CPU observations, raw nanoseconds,
  checksum, thread count, context-switch deltas, timer-overhead samples, and
  failure status.
- The process record contains only facts observed or computed by the running
  probe. Task 5 binds it to the externally recomputed probe executable
  SHA-256, compiler identity, repository commit/tree state, and boot ID digest
  in the retained campaign evidence. This keeps provenance independent of the
  executable it authenticates and avoids an undeclared C++ hashing dependency.

- [x] **Step 1: Add failing CLI and schema tests**

`qualification_probe_test.py` must assert:

```python
assert record["manifest_version"] == "xoas.target0-qualification-process.v1"
assert record["performance_claim"] is False
assert record["warmup_rounds"] == 5
assert len(record["samples"]) == 30
assert all(sample["elapsed_ns"] > 0 for sample in record["samples"])
assert all(sample["observed_cpu_start"] == requested_cpu for sample in record["samples"])
assert all(sample["observed_cpu_end"] == requested_cpu for sample in record["samples"])
assert record["max_observed_threads"] == 1
assert len(record["timer_overhead_ns"]) == 10000
```

Also require failures for an unknown option, a CPU outside the online set,
zero rounds, an existing output path, and an unwritable output directory.

Run:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target xoas-target0-qualification-probe
ctest --preset dev-debug -R target0-qualification-probe --output-on-failure
```

Expected before implementation: the target or test is absent and the command
fails.

- [x] **Step 2: Define the closed process-result schema**

Use draft 2020-12 and `additionalProperties: false` for every closed object.
Require exact manifest version, non-claiming boolean, CPU request, affinity
mask, warm-up and retained counts, fixed iteration count, seed, timer clock,
timer-overhead vector, process context-switch deltas, maximum thread count,
ordered raw samples, checksum, status, and failure reasons.

Each raw sample requires `round`, `elapsed_ns`, start/end CPU, checksum, and
voluntary/involuntary context-switch deltas. Reject nonpositive durations,
duplicate rounds, missing samples, and a claiming record.

Classify this schema as runtime-validated in repository policy. Its real
10,000-timer-sample instance remains a build-tree test artifact and is
validated by `target0-qualification-probe`; do not commit a synthetic timing
record merely to satisfy the repository schema inventory.

- [x] **Step 3: Implement the deterministic CPU probe**

Use `clock_gettime(CLOCK_MONOTONIC_RAW)` and validate that
`std::chrono::steady_clock::is_steady` is true. Pin with
`sched_setaffinity`, validate with `sched_getcpu` before and after every
sample, and read thread/context-switch state from `/proc/self/status`.

Every sample initializes `state` from `seed ^ round` and performs exactly
`16,777,216` iterations of:

```cpp
state ^= state >> 12U;
state ^= state << 25U;
state ^= state >> 27U;
checksum += state * UINT64_C(2685821657736338717);
```

Consume and serialize the checksum after timing. Measure 10,000 back-to-back
`CLOCK_MONOTONIC_RAW` deltas before warm-up. Use professional `///` Doxygen
blocks and rationale-only implementation comments.

- [x] **Step 4: Prove deterministic and negative behavior**

Run twice with the same seed and compare every field except timestamps,
elapsed samples, process ID, and context-switch counts. Require equal checksums
and sample order. Run the invalid-input cases and require nonzero exit with no
partial output file.

```bash
cmake --build --preset dev-debug --target xoas-target0-qualification-probe
ctest --preset dev-debug -R target0-qualification-probe --output-on-failure
python3 -m jsonschema \
  -i build/dev-debug/target0-probe-test.json \
  schemas/target0-host-qualification-v1.schema.json
```

- [x] **Step 5: Commit the probe contract**

```bash
git add AGENTS.md CMakeLists.txt cmake/quality/RepositoryPolicy.cmake docs/milestones/M0-acceptance.md tests/target0/CMakeLists.txt schemas/target0-host-qualification-v1.schema.json tools/target0/CMakeLists.txt tools/target0/qualification_probe.cpp tests/target0/qualification_probe_test.py docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md
git diff --cached --check
git commit -m "test: add Target 0 qualification probe"
```

---

## Task 2: Add Non-Secret Host Capture and Session Restoration Tools

**Files:**

- Create: `tools/target0/capture_host.py`
- Create: `tools/target0/measurement_session.sh`
- Create: `tests/target0/capture_host_test.py`
- Create: `tests/target0/measurement_session_test.py`
- Modify: `AGENTS.md`
- Modify: `docs/milestones/M0-acceptance.md`
- Modify: `docs/milestones/status.md`
- Modify: `tools/target0/CMakeLists.txt`
- Modify: `tests/target0/CMakeLists.txt`

**Interfaces:**

- `capture_host.py capture --phase prestate|campaign --output PATH` emits a
  closed non-secret host record.
- `capture_host.py select-core --capture PATH --interrupt-window-seconds 60`
  emits the selected physical CPU and SMT sibling.
- `measurement_session.sh --cpu UINT --sibling UINT --target-user NAME
  --restoration-record PATH -- COMMAND...` applies reversible controls,
  executes one unprivileged command, restores pre-state, and emits a closed
  restoration record at the explicit non-replacing evidence path. Keeping the
  path explicit prevents command output from mixing with restoration evidence.

- [x] **Step 1: Write fixture-driven capture tests**

Build a fake sysfs/proc fixture with two physical cores and siblings. Assert
that capture rejects missing CPU topology, mismatched siblings, virtualization,
non-TSC clocksource, unavailable `cycles`/`instructions`, and credential-like
fields. Assert that the core selector sorts by:

1. highest `amd_pstate_prefcore_ranking`;
2. lowest interrupt-count delta during the exact 60-second window;
3. lowest physical CPU number.

- [x] **Step 2: Implement closed non-secret capture**

Capture CPU vendor/family/model/stepping/model name/microcode/ISA; CPU, socket,
NUMA, SMT, L1/L2/L3, and sibling topology; memory/page state; OS/kernel/libc;
virtualization; clocksource; boot ID digest; cpufreq driver/governor/EPP/range;
boost; `k10temp`; powercap events; perf policy/events; NMI watchdog; IRQ
distribution; load; tool versions; package identities; and XOAS commit/tree
state.

Never serialize hostname, network devices/addresses, login identity, home
directory, access command, environment, or full kernel command line. Preserve
only the approved non-secret kernel-control flags as named booleans.

- [x] **Step 3: Write session-controller negative tests**

Use a temporary fake sysfs tree and assert exact restoration after success,
command failure, `TERM`, and an injected write failure. Require a hard failure
when CPU/sibling are not a pair, the sibling is already unexpectedly offline,
the governor lacks `performance`, EPP lacks `performance`, the target user is
root, or the command is empty.

- [x] **Step 4: Implement the reversible session controller**

The root portion must:

1. validate physical CPU/sibling pairing;
2. snapshot sibling-online, governor, EPP, boost, and selected-core IRQ counts;
3. leave boost unchanged;
4. set the selected CPU governor and EPP to `performance`;
5. offline only the sibling;
6. execute the command as the named non-root user with a minimal environment;
7. restore sibling, governor, and EPP in a trap;
8. verify exact restored values before returning;
9. return the command status unless restoration fails, in which case return a
   distinct restoration error.

Do not modify persistent files or global IRQ affinity.

- [x] **Step 5: Run script, Python, and policy checks**

```bash
python3 tests/target0/capture_host_test.py
python3 tests/target0/measurement_session_test.py
shellcheck tools/target0/measurement_session.sh
cmake --build --preset dev-debug --target repository-policy
ctest --preset dev-debug -R target0-host-tools --output-on-failure
git diff --check
```

- [x] **Step 6: Commit the host tools**

```bash
git add AGENTS.md docs/milestones/M0-acceptance.md docs/milestones/status.md docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md tools/target0/capture_host.py tools/target0/measurement_session.sh tests/target0/capture_host_test.py tests/target0/measurement_session_test.py tools/target0/CMakeLists.txt tests/target0/CMakeLists.txt
git diff --cached --check
git commit -m "tool: add reversible Target 0 host controls"
```

Implemented at `864f7fa17aa576831aaa2e54fa16cfe34817baa2`.

---

## Task 3: Capture Pre-State and Freeze the Exact Provisioning Lock

**Files:**

- Create: `schemas/target0-toolchain-lock-v1.schema.json`
- Create: `toolchains/target0-amd-ryzen9-7900x-v1.lock.json`
- Create: `docs/targets/target0-amd-ryzen9-7900x-v1.md`
- Create: `benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json`
- Modify: `AGENTS.md`
- Modify: `cmake/quality/RepositoryPolicy.cmake`
- Modify: `docs/architecture/README.md`
- Modify: `docs/milestones/M0-acceptance.md`
- Modify: `docs/milestones/status.md`
- Modify: `docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md`

**Interfaces:**

- The lock is the only provisioning input for Task 4.
- The target manifest remains `candidate_unqualified` until Task 7.

- [x] **Step 1: Verify the exact repository and host boundary**

Locally require a clean reviewed commit. On the authenticated physical host,
require bare metal, Ubuntu 26.04 `resolute`, x86-64, Ryzen 9 7900X family
25/model 97/stepping 2, 24 logical CPUs/12 cores, one NUMA node, TSC,
passwordless non-interactive sudo, and working privileged cycles/instructions.
Stop on any mismatch.

- [x] **Step 2: Capture collision-free pre-state**

Require `/opt/xoas/target0-v1` to be absent. Record package holds and the exact
`dpkg-query -W` pre-state in the target record. Require the host checkout to be
clean at the approved planning commit; create a normal `$HOME/XOAS` clone only
if no checkout exists, after proving `$HOME` is a non-root directory below
`/home`.

- [x] **Step 3: Define the closed toolchain lock schema**

Require OS/architecture, repository commit, APT package name/candidate/origin,
existing executable hashes, fixed source repository/tag/commit/license,
configure/build/install commands, install prefix, installed file hashes,
validation probes, rollback/quarantine path, and qualification booleans.
Forbid access and credential fields. Use `additionalProperties: false` at every
closed object.

- [x] **Step 4: Refresh APT metadata and resolve support packages**

Resolve exact candidates after `sudo apt-get update` for:

```text
build-essential
gfortran
doxygen
graphviz
shellcheck
hwloc
lm-sensors
libnuma-dev
pkg-config
```

Record candidates before installation and prove one simulated install using
`apt-get --simulate install name=version...`. Do not install baseline library
packages; their source builds are isolated in Task 4.

- [x] **Step 5: Freeze source and license identities**

Use `git ls-remote` to require every global-constraint commit. Clone into a
temporary root, checkout detached at the exact commit, verify the tag resolves
to it, record the source-tree Git archive SHA-256, and record each repository's
license-file SHA-256. Stop on any mismatch.

Record oneMKL as `not_installed_pending_M2_applicability_review`; record
JITSpMM as `source_identity_pinned_adapter_deferred_M2`. Neither status removes
an admitted baseline or asserts performance inapplicability.

The pinned JITSpMM revision contains no license or copyright statement. The
lock records the missing identity explicitly, forbids source use, and defers
the license/adapter boundary to M2 without removing the comparator from
admission.

- [x] **Step 6: Write candidate manifest and review record**

Set `target0_measurement_qualified=false`, `performance_claim=false`, and name
every remaining campaign, baseline, restoration, review, and reboot gate. Do
not compute the final compatibility digest; M1 owns canonical binary identity.

- [x] **Step 7: Validate and commit the lock**

```bash
python3 -m jsonschema -i toolchains/target0-amd-ryzen9-7900x-v1.lock.json schemas/target0-toolchain-lock-v1.schema.json
python3 -m json.tool benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json >/dev/null
cmake --build --preset dev-debug --target repository-policy docs-check
git diff --check
git add AGENTS.md cmake/quality/RepositoryPolicy.cmake docs/architecture/README.md docs/milestones/M0-acceptance.md docs/milestones/status.md docs/superpowers/plans/2026-08-29-amd-target0-host-qualification.md schemas/target0-toolchain-lock-v1.schema.json toolchains/target0-amd-ryzen9-7900x-v1.lock.json docs/targets/target0-amd-ryzen9-7900x-v1.md benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json
git commit -m "ops: lock Target 0 provisioning intent"
```

Implemented at `ee57ff5e4af01fecb11fffd985e376d636560434`.

---

## Task 4: Provision and Verify the Versioned Baseline Stack

**Files:**

- Modify: `toolchains/target0-amd-ryzen9-7900x-v1.lock.json`
- Modify: `docs/targets/target0-amd-ryzen9-7900x-v1.md`
- Modify: `benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json`

- [x] **Step 1: Reconfirm lock and collision preconditions**

Require the host checkout at the exact Task 3 commit, a clean tree, unchanged
APT candidates, unchanged host CPU/OS identity, and absent
`/opt/xoas/target0-v1`. Create `/opt/xoas/target0-v1` root-owned and mode 0755
only after every check passes.

- [x] **Step 2: Install exact support-package versions**

Install only the name/version pairs recorded in the lock. Re-query the full
installed dependency closure and record version, architecture, origin, and
package-file status. Do not change compiler alternatives or hold the kernel.

- [x] **Step 3: Build single-thread AOCL-BLAS 5.3.2**

Clone `amd/blis`, detach at
`25cad99a6840855ade0a49871197f48ee0e1d317`, and configure the public source
for LP64, CBLAS, shared/static libraries, the `amdzen` dynamic family, and its
default single-thread implementation. Use GCC 15.2.0 and install to:

```text
/opt/xoas/target0-v1/aocl-blas-5.3.2
```

Use the recorded source directory and run:

```bash
./configure \
  --prefix=/opt/xoas/target0-v1/aocl-blas-5.3.2 \
  --enable-cblas \
  amdzen
make -j12
make check
sudo make install
```

Run the upstream test suite. Compile and execute a CBLAS row-major SGEMM smoke
with `alpha=1`, `beta=0`, `BLIS_ARCH_DEBUG=1`, and thread-count observation.
Require Zen-family dispatch and one effective thread. Record source/configure
logs, compiler hashes, library hashes, `ldd`, exported CBLAS symbols, and test
results.

The installed build passed the upstream suite. The standalone smoke compile
used GNU C17 and a narrow `-Wno-unused-function` exception for an upstream
public-header static-inline warning. This exception applies only to the probe,
not XOAS source or repository quality policy.

- [x] **Step 4: Build single-thread OpenBLAS 0.3.34**

Detach at `e0166008be8e466242aa76b2ff75ce3f0fbf574a` and configure an LP64,
shared/static, `DYNAMIC_ARCH=ON`, `USE_THREAD=OFF`, `NUM_THREADS=1` build with
GCC 15.2.0. Install to:

```text
/opt/xoas/target0-v1/openblas-0.3.34
```

Use:

```bash
cmake -S . -B build-xoas -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=/usr/bin/gcc \
  -DCMAKE_Fortran_COMPILER=/usr/bin/gfortran \
  -DCMAKE_INSTALL_PREFIX=/opt/xoas/target0-v1/openblas-0.3.34 \
  -DBUILD_SHARED_LIBS=ON \
  -DDYNAMIC_ARCH=ON \
  -DUSE_THREAD=OFF \
  -DNUM_THREADS=1 \
  -DBUILD_TESTING=ON
cmake --build build-xoas --parallel 12
ctest --test-dir build-xoas --output-on-failure
sudo cmake --install build-xoas
```

Run upstream tests and the same row-major SGEMM smoke. Require
`OPENBLAS_NUM_THREADS=1`, one effective thread, recorded runtime core name,
library hashes, `ldd`, and exported symbols.

- [x] **Step 5: Build LIBXSMM 2.1.0**

Detach at `7944bf36cf847c846b3fa0eb194789295e00b624` and use the upstream
reference GNU Make build with Release optimization, shared libraries, GCC
15.2.0, and no Fortran interface. Install to:

```text
/opt/xoas/target0-v1/libxsmm-2.1.0
```

Use the same build variables for test and installation:

```bash
make -j12 \
  CC=/usr/bin/gcc \
  CXX=/usr/bin/g++ \
  FC= \
  FORTRAN=0 \
  STATIC=0 \
  PREFIX=/opt/xoas/target0-v1/libxsmm-2.1.0 \
  tests
sudo make \
  CC=/usr/bin/gcc \
  CXX=/usr/bin/g++ \
  FC= \
  FORTRAN=0 \
  STATIC=0 \
  PREFIX=/opt/xoas/target0-v1/libxsmm-2.1.0 \
  install
```

Run upstream tests and a fixed FP32 GEMM dispatch smoke with
`LIBXSMM_VERBOSE=2`. Record detected/JIT target, initialization state, one
effective thread, generated-code availability, library hashes, and `ldd`.

The initial invocation exposed that LIBXSMM generates pkg-config metadata
during the test build. Without `PREFIX`, the installed metadata retained the
temporary source path. The user approved adding the installation prefix to the
build/test command. A clean corrected build and full test run passed, and the
rejected logs remain retained as failed evidence.

- [x] **Step 6: Validate coexistence and record installed closure**

Compile one loader probe per library with explicit include/library/RPATH so no
ambient BLAS can be selected. Use `LD_DEBUG=libs` once per probe and record the
loaded absolute file. Require no cross-loading between AOCL-BLAS and OpenBLAS.

Update the lock to `installed_verified`, list every installed file hash, and
record a configuration digest computed over the lock with its digest field
omitted.

- [x] **Step 7: Record reversible rollback without executing it**

Rollback quarantines the complete prefix using:

```bash
xoasRollbackTimestamp=$(date -u +%Y%m%dT%H%M%SZ)
sudo mv /opt/xoas/target0-v1 \
  "/opt/xoas/target0-v1.quarantine-$xoasRollbackTimestamp"
```

If rollback is executed later, record the actual quarantine path. Because this
step records the rollback without executing it, Task 4 records the template and
the fact that no actual quarantine path exists. Package removal is outside this
plan and requires a separate administrator review.

- [x] **Step 8: Validate and commit provisioning evidence**

```bash
python3 -m jsonschema -i toolchains/target0-amd-ryzen9-7900x-v1.lock.json schemas/target0-toolchain-lock-v1.schema.json
git diff --check
git add toolchains/target0-amd-ryzen9-7900x-v1.lock.json docs/targets/target0-amd-ryzen9-7900x-v1.md benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json
git commit -m "ops: verify Target 0 baseline stack"
```

Implemented at `9d44f6431ebdaea60c796292e9da071f0f49522b`. The physical-host
installed-lock and live 288-file digest check passed. The repository-policy
diagnostic passed with only the documented temporary SC2329 exclusion required
by the host's newer ShellCheck; no exclusion was committed.
Evidence was bound to the repository at `9b28162152bfd4c0329a2d5de59f23c65f832a85`,
which passed the pinned `gpu-2` Debug and Release quality aggregates.

---

## Task 5: Run Qualification Campaign One

**Files:**

- Create: `benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-01.json`
- Create: `benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-01.sha256`
- Modify: `benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json`
- Modify: `docs/targets/target0-amd-ryzen9-7900x-v1.md`

Task 5 attempt 1 is retained as a terminal restoration rejection. Before core
selection, its accepted qualification-tool bundle was built natively from the
clean physical checkout at exact source
`1141713c3448eaaa392e09ace8924ebcaf0e38bd`, copied byte-for-byte to `gpu-2`,
and independently verified with matching inventory and normalized
executable-identity digests.

The repository-owned execution mechanism is controlled by the accepted
[`IDR-0003`](../../adr/IDR-0003-target0-qualification-campaign-runner.md) and
its [active implementation plan](2026-08-29-target0-qualification-campaign-runner.md).
Implementation Tasks 1–7 passed complete exact-commit quality at `7b486e1`;
replacement native bundle deployment and read-only physical preflight passed.
The live attempt stopped during primary process 1 before PMU because EPP did
not restore after the governor transition. Closed rejection SHA-256 is
`e6458e2dac1097fa5649371c0815403708c7985da0b80d2ebf5c8b049efc5868`.
Bounded recovery restored exact host pre-state. The rejected root is retained
and cannot be retried or rewritten.

The source defect was repaired test-first. Red subjects `485eb6b` and
`c68474c` captured the ordering, canonical-byte, and non-finite classification
failures. Exact repair through `c9af373` restores the sibling, governor, then
EPP and enforces canonical process/restoration JSON at production and ingestion
boundaries with closed rejection classes. Complete Debug and Release 50/50
suites, isolated sanitizer 3/3, and repository policy passed on
`wineth-ubuntu`; follow-up independent review reported no remaining finding.
This was source/fixture evidence only: at that checkpoint, physical restoration
verification, a new native bundle and replica, a new preflight, and separate
authority remained prerequisites for another Task 5 attempt.

One bounded restoration-only session subsequently passed on the physical host
at clean merged source `a396f642d5c2ec6ed670cc2341170ec7d9f1a886`.
The controller returned 0 around `/usr/bin/true`; an independent live audit
matched sibling, governor, EPP, and boost to the canonical restored record.
Its SHA-256 is
`5b6e2cefbac4c8c96f5228139978f776d55aff0dcffb9dc9fb19812cb50236e7`.
A fresh physical-native bundle at the same source was accepted by preparation
and fresh physical verification. Bundle-manifest, inventory, executable, and
normalized executable-identity SHA-256 values are
`15d58e20bbab593bd902782b917b79ba98a03cf1e79c784fbff2c450d23a99a0`,
`44d6ee1eec9791974098ce74c81647d1690bd0aef2bd54822e47635ebad1bbaf`,
`db82cd647e880b1780c2a5fb9d10f87398b184f35d4e84de9b6855db07fec015`,
and `753890dc53185727326bc5dba2585a59ed60bdf0465623dec3fb58bf63b388b3`.
The complete bundle was copied byte-for-byte to `gpu-2`, where a fresh verifier
at the same exact source accepted matching manifest, inventory, executable,
and normalized executable-identity digests. Fresh cross-host deployment is
therefore closed. No new preflight, Task 5 process, PMU phase, qualification,
or performance claim occurred. This proof neither authorized nor performed a
controlled campaign reboot; the incidental administrator reboot remains
non-campaign evidence.

Before each qualification process, independently recompute and retain the
accepted executable, compiler, linker, fixed source set, provisioning lock,
checkout commit/tree/clean state, and boot identities. Reject the complete
campaign if any identity differs from the accepted bundle or changes between
processes. Compatibility-test durations retained by the deployment bundle are
not warmup, retained, PMU, noise, campaign, or benchmark samples.

- [x] **Step 1: Select the measurement core deterministically**

Capture all physical cores, preferred-core ranks, sibling pairs, L3 groups,
and a 60-second interrupt delta. Apply the locked selector. Record the chosen
CPU and sibling; do not hard-code a result before capture.

- [x] **Step 2: Verify exact pre-session state**

Require exclusive-use confirmation, load below `0.5` at one-minute average,
no unexpected user sessions, no thermal alarm, TSC clocksource, unchanged boot
identity within the campaign, unchanged target/toolchain identity, and a clean
XOAS checkout at the exact campaign commit.

Before any process runs, enforce the accepted-bundle prerequisite above. Bind
every process record to the independently recomputed identities in the
campaign evidence; reject the campaign if any value changes.

- [ ] **Step 3: Execute five fresh qualification processes**

For each process, enter a fresh reversible measurement session, warm for five
rounds, retain 30 rounds, exit and verify restoration. Use deterministic seeds
derived from campaign ID and process index. Require each retained sample to be
20–200 ms, one thread, no migration, valid checksum, and no restoration error.

Retain process order, raw timer samples, temperatures, governor/EPP/boost,
interrupt/context-switch deltas, and before/after host capture.

- [ ] **Step 4: Collect separate PMU evidence**

Run privileged `perf stat` for the unprivileged pinned probe with:

```text
cycles
instructions
branches
branch-misses
cache-references
cache-misses
msr/aperf/
msr/mperf/
msr/tsc/
power/energy-pkg/
```

Record unsupported events rather than substituting estimates. Reject cycles
or instructions if multiplex scaling is non-unit; move optional events to
separate runs when necessary.

- [ ] **Step 5: Apply qualification acceptance rules**

Campaign one passes only when all five processes are valid, every process has
30 retained rounds, median absolute deviation divided by median is at most
`0.005` for at least four processes and at most `0.010` for every process,
the ratio of the 99th percentile to median is at most `1.02`, the selected CPU
has no migration, restoration is exact, and no thermal/throttling objective
failure occurs.

- [ ] **Step 6: Validate and commit campaign one**

Hash every retained evidence file, validate JSON, and set the target manifest
to `campaign_01_passed_campaign_02_required`. Do not set qualification true.

```bash
git add benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-01.json benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-01.sha256 benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json docs/targets/target0-amd-ryzen9-7900x-v1.md
git commit -m "bench: record Target 0 qualification campaign one"
```

---

## Task 6: Perform the Approved Reboot and Campaign Two

**Files:**

- Create: `benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-02.json`
- Create: `benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-02.sha256`
- Modify: `benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json`
- Modify: `docs/targets/target0-amd-ryzen9-7900x-v1.md`

- [ ] **Step 1: Stop for explicit reboot authority**

Report campaign-one commit, checks, exact host identity, clean state, expected
disconnect, and rollback state. Obtain explicit user approval for one
`systemctl reboot`. Do not infer reboot authority from approval of this plan.

- [ ] **Step 2: Reboot once and prove a new boot**

After approval, execute one controlled reboot. Reconnect only after the host
returns, require a different boot ID, and require identical CPU family/model/
stepping, microcode, ISA, topology, cache, clocksource, OS ABI, toolchain lock,
baseline hashes, and XOAS commit.

- [ ] **Step 3: Repeat the exact campaign-one procedure**

Re-run core selection. A changed selected CPU is permitted only if the
deterministic inputs justify it; otherwise it is an invalid campaign. Execute
five fresh processes, 30 rounds each, separate PMU runs, thermal capture, and
exact session restoration under the same thresholds and seeds derived from
campaign ID 2.

- [ ] **Step 4: Compare reboot-separated evidence**

Require campaign process-median ratio between `0.99` and `1.01`, unchanged
timer-overhead median within `5 ns` or `10%` (whichever is larger), unchanged
counter availability, no identity drift, and both campaign acceptance records
valid. A failure leaves the target unqualified and requires a documented
no-go/remediation decision, not repeated rebooting until success.

- [ ] **Step 5: Validate and commit campaign two**

```bash
git add benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-02.json benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-02.sha256 benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json docs/targets/target0-amd-ryzen9-7900x-v1.md
git commit -m "bench: record Target 0 qualification campaign two"
```

---

## Task 7: Review, Qualify the Manifest, and Decide M0

**Files:**

- Modify: `benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json`
- Modify: `docs/targets/target0-amd-ryzen9-7900x-v1.md`
- Modify: `docs/architecture/README.md`
- Modify: `docs/milestones/M0-acceptance.md`
- Modify: `docs/milestones/status.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Perform full evidence-integrity verification**

Validate both schemas and every JSON instance; recompute source, executable,
library, campaign, and manifest hashes; prove raw sample counts/order; prove
different boot IDs; prove exact identity equality; prove no credential/access
fields; and run the full debug, release, static-quality, sanitizer,
repository-policy, and target0 qualification test suites on `gpu-2` and the
physical host where applicable.

- [ ] **Step 2: Obtain independent review or explicit review-model acceptance**

Review host controls, restoration evidence, source/library provenance,
counter trust, statistics, and schema closure against AR-0001, AR-0002, and
the benchmark protocol. Self-review remains labeled self-review.

- [ ] **Step 3: Make the qualification decision**

Set `target0_measurement_qualified=true` only if every requirement and review
gate passes. Name the exact sole Target 0 compatibility authority, accepted
limitations, invalidation triggers, selected core/sibling policy, compiler and
baseline identities, and evidence digests. Otherwise retain candidate status
and record a no-go or bounded remediation decision.

- [ ] **Step 4: Decide M0 without starting M1 early**

Close M0 only if the target manifest, admitted baseline identities, charter,
prior-art, corpus, benchmark contract, schema, and review evidence all pass.
Record the exact tested commit and clean state. If any item remains open, keep
M0 `In progress` and name the earliest unresolved prerequisite.

- [ ] **Step 5: Run final verification and commit**

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target quality
ctest --preset dev-debug --output-on-failure
cmake --preset dev-release
cmake --build --preset dev-release --target quality
ctest --preset dev-release --output-on-failure
git diff --check
git status --short --branch
```

Stage only the reviewed target manifest, evidence records, target document,
architecture index, acceptance record, ledger, and operating-manual changes.
Commit with `docs: decide Target 0 host qualification` and publish through the
protected-main pull-request workflow.

---

## Completion Evidence

This plan is complete only when:

- the physical AMD host is bound to a qualified or explicit no-go manifest;
- two reboot-separated campaigns and every raw sample are retained;
- temporary measurement controls restored exact pre-state every time;
- cycles and instructions are trustworthy and versioned;
- AOCL-BLAS, OpenBLAS, and LIBXSMM source/artifact identities and one-thread
  behavior are locked;
- oneMKL and JITSpMM availability/applicability states are explicit rather than
  silently omitted;
- all repository, schema, probe, host-tool, and quality tests pass;
- review and M0 gate decisions name the exact commit and evidence;
- no performance, product-readiness, or M1 claim exceeds the evidence.
