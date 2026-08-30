# Target 0 AMD Ryzen 9 7900X Candidate v1

**State:** `candidate_unqualified`

**Performance claim:** none

**Task 3 implementation:** `ee57ff5e4af01fecb11fffd985e376d636560434`

**Task 4 provisioning subject:** `16d698dd80cabee0a5b6b5046914edde4535464a`

**Task 4 evidence implementation:** `9d44f6431ebdaea60c796292e9da071f0f49522b`

**Qualification-tool implementation subject:**
`a312aa2bbbb403b31ffb67cf40200da063527a4f`

**Controlling plan:**
[`2026-08-29-amd-target0-host-qualification.md`](../superpowers/plans/2026-08-29-amd-target0-host-qualification.md)

## Qualification boundary

This physical x86-64 Linux machine is the designated Target 0 measurement
candidate. It is not yet a measurement authority. The candidate manifest is
[`target0-amd-ryzen9-7900x-v1.json`](../../benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json),
and the installed provisioning record is
[`target0-amd-ryzen9-7900x-v1.lock.json`](../../toolchains/target0-amd-ryzen9-7900x-v1.lock.json).

Task 4 installed and verified the exact support-package closure and the
AOCL-BLAS, OpenBLAS, and LIBXSMM source builds below
`/opt/xoas/target0-v1`. That closes baseline-stack provisioning only. It does
not provide independent numerical admission, a controlled measurement
session, noise characterization, a benchmark campaign, or any performance
claim. `target0_measurement_qualified` therefore remains false.

## Verified host boundary

The closed read-only capture at `2026-08-29T18:01:12Z` established:

- Ubuntu 26.04 `resolute`, kernel `7.0.0-30-generic`, glibc 2.43, and x86-64;
- bare metal with no detected virtualization boundary;
- AMD Ryzen 9 7900X, family 25, model 97, stepping 2, microcode `0xa60120c`;
- 24 online logical CPUs, 12 physical cores, one socket, one NUMA node, and
  symmetric two-thread SMT pairs;
- TSC as the current clocksource;
- available privileged `cycles` and `instructions` events;
- `amd-pstate-epp`, per-CPU preferred-core ranking, governor/EPP controls,
  boost state, `k10temp`, cache topology, interrupt counters, and load capture;
- non-interactive privileged command availability; and
- an absent `/opt/xoas/target0-v1` prefix before provisioning.

The closed capture SHA-256 is
`019376b74df12d12129dca2618d215dfcd32ad51cdb0ca06b51b19d0977c0106`.
Its producer is `capture_host.py` at fix commit
`b7371ae1bbc74f4c6482b8ca4422ba9b058cfabd`, with source SHA-256
`b94327e0865ac266a2b040f8887d510aa4138558d92d87c6ab8243d5df08ae7f`.
Access aliases, login identity, credentials, network coordinates, home paths,
and full command-line or environment data are not retained.

## Support-package installation

The pre-state contained 1,502 sorted package entries and no holds. The exact
nine-package request installed the simulated 26-package closure with zero
upgrades and zero removals. All 26 closure packages passed `dpkg -V`; the
post-state contains 1,528 package entries and no holds.

| Evidence | SHA-256 |
|---|---|
| Package pre-state | `c84618dd993eb7daf56218d4e0b631385cab4409814f8e576498bac33e387c09` |
| Exact install simulation | `1fdb67a6407584d214e7e571f22752b686bfd738f9e6e39a6f93f661251d29bf` |
| Redacted APT install history | `e922840e5e69cc23de0589bec9eb9808c9aa76ffb543e87b2aa2584c1d7e4bc0` |
| Installed dpkg closure log | `bdcd9061011b95c4ce4d389e7d313bd094cdb4a822b0b214d96a4f0461be1cb3` |
| Package post-state | `160ebb0a03a71da3aabd3318c1f2bda7df96a3f7bfc53fbb758940dcd616ee07` |
| Package holds | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The installation added GNU Fortran 15.2.0, Doxygen 1.15.0, Graphviz 14.1.2,
ShellCheck 0.11.0, hwloc 2.13.0, lm-sensors 3.6.2, and the locked development
headers. GCC, G++, Clang, CMake, and Ninja executable hashes remained
unchanged. Package-managed `f77` and `f95` alternatives were added by the
GNU Fortran package; no compiler default alternative was changed manually.

## Verified baseline installations

Each source matched its locked commit, archive digest, and license identity
before build. The complete lock records all build commands and all 288 regular
installed-file hashes. Eleven installed symlinks were separately indexed.

| Baseline | Installed artifact | SHA-256 | Verification result |
|---|---|---|---|
| AOCL-BLAS 5.3.2 | `aocl-blas-5.3.2/lib/libblis.so.5.3.2` | `0670e0fcb11ddfd39304761aae957f78d1ed48c9bde0ea3dc8254febf2ce1381` | BLIS and BLAS suites passed; SGEMM checksum 415; Zen 4 dispatch; one effective thread |
| OpenBLAS 0.3.34 | `openblas-0.3.34/lib/libopenblas.so.0.3` | `8a2ab96cad5195422d4880eb42afcfb57d06a036a9178c3ea5b8bc3de06297c8` | 120/120 CTest cases passed; SGEMM checksum 415; one effective thread |
| LIBXSMM 2.1.0 | `libxsmm-2.1.0/lib/libxsmm.so.2.1.0` | `63e8fd17a5d5a759f5ee2058cf209e855aceff2857b14fbaa608bfdb95a92625` | full upstream suite passed; checksum 415; `cpx` JIT target; generated code; no worker thread |

AOCL-BLAS reported `zen4` dispatch and Genoa model classification. Its smoke
probe required GNU C17 plus a narrow `-Wno-unused-function` exception for an
upstream public-header static-inline warning; the exception was not applied to
XOAS source.

OpenBLAS reported runtime core name `Cooperlake`. This is the pinned upstream
source's feature-class selection for Zen 3/4 CPUs exposing AVX-512 BF16, not a
host-identity claim. The physical host identity remains the closed AMD capture.

The original LIBXSMM test invocation omitted `PREFIX`, causing generated
pkg-config metadata to reference its temporary source tree. The user approved
adding `PREFIX=/opt/xoas/target0-v1/libxsmm-2.1.0` to the build/test command.
A clean rebuild passed the upstream suite and installed metadata contains no
temporary path. The rejected test/install logs remain retained as failed
evidence rather than being discarded.

Explicit include, library, and RPATH probes loaded only the intended versioned
libraries. `LD_DEBUG=libs` showed no AOCL-BLAS/OpenBLAS cross-load. All three
pkg-config records resolve below the versioned prefix. No numerical-baseline
adapter has yet been compared with the independent oracle; that remains M2.

## Evidence identity and interruption boundary

The canonical lock configuration digest is
`810c21d5891b67e7aaccd4992318ad7dd86902070aa947baa817ef7ea5914de3`.
It is computed over canonical compact JSON with recursively sorted keys and
the `configuration_sha256` field omitted. The external Task 4 evidence bundle
is retained pending the repository artifact-store policy with SHA-256
`6cb7936cd8399158dfec83be898dced8319027c881260f05dfe6fb157b931dd4`.
The bundle is not committed as an ungoverned binary artifact.

An administrator-initiated reboot interrupted provisioning after the support
packages and source prefix had been installed. The boot-identity digest changed
from `3bba7d5411d8d3d1bb89570516512aaa0e038e74eb67c76aa42ab334654141b9`
to `e30d0884ab780b4d7fc18787fc7f4bf55132119a9762d34f0ef489211c2b3dea`.
Volatile temporary logs were lost; package-manager history and persistent
source/build evidence were recovered, rechecked, and re-indexed. This event was
not executed by the qualification session controller, was not an approved
campaign boundary, and does not satisfy either campaign or reboot gate.

The system Python remains 3.14.4. On 2026-08-30, the user explicitly approved
an isolated XOAS quality-toolchain supplement: Python 3.12.3, Doxygen 1.9.8,
and ShellCheck 0.9.0 below `/opt/xoas/development`, with only a versioned
`python3.12` link and no system-tool replacement. At clean `main` commit
`93f164cb6caedc6d4da8eca7315ccba9d9c80506`, the host passed both complete
50-test Debug and Release quality aggregates, explicit 50/50 replays for each,
and the final 3/3 sanitizer replay. Exact provenance and executable digests are
recorded in
[`../adr/IDR-0004-wineth-quality-toolchain.md`](../adr/IDR-0004-wineth-quality-toolchain.md).
This closes the physical-host repository-quality gap without changing native
artifact authority, measurement qualification, campaign, reboot, or
performance state.

## Qualification-tool deployment state

Repository code now implements the closed native preparation and independent
replica-verification interfaces. It validates the exact clean checkout before
creating a private `/var/tmp/xoas-target0-qualification-tools.ATTEMPT` root,
validates locked compiler/linker/target identities, builds the probe twice,
requires byte equality, inspects the ELF/runtime closure, runs the interpreted
and native compatibility suite, and publishes write-once acceptance or, after
a safe staging root exists, closed rejection evidence.

Exact implementation subject `a312aa2bbbb403b31ffb67cf40200da063527a4f`
passed 38/38 Debug tests, 38/38 Release tests, 3/3 isolated sanitizer tests,
repository policy, formatting, documentation, and Clang-Tidy on a clean
`gpu-2` checkout. A clean physical checkout at tree
`b7279b22e40c848da7aecd7f3e4197a6857aa85f` produced the accepted bundle
`target0-qualification-tools-a312aa2bbbb403b3`: both native builds were
byte-identical and all five compatibility checks passed.

Fresh physical and `gpu-2` verifiers matched bundle-manifest SHA-256
`0d62ab0c143fa224d31e4cde925e4c30a5a512c5cd391c4d8cd030b6608572ff`,
inventory SHA-256
`4ead541d5c43be871833509a561fb4c170ec83d0f297343f8dd6e78058407b20`,
executable SHA-256
`2b2352baf105ccb2b2ef3a1bb89046fc7a8259224f0c928747f473d11e215b8f`,
and normalized executable-identity SHA-256
`a976d18ae90df3d008749683592f9cc7663b7e94d667d5e3eb78654344b2ad25`.
The canonical non-secret receipt is
[`../../benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json`](../../benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json).
The accepted bundles remain external private evidence roots; Git contains no
ELF executable, raw log, access metadata, network coordinate, or external
evidence-root path.

## Campaign-one rejected attempt

On 2026-08-30, the accepted replacement bundle and read-only preflight were
used for campaign-one attempt 1 at exact source commit
`1141713c3448eaaa392e09ace8924ebcaf0e38bd` and tree
`c8f17838c6bb54ae278fd4d1e06b0f64d21493ad`. The preflight selected logical
CPU 2 and SMT sibling 14 after a 60-second interrupt observation. It accepted
bare metal, TSC, cycles/instructions availability, one-minute load `0.12`,
three expected and zero unexpected/root sessions, and zero thermal alarms,
faults, or threshold violations. Its canonical SHA-256 is
`c36ab9293eb622e17ee4e6869d12a8ce49a9994340203e6594dbb760b44a8abb`;
the core-selection SHA-256 is
`200b5f84aab4d32e097982f27b1e89b0cd7b5b4e3b4ccd54363645c197a36ed1`.

The first primary probe completed with command status 0 and retained 30 valid
samples, but the session controller returned restoration exit 70. Sibling
online state, governor, and boost matched pre-state; CPU 2 EPP remained
`performance` instead of `balance_performance`. The write-once rejection has
reason `restoration_failure`, phase `primary`, and SHA-256
`e6458e2dac1097fa5649371c0815403708c7985da0b80d2ebf5c8b049efc5868`.
The restoration record SHA-256 is
`415d0e134e1ddef8a3106709cf43b44b2977aa78c6bdaf7fd2ed04aa97fc8086`.
It binds 11 diagnostic files; no PMU, campaign manifest, inventory, acceptance,
qualification, or performance record exists.

The controller restores EPP before restoring the governor. On this
`amd-pstate-epp` host, the subsequent governor transition left EPP at
`performance`. A bounded recovery wrote only CPU 2 EPP back to its recorded
pre-state. Independent post-recovery capture matched the accepted sibling 1,
governor `powersave`, EPP `balance_performance`, boost 1, normalized boot-ID
SHA-256 `20da156151d62d87c68308e4bf82f1469c0db20c713a4178a0623bcc6d2beb8c`,
clean checkout, toolchain, source, bundle, and stable host identity. The public
fresh verifier rejected the root as required. The root is retained externally
and will not be retried or rewritten.

This is a terminal rejected qualification attempt, not a performance result.
No `perf` phase, controlled reboot, target qualification, or performance claim
occurred. The earlier rejected `bc800ff` build attempt also remains retained
as non-claiming failure evidence.

## Restoration-only repair proof and fresh physical bundle

On 2026-08-30, the repaired session controller was exercised once on this
physical host at clean merged source
`a396f642d5c2ec6ed670cc2341170ec7d9f1a886`. This was a bounded
restoration-only cycle around `/usr/bin/true`, not preflight or a qualification
campaign. CPU 2 and SMT sibling 14 restored to sibling online 1, governor
`powersave`, EPP `balance_performance`, and boost 1. The controller returned 0,
the canonical record reported `restored=true` with no failure reasons, and an
independent live audit matched every controlled sysfs value. The externally
retained restoration-record SHA-256 is
`5b6e2cefbac4c8c96f5228139978f776d55aff0dcffb9dc9fb19812cb50236e7`.

The same clean source produced physical-native qualification bundle
`target0-qualification-tools-a396f642d5c2ec6e`. Both preparation and a fresh
physical verifier accepted it. Its authoritative candidate digests are:

- bundle manifest:
  `15d58e20bbab593bd902782b917b79ba98a03cf1e79c784fbff2c450d23a99a0`;
- inventory:
  `44d6ee1eec9791974098ce74c81647d1690bd0aef2bd54822e47635ebad1bbaf`;
- executable:
  `db82cd647e880b1780c2a5fb9d10f87398b184f35d4e84de9b6855db07fec015`;
- normalized executable identity:
  `753890dc53185727326bc5dba2585a59ed60bdf0465623dec3fb58bf63b388b3`.

This closes physical restoration validation and the physical-native half of
fresh deployment only. IDR-0002 still requires the complete bundle to be
copied byte-for-byte to `gpu-2` and independently verified in a clean checkout
at the same source. No such replica, replacement preflight, new campaign, PMU
collection, reboot, qualification decision, or performance claim exists.

## Deferred comparator boundaries

The pinned JITSpMM tree contains no license or copyright statement. XOAS does
not infer permission and does not build or use that source. Its adapter and use
remain deferred to M2 pending license resolution.

Intel oneMKL remains
`not_installed_pending_M2_applicability_review`. That state does not assert
inapplicability and does not remove oneMKL from the admitted policy.

## Remaining qualification gates

The candidate remains unqualified until all applicable gates close:

1. resolve the open M0/M2 dependency for independent numerical admission of
   every applicable baseline adapter;
2. copy the accepted physical bundle at exact source `a396f64` byte-for-byte to
   `gpu-2` and pass a fresh independent verifier there;
3. pass a new read-only preflight and a separately authorized campaign-one
   attempt from a new immutable root;
4. pass non-claiming smoke, PMU, and noise characterization;
5. obtain separate approval for the exact controlled reboot action only after
   campaign one is accepted;
6. complete campaign two under a distinct controlled boot identity;
7. reconcile both campaigns and complete the accepted review model.

No final compatibility digest is computed here. M1 owns the versioned
canonical binary identity.

## Rollback boundary

The verified installation remains active at `/opt/xoas/target0-v1`. Rollback
was not executed, so no actual quarantine path exists. If a later reviewed
rollback is authorized, it quarantines the complete prefix to the timestamped
sibling path recorded in the lock. Package removal remains prohibited without
a separate administrator review.
