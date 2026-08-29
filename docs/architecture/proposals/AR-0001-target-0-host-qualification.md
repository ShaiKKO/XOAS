# AR-0001: Target 0 Host Qualification

**Status:** Primary development role approved; Target 0 measurement decision required

**Decision owner:** User / architecture authority

**Prepared:** 2026-08-28

## Requested decision

The user confirmed on 2026-08-28 that `gpu-2` is XOAS's primary development environment.
No alternative server is currently designated; an AMD desktop may be evaluated later.
That development role is approved and no longer part of the open decision.

The remaining decision is whether the `gpu-2` OpenStack/KVM server should:

1. be conditionally qualified as the sole Target 0 measurement host after all controls below close;
2. remain the primary development host while XOAS acquires or designates a more controllable Target 0 measurement host; or
3. become the measurement host under a deliberately narrower VM-specific claim that accepts unavailable controls and counters.

The recommendation is **Option 2 now**. Keep `gpu-2` as the primary development host, do not bind performance claims or cache compatibility to it as a qualified Target 0, and seek a controlled x86-64 measurement environment. If the current provider can expose the required PMU, isolation, reboot identity, and host-stability controls, reconsider Option 1 through an evidence update to this proposal before acquiring another host.

## Affected specifications, interfaces, and milestones

- Build plan section 2.1, one exact Target 0 machine and hardware fingerprint.
- Build plan section 3.3, measurement-quality gate.
- Build plan section 11.1, target environment and repeatability.
- Build plan section 11.2, minimum cycles and instructions metrics.
- Build plan M0, baseline availability and reference target manifest.
- Future Problem IR target identity, plan/cache identity, artifact compatibility, benchmark result schema, and baseline dispatch.
- M0 exit gate and all later performance gates.

No public ABI or executable artifact exists yet.

## Evidence motivating the decision

The read-only capture at `2026-08-28T23:01:51Z` is recorded in [`../../../benchmarks/manifests/target-gpu-2-candidate.json`](../../../benchmarks/manifests/target-gpu-2-candidate.json).

### Evidence supporting candidacy

- Ubuntu 24.04.4 LTS, x86-64, one NUMA node.
- Intel Xeon Gold 6348 guest CPU identity, family 6/model 106/stepping 6.
- Eight reported cores with two hardware threads each.
- AVX2, FMA, and broad AVX-512 features exposed.
- TSC is the current clocksource and `constant_tsc`, `nonstop_tsc`, and `tsc_known_freq` are exposed.
- Adequate memory and storage were observed during discovery.
- SSH development access has been verified repeatedly.

### Evidence blocking qualification

- The guest is a KVM/OpenStack VM. Physical-host identity, exclusivity, overcommit, and live-migration policy are unavailable to the guest.
- SMT is active, no CPUs are isolated, and no measurement core/sibling policy has been established.
- The guest has no cpufreq or intel_pstate interface. Governor, turbo, power-limit, and thermal controls are unavailable.
- `kernel.perf_event_paranoid=4`; unprivileged `task-clock` and `cycles` measurements are unavailable. The build plan currently requires cycles and instructions at minimum.
- Reboot persistence of CPU identity, topology, timer behavior, and cloud placement has not been measured.
- Process- and reboot-level timing noise has not been characterized under the locked protocol.
- No C/C++ compiler, CMake, Ninja, baseline BLAS library, LIBXSMM, or local benchmark checkout is installed.

The PMU issue is a direct specification conflict, not an optional enhancement. Silently waiving it would change the approved measurement gate.

## Alternatives considered

### Option 1: Conditionally qualify `gpu-2`

Required before approval:

- provider or administrator establishes an exclusive-use/no-migration window or an equivalently enforceable VM-placement contract;
- a physical core and SMT-sibling policy is enforced and verified;
- cycles and instructions become trustworthy and available, including event/version provenance;
- frequency/turbo/power/thermal state becomes observable or the architecture authority explicitly accepts bounded limitations without removing the minimum counter requirement;
- two reboot-separated qualification campaigns reproduce CPU, topology, ISA, clocksource, kernel, and timer behavior;
- toolchain and baseline libraries are provisioned with pinned versions and hashes;
- timing noise meets the v1 protocol's practical floor and sample design.

**Advantages:** uses the existing server; its Intel ISA envelope fits Target 0; development and measurement share one environment.

**Disadvantages:** qualification depends on controls outside the guest; a cloud migration could invalidate artifacts and evidence; the current PMU gate fails.

### Option 2: Development host only; designate a controlled measurement host

Requirements for the new host remain the same Target 0 contract, but hardware ownership or a controlled dedicated VM should expose PMU, core/SMT, frequency, reboot, and exclusivity evidence.

**Advantages:** preserves the approved measurement gate and produces stronger reproducibility and compatibility evidence.

**Disadvantages:** additional infrastructure, provisioning, and integration cost; compiler development remains separate from final measurements.

### Option 3: Accept `gpu-2` with a narrower VM claim

This option would identify the target as the observed VM fingerprint, use wall time as the primary metric, disclose unavailable controls, and increase repeated-process/reboot sampling. It still cannot satisfy the current “cycles and instructions at minimum” text.

**Advantages:** fastest route to early signal on the available server.

**Disadvantages:** requires an approved architecture change to the measurement gate; weaker causal evidence; provider migration may invalidate results; not recommended as the default research claim.

## Recommended option

Approve Option 2 for M0: `gpu-2` is the primary development host but not the Target 0 measurement host. In parallel, ask the provider whether Option 1 controls can be supplied. If they can, update the evidence and request approval to promote `gpu-2`; if they cannot, designate a controlled x86-64 host and capture a new reference manifest.

Do not change the CPU-only Target 0 scope. The visible NVIDIA L4 is irrelevant to this decision.

## Correctness and numerical impact

The target choice does not change matrix semantics or the `strict`/`contracted` numerical definitions. It affects whether compiler flags, FMA/ISA features, subnormal environment, special-value behavior, and target compatibility can be verified reproducibly.

No numerical mode may be weakened to make a baseline or host applicable.

## ABI, identity, cache, artifact, and migration impact

- A candidate target manifest must never satisfy a runtime plan compatibility check.
- M1 canonical identity must distinguish candidate, qualified, and invalidated target records.
- Target identity must include CPU/ISA/OS/ABI facts required by the approved target contract, not the hostname alone.
- A changed CPU model/stepping, ISA exposure, kernel/ABI requirement, compiler rule, or accepted target-control contract invalidates affected plans and benchmark evidence.
- Because no executable artifacts exist, moving to another measurement host has no current artifact migration cost.
- Development artifacts built on `gpu-2` may be correctness aids but cannot become winning cached plans without qualification and target-bound rebuilding/verification.

## Benchmark and performance-gate impact

Under the recommendation:

- no Target 0 performance, proof-gate, product-class, or break-even claim may cite `gpu-2` measurements as gate evidence;
- smoke measurements may later diagnose harness behavior when clearly labeled non-claiming;
- baseline availability remains open until the selected measurement host has exact pinned libraries;
- the target manifest required by M0 is not locked, so M0 remains open;
- no research threshold or sampling rule changes.

## Work blocked by the decision

- M0 gate closure and its exact reference-target statement.
- M1 start under the build plan's “no compiler implementation before M0” dependency.
- Baseline installation/qualification as reference-machine evidence.
- Any generated-kernel performance claim, cache compatibility decision, or break-even report.

## Work that can continue independently

- Review and correct M0 charter, prior-art, baseline, corpus, schema, and protocol documents.
- Obtain the user's remaining measurement-role decision on this proposal.
- Collect provider facts about PMU access, VM exclusivity, migration, and reboot persistence.
- Prepare a separately reviewed, reversible provisioning plan for the selected host.
- Verify external source artifacts and JSON/document consistency.

Product compiler scaffolding does not continue independently because the approved milestone order makes M0 a prerequisite.

## Qualification evidence required after approval

Whichever host is selected must produce a versioned manifest and acceptance record containing:

1. two reboot-separated non-secret hardware/OS/ISA/topology captures with stable identity;
2. selected core, sibling, NUMA, affinity, exclusivity, and interference policy;
3. frequency/turbo/power/thermal facts and accepted limitations;
4. timer-overhead, timer-stability, process-noise, and reboot-noise characterization;
5. working cycles and instructions evidence under the approved PMU policy;
6. exact compiler, linker, C++ library, OpenBLAS, oneMKL, LIBXSMM, and comparator identities as applicable;
7. clean XOAS checkout and exact commit;
8. benchmark smoke result explicitly marked non-claiming;
9. review and approval that the manifest is the sole Target 0 compatibility authority.

## Decision record

On 2026-08-28, the user explicitly designated `gpu-2` as the primary development environment and stated that no alternative server is currently available, while noting that an AMD desktop could be considered later.

This approves the development role only.
It does not qualify `gpu-2` for Target 0 measurements, waive any blocker above, or select Options 1, 2, or 3 for performance-gate evidence.
The measurement-role decision remains open and must be recorded explicitly with its exact commit.
