# Target 0 Qualification-Tool Deployment Design

**Status:** Approved

**Written-spec approval:** Approved by the user on 2026-08-29.

**Decision owner:** User / architecture authority

**Implementation owner:** Head engineering and integration agent

**Controlling plan:**
[`../plans/2026-08-29-amd-target0-host-qualification.md`](../plans/2026-08-29-amd-target0-host-qualification.md)

## Purpose

Define the exact, reviewable path that builds and deploys XOAS's existing
Target 0 qualification tools on the physical AMD measurement candidate without
weakening the pinned development quality system or treating a development-host
binary as target-authoritative.

This design closes only the deployment prerequisite immediately before the
first controlled qualification campaign. It does not execute a measurement
session, collect campaign evidence, qualify the host, authorize a reboot, or
start M1.

## Controlling requirements

This design preserves the following approved boundaries:

- `gpu-2` is the primary development and full quality-enforcement lane, but is
  not a Target 0 measurement host.
- The physical AMD Ryzen 9 7900X host is the sole current Target 0 measurement
  candidate and remains unqualified.
- Development-host artifacts may aid correctness work but cannot become
  target-authoritative measurement artifacts without native target rebuilding
  and verification.
- Task 5 must bind every process envelope to an independently recomputed probe
  executable digest, compiler identity, repository state, and boot identity.
- No benchmark or qualification candidate may run before correctness,
  compatibility, provenance, and reversible-control prerequisites close.
- The full pinned quality aggregate remains authoritative even where the
  measurement host intentionally carries a different Python or ShellCheck
  version.

The physical host currently exposes the locked Clang 21.1.8 compiler but Python
3.14.4 and ShellCheck 0.11.0. The top-level development configuration requires
Python 3.12.3 exactly and the pinned development ShellCheck behavior. Installing
a second development environment on the measurement host would add state and
duplicate `gpu-2`'s role without strengthening the native executable identity.

## Decision

XOAS will add a narrow repository-owned preparation tool that builds the
qualification probe natively on the physical host from one clean, exact
campaign commit. The tool will validate the installed Target 0 lock, construct
one fixed compilation contract, build the probe twice, prove identical output,
inspect the resulting ELF artifact and dependencies, run target-compatibility
tests, and emit a closed evidence bundle.

The preparation tool is not a second product build system. It owns only the
already-approved M0 qualification executable and its interpreted companion
tools. Full configure, formatting, linting, documentation, static analysis,
sanitizer, repository-policy, and test authority remains on `gpu-2` and hosted
CI at the same exact commit.

## Scope

### In scope

- Native release build of `xoas-target0-qualification-probe` on the physical
  host.
- Exact source, repository, compiler, linker, runtime, and artifact provenance.
- Target-runtime verification of the probe, capture tool, and session
  controller.
- Deterministic evidence serialization, file inventory, and digest replication.
- Development-lane tests and quality integration for the preparation code.
- A durable semantics-neutral IDR and milestone/frontier documentation.

### Out of scope

- Git fetching, checkout mutation, package installation, or compiler-alternative
  changes from the preparation command.
- Privilege escalation, measurement-control changes, performance timing, PMU
  collection, campaign execution, or target qualification.
- Rebooting the target.
- Product compiler, IR, code-generation, baseline adapters, or M1 work.
- Changing Target 0, numerical semantics, benchmark thresholds, cache identity,
  public ABI, or artifact compatibility rules.

## Architecture and ownership

### Development lane

`gpu-2` owns the complete repository quality contract. Before a physical bundle
is admissible, the exact implementation commit must pass the required Debug,
Release, sanitizer, formatting, documentation, static-analysis,
repository-policy, and test aggregates on that lane. Physical-host tools do not
override those results.

### Physical target lane

An operator advances the physical checkout explicitly to the reviewed full
commit, verifies that it is clean, and invokes the preparation command. The
command itself does not contact Git remotes or alter the checkout. It validates
the checkout independently before creating an output directory.

The physical host invokes `/usr/bin/clang++-21` as the C++ driver. The command
must resolve and hash the underlying executable and match the compiler identity
recorded by the installed Target 0 lock. The LLD executable is validated in the
same fail-closed spirit without rewriting the completed provisioning record:
its exact package version must match the installed lock, `dpkg -V` must pass,
and its live absolute path, resolved path, version, and SHA-256 are retained in
the deployment bundle.

### Evidence retention lane

The physical build produces a new evidence bundle below an explicitly supplied,
previously nonexistent staging directory. The executable is not installed
globally and `/opt/xoas/target0-v1` remains read-only input.

After acceptance, the complete bundle is copied byte-for-byte to `gpu-2` and
the inventory digest is recomputed there. Both hosts retain the bundle. Git
retains the compact manifest, inventory digest, executable digest, and external
storage locations, but not the executable binary.

## Operator interface

The planned command is:

```text
python3 tools/target0/prepare_qualification_bundle.py
  --repository-root PATH
  --expected-commit FULL_SHA
  --toolchain-lock PATH
  --output-directory NEW_PATH
```

All four inputs are mandatory. The command accepts no implicit `HEAD`, compiler
from `PATH`, default lock, or default output location. The expected campaign
commit is independent of the provisioning lock's historical execution subject;
both identities are retained.

The output directory must not exist. On the physical host it must be an
immediate child of `/var/tmp` whose basename starts with
`xoas-target0-qualification-tools.`. It may not be a repository root, home
directory, system root, install prefix, symlink, or ancestor of one of those
paths. Tests exercise the same policy against isolated fixture roots rather
than writing to the real physical-host location.

## Compilation contract

The preparation tool constructs the compiler invocation as a fixed argument
array. The initial contract contains:

- the absolute Clang C++ driver;
- C++23 with GNU extensions disabled;
- release optimization and `NDEBUG`;
- the complete warning-as-error set in `cmake/quality/XoasWarnings.cmake`;
- the absolute locked LLD linker;
- one explicit source file and one output file;
- no fast-math, native-architecture, profile, environment-supplied, or
  user-supplied compiler flags.

The exact realized argument array is retained in the bundle. A repository test
must prevent silent drift between the preparation contract and the existing
qualification-probe Release contract.

The tool builds twice in separate private subdirectories under the new staging
root. Both regular executable files must have the same SHA-256. A mismatch is a
hard rejection, not permission to select one output. The accepted executable is
copied from one verified build into the immutable bundle layout only after the
comparison succeeds.

## Evidence contract

Add a closed draft-2020-12 schema for
`xoas.target0-qualification-tool-bundle.v1`. The manifest includes at least:

- manifest version, bundle ID, creation time, target ID, and
  `performance_claim: false`;
- expected campaign commit, actual full commit, tree object, clean state, and
  public remote;
- provisioning-lock ID, historical execution subject, stable configuration
  digest, and lock-file digest;
- SHA-256 values for the preparation tool, probe source, capture tool, session
  controller, process schema, bundle schema, and any other retained contract
  input;
- compiler driver path, resolved path, version, target triple, and SHA-256;
- linker path, resolved path, version, and SHA-256;
- exact compile argument array, working directory classification, and
  allowlisted environment;
- both independent-build executable digests and equality decision;
- accepted executable path relative to the bundle, SHA-256, byte size, ELF
  header identity, build ID when present, and inspection-record digests;
- dynamic loader and library paths, package identities where available, and
  hashes for every resolved runtime dependency;
- every compatibility test name, command classification, exit status, and log
  digest;
- final acceptance state and an empty-or-closed rejection list.

The tool serializes JSON with sorted keys, fixed separators, UTF-8, and one
terminal newline. The finalized layout contains the accepted executable,
`bundle.json`, inspection and test logs, `inventory.json`, and an acceptance
record that names the inventory digest. The bundle inventory lists relative
paths, sizes, and SHA-256 values in bytewise path order. Its digest covers every
retained bundle file except the inventory and acceptance files; the acceptance
record authenticates that inventory digest without introducing a recursive
hash dependency.

Timestamps, physical staging paths, and replica locations are evidence metadata
and do not participate in executable identity.

## Independent authentication

The probe does not authenticate itself. The preparation tool computes source,
compiler, linker, runtime, and executable identities outside the generated
process record. Task 5 independently recomputes the bundle inventory and
executable digest before the first process and binds those values into every
campaign process envelope.

Task 5 also recomputes the compiler digest and version, full repository commit
and tree state, and boot ID digest. Any change during the campaign rejects the
entire campaign.

## Target-runtime verification

Successful preparation requires all of the following on the physical host:

1. Python byte-compilation and focused capture-tool tests.
2. Bash syntax validation and focused session-controller fixture tests.
3. Qualification-probe CLI, invalid-input, deterministic-contract, valid-record,
   and process-schema tests.
4. Two-build executable digest equality.
5. ELF, linker, loader, and dynamic-dependency inspection.
6. Draft-2020-12 meta-validation of the bundle schema and full validation of the
   bundle and probe process records.
7. A final independent inventory and digest check.

These checks establish target compatibility and deployment integrity only.
Their timings are not benchmark samples, qualification evidence, or a kernel
performance claim.

ShellCheck 0.11.0 on the physical host may be recorded as an observed tool but
is not allowed to replace or amend the pinned `gpu-2` ShellCheck gate. A
physical-only diagnostic difference cannot justify a source suppression unless
the normal change-control and quality review accept it.

## Failure and safety behavior

The preparation command:

- performs no network access;
- performs no `sudo` or other privilege escalation;
- does not write the source checkout or install prefix;
- does not change CPU affinity, governor, EPP, boost, sibling state, services,
  kernel settings, or power state;
- does not start a qualification campaign or invoke `perf`;
- uses subprocess argument arrays and never shell-evaluated command strings;
- passes only a documented environment allowlist;
- refuses output replacement, unsafe destinations, symlink traversal, and
  unexpected file types.

Every precondition and verification is fail-closed. A failed attempt returns a
nonzero status and cannot produce the acceptance marker consumed by Task 5.
When safe, the failed staging root retains diagnostics, observed identities,
and hashes with an explicit rejected state. It is never silently repurposed as
a later successful bundle.

The preparation tool does not delete a failed or successful evidence root.
Evidence cleanup requires a separate exact-target decision under repository
retention policy.

## Repository integration

The implementation is expected to create or update:

- `tools/target0/prepare_qualification_bundle.py`;
- `schemas/target0-qualification-tool-bundle-v1.schema.json`;
- `tests/target0/prepare_qualification_bundle_test.py`;
- `tools/target0/CMakeLists.txt`;
- `tests/target0/CMakeLists.txt`;
- `cmake/quality/RepositoryPolicy.cmake` only if required to register the new
  tracked tool or evidence checks;
- `docs/adr/IDR-0002-target0-qualification-tool-deployment.md`;
- `docs/milestones/M0-acceptance.md`;
- `docs/milestones/status.md`;
- `docs/targets/target0-amd-ryzen9-7900x-v1.md`;
- `AGENTS.md` after commands are implemented and verified.

The implementation plan may narrow this list when tests prove a file is not
required. It may not add product/compiler scaffolding or broaden the deployment
tool into a general remote build service.

## Verification design

Development-lane tests must cover at least:

- exact CLI requirements and rejected missing inputs;
- clean and dirty repository fixtures;
- exact and mismatched commit/tree/remote identities;
- valid and invalid locks, compiler hashes, versions, and resolved paths;
- argument-array construction and prohibited flag/environment injection;
- successful identical dual builds and deliberate digest mismatch;
- safe output-path acceptance and rejection, including symlinks and existing
  destinations;
- compiler, linker, ELF, dependency, and package-evidence parsing;
- successful and failing target-test records;
- deterministic manifest and inventory bytes;
- closed-schema positive and negative validation;
- rejected bundles lacking an acceptance marker;
- accepted-bundle revalidation and replica digest comparison.

The exact implementation commit must pass all required `gpu-2` quality
aggregates. The physical host then runs the target-runtime verification against
that same commit. Documentation records the exact commit, clean/dirty state,
commands, logs, bundle digest, executable digest, replica verification, and any
residual evidence gap.

## Task 5 handoff gate

Qualification campaign one may begin only after all of these are true:

1. The implementation and IDR have passed review.
2. The exact pushed commit passes the complete development quality contract.
3. The physical checkout is clean at that exact commit.
4. The native bundle is accepted by its closed validator.
5. The two native builds produce identical executable bytes.
6. The physical and `gpu-2` bundle inventory digests match.
7. The executable, compiler, linker, runtime, source, lock, and repository
   identities are retained.
8. The milestone acceptance record identifies the bundle and confirms that no
   campaign, performance claim, host qualification, or reboot occurred.

Task 5 remains a separate execution slice. Task 6 continues to require the
user's explicit approval of the exact reboot action.

## Alternatives considered

### Narrow repository-owned native preparation tool

Selected. It gives the target-authoritative executable a deterministic,
fail-closed provenance path while keeping the measurement host narrow.

### Complete pinned development environment on the physical host

Rejected for this slice. It duplicates `gpu-2`, mutates measurement-host state,
and does not improve the native executable's source/compiler/artifact binding.

### Manual native compilation procedure

Rejected. A narrative command cannot reliably enforce clean-checkout,
compiler, dual-build, dependency, schema, and retention obligations.

### Copy a `gpu-2` executable to the physical host

Rejected as target authority. It violates the approved target-bound rebuilding
and verification boundary. Such a binary may be a non-authoritative correctness
aid only.

## Consequences and risks

### Benefits

- Campaign evidence authenticates a physical-target-native artifact.
- Development quality and measurement-host compatibility remain distinct and
  independently reviewable.
- The physical host avoids a second Python/ShellCheck toolchain solely for
  top-level CMake configuration.
- Failed and successful deployment attempts are reproducible and auditable.

### Costs

- The fixed compile contract exists outside the top-level CMake invocation and
  therefore requires an explicit drift test.
- Bundle replication and retention remain operator steps.
- Target-runtime tests run a second time outside the normal CTest aggregate.

### Risks and mitigations

- **Compile-contract drift:** fail a development test when CMake and preparation
  contracts diverge.
- **Measurement-host contamination:** prohibit package, privilege, network, and
  control mutations in the preparation command.
- **Self-authentication:** compute all authoritative identities outside the
  probe process record and recompute them at campaign start.
- **Evidence loss:** retain byte-identical bundles on both physical and
  development hosts and commit compact digests and locations.
- **False performance interpretation:** mark every bundle and compatibility
  record `performance_claim: false` and keep campaign execution separate.

## Approval and change control

The user approved the architecture/artifact flow, provenance contract,
fail-closed behavior, and repository/Task 5 integration sections on 2026-08-29.
Implementation begins only after the user approves this written specification
and a task-level implementation plan is written under `docs/superpowers/plans/`.

Changes to Target 0, numerical semantics, benchmark gates, plan/cache identity,
public ABI, IR ownership, or qualification authority require an architecture
proposal. Semantics-neutral changes to this durable deployment decision are
recorded in IDR-0002 and reviewed against this specification.
