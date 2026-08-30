# IDR-0002: Target 0 Qualification-Tool Deployment

**Status:** Accepted; native deployment and cross-host verification passed

**Written-spec approval:** Approved by the user on 2026-08-29.

**Decision date:** 2026-08-29

**Decision owner:** User / architecture authority

**Normative design:**
[`../superpowers/specs/2026-08-29-target0-qualification-tool-deployment-design.md`](../superpowers/specs/2026-08-29-target0-qualification-tool-deployment-design.md)

**Implementation plan:**
[`../superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md`](../superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md)

## Context

The pinned repository quality system is authoritative on `gpu-2`, while the
physical AMD Ryzen 9 7900X candidate must supply the native executable used by
its qualification campaigns. The physical host intentionally has a different
Python and ShellCheck environment and must not become a second development
lane merely to build one already-approved M0 probe.

A copied development-host executable would not authenticate the measurement
target's compiler, linker, runtime closure, or emitted bytes. A narrative
compile command would not fail closed on checkout, lock, or dependency drift.
XOAS therefore needs a narrow native preparation path whose output can be
recomputed on both hosts before campaign work begins.

## Decision

XOAS uses
[`../../tools/target0/prepare_qualification_bundle.py`](../../tools/target0/prepare_qualification_bundle.py)
to build and authenticate the existing qualification probe natively on the
physical target. The tool validates a clean public checkout at one explicit
full commit before creating output, validates the installed target lock and
host identity, constructs one fixed compiler invocation, builds twice, and
accepts only byte-identical executable output.

The physical native build is authoritative for the qualification executable.
The complete Debug, Release, sanitizer, formatting, documentation,
static-analysis, repository-policy, and test aggregates on `gpu-2` remain
authoritative for source and engineering quality. Neither lane substitutes for
the other.

### Operator interface

The preparation interface is exactly:

```text
python3 tools/target0/prepare_qualification_bundle.py
  --repository-root PATH
  --expected-commit FULL_SHA
  --toolchain-lock PATH
  --output-directory /var/tmp/xoas-target0-qualification-tools.ATTEMPT
```

Every option is mandatory. The commit is 40 lowercase hexadecimal digits. The
output must be a canonical, previously nonexistent immediate child of
`/var/tmp` with the required basename prefix. It cannot overlap the checkout,
home directory, `/opt/xoas/target0-v1`, or another protected path. The command
does not fetch, modify the checkout, install files, use privilege, access the
network, or change measurement controls.

An accepted replica is independently checked in a fresh process with:

```text
python3 tools/target0/verify_qualification_bundle.py
  --bundle-directory PATH
  --schema schemas/target0-qualification-tool-bundle-v1.schema.json
```

The verifier trusts no retained digest. It revalidates the closed schema and
semantic relationships, rehashes every inventoried file, rejects missing,
changed, added, symlinked, or non-regular entries, and emits the accepted
digest record only on success.

### Compiler, linker, and runtime authority

The compiler driver is `/usr/bin/clang++-21`. Its direct path, resolved path,
version, target triple, and live SHA-256 must match the installed target lock.
The linker is `/usr/bin/ld.lld-21`; its package owner and exact locked package
version must match, `dpkg -V` must pass, and its live direct path, resolved
path, version, and SHA-256 are retained.

The compiler argument array fixes C++23 without GNU extensions, release
optimization, `NDEBUG`, the repository warning-as-error set, the absolute LLD
linker, one source, one output, and an allowlisted six-variable environment.
Fast-math, native-architecture, profile, ambient, and operator-supplied flags
are outside the interface.

Two isolated builds must produce regular executable files with identical
SHA-256 values. Only then is one copy admitted as
`bin/xoas-target0-qualification-probe`. ELF inspection retains `file`,
`readelf`, and `ldd` results; validates ELF64 little-endian x86-64 identity,
loader, and direct dependencies; and binds every runtime file to a system
path, real path, size, SHA-256, package owner, and exact locked version.

Compatibility verification covers Python byte-compilation and focused capture
fixtures, Bash syntax and focused reversible-session fixtures, the real probe
CLI and deterministic process contract, and both process and bundle schema
validation. Each status and stdout/stderr digest is retained. These runs prove
deployment compatibility only; their durations are not campaign or benchmark
samples.

### Finalization and retention

Successful finalization writes canonical `bundle.json`, a bytewise-sorted
inventory, and `acceptance.json` last using write-once files and flushed
directories. The acceptance record binds manifest, inventory, executable, and
normalized executable-identity digests. The normalized identity excludes
attempt timestamps, bundle IDs, and staging/replica paths.

Once a safe staging root exists, a failed attempt writes one closed,
non-accepting `rejection.json` where possible and returns nonzero. A failure
before safe root creation writes no acceptance marker. An accepted or rejected
root is never converted in place into a later attempt.

The complete accepted bundle is retained on the physical host and copied
byte-for-byte to `gpu-2`; the fresh verifier must produce matching inventory
and executable identities on both hosts. Git retains only compact non-secret
manifest/digest evidence and external retention references. It does not retain
the executable binary, credentials, network coordinates, or private paths.

## Authority boundary

This decision authorizes only repository implementation and, after the exact
development subject passes review, native preparation and replica validation.
It grants no authority to:

- start a measurement session or qualification campaign;
- treat compatibility timings as performance evidence;
- invoke `perf`, change CPU/power/sibling/service state, or use privilege;
- qualify the physical host or close M0;
- reboot either host;
- install or replace source, toolchains, baselines, or runtime files;
- implement product compiler, IR, code generation, benchmarks, or M1 work.

Campaign one remains gated on an accepted bundle at the exact pushed campaign
commit, matching physical/`gpu-2` inventory digests, and fresh identity checks
defined by the controlling qualification plan.

## Alternatives considered

### Narrow repository-owned native preparation tool

Selected. It authenticates a target-native executable while preserving the
separate development-quality authority.

### Install the complete development environment on the physical host

Rejected. It adds measurement-host state and duplicates `gpu-2` without
strengthening native artifact provenance.

### Compile manually

Rejected. A narrative command does not close checkout, compiler, linker,
runtime, reproducibility, or retained-evidence boundaries.

### Copy the `gpu-2` executable

Rejected as target authority. It may aid non-authoritative diagnostics but
cannot authenticate physical-host-native emitted bytes.

## Consequences

The target-native artifact has replayable source, checkout, toolchain, ELF,
runtime, compatibility, and inventory evidence. The fixed compile contract is
intentionally duplicated outside CMake, so repository tests must continue to
reject drift. The required full-bundle replication completed for implementation
subject `a312aa2`; any later campaign commit must independently satisfy the same
fresh-verification prerequisite before campaign one.

This decision does not change Target 0, numerical semantics, benchmark gates,
public ABI, canonical plan identity, cache invalidation, IR ownership, or
qualification authority.

## Verification

The repository implementation is accepted only after the exact subject passes:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug \
  --target xoas-target0-qualification-probe target0-host-tools
ctest --preset dev-debug \
  -R '^target0-(qualification-bundle|qualification-probe|host-tools-)' \
  --output-on-failure
```

Implementation subject `a312aa2bbbb403b31ffb67cf40200da063527a4f`
passed the complete Debug and Release CTest surfaces plus the isolated
ASan/UBSan gates on `gpu-2`. A clean physical checkout at that subject produced
an accepted native bundle after two byte-identical builds and five passing
compatibility checks. Fresh physical and `gpu-2` verifiers returned matching
manifest, inventory, executable, and normalized executable-identity digests.
The compact non-secret receipt is retained in
[`../../benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json`](../../benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json).

This closes deployment compatibility only. It is not campaign, benchmark,
qualification, reboot, or performance evidence.

## Reversal and invalidation

The preparation command changes no checkout, installation, package, service,
or measurement state, so reversal requires no source or host rollback. It does
not delete accepted or failed evidence roots automatically. Cleanup, if later
authorized, must name exact retained roots and follow the evidence-retention
policy.

Any checkout, source, lock, target, compiler, linker, runtime, compatibility,
inventory, or executable drift invalidates the bundle for campaign use. A new
attempt must use a new `/var/tmp` root and produce a new acceptance record.
Any material expansion of authority requires the appropriate architecture
proposal; semantics-neutral changes to this mechanism require a superseding or
amended IDR with migration and revalidation evidence.
