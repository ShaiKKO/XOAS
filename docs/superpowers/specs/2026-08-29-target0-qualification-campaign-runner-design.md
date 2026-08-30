# Target 0 Qualification Campaign Runner Design

**Status:** Approved

**Written-spec approval:** Approved by the user on 2026-08-29.

**Decision owner:** User / architecture authority

**Implementation owner:** Head engineering and integration agent

**Controlling plan:**
[`../plans/2026-08-29-amd-target0-host-qualification.md`](../plans/2026-08-29-amd-target0-host-qualification.md)

## Purpose

Define the closed, replayable mechanism that executes one Target 0 host
qualification campaign on the designated physical AMD candidate.
The mechanism binds five primary timing processes, separate privileged PMU
collection, exact reversible controls, independently recomputed identities,
raw evidence, statistics, and acceptance into one write-once campaign bundle.

This design closes the implementation prerequisite for Task 5.
It does not itself qualify the host, authorize a reboot, make a kernel
performance claim, change Target 0, or begin M1.

## Controlling requirements

The implementation preserves these approved boundaries:

- `gpu-2` remains the primary development and full quality-enforcement lane.
- The physical AMD Ryzen 9 7900X host remains the sole Target 0 measurement
  candidate and remains unqualified until both campaigns and review close.
- Campaign one uses an accepted physical-native qualification bundle produced
  from the exact pushed campaign commit.
- The complete bundle is independently verified on the physical host and
  `gpu-2`, with matching inventory and normalized executable identities.
- Every primary process independently recomputes the accepted executable,
  compiler, linker, fixed source set, provisioning lock, checkout commit,
  checkout tree, clean state, and boot identity.
- Primary timing runs in five fresh processes with five warm-up rounds and 30
  retained rounds per process.
- PMU collection is separate from the five primary elapsed-time processes.
- Every temporary governor, EPP, and SMT-sibling change restores exactly.
- Campaign evidence contains no credentials, usernames, login identifiers,
  network coordinates, private keys, or private filesystem locations.
- Campaign one stops before the separately authorized controlled reboot.

## Decision

XOAS will add a repository-owned Python campaign contract, operator runner,
fresh-process verifier, closed draft-2020-12 campaign schema, and fixture-based
tests.
The existing measurement-session controller will gain one dedicated
privileged-`perf` execution mode.

The campaign runner has two explicit phases:

1. `preflight` performs read-only qualification checks, creates one new
   external evidence root, captures the initial host state, verifies every
   identity, and selects a core using the locked 60-second selector.
2. `run` consumes exactly one accepted preflight root, applies reversible
   controls through the existing session controller, executes five primary
   processes and separate PMU processes, evaluates the locked thresholds, and
   finalizes either an accepted campaign or a retained rejection.

No successful or rejected root can be reused for another attempt.
No partial attempt can be resumed after a command has entered a measurement
session.

## Scope

### In scope

- A closed campaign manifest and independent verifier.
- Deterministic process seeds and exact statistical definitions.
- Five primary process sessions and their raw process records.
- Separate required and optional PMU sessions.
- Exact identity, environment, temperature, interrupt, context-switch, and
  restoration evidence.
- Write-once inventory, acceptance, and rejection records.
- Development-lane schema, unit, failure-injection, integration, formatting,
  static-analysis, sanitizer, and repository-policy coverage.
- A fresh exact-commit native qualification bundle after implementation.
- Campaign one execution only after all implementation gates pass.

### Out of scope

- Rebooting either host.
- Campaign two or cross-reboot acceptance.
- Setting `target0_measurement_qualified` to true.
- Kernel, BLAS, or generated-code performance comparison.
- Product benchmark, compiler, IR, code-generation, cache, or runtime work.
- General command execution as root.
- Remote orchestration, service installation, persistent daemon state, or
  scheduled execution.
- Automatic retries, evidence deletion, or outlier removal.

## Repository components

The implementation owns these focused components:

- `tools/target0/qualification_campaign.py` owns canonical serialization,
  campaign validation, seed derivation, identity comparison, statistics,
  inventory construction, finalization, and replay verification.
- `tools/target0/run_qualification_campaign.py` owns the closed operator CLI,
  process ordering, bounded subprocess execution, and phase transitions.
- `tools/target0/verify_qualification_campaign.py` owns the fresh-process
  verification CLI and emits only a compact accepted digest record.
- `schemas/target0-qualification-campaign-v1.schema.json` owns the accepted
  campaign-manifest shape.
- `tools/target0/measurement_session.sh` remains the sole owner of temporary
  CPU-control application and restoration.

The campaign code imports existing bundle and capture validators rather than
copying their contracts.
It does not add a general benchmark framework.

## Operator interface

The read-only preflight interface is:

```text
python3 tools/target0/run_qualification_campaign.py preflight
  --repository-root PATH
  --expected-commit FULL_SHA
  --bundle-directory PATH
  --bundle-schema PATH
  --campaign-schema PATH
  --process-schema PATH
  --toolchain-lock PATH
  --campaign-id ID
  --campaign-number 1
  --target-user NAME
  --output-directory /var/tmp/xoas-target0-qualification-campaign.ATTEMPT
  --exclusive-use-confirmed
```

Preflight requires every option.
It creates only the new evidence root and read-only observation records.
It performs no governor, EPP, boost, sibling, service, or affinity mutation.
The target username is used only for live eligibility checks and is never
serialized.

The controlled execution interface is:

```text
sudo -n /usr/bin/python3 tools/target0/run_qualification_campaign.py run
  --repository-root PATH
  --campaign-directory PATH
  --target-user NAME
```

`run` requires effective UID zero and a real non-root target user.
It accepts no implicit repository, campaign root, or target user.
It refuses a campaign root that lacks an accepted preflight, contains a
rejection or acceptance marker, contains process output, or differs from the
current exact identities.

## Preflight contract

Preflight must complete all of the following before host controls are eligible:

1. Verify the finalized qualification bundle against its closed schema.
2. Recompute the repository commit, tree, clean state, and public remote.
3. Validate the installed Target 0 toolchain lock and stable configuration
   digest.
4. Recompute compiler and linker identities using the deployment validators.
5. Rehash the fixed source set and require exact equality with the accepted
   bundle manifest.
6. Rehash the accepted executable and require the acceptance digest.
7. Produce a fresh validated campaign-phase host capture.
8. Require bare metal, TSC, cycles, instructions, one-minute load below `0.5`,
   no active thermal alarm, and no unexpected interactive session.
9. Require the explicit exclusive-use confirmation.
10. Observe interrupts for exactly 60 seconds and apply the locked selector.
11. Publish canonical `preflight.json` and `core-selection.json` without
    replacement.

The retained preflight records contain only aggregate session eligibility.
They do not contain usernames, session identifiers, terminals, hosts,
addresses, or command lines.

## Exact identity snapshot

The identity snapshot is recomputed before every primary process and before
every PMU process.
It contains:

- accepted bundle ID and manifest, inventory, executable, and normalized
  executable-identity SHA-256 values;
- expected and actual full Git commit, tree object, clean state, and public
  remote;
- provisioning lock ID, lock-file SHA-256, and configuration SHA-256;
- compiler direct path, resolved path, version, target triple, package, and
  SHA-256;
- linker direct path, resolved path, version, package, and SHA-256;
- the bytewise-sorted fixed source paths and SHA-256 values;
- the SHA-256 of the current boot ID;
- the selected logical CPU and SMT sibling.

The runner compares canonical identity bytes with the accepted preflight
identity.
Any difference rejects the whole campaign before another session begins.

Adding campaign code changes the fixed source set.
Therefore implementation invalidates the currently accepted bundle and
requires a new exact-commit physical dual build and cross-host replica
verification before live preflight.

## Deterministic process contract

The campaign identifier is an ASCII token matching
`^[a-z0-9][a-z0-9._-]{0,95}$`.
Campaign numbers are `1` or `2`.
Primary process indexes are one through five.

Each seed is derived as follows:

```text
material = UTF-8("xoas.target0-qualification-seed.v1\0")
         || UTF-8(campaign_id)
         || UTF-8("\0")
         || ASCII(decimal_process_index)
seed = unsigned_big_endian(first_8_bytes(SHA-256(material)))
```

The runner invokes the accepted probe with exactly:

```text
--cpu SELECTED_CPU
--warmup-rounds 5
--rounds 30
--iterations 16777216
--seed DERIVED_UINT64
--output NEW_PROCESS_RECORD
```

Each primary process runs inside a fresh ordinary measurement session.
The selected SMT sibling must be online before every session and must be
restored online afterward.
The selected CPU governor and EPP must restore byte-for-byte to their captured
pre-state.
Boost is observed but not changed and must remain unchanged.

## Primary-process acceptance

The runner validates each process record against
`target0-host-qualification-v1.schema.json` and then applies these checks:

- exactly five warm-up rounds are declared;
- exactly 30 retained samples exist in round order;
- every elapsed sample is from `20,000,000` through `200,000,000` nanoseconds,
  inclusive;
- every observed start and end CPU equals the selected CPU;
- the affinity set contains only the selected CPU;
- `max_observed_threads` is exactly one;
- process status is `passed` and failure reasons are empty;
- every checksum matches the probe contract and the process checksum is valid;
- the restoration record reports exact restoration and command status zero;
- before and after captures retain the same boot and load-bearing host
  identity;
- no captured thermal alarm or objective throttling failure occurs.

The five primary processes execute in ascending index order.
There is no retry or replacement for an invalid process.

## Statistical definitions

All statistics use integer elapsed nanoseconds from the retained process
record.
No sample is removed or winsorized.

For each process:

- `median_ns` is the ordinary median; with 30 values it is the arithmetic mean
  of the two central ordered values and may therefore be a half-integer.
- `mad_ns` is the median of the 30 absolute deviations from `median_ns`.
- `mad_ratio` is `mad_ns / median_ns`.
- `p99_ns` uses the conservative empirical nearest-rank definition:
  ordered value at rank `ceil(0.99 * n)`, indexed from one.
  With 30 samples this is the maximum retained value.
- `p99_ratio` is `p99_ns / median_ns`.

Accepted JSON serializes medians and MAD values as exact numerator and
denominator integer pairs and ratios as decimal strings rounded once to 12
digits after the decimal point using round-half-even.
Acceptance comparisons use exact rational arithmetic before serialization.

Campaign one passes primary noise acceptance only when:

- all five processes are valid;
- all five `mad_ratio` values are at most `0.010`;
- at least four `mad_ratio` values are at most `0.005`;
- all five `p99_ratio` values are at most `1.02`;
- no process migrated, added a thread, failed restoration, or triggered a
  thermal/throttling objective failure.

## Privileged PMU boundary

The measurement-session controller gains an explicit execution mode with two
values:

- `probe`, the existing behavior and default, runs the supplied command as the
  non-root target user in the closed environment;
- `privileged-perf`, runs the fixed `/usr/bin/perf stat` frontend as root but
  constructs the measured child as `runuser` to the same non-root target user.

The privileged mode does not accept a root wrapper command.
It accepts only:

- one previously nonexistent perf-output file;
- an event list drawn from the closed campaign allowlist;
- the ordinary probe argument array that is demoted before execution.

It uses delimiter `;`, disables locale-dependent number grouping, and writes
the raw `perf stat` record directly to the requested evidence file.
The session controller still owns all apply, signal, and restoration behavior.

The required PMU session contains `cycles,instructions` together.
Both events must be supported and report 100 percent running time.
A missing, malformed, unsupported, or multiplex-scaled required event rejects
the campaign.

Optional events are:

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

Each optional event runs in its own fresh session, so optional-event
multiplexing cannot be hidden by grouping.
Unsupported optional events are retained with status `unsupported` and no
substitute or estimate.
A supported optional event must have a parseable raw count and 100 percent
running time.

PMU process records, restoration records, and raw `perf` output are retained.
Their elapsed samples are not part of the five-process noise statistics.

## Evidence layout

Every attempt root is a previously nonexistent immediate child of `/var/tmp`
whose basename begins with `xoas-target0-qualification-campaign.`.
It may not be a symlink, checkout, home directory, install prefix, accepted
qualification bundle, or ancestor of those paths.

An accepted root has this logical layout:

```text
preflight.json
core-selection.json
process-01/identity-before.json
process-01/host-before.json
process-01/process.json
process-01/restoration.json
process-01/host-after.json
...
process-05/...
pmu/required/...
pmu/optional-branches/...
...
inventory.json
campaign.json
acceptance.json
```

The raw-evidence inventory contains every retained regular file except
`inventory.json`, `campaign.json`, `acceptance.json`, and `rejection.json`.
It lists bytewise-sorted relative paths, sizes, and SHA-256 values.
The campaign manifest binds the inventory SHA-256 and every process/PMU
summary.
The acceptance record binds the manifest, inventory, expected commit, boot,
and selected CPU identities.

The canonical `campaign.json` is the compact repository receipt copied to
`benchmarks/evidence/target0-amd-ryzen9-7900x-v1/campaign-01.json`.
It contains external raw-evidence digests but no private storage path.
The adjacent `.sha256` file hashes the canonical receipt bytes.

Every JSON file uses UTF-8, sorted keys, compact separators, no NaN or
Infinity, and one terminal newline.
Files are created with exclusive semantics, flushed before publication, and
never replaced.

## Failure and rejection

Every precondition and validation fails closed.
Once a safe attempt root exists, a failure writes one canonical
`rejection.json` last when restoration state is known.
The rejection record contains a closed reason code, phase, command status when
available, and the relative paths and digests of retained diagnostics.
It cannot contain arbitrary exception text, command output, private paths, or
access information.

The closed rejection reasons include:

- unsafe output root;
- preflight identity mismatch;
- bundle verification failure;
- exclusive-use failure;
- load failure;
- unexpected session failure;
- thermal precondition failure;
- core-selection failure;
- per-process identity drift;
- process execution or schema failure;
- sample-bound or migration failure;
- restoration failure;
- required PMU failure;
- campaign threshold failure;
- evidence inventory or schema failure;
- unexpected internal failure.

A restoration failure always dominates the operator-visible exit status.
No rejected root is retried or converted to an accepted root.
Cleanup is never automatic.

## Independent verification

The fresh verifier accepts only:

```text
python3 tools/target0/verify_qualification_campaign.py
  --campaign-directory PATH
  --campaign-schema PATH
  --process-schema PATH
  --bundle-schema PATH
```

It trusts no retained digest or status.
It revalidates the campaign schema, rehashes the raw inventory, validates every
host capture, process record, restoration record, identity record, and PMU
record, recomputes every statistic and decision, and verifies the acceptance
binding.
It emits only one compact accepted digest record on success and returns
nonzero without echoing private retained data on failure.

The verifier does not modify host controls, invoke the probe, invoke `perf`, or
contact the network.

## Testing and quality

Development-lane tests cover at least:

- CLI omissions, malformed identifiers, unsafe roots, and prior-output refusal;
- the hand-derived deterministic seed vectors;
- exact median, MAD, nearest-rank p99, rational comparisons, and decimal
  rendering;
- schema meta-validation, positive example validation, and closed-field
  rejection;
- accepted-bundle, repository, lock, compiler, linker, source, executable, and
  boot identity matching and drift;
- preflight load, exclusivity, session, thermal, and core-selector failure;
- five-process order and exact probe arguments;
- sample duration, migration, thread, checksum, restoration, and thermal
  failures;
- dedicated privileged-perf construction, target-user demotion, event
  allowlisting, output non-replacement, signal handling, and exact restoration;
- required counter support and unit scaling;
- optional supported, unsupported, and malformed counter outcomes;
- deterministic raw inventory, manifest, acceptance, and fresh verification;
- retained rejection records and absence of acceptance markers after failure;
- prohibition of credential, access, username, address, command-line, and
  private-path fields throughout retained JSON.

The exact implementation commit must pass the complete Debug and Release
quality aggregates plus isolated sanitizer gates on `gpu-2`.
The physical host then builds and verifies a fresh native bundle from that same
pushed commit before campaign preflight.

## Authority and stopping boundary

This design authorizes repository implementation, development verification,
fresh bundle preparation, accepted preflight, and campaign one after all
prerequisites pass.

It grants no authority to:

- reboot the physical host;
- run campaign two;
- qualify the host or close M0;
- alter the locked thresholds or numerical semantics;
- install packages or persistent services;
- remove evidence;
- claim kernel, product, or baseline performance.

After campaign one is retained and committed, work stops at Task 6 Step 1 and
requests explicit authority for exactly one controlled reboot.
